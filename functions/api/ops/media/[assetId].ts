import { requireOperator, type OpsEnv } from "../../../lib/order-os/ops-auth";

interface Env extends OpsEnv { MEDIA_BUCKET?: R2Bucket; }
const json=(value:unknown,status:number)=>new Response(JSON.stringify(value),{
  status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"private, no-store"}
});
export const onRequestGet:PagesFunction<Env>=async ({request,env,params})=>{
  if(!env.DB||!env.MEDIA_BUCKET)return json({error:"MEDIA_NOT_CONFIGURED"},503);
  try{await requireOperator(request,env);}catch{return json({error:"UNAUTHORIZED"},401);}
  const assetId=String(params.assetId||"");
  if(!/^[0-9a-f]{8}-[0-9a-f-]{27,36}$/i.test(assetId))return json({error:"INVALID_MEDIA_ID"},400);
  let item:{storage_key:string;mime_type:string;lifecycle:string}|null;
  try{
    item=await env.DB.prepare("SELECT storage_key,mime_type,lifecycle FROM commerce_media_assets WHERE id=?")
      .bind(assetId).first();
  }catch{return json({error:"MEDIA_SCHEMA_UNAVAILABLE"},503);}
  if(!item || !item.storage_key.startsWith("sos/private/drafts/"))return json({error:"MEDIA_NOT_FOUND"},404);
  if(!["image/png","image/jpeg","image/webp","video/mp4","video/webm","video/quicktime"].includes(item.mime_type))return json({error:"MEDIA_TYPE_UNAVAILABLE"},415);
  const stored=await env.MEDIA_BUCKET.get(item.storage_key);
  if(!stored)return json({error:"OBJECT_NOT_FOUND"},404);
  return new Response(stored.body,{
    status:200,
    headers:{
      "content-type":item.mime_type,
      "cache-control":"private, no-store, max-age=0",
      "x-content-type-options":"nosniff",
      "content-security-policy":"default-src 'none'; sandbox",
      "x-robots-tag":"noindex, nofollow",
      "content-disposition":item.mime_type.startsWith("video/") ? `attachment; filename="${assetId}.${item.mime_type==="video/mp4"?"mp4":item.mime_type==="video/webm"?"webm":"mov"}"` : "inline"
    }
  });
};