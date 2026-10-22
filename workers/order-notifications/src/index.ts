interface Env {
  DB: D1Database;
  ORDER_NOTIFICATION_WEBHOOK: string;
}

type OutboxRow={
  id:number;
  order_id:string|null;
  payload_json:string;
  attempt_count:number;
};

function nextRetry(attempt:number){
  const minutes=Math.min(60,Math.pow(2,Math.max(0,attempt))*2);
  return new Date(Date.now()+minutes*60_000).toISOString();
}

export default {
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil(processDue(env));
  }
};

async function processDue(env:Env){
  if(!env.DB||!env.ORDER_NOTIFICATION_WEBHOOK) throw new Error("NOTIFICATION_WORKER_NOT_CONFIGURED");
  const due=await env.DB.prepare(`SELECT id,order_id,payload_json,attempt_count
    FROM notification_outbox
    WHERE status IN ('pending','failed') AND next_attempt_at<=?
    ORDER BY priority ASC,id ASC LIMIT 25`).bind(new Date().toISOString()).all<OutboxRow>();

  for(const row of due.results||[]){
    const ts=new Date().toISOString();
    await env.DB.prepare("UPDATE notification_outbox SET status='sending',updated_at=? WHERE id=?")
      .bind(ts,row.id).run();
    let ok=false; let err="";
    try{
      const payload=JSON.parse(row.payload_json||"{}");
      const r=await fetch(env.ORDER_NOTIFICATION_WEBHOOK,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({type:"saveonsub.notification_retry",...payload})});
      ok=r.ok; if(!r.ok) err=`http_${r.status}`;
    }catch{err="network_error";}

    const attempts=row.attempt_count+1;
    if(ok){
      await env.DB.prepare("UPDATE notification_outbox SET status='sent',attempt_count=?,sent_at=?,last_error=NULL,updated_at=? WHERE id=?")
        .bind(attempts,ts,ts,row.id).run();
    }else if(attempts>=8){
      await env.DB.prepare("UPDATE notification_outbox SET status='dead',attempt_count=?,last_error=?,updated_at=? WHERE id=?")
        .bind(attempts,err,ts,row.id).run();
    }else{
      await env.DB.prepare("UPDATE notification_outbox SET status='failed',attempt_count=?,last_error=?,next_attempt_at=?,updated_at=? WHERE id=?")
        .bind(attempts,err,nextRetry(attempts),ts,row.id).run();
    }
  }
}
