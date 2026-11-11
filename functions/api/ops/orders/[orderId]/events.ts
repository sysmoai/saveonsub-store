import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { shapeEvent } from "../../../../lib/order-os/redaction";
import { json } from "../../../../lib/order-os/http";

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  const orderId = String(params.orderId || "");
  const order = await env.DB.prepare("SELECT id FROM orders WHERE public_order_id=?").bind(orderId).first<any>();
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  const events = await env.DB.prepare(
    "SELECT event_type,actor_type,actor_id,payload_json,created_at FROM order_events WHERE order_id=? ORDER BY id ASC"
  ).bind(order.id).all<any>();
  return json({ ok: true, events: (events.results || []).map(ev => shapeEvent(operator.role, ev)) });
};
