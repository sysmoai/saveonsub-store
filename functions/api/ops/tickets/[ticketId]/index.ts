import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { shapeOrderRow } from "../../../../lib/order-os/redaction";
import {
  canAssignTickets, canReadTickets, canReplyTickets, canSeeAllTickets, isTicketStatus, newAccessToken, redactBody, sha256Hex,
} from "../../../../lib/order-os/support-tickets";
import { json, nowIso, readJson } from "../../../../lib/order-os/http";

async function load(env: OpsEnv, operator: { id: string; role: any }, ticketId: string) {
  const row = await env.DB.prepare(`SELECT t.id,t.public_ticket_id,t.status AS ticket_status,t.subject,t.category,t.verification_status,t.verification_method,t.escalated_at,t.escalation_reason,t.assigned_operator_id AS ticket_assignee,t.created_at,t.updated_at,
      o.public_order_id,o.status,o.customer_name,o.customer_phone,o.customer_email,o.assigned_operator_id
    FROM support_threads t LEFT JOIN orders o ON o.id=t.order_id WHERE t.public_ticket_id=?`).bind(ticketId).first<any>();
  if (!row) return null;
  if (!canSeeAllTickets(operator.role) && row.assigned_operator_id !== operator.id) return null; // same 404 as unknown
  return row;
}

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!canReadTickets(operator.role)) return json({ error: "FORBIDDEN" }, 403);
  const t = await load(env, operator, String(params.ticketId || ""));
  if (!t) return json({ error: "TICKET_NOT_FOUND" }, 404);
  const c = shapeOrderRow(operator.role, operator.id, t);
  const ev = await env.DB.prepare(
    "SELECT actor_type,actor_id,event_type,body_redacted,created_at FROM support_events WHERE thread_id=? ORDER BY id ASC"
  ).bind(t.id).all<any>();
  return json({
    ok: true,
    ticket: {
      ticket_id: t.public_ticket_id, status: t.ticket_status, subject: t.subject, order_id: t.public_order_id,
      category: t.category, verification: t.verification_status, verification_method: t.verification_method,
      escalated: !!t.escalated_at, escalation_reason: t.escalation_reason, assigned_to: t.ticket_assignee ?? null,
      customer_name: c.customer_name ?? null, customer_phone: c.customer_phone ?? null, customer_email: c.customer_email ?? null,
      created_at: t.created_at, updated_at: t.updated_at,
    },
    messages: (ev.results || []).map(e => ({ from: e.actor_type, by: e.actor_type === "operator" ? e.actor_id : null, type: e.event_type, body: e.body_redacted, at: e.created_at })),
  });
};

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!canReplyTickets(operator.role)) return json({ error: "FORBIDDEN" }, 403);
  const t = await load(env, operator, String(params.ticketId || ""));
  if (!t) return json({ error: "TICKET_NOT_FOUND" }, 404);
  if (t.ticket_status === "closed") return json({ error: "TICKET_CLOSED" }, 409);
  const body = await readJson(request, 8192);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const ts = nowIso();
  const message = body.message === undefined ? "" : redactBody(body.message);
  const next = body.status === undefined ? null : body.status;
  if (next !== null && !isTicketStatus(next)) return json({ error: "INVALID_STATUS" }, 400);
  const escalate = body.escalate === undefined ? "" : redactBody(body.escalate).slice(0, 300);
  if (body.escalate !== undefined && !escalate) return json({ error: "ESCALATION_REASON_REQUIRED" }, 400);
  const assignTo = body.assign_to === undefined ? null : String(body.assign_to).slice(0, 80);
  const rotate = body.rotate_code === true;
  if (assignTo !== null && !canAssignTickets(operator.role)) return json({ error: "FORBIDDEN" }, 403);
  if (!message && next === null && !escalate && assignTo === null && !rotate) return json({ error: "NOTHING_TO_DO" }, 400);
  if (assignTo !== null) {
    const target = await env.DB.prepare("SELECT id FROM operators WHERE id=? AND active=1").bind(assignTo).first<any>();
    if (!target) return json({ error: "ASSIGNEE_NOT_FOUND" }, 404);
  }
  const code = rotate ? newAccessToken() : null;
  const status = next ?? (message ? "waiting_customer" : t.ticket_status);
  const mkEvent = (type: string, text: string) => env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'operator',?,?,?,?)`).bind(t.id, operator.id, type, text, ts);

  try {
    await env.DB.batch([
      ...(message ? [env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'operator',?,'staff_reply',?,?)`).bind(t.id, operator.id, message, ts)] : []),
      ...(next !== null ? [env.DB.prepare(`INSERT INTO support_events(thread_id,actor_type,actor_id,event_type,body_redacted,created_at)
        VALUES (?,'operator',?,'status_change',?,?)`).bind(t.id, operator.id, `${t.ticket_status} -> ${next}`, ts)] : []),
      ...(escalate ? [mkEvent("escalated", escalate)] : []),
      ...(assignTo !== null ? [mkEvent("assigned", `assigned to ${assignTo}`)] : []),
      ...(rotate ? [mkEvent("access_code_rotated", "new access code issued; previous code no longer works")] : []),
      env.DB.prepare(`UPDATE support_threads SET status=?,
          assigned_operator_id=COALESCE(?,assigned_operator_id,?),
          priority=CASE WHEN ? THEN 0 ELSE priority END,
          escalated_at=CASE WHEN ? THEN COALESCE(escalated_at,?) ELSE escalated_at END,
          escalation_reason=CASE WHEN ? THEN ? ELSE escalation_reason END,
          access_token_hash=COALESCE(?,access_token_hash),
          updated_at=? WHERE id=?`)
        .bind(status, assignTo, operator.id, escalate ? 1 : 0, escalate ? 1 : 0, ts, escalate ? 1 : 0, escalate || null,
          code ? await sha256Hex(code) : null, ts, t.id),
    ]);
  } catch {
    return json({ error: "WRITE_FAILED" }, 503);
  }
  return json({ ok: true, ticket_id: t.public_ticket_id, status, ...(code ? { access_code: code } : {}) });
};
