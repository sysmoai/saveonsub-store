import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { decideTransition, isOrderStatus, isPrivileged } from "../../../../lib/order-os/order-workflow";
import { json, nowIso, readJson, writeFailure } from "../../../../lib/order-os/http";
import { EVIDENCE_REF, bdtToMinor } from "../../../../lib/order-os/money";

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
    order = await env.DB.prepare("SELECT id,status,assigned_operator_id,total_minor FROM orders WHERE public_order_id=?")
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

  // G6: a refund must record the money actually sent back, with private
  // evidence (statement / R2 object), in the same guarded write.
  let refund: { amount_minor: number; channel: string; evidence_ref: string } | null = null;
  if (to === "refunded") {
    const r = body.refund && typeof body.refund === "object" ? body.refund as Record<string, unknown> : null;
    const channel = r && typeof r.channel === "string" ? r.channel : "";
    const evidence = r && typeof r.evidence_ref === "string" ? r.evidence_ref.trim() : "";
    const amountMinor = bdtToMinor(r?.amount_bdt);
    if (amountMinor === null) return json({ error: "REFUND_AMOUNT_REQUIRED" }, 400);
    if (amountMinor > Number(order.total_minor)) return json({ error: "REFUND_EXCEEDS_TOTAL" }, 400);
    if (!["bkash", "nagad", "rocket", "bank_transfer", "other"].includes(channel)) return json({ error: "REFUND_CHANNEL_REQUIRED" }, 400);
    if (!EVIDENCE_REF.test(evidence)) {
      return json({ error: "REFUND_EVIDENCE_REQUIRED" }, 400);
    }
    refund = { amount_minor: amountMinor, channel, evidence_ref: evidence };
  }

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

  const statements = [
    env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
      SELECT id,'status_changed','operator',?,?,? FROM orders WHERE ${guard}`)
      .bind(operator.id, JSON.stringify({ from: order.status, to, note, ...(refund ? { refund_amount_minor: refund.amount_minor } : {}) }), ts, ...guardBinds),
  ];
  if (refund) {
    statements.push(env.DB.prepare(`INSERT INTO order_refunds(id,order_id,amount_minor,currency,channel,evidence_ref,recorded_by,created_at)
      SELECT ?,id,?,'BDT',?,?,?,? FROM orders WHERE ${guard}`)
      .bind(crypto.randomUUID(), refund.amount_minor, refund.channel, refund.evidence_ref, operator.id, ts, ...guardBinds));
  }
  const updateIndex = statements.length;
  statements.push(env.DB.prepare(`UPDATE orders SET ${sets.join(",")} WHERE ${guard}`).bind(...setBinds, ...guardBinds));

  try {
    const results = await env.DB.batch(statements);
    if (results[updateIndex].meta.changes !== 1) return json({ error: "STALE_STATE" }, 409);
  } catch (e) { return writeFailure(e); }

  return json({ ok: true, order_id: orderId, from: order.status, to, privileged: isPrivileged(operator.role) });
};
