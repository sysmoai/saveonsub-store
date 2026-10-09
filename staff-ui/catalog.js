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
$("mediaForm").addEventListener("submit",async event=>{
  event.preventDefault();const form=event.currentTarget,button=form.querySelector('button[type="submit"]');
  const d=new FormData(form),file=d.get("file");
  if(!(file instanceof File)||file.size===0){notice("Choose an image file.",true);return;}
  if(file.size>8*1024*1024){notice("Maximum 8MB image.",true);return;}
  button.disabled=true;
  try{
    const headers={
      "content-type":file.type,
      "x-sos-title":encodeURIComponent(String(d.get("title")||"")),
      "x-sos-alt-text":encodeURIComponent(String(d.get("alt_text")||"")),
      "x-sos-rights-type":encodeURIComponent(String(d.get("rights_type")||"unknown")),
      "x-sos-rights-evidence":encodeURIComponent(String(d.get("rights_evidence")||""))
    };
    const result=await call("/api/ops/media",{method:"POST",headers,body:file});
    notice("Image uploaded privately as DRAFT ("+result.id+"). It is not public.");form.reset();
  }catch(error){notice("Could not upload private image: "+error.message,true);}
  finally{button.disabled=false;}
});
refresh();