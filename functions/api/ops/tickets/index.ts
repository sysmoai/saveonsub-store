import { requireOperator, authFailure, type OpsEnv } from "../../../lib/order-os/ops-auth";
import { shapeOrderRow } from "../../../lib/order-os/redaction";
import {
  MAX_OPEN_TICKETS_PER_ORDER, canCreateAssistedTicket, canReadTickets, canSeeAllTickets, isCategory,
  isTicketStatus, isVerificationMethod, newAccessToken, newPublicTicketId, redactBody, sha256Hex,
} from "../../../lib/order-os/support-tickets";
import { json, nowIso, readJson } from "../../../lib/order-os/http";

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!canReadTickets(operator.role)) return json({ error: "FORBIDDEN" }, 403);

  const url = new URL(request.url);
  const status = url.searchParams.get("status");
  if (status && !isTicketStatus(status)) return json({ error: "INVALID_STATUS" }, 400);
  const asked = Number(url.searchParams.get("limit") || 50);
  const limit = Number.isFinite(asked) ? Math.min(Math.max(Math.floor(asked), 1), 100) : 50;

  const where: string[] = [];
  const binds: any[] = [];
  if (status) { where.push("t.status=?"); binds.push(status); }
  // fulfillment sees only tickets on orders assigned to them; the rest see all.
  if (!canSeeAllTickets(operator.role)) { where.push("o.assigned_operator_id=?"); binds.push(operator.id); }
  const sql = `SELECT t.public_ticket_id,t.status AS ticket_status,t.priority,t.subject,t.category,t.verification_status,t.escalated_at,t.assigned_operator_id AS ticket_assignee,t.created_at,t.updated_at,
      o.public_order_id,o.status,o.customer_name,o.customer_phone,o.customer_email,o.assigned_operator_id
    FROM support_threads t LEFT JOIN orders o ON o.id=t.order_id
    ${where.length ? "WHERE " + where.join(" AND ") : ""}
    ORDER BY t.priority ASC, t.updated_at DESC LIMIT ?`;
  binds.push(limit);
  const rows = await env.DB.prepare(sql).bind(...binds).all<any>();
  const tickets = (rows.results || []).map(r => {
    const c = shapeOrderRow(operator.role, operator.id, r);
    return {
      ticket_id: r.public_ticket_id, status: r.ticket_status, priority: r.priority, subject: r.subject,
      category: r.category, verification: r.verification_status, escalated: !!r.escalated_at, assigned_to: r.ticket_assignee ?? null,
      order_id: r.public_order_id, customer_name: c.customer_name ?? null,
      created_at: r.created_at, updated_at: r.updated_at,
    };
  });
  return json({ ok: true, operator: { id: operator.id, role: operator.role }, tickets });
};

// Staff-assisted intake for customers who have no Order OS tracking token (for
// example orders fulfilled by hand over WhatsApp). The operator verifies ownership
// out of band, names the method, and relays the one-time access code over the same
// verified channel. No order is ever created or guessed here: an unknown order id
// is refused and writes nothing.
export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!canCreateAssistedTicket(operator.role)) return json({ error: "FORBIDDEN" }, 403);
  const body = await readJson(request, 8192);
  if (!body) return json({ error: "INVALID_JSON" }, 400);

  const category = body.category === undefined ? "subscription_support" : body.category;
  if (!isCategory(category)) return json({ error: "INVALID_CATEGORY" }, 400);
  const message = redactBody(body.message);
  if (!message) return json({ error: "MESSAGE_REQUIRED" }, 400);
  const subject = redactBody(body.subject).slice(0, 120) || null;

  let orderId: string | null = null;
  let verification = "unverified";
  let method: string | null = null;
  if (body.order_id !== undefined && body.order_id !== null && body.order_id !== "") {
    if (!isVerificationMethod(body.verification_method)) return json({ error: "VERIFICATION_METHOD_REQUIRED" }, 400);
    if (body.verified !== true) return json({ error: "VERIFICATION_NOT_CONFIRMED" }, 400);
    const order = await env.DB.prepare("SELECT id FROM orders WHERE public_order_id=?")
      .bind(String(body.order_id).slice(0, 40)).first<any>();
    if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
    const open = await env.DB.prepare(
      "SELECT COUNT(*) AS n FROM support_threads WHERE order_id=? AND status IN ('open','waiting_customer','waiting_staff')"
    ).bind(order.id).first<any>();
    if ((open?.n ?? 0) >= MAX_OPEN_TICKETS_PER_ORDER) return json({ error: "TOO_MANY_OPEN_TICKETS" }, 429);
    orderId = order.id; verification = "staff_verified"; method = body.verification_method;
  }

  const id = crypto.randomUUID();
  const publicId = newPublicTicketId();
  const code = newAccessToken();
  const ts = nowIso();
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO support_threads(id,order_id,status,priority,subject,public_ticket_id,access_token_hash,
          category,verification_status,verification_method,verified_by,verified_at,channel,assigned_operator_id,created_at,updated_at)
        VALUES (?,?,'waiting_customer',2,?,?,?,?,?,?,?,?,'whatsapp_assisted',?,?,?)`)
        .bind(id, orderId, subject, publicId, await sha256Hex(code), category, verification, method,
          orderId ? operator.id : null, orderId ? ts : null, operator.id, ts, ts),
      env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'operator',?,'assisted_intake',?,?)`).bind(id, operator.id,
          orderId ? `ownership verified by ${method}` : "no order linked (unverified)", ts),
      env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'customer',NULL,'customer_message',?,?)`).bind(id, message, ts),
    ]);
  } catch {
    return json({ error: "WRITE_FAILED" }, 503);
  }
  // Shown once to the operator, to be relayed to the verified customer. Only a hash is stored.
  return json({ ok: true, ticket_id: publicId, access_code: code, verification }, 201);
};
