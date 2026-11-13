import { json, nowIso, readJson } from "../../../lib/order-os/http";
import { NOT_FOUND_BODY, redactBody, sha256Hex } from "../../../lib/order-os/support-tickets";

interface Env { DB: D1Database }

// Looks a ticket up by BOTH its public id and the per-ticket secret. Any
// mismatch (unknown id, wrong token, someone else's token) returns the same
// 404 body, so ids and tokens cannot be enumerated.
async function findTicket(env: Env, ticketId: unknown, token: unknown) {
  const id = typeof ticketId === "string" ? ticketId.slice(0, 40) : "";
  const tok = typeof token === "string" ? token : "";
  const hash = await sha256Hex(tok);
  if (!id || tok.length < 40 || tok.length > 200) return null;
  return env.DB.prepare(
    "SELECT id,public_ticket_id,status,created_at,updated_at FROM support_threads WHERE public_ticket_id=? AND access_token_hash=?"
  ).bind(id, hash).first<any>();
}

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.DB) return json({ error: "SUPPORT_BACKEND_NOT_CONFIGURED" }, 503);
  const url = new URL(request.url);
  // The secret travels in a header, never in the URL (URLs reach logs and referrers).
  const t = await findTicket(env, url.searchParams.get("ticket"), request.headers.get("x-ticket-token"));
  if (!t) return json(NOT_FOUND_BODY, 404);
  const ev = await env.DB.prepare(
    "SELECT actor_type,body_redacted,created_at FROM support_events WHERE thread_id=? AND event_type IN ('customer_message','staff_reply') ORDER BY id ASC"
  ).bind(t.id).all<any>();
  return json({
    ok: true,
    ticket_id: t.public_ticket_id,
    status: t.status,
    updated_at: t.updated_at,
    // Staff identities never leave the server: the customer sees "you" or "support".
    messages: (ev.results || []).map(e => ({ from: e.actor_type === "customer" ? "you" : "support", body: e.body_redacted, at: e.created_at })),
  });
};

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.DB) return json({ error: "SUPPORT_BACKEND_NOT_CONFIGURED" }, 503);
  const body = await readJson(request, 8192);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const t = await findTicket(env, body.ticket, request.headers.get("x-ticket-token"));
  if (!t) return json(NOT_FOUND_BODY, 404);
  if (t.status === "closed") return json({ error: "TICKET_CLOSED" }, 409);
  const message = redactBody(body.message);
  if (!message) return json({ error: "MESSAGE_REQUIRED" }, 400);
  const ts = nowIso();
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'customer',NULL,'customer_message',?,?)`).bind(t.id, message, ts),
      env.DB.prepare("UPDATE support_threads SET status='waiting_staff',updated_at=? WHERE id=? AND status!='closed'").bind(ts, t.id),
    ]);
  } catch {
    return json({ error: "WRITE_FAILED" }, 503);
  }
  return json({ ok: true, ticket_id: t.public_ticket_id, status: "waiting_staff" });
};
