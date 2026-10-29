/* SaveOnSub Meta Pixel bridge — maps first-party sos:track events to Meta.
 *
 * Fail-closed: while PIXEL_ID is empty this file makes no network request and
 * shows nothing. Setting the ID (a public value, not a secret) turns it on.
 *
 * Consent: Global Privacy Control / Do Not Track always win. Otherwise a small
 * notice offers Accept / Decline. CONSENT_MODE 'opt-in' loads nothing until
 * Accept; 'notice' loads at once and stops for good on Decline.
 *
 * Event map (browser):
 *   every page            → PageView
 *   /p/<id>.html          → ViewContent   (content_ids, value = lowest price)
 *   sos_add_to_cart       → AddToCart     (value, BDT)
 *   checkout with a cart  → InitiateCheckout (value, num_items)
 *   sos_order_submit      → Lead          (value, eventID = order id)
 *   sos_whatsapp_click    → Contact
 * Purchase is NOT sent from the browser: payment is confirmed by a human
 * (bKash/Nagad/Rocket), so it goes server-side via marketing/meta_capi.py.
 */
(function(){
  'use strict';

  const PIXEL_ID = '';            // e.g. '123456789012345' — from Meta Events Manager
  const CONSENT_MODE = 'notice';  // 'notice' | 'opt-in'
  const CURRENCY = 'BDT';
  const CONSENT_KEY = 'sos_ads_consent_v1';

  if(!/^\d{6,20}$/.test(PIXEL_ID)) return;

  const nav = navigator || {};
  if(nav.globalPrivacyControl === true || nav.doNotTrack === '1' || window.doNotTrack === '1') return;

  function getConsent(){ try { return localStorage.getItem(CONSENT_KEY) || ''; } catch(e){ return ''; } }
  function setConsent(v){ try { localStorage.setItem(CONSENT_KEY, v); } catch(e){} }

  let loaded = false;
  let viewedCheckout = false;

  function loadPixel(){
    if(loaded) return;
    loaded = true;
    /* Meta's standard base code, unminified */
    if(!window.fbq){
      const n = window.fbq = function(){ n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
      if(!window._fbq) window._fbq = n;
      n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
      const s = document.createElement('script');
      s.async = true; s.src = 'https://connect.facebook.net/en_US/fbevents.js';
      document.head.appendChild(s);
    }
    window.fbq('init', PIXEL_ID);
    window.fbq('track', 'PageView');
    pageEvents();
  }

  function send(name, params, eventId){
    if(!loaded || !window.fbq) return;
    if(eventId) window.fbq('track', name, params || {}, {eventID: eventId});
    else window.fbq('track', name, params || {});
  }

  function cartItems(){
    try { return JSON.parse(localStorage.getItem('sos_cart') || '[]') || []; } catch(e){ return []; }
  }
  function cartValue(items){
    return items.reduce(function(s, i){ return s + (Number(i.bdt) || 0) * (Number(i.qty) || 1); }, 0);
  }

  function productFromPage(){
    const m = location.pathname.match(/\/p\/([a-z0-9-]+)(?:\.html)?$/i);
    if(!m) return null;
    const out = {id: m[1], name: '', value: 0, category: ''};
    document.querySelectorAll('script[type="application/ld+json"]').forEach(function(s){
      try {
        const d = JSON.parse(s.textContent);
        if(d && d['@type'] === 'Product'){
          out.name = String(d.name || '');
          out.category = String(d.category || '');
          const o = d.offers || {};
          out.value = Number(o.lowPrice || o.price) || 0;
        }
      } catch(e){}
    });
    return out;
  }

  function pageEvents(){
    const p = productFromPage();
    if(p){
      send('ViewContent', {
        content_ids: [p.id], content_type: 'product', content_name: p.name,
        content_category: p.category, value: p.value, currency: CURRENCY
      });
    }
    if(/\/checkout(?:\.html)?$/i.test(location.pathname)) initiateCheckout();
  }

  function initiateCheckout(){
    if(viewedCheckout) return;
    const items = cartItems();
    if(!items.length) return;
    viewedCheckout = true;
    send('InitiateCheckout', {
      content_ids: items.map(function(i){ return String(i.id); }), content_type: 'product',
      num_items: items.reduce(function(s, i){ return s + (Number(i.qty) || 1); }, 0),
      value: cartValue(items), currency: CURRENCY
    });
  }

  window.addEventListener('sos:track', function(e){
    const d = (e && e.detail) || {};
    switch(d.event){
      case 'sos_add_to_cart':
        send('AddToCart', {
          content_ids: [String(d.product_id || '')], content_type: 'product',
          content_name: String(d.plan || ''), value: Number(d.value_bdt) || 0, currency: CURRENCY
        });
        break;
      case 'sos_order_submit':
        // eventID = order id, so a later server-side Lead for the same order is deduplicated.
        send('Lead', {
          content_ids: (d.product_ids || []).map(String), content_type: 'product',
          value: Number(d.value_bdt) || 0, currency: CURRENCY, order_kind: String(d.order_kind || '')
        }, d.order_id ? ('lead-' + d.order_id) : '');
        break;
      case 'sos_whatsapp_click':
        send('Contact', {content_name: String(d.link_text || '')});
        break;
    }
  });

  function showNotice(){
    if(document.getElementById('sos-ads-consent')) return;
    const bn = (document.documentElement.lang || '').startsWith('bn');
    const bar = document.createElement('div');
    bar.id = 'sos-ads-consent';
    bar.setAttribute('role', 'region');
    bar.setAttribute('aria-label', bn ? 'কুকি' : 'Cookies');
    bar.style.cssText = 'position:fixed;left:12px;right:12px;bottom:12px;z-index:9998;max-width:560px;margin:0 auto;'
      + 'background:var(--card,#103433);border:1px solid var(--line,#24504c);border-radius:14px;'
      + 'padding:12px 14px;display:flex;flex-wrap:wrap;align-items:center;gap:10px;font-size:13.5px;'
      + 'box-shadow:0 8px 30px rgba(0,0,0,.4)';
    const text = document.createElement('span');
    text.style.flex = '1 1 240px';
    text.innerHTML = bn
      ? 'আমাদের Facebook বিজ্ঞাপন কতটা কাজ করছে তা মাপতে আমরা Meta Pixel ব্যবহার করি। <a href="/privacy.html" style="color:var(--green2,#14d4b8)">বিস্তারিত</a>'
      : 'We use the Meta Pixel to measure our Facebook ads. <a href="/privacy.html" style="color:var(--green2,#14d4b8)">Details</a>';
    const ok = document.createElement('button');
    ok.className = 'btn btn-primary btn-sm';
    ok.textContent = bn ? 'ঠিক আছে' : 'OK';
    const no = document.createElement('button');
    no.className = 'btn btn-sm';
    no.style.cssText = 'background:none;border:1px solid var(--line,#24504c);color:inherit';
    no.textContent = bn ? 'না' : 'Decline';
    ok.onclick = function(){ setConsent('granted'); bar.remove(); loadPixel(); };
    no.onclick = function(){
      setConsent('denied'); bar.remove();
      if(loaded && window.fbq) window.fbq('consent', 'revoke');
    };
    bar.appendChild(text); bar.appendChild(ok); bar.appendChild(no);
    document.body.appendChild(bar);
  }

  function start(){
    const c = getConsent();
    if(c === 'denied') return;
    if(c === 'granted' || CONSENT_MODE === 'notice') loadPixel();
    if(c !== 'granted') showNotice();
  }

  // Lets the privacy page offer "change my choice".
  window.sosAdsConsentReset = function(){ try { localStorage.removeItem(CONSENT_KEY); } catch(e){} showNotice(); };

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
