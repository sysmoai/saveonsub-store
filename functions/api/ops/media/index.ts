import { requireOperator, type OpsEnv } from "../../../lib/order-os/ops-auth";
interface Env extends OpsEnv { MEDIA_BUCKET?: R2Bucket; }
const MAX_IMAGE_BYTES=8*1024*1024;
const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{
  "content-type":"application/json; charset=utf-8","cache-control":"private, no-store","x-content-type-options":"nosniff"
}});
function validMagic(type:string,bytes:Uint8Array):boolean {
  if(type==="image/png")return bytes.length>=8 && [137,80,78,71,13,10,26,10].every((v,i)=>bytes[i]===v);
  if(type==="image/jpeg")return bytes.length>=3 && bytes[0]===255 && bytes[1]===216 && bytes[2]===255;
  if(type==="image/webp")return bytes.length>=12 && [82,73,70,70].every((v,i)=>bytes[i]===v) && [87,69,66,80].every((v,i)=>bytes[i+8]===v);
  return false;
}
async function bytesCapped(request:Request,cap:number):Promise<Uint8Array>{
  const reader=request.body?.getReader();if(!reader)throw Error("EMPTY_FILE");
  let total=0;const chunks:Uint8Array[]=[];
  while(true){const {value,done}=await reader.read();if(done)break;
    total+=value.byteLength;if(total>cap){await reader.cancel();throw Error("FILE_TOO_LARGE");}chunks.push(value);
  }
  const result=new Uint8Array(total);let at=0;
  for(const chunk of chunks){result.set(chunk,at);at+=chunk.byteLength;}
  return result;
}
async function operatorFor(request:Request,env:Env){
  try{return await requireOperator(request,env);}catch{return null;}
}
export const onRequestGet:PagesFunction<Env>=async ({request,env})=>{
  if(!env.DB)return json({error:"SSOT_NOT_CONFIGURED"},503);
  const actor=await operatorFor(request,env);if(!actor)return json({error:"UNAUTHORIZED"},401);
  try{
    const rows=await env.DB.prepare("SELECT id,title,kind,mime_type,byte_count,alt_text,rights_type,lifecycle,created_at FROM commerce_media_assets ORDER BY created_at DESC LIMIT 100").all();
    return json({ok:true,assets:rows.results||[],role:actor.role});
  }catch{return json({error:"SSOT_SCHEMA_UNAVAILABLE"},503);}
};
export const onRequestPost:PagesFunction<Env>=async ({request,env})=>{
  if(!env.DB||!env.MEDIA_BUCKET)return json({error:"MEDIA_BACKEND_NOT_CONFIGURED"},503);
  const actor=await operatorFor(request,env);if(!actor)return json({error:"UNAUTHORIZED"},401);
  if(actor.role==="viewer")return json({error:"UPLOAD_FORBIDDEN"},403);
  const mime=(request.headers.get("content-type")||"").split(";")[0].toLowerCase();
  if(!["image/png","image/jpeg","image/webp"].includes(mime))return json({error:"IMAGE_TYPE_REQUIRED"},415);
  const length=Number(request.headers.get("content-length")||0);
  if(length>MAX_IMAGE_BYTES)return json({error:"IMAGE_TOO_LARGE"},413);
  const textHeader=(key:string)=>{try{return decodeURIComponent(request.headers.get(key)||"").trim();}catch{return "";}};
  const title=textHeader("x-sos-title");
  const alt=textHeader("x-sos-alt-text");
  const rights=textHeader("x-sos-rights-type")||"unknown";
  const evidence=textHeader("x-sos-rights-evidence");
  if(title.length<2||title.length>150||alt.length>400||evidence.length>700||
    !["created_by_business","licensed","provider_supplied","unknown"].includes(rights))
    return json({error:"INVALID_ASSET_METADATA"},400);
  let image:Uint8Array;
  try{image=await bytesCapped(request,MAX_IMAGE_BYTES);}catch{return json({error:"IMAGE_TOO_LARGE_OR_EMPTY"},413);}
  if(!validMagic(mime,image))return json({error:"IMAGE_SIGNATURE_MISMATCH"},415);
  const id=crypto.randomUUID();
  const key="sos/private/drafts/"+id+(mime==="image/png"?".png":mime==="image/webp"?".webp":".jpg");
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",image))).map(b=>b.toString(16).padStart(2,"0")).join("");
  const now=new Date().toISOString();
  try{
    await env.MEDIA_BUCKET.put(key,image,{httpMetadata:{contentType:mime},customMetadata:{tenant:"SOS",sha256:hash}});
    await env.DB.batch([
      env.DB.prepare("INSERT INTO commerce_media_assets (id,storage_key,kind,mime_type,byte_count,sha256_hex,alt_text,title,rights_type,rights_evidence_ref,lifecycle,uploaded_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,'draft',?,?,?)")
        .bind(id,key,"image",mime,image.byteLength,hash,alt,title,rights,evidence||null,actor.id,now,now),
      env.DB.prepare("INSERT INTO commerce_audit_events (id,actor_type,actor_id,event_type,entity_type,entity_id,metadata_json,created_at) VALUES(?,'operator',?,'commerce.media_draft_uploaded','media',?,?,?)")
        .bind(crypto.randomUUID(),actor.id,id,JSON.stringify({sha256:hash,byte_count:image.byteLength}),now)
    ]);
  }catch{
    try{await env.MEDIA_BUCKET.delete(key);}catch{console.error("orphan_media_cleanup_failed",id);}
    return json({error:"MEDIA_SAVE_FAILED"},503);
  }
  return json({ok:true,id,kind:"image",lifecycle:"draft",publish_allowed:false},201);
};
