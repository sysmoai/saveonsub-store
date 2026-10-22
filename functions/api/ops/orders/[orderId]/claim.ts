import { requireOperator, type OpsEnv } from "../../../../lib/order-os/ops-auth";

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
const now=()=>new Date().toISOString();

export const onRequestPost: PagesFunction<OpsEnv> = async ({request,env,params}) => {
  let operator;
  try { operator=await requireOperator(request,env); }
  catch(e){ return json({error:String(e)},401); }
  if(operator.role==="viewer"||operator.role==="support") return json({error:"FORBIDDEN"},403);

  const orderId=String(params.orderId||"");
  const order=await env.DB.prepare("SELECT id,status,assigned_operator_id FROM orders WHERE public_order_id=?")
    .bind(orderId).first<any>();
  if(!order) return json({error:"ORDER_NOT_FOUND"},404);
  if(order.assigned_operator_id && order.assigned_operator_id!==operator.id) return json({error:"ALREADY_CLAIMED"},409);

  const ts=now();
  const nextStatus=order.status==="payment_confirmed"||order.status==="payment_review" ? "assigned" : order.status;
  const result=await env.DB.batch([
    env.DB.prepare("UPDATE orders SET assigned_operator_id=?,status=?,claimed_at=COALESCE(claimed_at,?),updated_at=? WHERE id=?")
      .bind(operator.id,nextStatus,ts,ts,order.id),
    env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
      VALUES(?,'order_claimed','operator',?,'{}',?)`).bind(order.id,operator.id,ts)
  ]);
  return json({ok:true,order_id:orderId,status:nextStatus,assigned_operator_id:operator.id,result:result.length});
};
