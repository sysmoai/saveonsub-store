import { requireOperator, authFailure, type OpsEnv } from "../../../lib/order-os/ops-auth";
import { shapeOrderRow } from "../../../lib/order-os/redaction";
import { canReadTickets, canSeeAllTickets, isTicketStatus } from "../../../lib/order-os/support-tickets";
import { json } from "../../../lib/order-os/http";

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
  const sql = `SELECT t.public_ticket_id,t.status AS ticket_status,t.priority,t.subject,t.created_at,t.updated_at,
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
      order_id: r.public_order_id, customer_name: c.customer_name ?? null,
      created_at: r.created_at, updated_at: r.updated_at,
    };
  });
  return json({ ok: true, tickets });
};
