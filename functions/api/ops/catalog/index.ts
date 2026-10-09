import { requireOperator, type OpsEnv } from "../../../lib/order-os/ops-auth";

const json = (data: unknown, status=200) => new Response(JSON.stringify(data), {status,headers:{
  "content-type":"application/json; charset=utf-8", "cache-control":"private, no-store", "x-content-type-options":"nosniff"
}});
const allowedKinds = new Set(["subscription","service","bundle"]);
const allowedStatus = new Set(["draft","review","approved","published","paused","blocked","archived"]);
const fields = new Set(["slug","title","category","kind","provider_name","provider_official_url","summary"]);

async function readLimitedJson(request: Request, limit=16384): Promise<Record<string,unknown>> {
  const length = Number(request.headers.get("content-length")||0);
  if(length > limit) throw new Error("PAYLOAD_TOO_LARGE");
  const reader = request.body?.getReader();
  if(!reader) throw new Error("EMPTY_BODY");
  const parts: Uint8Array[]=[];
  let size=0;
  while(true){
    const {value,done}=await reader.read();
    if(done) break;
    size += value.byteLength;
    if(size > limit) {await reader.cancel();throw new Error("PAYLOAD_TOO_LARGE");}
    parts.push(value);
  }
  const bytes = new Uint8Array(size);let offset=0;
  for(const part of parts){bytes.set(part,offset);offset+=part.byteLength;}
  const value:unknown = JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
  if(!value || Array.isArray(value) || typeof value!=="object") throw new Error("INVALID_BODY");
  return value as Record<string,unknown>;
}
async function authorize(request:Request, env:OpsEnv){
  try { return await requireOperator(request,env); }
  catch {return null;}
}
export const onRequestGet: PagesFunction<OpsEnv> = async ({request,env}) => {
  if(!env.DB) return json({error:"SSOT_NOT_CONFIGURED"},503);
  const actor=await authorize(request,env);
  if(!actor) return json({error:"UNAUTHORIZED"},401);
  const url=new URL(request.url);
  const state=url.searchParams.get("lifecycle")||"";
  if(state && !allowedStatus.has(state)) return json({error:"INVALID_LIFECYCLE"},400);
  const asked=Number(url.searchParams.get("limit")||50);
  const limit=Number.isFinite(asked)?Math.min(100,Math.max(1,Math.floor(asked))):50;
  const sql="SELECT id,slug,title,category,kind,provider_name,provider_official_url,summary,"+
    "lifecycle,authorization,source_verified_at,revision,created_at,updated_at FROM commerce_products "+
    (state?"WHERE lifecycle=? ":"")+"ORDER BY updated_at DESC LIMIT ?";
  try{
    const rows=await env.DB.prepare(sql).bind(...(state?[state,limit]:[limit])).all();
    return json({ok:true,products:rows.results||[],view_role:actor.role});
  }catch {return json({error:"SSOT_SCHEMA_UNAVAILABLE"},503);}
};
export const onRequestPost: PagesFunction<OpsEnv> = async ({request,env}) => {
  if(!env.DB) return json({error:"SSOT_NOT_CONFIGURED"},503);
  const actor=await authorize(request,env);
  if(!actor) return json({error:"UNAUTHORIZED"},401);
  if(actor.role==="viewer") return json({error:"NOT_ALLOWED_TO_DRAFT"},403);
  if(!(request.headers.get("content-type")||"").toLowerCase().startsWith("application/json"))
    return json({error:"JSON_REQUIRED"},415);
  let input:Record<string,unknown>;
  try {input=await readLimitedJson(request);}
  catch {return json({error:"INVALID_OR_OVERSIZED_JSON"},400);}
  if(Object.keys(input).some(k=>!fields.has(k))) return json({error:"UNSUPPORTED_OR_PRIVILEGED_FIELDS"},400);
  const slug=String(input.slug||"").trim().toLowerCase();
  const title=String(input.title||"").trim();
  const category=String(input.category||"").trim();
  const kind=String(input.kind||"subscription");
  const provider=String(input.provider_name||"").trim();
  const summary=String(input.summary||"").trim();
  const link=String(input.provider_official_url||"").trim();
  if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)||slug.length>90||title.length<2||title.length>140||category.length<2||category.length>70||
    !allowedKinds.has(kind)||provider.length>140||summary.length>1500) return json({error:"INVALID_PRODUCT_FIELDS"},400);
  if(link){
    try{const u=new URL(link);if(u.protocol!=="https:"||u.username||u.password||link.length>600)throw Error();}
    catch{return json({error:"HTTPS_PROVIDER_URL_REQUIRED"},400);}
  }
  const id=crypto.randomUUID(), timestamp=new Date().toISOString();
  try{
    await env.DB.batch([
      env.DB.prepare("INSERT INTO commerce_products "+
        "(id,slug,title,category,kind,provider_name,provider_official_url,summary,lifecycle,authorization,created_by,updated_by,created_at,updated_at) "+
        "VALUES(?,?,?,?,?,?,?,?,'draft','unknown',?,?,?,?)")
        .bind(id,slug,title,category,kind,provider||null,link||null,summary,actor.id,actor.id,timestamp,timestamp),
      env.DB.prepare("INSERT INTO commerce_audit_events "+
        "(id,actor_type,actor_id,event_type,entity_type,entity_id,metadata_json,created_at) "+
        "VALUES(?,'operator',?,'commerce.product_draft_created','product',?,?,?)")
        .bind(crypto.randomUUID(),actor.id,id,JSON.stringify({slug}),timestamp)
    ]);
  }catch(e){
    if(String(e).toLowerCase().includes("unique"))return json({error:"SLUG_ALREADY_EXISTS"},409);
    return json({error:"WRITE_FAILED_NO_PUBLISH"},503);
  }
  return json({ok:true,id,slug,lifecycle:"draft",authorization:"unknown",publish_allowed:false},201);
};
