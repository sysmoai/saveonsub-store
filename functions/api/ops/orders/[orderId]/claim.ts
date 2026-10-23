import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { CLAIMABLE_STATUSES, TERMINAL_STATUSES, canClaim } from "../../../../lib/order-os/order-workflow";
import { json, nowIso, writeFailure } from "../../../../lib/order-os/http";

const claimable = CLAIMABLE_STATUSES.map(s => `'${s}'`).join(",");

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!canClaim(operator.role)) return json({ error: "FORBIDDEN" }, 403);

  const orderId = String(params.orderId || "");
  const ts = nowIso();
  // One conditional UPDATE decides the winner. Two simultaneous claims cannot
  // both match "assigned_operator_id IS NULL", so the loser changes 0 rows.
  // The event is inserted under the same condition, immediately before.
  const where = `public_order_id=? AND assigned_operator_id IS NULL AND status IN (${claimable})`;
  let results;
  try {
    results = await env.DB.batch([
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        SELECT id,'order_claimed','operator',?,'{}',? FROM orders WHERE ${where}`).bind(operator.id, ts, orderId),
      env.DB.prepare(`UPDATE orders SET assigned_operator_id=?,
          status=CASE WHEN status='payment_confirmed' THEN 'assigned' ELSE status END,
          claimed_at=COALESCE(claimed_at,?),updated_at=? WHERE ${where}`).bind(operator.id, ts, ts, orderId),
    ]);
  } catch (e) { return writeFailure(e); }

  const current = await env.DB.prepare("SELECT status,assigned_operator_id FROM orders WHERE public_order_id=?")
    .bind(orderId).first<any>();
  if (!current) return json({ error: "ORDER_NOT_FOUND" }, 404);

  if (results[1].meta.changes === 1) {
    return json({ ok: true, order_id: orderId, status: current.status, assigned_operator_id: operator.id });
  }
  if (current.assigned_operator_id === operator.id) {
    return json({ ok: true, order_id: orderId, status: current.status, assigned_operator_id: operator.id, already_yours: true });
  }
  if (current.assigned_operator_id) return json({ error: "ALREADY_CLAIMED" }, 409);
  if (TERMINAL_STATUSES.has(current.status)) return json({ error: "ORDER_CLOSED" }, 409);
  return json({ error: "PAYMENT_NOT_VERIFIED" }, 409);
};
