import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { decideTransition, isOrderStatus, isPrivileged } from "../../../../lib/order-os/order-workflow";
import { json, nowIso, readJson, writeFailure } from "../../../../lib/order-os/http";

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }

  const body = await readJson(request);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const to = typeof body.status === "string" ? body.status : "";
  if (!isOrderStatus(to) || to === "submitted") return json({ error: "INVALID_STATUS" }, 400);
  const note = typeof body.note === "string" ? body.note.slice(0, 500) : "";
  const expected = typeof body.expected_status === "string" ? body.expected_status : "";

  const orderId = String(params.orderId || "");
  let order;
  try {
    order = await env.DB.prepare("SELECT id,status,assigned_operator_id FROM orders WHERE public_order_id=?")
      .bind(orderId).first<any>();
  } catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  if (expected && expected !== order.status) return json({ error: "STALE_STATE", current: order.status }, 409);

  const decision = decideTransition(operator.role, order.status, to);
  if (!decision.ok) return json({ error: decision.code, from: order.status, to }, decision.status);

  // Fulfilment work must be done by the operator the order is assigned to.
  const isFulfiller = operator.role === "fulfillment";
  if (to === "fulfilling" && !order.assigned_operator_id) return json({ error: "CLAIM_REQUIRED" }, 409);
  if (isFulfiller && order.assigned_operator_id !== operator.id) return json({ error: "NOT_ASSIGNED_OPERATOR" }, 403);

  const ts = nowIso();
  const stamp = to === "delivered" ? "delivered_at" : to === "completed" ? "completed_at" : null;
  const sets = ["status=?", "updated_at=?"];
  const setBinds: unknown[] = [to, ts];
  if (stamp) { sets.push(`${stamp}=?`); setBinds.push(ts); }

  // Compare-and-set: the write only applies if the order is still in the state
  // we validated against (and, for fulfillers, still assigned to them). The
  // audit event shares the identical guard, so a lost race or refused change
  // leaves no event behind.
  let guard = "id=? AND status=?";
  const guardBinds: unknown[] = [order.id, order.status];
  if (isFulfiller) { guard += " AND assigned_operator_id=?"; guardBinds.push(operator.id); }

  try {
    const results = await env.DB.batch([
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        SELECT id,'status_changed','operator',?,?,? FROM orders WHERE ${guard}`)
        .bind(operator.id, JSON.stringify({ from: order.status, to, note }), ts, ...guardBinds),
      env.DB.prepare(`UPDATE orders SET ${sets.join(",")} WHERE ${guard}`).bind(...setBinds, ...guardBinds),
    ]);
    if (results[1].meta.changes !== 1) return json({ error: "STALE_STATE" }, 409);
  } catch (e) { return writeFailure(e); }

  return json({ ok: true, order_id: orderId, from: order.status, to, privileged: isPrivileged(operator.role) });
};
