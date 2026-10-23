import { requireOperator, authFailure, type OpsEnv } from "../../../lib/order-os/ops-auth";
import { isOrderStatus } from "../../../lib/order-os/order-workflow";
import { shapeOrderRow } from "../../../lib/order-os/redaction";
import { json } from "../../../lib/order-os/http";

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }

  const url = new URL(request.url);
  const status = url.searchParams.get("status");
  if (status && !isOrderStatus(status)) return json({ error: "INVALID_STATUS" }, 400);
  const asked = Number(url.searchParams.get("limit") || 50);
  const limit = Number.isFinite(asked) ? Math.min(Math.max(Math.floor(asked), 1), 100) : 50;

  let sql = `SELECT public_order_id,status,priority,payment_method,total_minor,currency,
    customer_name,customer_phone,customer_email,assigned_operator_id,sla_due_at,
    created_at,updated_at
    FROM orders`;
  const binds: any[] = [];
  if (status) { sql += " WHERE status=?"; binds.push(status); }
  sql += " ORDER BY priority ASC, COALESCE(sla_due_at,created_at) ASC, created_at ASC LIMIT ?";
  binds.push(limit);

  const rows = await env.DB.prepare(sql).bind(...binds).all<any>();
  // Contact data is filtered here, per role, before the response exists.
  const orders = (rows.results || []).map(o => shapeOrderRow(operator.role, operator.id, o));
  return json({ ok: true, operator: { id: operator.id, name: operator.display_name, role: operator.role }, orders });
};
