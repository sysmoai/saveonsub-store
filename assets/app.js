/* SAVEONSUB shared app.js — authority-aware compatibility runtime */
const SUPPORT_EMAIL = "support@saveonsub.com";
const COMMERCE_ENABLED = false;

/* ---------- Cart (localStorage compatibility) ---------- */
function cartGet(){ try{return JSON.parse(localStorage.getItem('sos_cart')||'[]')}catch(e){return []} }
function cartSet(c){ localStorage.setItem('sos_cart', JSON.stringify(c)); cartBadge(); }
function cartAdd(id, planLabel, bdt, name){
  if(!COMMERCE_ENABLED){
    toast('Ordering is not enabled while plan and payment verification is pending.');
    return;
  }
  const c = cartGet();
  const ex = c.find(i=>i.id===id && i.plan===planLabel);
  if(ex){ ex.qty++; } else { c.push({id, plan:planLabel, bdt:Number(bdt), name, qty:1}); }
  cartSet(c); toast(`✅ ${name} added to cart`);
}
function cartRemove(idx){ const c=cartGet(); c.splice(idx,1); cartSet(c); if(window.renderCart)renderCart(); }
function cartTotal(){ return cartGet().reduce((s,i)=>s+Number(i.bdt||0)*i.qty,0); }
function cartCount(){ return COMMERCE_ENABLED ? cartGet().reduce((s,i)=>s+i.qty,0) : 0; }
function cartBadge(){ document.querySelectorAll('.cartn').forEach(el=>{ el.textContent=cartCount(); el.style.display=cartCount()?'block':'none'; }); }

/* ---------- Toast ---------- */
function toast(msg){
  let t=document.getElementById('toast');
  if(!t){ t=document.createElement('div'); t.id='toast'; document.body.appendChild(t); }
  t.textContent=msg; t.style.display='block';
  clearTimeout(t._h); t._h=setTimeout(()=>t.style.display='none', 2400);
}

/* ---------- Legacy order-ID compatibility ---------- */
function orderId(){
  const d=new Date(), p=n=>String(n).padStart(2,'0');
  return `SOS-${String(d.getFullYear()).slice(2)}${p(d.getMonth()+1)}${p(d.getDate())}-${Math.floor(1000+Math.random()*9000)}`;
}
function saveOrder(o){
  if(!COMMERCE_ENABLED) return;
  try{
    localStorage.setItem('sos_last_order', JSON.stringify(o));
    const hist=JSON.parse(localStorage.getItem('sos_orders')||'[]');
    hist.unshift(o); localStorage.setItem('sos_orders', JSON.stringify(hist.slice(0,20)));
  }catch(e){}
}
function lastOrder(){ try{return JSON.parse(localStorage.getItem('sos_last_order')||'null')}catch(e){return null} }

/* ---------- Contact compatibility ---------- */
function supportMailto(subject, body){
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject||'SAVEONSUB support')}&body=${encodeURIComponent(body||'')}`;
}
// Historical templates may still call waLink/waOrder until every generated page
// is rebuilt. Keep the function names as compatibility aliases, but never route
// them to an unapproved WhatsApp number or expose a client-authoritative order.
function waLink(text){ return supportMailto('SAVEONSUB support', text||''); }
function waOrder(extra){
  return supportMailto(
    'SAVEONSUB order enquiry',
    `Ordering is currently verification-gated.${extra&&extra.oid?` Reference: ${extra.oid}`:''}`
  );
}

/* ---------- Truth-safe ticker ---------- */
const TICKS=[
  "Compare plans before choosing a subscription",
  "English + Bangla product guidance",
  "Official-provider links are available on product pages",
  "Plan eligibility is verified separately from product information",
  "No automatic renewal or payment is enabled while commerce verification is pending"
];
function startTicker(){
  const el=document.getElementById('tick'); if(!el) return;
  let i=0;
  const show=()=>{ el.textContent=TICKS[i%TICKS.length]; i++; };
  show(); setInterval(show, 4200);
}

/* ---------- Copy ---------- */
function copyText(txt,label){ navigator.clipboard&&navigator.clipboard.writeText(txt).then(()=>toast(`📋 ${label||'Copied'}!`)); }

/* ---------- Mobile nav ---------- */
function navToggle(){ const l=document.querySelector('.navlinks'); if(l) l.classList.toggle('open'); }

/* ---------- PWA ---------- */
if('serviceWorker' in navigator){
  window.addEventListener('load', ()=>{ navigator.serviceWorker.register('/sw.js').catch(()=>{}); });
}
let sosDeferredPrompt=null;
window.addEventListener('beforeinstallprompt', (e)=>{
  e.preventDefault(); sosDeferredPrompt=e;
  const b=document.getElementById('installBtn'); if(b){ b.style.display='inline-flex';
    b.onclick=async()=>{ b.style.display='none'; sosDeferredPrompt.prompt(); await sosDeferredPrompt.userChoice; sosDeferredPrompt=null; }; }
});

/* ---------- Bangla language auto-suggest ---------- */
function suggestBangla(){
  try{
    if((document.documentElement.lang||'').startsWith('bn')) return;
    if(localStorage.getItem('sos_lang_dismissed')) return;
    const langs = navigator.languages || [navigator.language || ''];
    if(!langs.some(l => (l||'').toLowerCase().startsWith('bn'))) return;
    const alt = document.querySelector('link[hreflang="bn-bd"]');
    if(!alt || !alt.href || alt.href === location.href) return;
    const bar = document.createElement('div');
    bar.setAttribute('role','region'); bar.setAttribute('aria-label','ভাষা');
    bar.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:9999;max-width:520px;margin:0 auto;'
      +'background:var(--card,#103433);border:1px solid var(--green,#14d4b8);border-radius:14px;'
      +'padding:12px 14px;display:flex;align-items:center;gap:12px;box-shadow:0 8px 30px rgba(0,0,0,.4);font-size:14.5px';
    bar.innerHTML='<span style="flex:1">🇧🇩 বাংলায় দেখতে চান? <b>এই পেজটি বাংলায়ও আছে।</b></span>'
      +'<a class="btn btn-primary btn-sm" href="'+alt.href+'">বাংলায় দেখুন</a>'
      +'<button aria-label="বন্ধ করুন" style="background:none;border:none;color:var(--muted,#a3c9c4);font-size:20px;cursor:pointer;line-height:1">✕</button>';
    bar.querySelector('button').onclick=function(){ try{localStorage.setItem('sos_lang_dismissed','1')}catch(e){}; bar.remove(); };
    bar.querySelector('a').onclick=function(){ try{localStorage.setItem('sos_lang_dismissed','1')}catch(e){}; };
    document.body.appendChild(bar);
  }catch(e){}
}

/* ---------- Deal-alert interest form ---------- */
function setupNewsletterForm(){
  const form = document.getElementById('newsletter-form');
  if(!form) return;
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = form.querySelector('input[type="email"]')?.value?.trim();
    if(!email) return;
    // No newsletter backend is connected. Never claim the address was stored or
    // subscribed. Open a normal email draft so the user intentionally contacts
    // the known support mailbox instead of silently sending PII somewhere.
    location.href = supportMailto('SAVEONSUB deal alerts', `Please add this address to future SAVEONSUB deal alerts: ${email}`);
    toast('Opening your email app so you can confirm the request.');
  });
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', ()=>{ cartBadge(); startTicker(); suggestBangla(); setupNewsletterForm(); });
