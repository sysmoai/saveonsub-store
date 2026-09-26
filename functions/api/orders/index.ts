interface Env {
  DB: D1Database;
  ORDER_NOTIFICATION_WEBHOOK?: string;
}

type CreateOrderItem = {
  product_id: string;
  plan_id: string;
  quantity: number;
};

type CreateOrderBody = {
  idempotency_key: string;
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

// This branch intentionally uses a tiny governed snapshot.
// Production must generate this file from the canonical catalog/policy build,
// never maintain prices by hand in the API.
import { resolveGovernedPlan } from "../../../lib/order-os/catalog-policy";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });

const nowIso = () => new Date().toISOString();

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
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
  if (!env.DB) return json({ error: "ORDER_BACKEND_NOT_CONFIGURED" }, 503);

  let body: CreateOrderBody;
  try {
    body = await request.json<CreateOrderBody>();
  } catch {
    return json({ error: "INVALID_JSON" }, 400);
  }

  if (!body?.idempotency_key || body.idempotency_key.length < 16 || body.idempotency_key.length > 128) {
    return json({ error: "INVALID_IDEMPOTENCY_KEY" }, 400);
  }
  if (!Array.isArray(body.items) || body.items.length < 1 || body.items.length > 20) {
    return json({ error: "INVALID_ITEMS" }, 400);
  }

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
    if (!governed) return json({ error: "UNKNOWN_OR_UNAVAILABLE_PLAN", product_id: item.product_id, plan_id: item.plan_id }, 409);
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
      VALUES (?, ?, ?, ?, 'payment_review', 1, ?, ?, 'BDT', ?, ?, ?, ?, ?, 'website', ?, ?)`)
      .bind(
        internalId, orderId, trackingHash, body.idempotency_key,
        body.payment_method || null, body.payment_reference || null, totalMinor,
        body.customer?.name || null, body.customer?.phone || null,
        body.customer?.email || null, body.customer?.locale || null, now, now
      ),
    env.DB.prepare(`INSERT INTO order_events
      (order_id, event_type, actor_type, payload_json, created_at)
      VALUES (?, 'order_submitted', 'customer', ?, ?)`)
      .bind(internalId, JSON.stringify({ item_count: resolved.length, payment_method: body.payment_method || null }), now),
    env.DB.prepare(`INSERT INTO notification_outbox
      (order_id, channel, destination_key, template_key, payload_json, priority,
       status, attempt_count, next_attempt_at, created_at, updated_at)
      VALUES (?, 'webhook', 'ops-primary', 'new_order_priority', ?, 1, 'pending', 0, ?, ?, ?)`)
      .bind(internalId, JSON.stringify({ order_id: orderId, total_minor: totalMinor }), now, now, now),
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
    next_action: "A human operator must verify payment before fulfillment.",
  }, 201);
};
