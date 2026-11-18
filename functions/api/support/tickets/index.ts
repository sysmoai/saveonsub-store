import { json, nowIso, readJson } from "../../../lib/order-os/http";
import {
  MAX_OPEN_TICKETS_PER_ORDER, NOT_FOUND_BODY, newAccessToken, newPublicTicketId, redactBody, sha256Hex,
} from "../../../lib/order-os/support-tickets";

interface Env { DB: D1Database; TURNSTILE_SECRET_KEY?: string }

async function verifyTurnstile(token: string, secret: string, ip?: string | null) {
  const form = new FormData();
  form.set("secret", secret);
  form.set("response", token);
  if (ip) form.set("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: form });
  if (!r.ok) return false;
  const data = (await r.json()) as { success?: boolean };
  return data.success === true;
}

// Create a ticket. The caller proves they own the order with its tracking token
// (the same secret /api/orders/track uses), so no account or contact lookup exists.
export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.DB) return json({ error: "SUPPORT_BACKEND_NOT_CONFIGURED" }, 503);
  if (!env.TURNSTILE_SECRET_KEY) return json({ error: "BOT_CHECK_NOT_CONFIGURED" }, 503);
  const body = await readJson(request, 8192);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  if (typeof body.turnstile_token !== "string" || !body.turnstile_token) return json({ error: "BOT_CHECK_REQUIRED" }, 400);
  if (!(await verifyTurnstile(body.turnstile_token, env.TURNSTILE_SECRET_KEY, request.headers.get("CF-Connecting-IP")))) {
    return json({ error: "BOT_CHECK_FAILED" }, 403);
  }

  const tracking = typeof body.tracking_token === "string" ? body.tracking_token : "";
  const message = redactBody(body.message);
  const subject = redactBody(body.subject).slice(0, 120) || null;
  if (!message) return json({ error: "MESSAGE_REQUIRED" }, 400);

  // Constant work for every outcome: hash first, then one lookup.
  const hash = await sha256Hex(tracking);
  const order = tracking.length >= 40 && tracking.length <= 200
    ? await env.DB.prepare("SELECT id FROM orders WHERE tracking_token_hash = ?").bind(hash).first<any>()
    : null;
  if (!order) return json(NOT_FOUND_BODY, 404);

  const open = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM support_threads WHERE order_id=? AND status IN ('open','waiting_customer','waiting_staff')"
  ).bind(order.id).first<any>();
  if ((open?.n ?? 0) >= MAX_OPEN_TICKETS_PER_ORDER) return json({ error: "TOO_MANY_OPEN_TICKETS" }, 429);

  const id = crypto.randomUUID();
  const publicId = newPublicTicketId();
  const token = newAccessToken();
  const ts = nowIso();
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO support_threads(id,order_id,status,priority,subject,public_ticket_id,access_token_hash,created_at,updated_at)
        VALUES (?,?,'waiting_staff',2,?,?,?,?,?)`).bind(id, order.id, subject, publicId, await sha256Hex(token), ts, ts),
      env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'customer',NULL,'customer_message',?,?)`).bind(id, message, ts),
    ]);
  } catch {
    console.error("ticket_write_failed");
    return json({ error: "WRITE_FAILED" }, 503);
  }
  // The access token is shown once. Only its hash is stored.
  return json({ ok: true, ticket_id: publicId, access_token: token }, 201);
};
