// G4: record when a delivered subscription ends, so renewals can be followed up.
import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { json, nowIso, readJson } from "../../../../lib/order-os/http";
import { addDays, isIsoDate } from "../../../../lib/order-os/money";

const SERVICE_STATUSES = new Set(["delivered", "support_open", "completed"]);
const MAX_PERIOD_DAYS = 400;

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!["owner", "manager", "fulfillment"].includes(operator.role)) return json({ error: "FORBIDDEN" }, 403);
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "FORBIDDEN_ORIGIN" }, 403);

  const body = await readJson(request);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const starts = body.service_starts_on;
  const ends = body.service_ends_on;
  if (!isIsoDate(starts) || !isIsoDate(ends) || ends <= starts) return json({ error: "INVALID_SERVICE_PERIOD" }, 400);
  if (ends > addDays(starts, MAX_PERIOD_DAYS)) return json({ error: "SERVICE_PERIOD_TOO_LONG" }, 400);

  let order;
  try {
    order = await env.DB.prepare("SELECT id,status,assigned_operator_id FROM orders WHERE public_order_id=?")
      .bind(String(params.orderId || "")).first<any>();
  } catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  if (!SERVICE_STATUSES.has(order.status)) return json({ error: "ORDER_NOT_DELIVERED" }, 409);
  if (operator.role === "fulfillment" && order.assigned_operator_id !== operator.id) {
    return json({ error: "NOT_ASSIGNED_OPERATOR" }, 403);
  }

  const ts = nowIso();
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO order_service_periods(order_id,service_starts_on,service_ends_on,set_by,updated_at)
        VALUES (?,?,?,?,?)
        ON CONFLICT(order_id) DO UPDATE SET service_starts_on=excluded.service_starts_on,
          service_ends_on=excluded.service_ends_on, set_by=excluded.set_by, updated_at=excluded.updated_at`)
        .bind(order.id, starts, ends, operator.id, ts),
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        VALUES (?,'service_period_set','operator',?,?,?)`)
        .bind(order.id, operator.id, JSON.stringify({ from: starts, to: ends }), ts),
    ]);
  } catch {
    console.error("service_period_write_failed");
    return json({ error: "WRITE_FAILED" }, 503);
  }
  return json({ ok: true, order_id: String(params.orderId), service_starts_on: starts, service_ends_on: ends });
};
