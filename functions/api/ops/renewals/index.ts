// G4: subscriptions ending soon (Asia/Dhaka dates). Owner/manager see all;
// fulfillment sees only orders it delivered. Contact data is role-shaped.
import { requireOperator, authFailure, type OpsEnv } from "../../../lib/order-os/ops-auth";
import { shapeOrderRow } from "../../../lib/order-os/redaction";
import { json } from "../../../lib/order-os/http";
import { addDays, dhakaToday } from "../../../lib/order-os/money";

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!["owner", "manager", "fulfillment"].includes(operator.role)) return json({ error: "FORBIDDEN" }, 403);

  const url = new URL(request.url);
  const asked = Number(url.searchParams.get("days") || 7);
  const days = Number.isFinite(asked) ? Math.min(Math.max(Math.floor(asked), 0), 60) : 7;
  const today = dhakaToday();
  const until = addDays(today, days);
  // Already-expired periods stay visible for 14 days so a missed renewal is not lost.
  const from = addDays(today, -14);

  let sql = `SELECT o.public_order_id,o.status,o.customer_name,o.customer_phone,o.customer_email,
      o.assigned_operator_id,p.service_starts_on,p.service_ends_on,
      (SELECT product_name_snapshot || ' / ' || plan_name_snapshot FROM order_items i WHERE i.order_id=o.id ORDER BY i.id LIMIT 1) AS item
    FROM order_service_periods p JOIN orders o ON o.id=p.order_id
    WHERE p.service_ends_on BETWEEN ? AND ? AND o.status NOT IN ('cancelled','refunded')`;
  const binds: unknown[] = [from, until];
  if (operator.role === "fulfillment") { sql += " AND o.assigned_operator_id=?"; binds.push(operator.id); }
  sql += " ORDER BY p.service_ends_on ASC LIMIT 200";

  let rows;
  try { rows = await env.DB.prepare(sql).bind(...binds).all<any>(); }
  catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  const renewals = (rows.results || []).map((r: any) => ({
    ...shapeOrderRow(operator.role, operator.id, r),
    days_left: Math.round((Date.parse(`${r.service_ends_on}T00:00:00Z`) - Date.parse(`${today}T00:00:00Z`)) / 86400000),
  }));
  return json({ ok: true, today, until, renewals });
};
