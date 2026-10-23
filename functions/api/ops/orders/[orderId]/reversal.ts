import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { TERMINAL_STATUSES } from "../../../../lib/order-os/order-workflow";
import { json, nowIso, readJson, writeFailure } from "../../../../lib/order-os/http";

// The only route out of cancelled / refunded. Owner only, with a written
// reason. The order goes back to payment_review - never to a paid or
// fulfilment state - and any earlier payment verification is voided, so money
// must be verified again before fulfilment can restart. The reversal row is
// what the database trigger looks for; without it the status cannot change.

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (operator.role !== "owner") return json({ error: "REVERSAL_OWNER_ONLY" }, 403);

  const body = await readJson(request);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const reason = typeof body.reason === "string" ? body.reason.trim() : "";
  if (reason.length < 20 || reason.length > 500) return json({ error: "REASON_REQUIRED" }, 400);

  const orderId = String(params.orderId || "");
  let order;
  try {
    order = await env.DB.prepare("SELECT id,status FROM orders WHERE public_order_id=?").bind(orderId).first<any>();
  } catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  if (!TERMINAL_STATUSES.has(order.status)) return json({ error: "NOT_TERMINAL" }, 409);

  const reversalId = crypto.randomUUID();
  const ts = nowIso();
  const to = "payment_review";
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO order_reversals (id,order_id,from_status,to_status,reason,authorized_by,created_at)
        SELECT ?,id,status,?,?,?,? FROM orders WHERE id=? AND status=?`)
        .bind(reversalId, to, reason, operator.id, ts, order.id, order.status),
      env.DB.prepare(`UPDATE payment_verifications SET voided_at=?,voided_by=?,void_reason=?
        WHERE order_id=? AND voided_at IS NULL AND EXISTS (SELECT 1 FROM order_reversals WHERE id=?)`)
        .bind(ts, operator.id, "order reversal", order.id, reversalId),
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        SELECT order_id,'terminal_reversal','operator',?,?,? FROM order_reversals WHERE id=?`)
        .bind(operator.id, JSON.stringify({ from: order.status, to, reason }), ts, reversalId),
      env.DB.prepare(`UPDATE orders SET status=?,assigned_operator_id=NULL,claimed_at=NULL,payment_confirmed_at=NULL,
          delivered_at=NULL,completed_at=NULL,updated_at=? WHERE id=? AND status=?
          AND EXISTS (SELECT 1 FROM order_reversals WHERE id=? AND applied_at IS NULL)`)
        .bind(to, ts, order.id, order.status, reversalId),
      env.DB.prepare("UPDATE order_reversals SET applied_at=? WHERE id=? AND applied_at IS NULL").bind(ts, reversalId),
    ]);
  } catch (e) { return writeFailure(e); }

  const now = await env.DB.prepare("SELECT status FROM orders WHERE id=?").bind(order.id).first<any>();
  if (now?.status !== to) return json({ error: "STALE_STATE" }, 409);
  return json({ ok: true, order_id: orderId, from: order.status, to, reversal_id: reversalId });
};
