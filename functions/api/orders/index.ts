interface Env {
  DB: D1Database;
  TURNSTILE_SECRET_KEY?: string;
}

type CreateOrderItem = {
  product_id: string;
  plan_id: string;
  quantity: number;
};

type CreateOrderBody = {
  idempotency_key: string;
  turnstile_token: string;
  payment_method?: string;
  payment_reference?: string;
  customer?: {
    name?: string;
    phone?: string;
    email?: string;
    locale?: string;
  };
  items: CreateOrderItem[];
};

// Plans resolve only from the governed public catalog (catalog.json). While the
// EXEC-010 HOLD is active every product is request_price, so every order is 409.
import { resolveGovernedPlan } from "../../lib/order-os/catalog-policy";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });

const nowIso = () => new Date().toISOString();

// Customer-supplied free text is shown to staff; bound its type and length at
// the door so the queue cannot be flooded or carry oversized payloads.
const text = (value: unknown, max: number): string | null =>
  typeof value === "string" && value.trim() ? value.trim().slice(0, max) : null;

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

async function verifyTurnstile(token: string, secret: string, ip?: string | null) {
  const form = new FormData();
  form.set("secret", secret);
  form.set("response", token);
  if (ip) form.set("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: form,
  });
  if (!r.ok) return false;
  const data = await r.json<{ success?: boolean }>();
  return data.success === true;
}

function publicOrderId() {
  const d = new Date();
  const yy = String(d.getUTCFullYear()).slice(2);
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const rand = crypto.getRandomValues(new Uint32Array(1))[0].toString(36).slice(-5).toUpperCase();
  return `SOS-${yy}${mm}${dd}-${rand}`;
}

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  // Fail closed: production must explicitly bind the database and anti-abuse secret.
  if (!env.DB || !env.TURNSTILE_SECRET_KEY) {
    return json({ error: "ORDER_BACKEND_NOT_CONFIGURED" }, 503);
  }

  let body: CreateOrderBody;
  try {
    body = await request.json<CreateOrderBody>();
  } catch {
    return json({ error: "INVALID_JSON" }, 400);
  }

  if (!body?.turnstile_token) return json({ error: "BOT_CHECK_REQUIRED" }, 400);
  const botOk = await verifyTurnstile(
    body.turnstile_token,
    env.TURNSTILE_SECRET_KEY,
    request.headers.get("CF-Connecting-IP")
  );
  if (!botOk) return json({ error: "BOT_CHECK_FAILED" }, 403);

  if (!body?.idempotency_key || body.idempotency_key.length < 16 || body.idempotency_key.length > 128) {
    return json({ error: "INVALID_IDEMPOTENCY_KEY" }, 400);
  }
  if (!Array.isArray(body.items) || body.items.length < 1 || body.items.length > 20) {
    return json({ error: "INVALID_ITEMS" }, 400);
  }

  const customerName = text(body.customer?.name, 100);
  const customerPhone = text(body.customer?.phone, 30);
  const customerEmail = text(body.customer?.email, 254);
  const customerLocale = text(body.customer?.locale, 10);
  // These are payment instructions, never an API-confirmed payment.
  const rawPaymentMethod = (text(body.payment_method, 30) || "").toLowerCase().replace(/[\\s-]+/g, "_");
  const paymentMethod = rawPaymentMethod === "bank" ? "bank_transfer" : rawPaymentMethod;
  if (!["bkash", "nagad", "rocket", "bank_transfer"].includes(paymentMethod)) {
    return json({ error: "UNSUPPORTED_PAYMENT_METHOD" }, 400);
  }
  const paymentReference = text(body.payment_reference, 64);

  const existing = await env.DB.prepare(
    "SELECT public_order_id, status FROM orders WHERE idempotency_key = ?"
  ).bind(body.idempotency_key).first<{ public_order_id: string; status: string }>();
  if (existing) return json({ ok: true, duplicate: true, order_id: existing.public_order_id, status: existing.status });

  const resolved = [];
  let totalMinor = 0;
  for (const item of body.items) {
    if (!item?.product_id || !item?.plan_id || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 20) {
      return json({ error: "INVALID_ITEM" }, 400);
    }
    const governed = resolveGovernedPlan(item.product_id, item.plan_id);
    if (!governed) {
      return json(
        { error: "UNKNOWN_OR_UNAVAILABLE_PLAN", product_id: item.product_id, plan_id: item.plan_id },
        409
      );
    }
    totalMinor += governed.price_bdt * 100 * item.quantity;
    resolved.push({ ...governed, quantity: item.quantity });
  }

  const internalId = crypto.randomUUID();
  const orderId = publicOrderId();
  const trackingToken = crypto.randomUUID() + crypto.randomUUID();
  const trackingHash = await sha256Hex(trackingToken);
  const now = nowIso();

  const statements = [
    env.DB.prepare(`INSERT INTO orders
      (id, public_order_id, tracking_token_hash, idempotency_key, status, priority,
       payment_method, payment_reference, currency, total_minor,
       customer_name, customer_phone, customer_email, customer_locale,
       source, created_at, updated_at)
      VALUES (?, ?, ?, ?, 'payment_review', 3, ?, ?, 'BDT', ?, ?, ?, ?, ?, 'website', ?, ?)`)
      .bind(
        internalId, orderId, trackingHash, body.idempotency_key,
        paymentMethod, paymentReference, totalMinor,
        customerName, customerPhone, customerEmail, customerLocale, now, now
      ),
    env.DB.prepare(`INSERT INTO order_events
      (order_id, event_type, actor_type, payload_json, created_at)
      VALUES (?, 'order_submitted', 'customer', ?, ?)`)
      .bind(internalId, JSON.stringify({ item_count: resolved.length, payment_method: paymentMethod }), now)
  ];

  for (const item of resolved) {
    statements.push(
      env.DB.prepare(`INSERT INTO order_items
        (order_id, product_id, plan_id, product_name_snapshot, plan_name_snapshot,
         unit_price_minor, quantity, access_type_snapshot, support_terms_snapshot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
        .bind(
          internalId, item.product_id, item.plan_id, item.product_name, item.plan_name,
          item.price_bdt * 100, item.quantity, item.access_type || null, item.support_terms || null
        )
    );
  }

  try {
    await env.DB.batch(statements);
  } catch (err) {
    console.error("order persistence failed", err);
    return json({ error: "ORDER_PERSISTENCE_FAILED" }, 503);
  }

  return json({
    ok: true,
    order_id: orderId,
    status: "payment_review",
    total_bdt: totalMinor / 100,
    tracking_token: trackingToken,
    staff_notification: "not_sent_unpaid",
    next_action: "Await recipient-account receipt verification before fulfillment. A submitted reference is not proof of payment.",
  }, 201);
};
