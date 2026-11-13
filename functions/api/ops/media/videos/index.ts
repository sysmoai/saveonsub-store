import { requireOperator, type OpsEnv } from "../../../../lib/order-os/ops-auth";

interface Env extends OpsEnv { MEDIA_BUCKET?: R2Bucket; }
const LIMIT_BYTES=12*1024*1024;
const SUPPORTED=new Map([
  ["video/mp4",".mp4"],["video/webm",".webm"],["video/quicktime",".mov"]
]);
const json=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{
  "content-type":"application/json; charset=utf-8","cache-control":"private, no-store","x-content-type-options":"nosniff"
}});
function looksLikeVideo(mime:string,bytes:Uint8Array){
  if(mime==="video/webm")return bytes.length>4&&bytes[0]===0x1a&&bytes[1]===0x45&&bytes[2]===0xdf&&bytes[3]===0xa3;
  if(mime==="video/mp4"||mime==="video/quicktime")
    return bytes.length>12&&String.fromCharCode(...bytes.slice(4,8))==="ftyp";
  return false;
}
async function cappedBody(request:Request){
  const reader=request.body?.getReader();if(!reader)throw Error("EMPTY_BODY");
  const chunks:Uint8Array[]=[];let size=0;
  while(true){
    const {value,done}=await reader.read();if(done)break;
    size+=value.byteLength;if(size>LIMIT_BYTES){await reader.cancel();throw Error("VIDEO_TOO_LARGE");}
    chunks.push(value);
  }
  if(!size)throw Error("EMPTY_BODY");
  const bytes=new Uint8Array(size);let offset=0;
  for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
  return bytes;
}
const decode=(request:Request,key:string)=>{try{return decodeURIComponent(request.headers.get(key)||"").trim();}catch{return "";}};
export const onRequestPost: PagesFunction<Env>=async ({request,env})=>{
  if(!env.DB||!env.MEDIA_BUCKET)return json({error:"MEDIA_BACKEND_NOT_CONFIGURED"},503);
  let actor;
  try{actor=await requireOperator(request,env);}catch{return json({error:"UNAUTHORIZED"},401);}
  if(actor.role==="viewer")return json({error:"UPLOAD_FORBIDDEN"},403);
  const mime=(request.headers.get("content-type")||"").split(";")[0].toLowerCase();
  if(!SUPPORTED.has(mime))return json({error:"VIDEO_TYPE_UNSUPPORTED"},415);
  const length=Number(request.headers.get("content-length")||0);
  if(length>LIMIT_BYTES)return json({error:"VIDEO_TOO_LARGE"},413);
  const title=decode(request,"x-sos-title");
  const description=decode(request,"x-sos-alt-text");
  const rights=decode(request,"x-sos-rights-type")||"unknown";
  const evidence=decode(request,"x-sos-rights-evidence");
  if(title.length<2||title.length>150||description.length>400||evidence.length>700||
     !["created_by_business","licensed","provider_supplied","unknown"].includes(rights))
    return json({error:"INVALID_VIDEO_METADATA"},400);
  let bytes;
  try{bytes=await cappedBody(request);}catch{return json({error:"EMPTY_OR_OVERSIZED_VIDEO"},413);}
  if(!looksLikeVideo(mime,bytes))return json({error:"VIDEO_SIGNATURE_MISMATCH"},415);
  const id=crypto.randomUUID(),now=new Date().toISOString();
  const key="sos/private/drafts/videos/"+id+SUPPORTED.get(mime);
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)))
    .map(v=>v.toString(16).padStart(2,"0")).join("");
  try{
    await env.MEDIA_BUCKET.put(key,bytes,{httpMetadata:{contentType:mime},customMetadata:{tenant:"SOS",sha256:hash}});
    await env.DB.batch([
      env.DB.prepare("INSERT INTO commerce_media_assets (id,storage_key,kind,mime_type,byte_count,sha256_hex,alt_text,title,rights_type,rights_evidence_ref,lifecycle,uploaded_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,'draft',?,?,?)")
        .bind(id,key,"video",mime,bytes.byteLength,hash,description,title,rights,evidence||null,actor.id,now,now),
      env.DB.prepare("INSERT INTO commerce_audit_events (id,actor_type,actor_id,event_type,entity_type,entity_id,metadata_json,created_at) VALUES(?,'operator',?,'commerce.video_draft_uploaded','media',?,?,?)")
        .bind(crypto.randomUUID(),actor.id,id,JSON.stringify({sha256:hash,bytes:bytes.byteLength}),now)
    ]);
  }catch{
    try{await env.MEDIA_BUCKET.delete(key);}catch{console.error("video_orphan_cleanup_failed",id);}
    return json({error:"VIDEO_DRAFT_SAVE_FAILED"},503);
  }
  return json({ok:true,id,kind:"video",lifecycle:"draft",publish_allowed:false,
    warning:"This is a private original, not transcoded or approved for public playback."},201);
};