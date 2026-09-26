import { requireOperator, type OpsEnv } from "../../../../lib/order-os/ops-auth";

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});

export const onRequestGet: PagesFunction<OpsEnv> = async ({request,env,params}) => {
  try { await requireOperator(request,env); }
  catch(e){ return json({error:String(e)},401); }
  const orderId=String(params.orderId||"");
  const order=await env.DB.prepare("SELECT id FROM orders WHERE public_order_id=?").bind(orderId).first<any>();
  if(!order) return json({error:"ORDER_NOT_FOUND"},404);
  const events=await env.DB.prepare("SELECT event_type,actor_type,actor_id,payload_json,created_at FROM order_events WHERE order_id=? ORDER BY id ASC")
    .bind(order.id).all();
  return json({ok:true,events:events.results||[]});
};
