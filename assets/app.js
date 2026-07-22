/* SAVEONSUB Store — shared app.js (Step 3) */
const WA = "8801305869242";
const BKASH = "+8801305869242";

/* ---------- Cart (localStorage) ---------- */
function cartGet(){ try{return JSON.parse(localStorage.getItem('sos_cart')||'[]')}catch(e){return []} }
function cartSet(c){ localStorage.setItem('sos_cart', JSON.stringify(c)); cartBadge(); }
function cartAdd(id, planLabel, bdt, name){
  const c = cartGet();
  const ex = c.find(i=>i.id===id && i.plan===planLabel);
  if(ex){ ex.qty++; } else { c.push({id, plan:planLabel, bdt:Number(bdt), name, qty:1}); }
  cartSet(c); toast(`✅ ${name} added — ৳${bdt}`);
}
function cartRemove(idx){ const c=cartGet(); c.splice(idx,1); cartSet(c); if(window.renderCart)renderCart(); }
function cartTotal(){ return cartGet().reduce((s,i)=>s+i.bdt*i.qty,0); }
function cartCount(){ return cartGet().reduce((s,i)=>s+i.qty,0); }
function cartBadge(){ document.querySelectorAll('.cartn').forEach(el=>{ el.textContent=cartCount(); el.style.display=cartCount()?'block':'none'; }); }

/* ---------- Toast ---------- */
function toast(msg){
  let t=document.getElementById('toast');
  if(!t){ t=document.createElement('div'); t.id='toast'; document.body.appendChild(t); }
  t.textContent=msg; t.style.display='block';
  clearTimeout(t._h); t._h=setTimeout(()=>t.style.display='none', 2400);
}

/* ---------- Order ID ---------- */
function orderId(){
  const d=new Date(), p=n=>String(n).padStart(2,'0');
  return `SOS-${String(d.getFullYear()).slice(2)}${p(d.getMonth()+1)}${p(d.getDate())}-${Math.floor(1000+Math.random()*9000)}`;
}

/* ---------- Order record (localStorage) — on-site receipt + fallback ---------- */
function saveOrder(o){
  try{
    localStorage.setItem('sos_last_order', JSON.stringify(o));
    const hist=JSON.parse(localStorage.getItem('sos_orders')||'[]');
    hist.unshift(o); localStorage.setItem('sos_orders', JSON.stringify(hist.slice(0,20)));
  }catch(e){}
}
function lastOrder(){ try{return JSON.parse(localStorage.getItem('sos_last_order')||'null')}catch(e){return null} }

/* ---------- WhatsApp helpers ---------- */
function waLink(text){ return `https://wa.me/${WA}?text=${encodeURIComponent(text)}`; }
function waOrder(extra){
  const c=cartGet();
  const lines=c.map(i=>`• ${i.name} — ${i.plan} ×${i.qty} = ৳${i.bdt*i.qty}`).join('\n');
  return waLink(`🛒 NEW ORDER ${extra&&extra.oid?extra.oid:orderId()}\n${lines}\nTOTAL: ৳${cartTotal()}\nPayment: ${extra&&extra.method?extra.method:'(choosing)'} ${extra&&extra.txn?('TxnID: '+extra.txn):''}\n— sent from saveonsub store`);
}

/* ---------- Real-facts ticker (honest — lifetime records, no fake timestamps) ---------- */
const TICKS=[
  "211+ lifetime orders — Google AI Pro ৳500 (our #1)",
  "201+ lifetime orders — Grammarly Premium ৳470",
  "178+ lifetime orders — Leonardo AI ৳599",
  "156+ lifetime orders — Midjourney from ৳1,199",
  "145+ lifetime orders — ChatGPT Plus from ৳350",
  "1,600+ total orders delivered since 2024",
  "Warranty promise: replacement within 1 hour",
  "Pay-after-testing available on first orders",
  "Delivery SLA: 5–15 min on instant products"
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

/* ---------- PWA: register service worker (offline resilience) ---------- */
if('serviceWorker' in navigator){
  window.addEventListener('load', ()=>{ navigator.serviceWorker.register('/sw.js').catch(()=>{}); });
}
/* Custom install prompt (Android/desktop): capture event, show a subtle button if present */
let sosDeferredPrompt=null;
window.addEventListener('beforeinstallprompt', (e)=>{
  e.preventDefault(); sosDeferredPrompt=e;
  const b=document.getElementById('installBtn'); if(b){ b.style.display='inline-flex';
    b.onclick=async()=>{ b.style.display='none'; sosDeferredPrompt.prompt(); await sosDeferredPrompt.userChoice; sosDeferredPrompt=null; }; }
});

/* ---------- Bangla language auto-suggest (honest, dismissible, once) ---------- */
function suggestBangla(){
  try{
    if((document.documentElement.lang||'').startsWith('bn')) return;      // already Bangla
    if(localStorage.getItem('sos_lang_dismissed')) return;                 // user said no
    const langs = navigator.languages || [navigator.language || ''];
    if(!langs.some(l => (l||'').toLowerCase().startsWith('bn'))) return;    // not a Bangla browser
    const alt = document.querySelector('link[hreflang="bn-bd"]');
    if(!alt || !alt.href || alt.href === location.href) return;             // no distinct Bangla page
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

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', ()=>{ cartBadge(); startTicker(); suggestBangla(); });
