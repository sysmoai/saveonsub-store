import { requireOperator, type OpsEnv } from "../../../lib/order-os/ops-auth";

const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});

export const onRequestGet: PagesFunction<OpsEnv> = async ({request,env}) => {
  let operator;
  try { operator=await requireOperator(request,env); }
  catch(e){ return json({error:String(e)},401); }

  const url=new URL(request.url);
  const status=url.searchParams.get("status");
  const limit=Math.min(Math.max(Number(url.searchParams.get("limit")||50),1),100);

  let sql=`SELECT public_order_id,status,priority,payment_method,total_minor,currency,
    customer_name,customer_phone,customer_email,assigned_operator_id,sla_due_at,
    created_at,updated_at
    FROM orders`;
  const binds:any[]=[];
  if(status){ sql+=" WHERE status=?"; binds.push(status); }
  sql+=" ORDER BY priority ASC, COALESCE(sla_due_at,created_at) ASC, created_at ASC LIMIT ?";
  binds.push(limit);

  const rows=await env.DB.prepare(sql).bind(...binds).all();
  return json({ok:true,operator:{id:operator.id,name:operator.display_name,role:operator.role},orders:rows.results||[]});
};
