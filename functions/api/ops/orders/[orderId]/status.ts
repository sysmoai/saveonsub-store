import { requireOperator, canTransition, type OpsEnv } from "../../../../lib/order-os/ops-auth";

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
const now=()=>new Date().toISOString();

export const onRequestPost: PagesFunction<OpsEnv> = async ({request,env,params}) => {
  let operator;
  try { operator=await requireOperator(request,env); }
  catch(e){ return json({error:String(e)},401); }

  let body:{status?:string;note?:string};
  try{ body=await request.json(); }catch{ return json({error:"INVALID_JSON"},400); }
  const to=String(body.status||"");
  const allowed=new Set(["payment_review","payment_confirmed","assigned","fulfilling","delivered","support_open","completed","cancelled","refunded"]);
  if(!allowed.has(to)) return json({error:"INVALID_STATUS"},400);

  const orderId=String(params.orderId||"");
  const order=await env.DB.prepare("SELECT id,status,assigned_operator_id FROM orders WHERE public_order_id=?")
    .bind(orderId).first<any>();
  if(!order) return json({error:"ORDER_NOT_FOUND"},404);
  if(!canTransition(operator.role,order.status,to)) return json({error:"TRANSITION_FORBIDDEN",from:order.status,to},403);

  if(["payment_confirmed","cancelled","refunded"].includes(to) && !["owner","manager"].includes(operator.role)){
    return json({error:"MANAGER_APPROVAL_REQUIRED"},403);
  }
  if(["assigned","fulfilling","delivered"].includes(to) && order.assigned_operator_id && order.assigned_operator_id!==operator.id && !["owner","manager"].includes(operator.role)){
    return json({error:"NOT_ASSIGNED_OPERATOR"},403);
  }

  const ts=now();
  const field = to==="payment_confirmed" ? "payment_confirmed_at" :
                to==="delivered" ? "delivered_at" :
                to==="completed" ? "completed_at" : null;

  const updates=["status=?","updated_at=?"];
  const values:any[]=[to,ts];
  if(field){updates.push(`${field}=?`);values.push(ts);}
  values.push(order.id);

  await env.DB.batch([
    env.DB.prepare(`UPDATE orders SET ${updates.join(",")} WHERE id=?`).bind(...values),
    env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
      VALUES(?,'status_changed','operator',?,?,?)`)
      .bind(order.id,operator.id,JSON.stringify({from:order.status,to,note:(body.note||"").slice(0,500)}),ts)
  ]);

  return json({ok:true,order_id:orderId,from:order.status,to});
};
