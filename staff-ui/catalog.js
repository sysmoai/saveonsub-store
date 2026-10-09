"use strict";
const $=id=>document.getElementById(id);
const notice=(text,error=false)=>{const box=$("message");box.textContent=text;box.className="message"+(error?" error":"");};
async function call(url,options){
  const r=await fetch(url,{credentials:"same-origin",cache:"no-store",...options});
  let data;try{data=await r.json();}catch{throw new Error("Backend unavailable or returned non-JSON");}
  if(!r.ok)throw new Error(data.error||("HTTP "+r.status));
  return data;
}
function td(value){const el=document.createElement("td");el.textContent=String(value??"—");return el;}
async function refresh(){
  try{
    const data=await call("/api/ops/catalog?limit=100");
    $("operator").textContent="Operator role: "+(data.view_role||"unknown");
    $("count").textContent=String(data.products.length)+" items";
    const body=$("productRows");body.replaceChildren();
    if(!data.products.length){const tr=document.createElement("tr"),cell=td("No D1 drafts yet. Old catalog import requires review.");cell.colSpan=5;tr.appendChild(cell);body.appendChild(tr);}
    for(const product of data.products){
      const tr=document.createElement("tr");
      for(const value of [product.title,product.category,product.authorization,product.lifecycle,product.updated_at])
        tr.appendChild(td(value));
      body.appendChild(tr);
    }
    notice("Private draft inventory loaded. Nothing here publishes automatically.");
  }catch(error){$("operator").textContent="Not activated";notice("Protected backend not ready: "+error.message,true);}
}
$("refresh").addEventListener("click",refresh);
$("productForm").addEventListener("submit",async event=>{
  event.preventDefault();const form=event.currentTarget,button=form.querySelector('button[type="submit"]');
  const values=Object.fromEntries(new FormData(form).entries());
  button.disabled=true;
  try{
    const result=await call("/api/ops/catalog",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(values)});
    notice("Product "+result.slug+" recorded as DRAFT. CEO approval is still required.");form.reset();await refresh();
  }catch(error){notice("Could not save product draft: "+error.message,true);}
  finally{button.disabled=false;}
});
async function refreshMedia(){
  const tbody=$("mediaRows");
  try{
    const response=await call("/api/ops/media");
    tbody.replaceChildren();
    $("mediaCount").textContent=String(response.assets.length)+" assets";
    if(!response.assets.length){const tr=document.createElement("tr"),cell=td("No image or video drafts yet.");cell.colSpan=6;tr.appendChild(cell);tbody.appendChild(tr);}
    for(const asset of response.assets){
      const tr=document.createElement("tr");
      for(const value of [asset.title,asset.kind,asset.byte_count,asset.rights_type,asset.lifecycle])tr.appendChild(td(value));
      const cell=document.createElement("td"),link=document.createElement("a");
      link.href="/api/ops/media/"+encodeURIComponent(String(asset.id));
      link.target="_blank";link.rel="noopener noreferrer";link.textContent="Private file";
      link.style.color="#70e2c4";cell.appendChild(link);tr.appendChild(cell);
      tbody.appendChild(tr);
    }
  }catch{
    tbody.replaceChildren();
    const tr=document.createElement("tr"),cell=td("Media backend not connected. No public media is exposed.");cell.colSpan=6;tr.appendChild(cell);tbody.appendChild(tr);
  }
}
function contentType(file){
  if(file.type)return file.type;
  const name=file.name.toLowerCase();
  if(name.endsWith(".mov"))return "video/quicktime";
  if(name.endsWith(".mp4"))return "video/mp4";
  if(name.endsWith(".webm"))return "video/webm";
  return "";
}
async function uploadPrivate(event,endpoint,maxBytes,label){
  event.preventDefault();
  const form=event.currentTarget,button=form.querySelector('button[type="submit"]');
  const d=new FormData(form),file=d.get("file");
  if(!(file instanceof File)||!file.size){notice("Select a nonempty file.",true);return;}
  if(file.size>maxBytes){notice(label+" size exceeds the allowed limit.",true);return;}
  button.disabled=true;
  try{
    const headers={
      "content-type":contentType(file),
      "x-sos-title":encodeURIComponent(String(d.get("title")||"")),
      "x-sos-alt-text":encodeURIComponent(String(d.get("alt_text")||"")),
      "x-sos-rights-type":encodeURIComponent(String(d.get("rights_type")||"unknown")),
      "x-sos-rights-evidence":encodeURIComponent(String(d.get("rights_evidence")||""))
    };
    const result=await call(endpoint,{method:"POST",headers,body:file});
    notice(label+" uploaded privately as DRAFT ("+result.id+"). CEO approval is still required.");
    form.reset();await refreshMedia();
  }catch(error){notice("Could not save "+label.toLowerCase()+" draft: "+error.message,true);}
  finally{button.disabled=false;}
}
$("mediaForm").addEventListener("submit",event=>uploadPrivate(event,"/api/ops/media",8*1024*1024,"Image"));
$("videoForm").addEventListener("submit",event=>uploadPrivate(event,"/api/ops/media/videos",12*1024*1024,"Video"));
refresh();
refreshMedia();
