/* SaveOnSub Google Analytics 4 bridge — maps first-party sos:track events to GA4.
 *
 * Fail-closed: if MEASUREMENT_ID is emptied this file makes no network request.
 * The ID is a public value, not a secret ("SaveOnSub Website" property 561849452,
 * account 414322003, web stream 16249309705).
 *
 * Consent: opt-in only. gtag.js is never requested until the visitor presses OK
 * on the cookie notice shown by meta-pixel.js (shared key sos_ads_consent_v1).
 * Global Privacy Control / Do Not Track always win. Decline after Accept stops
 * further hits on the next page and turns analytics_storage off at once.
 *
 * Event map:
 *   every page            → page_view (gtag config)
 *   /p/<id>.html          → view_item       (item_id, value = lowest price)
 *   sos_add_to_cart       → add_to_cart     (value, BDT)
 *   checkout with a cart  → begin_checkout  (value, items)
 *   sos_order_submit      → generate_lead   (value, transaction_id = order id)
 *   sos_whatsapp_click    → whatsapp_click
 * purchase is NOT sent from the browser: payment is confirmed by a human.
 */
(function(){
  'use strict';

  const MEASUREMENT_ID = 'G-YK7GRJ6X3X';
  const CURRENCY = 'BDT';
  const CONSENT_KEY = 'sos_ads_consent_v1';

  if(!/^G-[A-Z0-9]{6,12}$/.test(MEASUREMENT_ID)) return;

  const nav = navigator || {};
  if(nav.globalPrivacyControl === true || nav.doNotTrack === '1' || window.doNotTrack === '1') return;

  function getConsent(){ try { return localStorage.getItem(CONSENT_KEY) || ''; } catch(e){ return ''; } }

  let loaded = false;
  let viewedCheckout = false;

  window.dataLayer = window.dataLayer || [];
  function gtag(){ window.dataLayer.push(arguments); }

  function loadGa(){
    if(loaded) return;
    loaded = true;
    gtag('consent', 'default', {
      analytics_storage: 'granted', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied'
    });
    const s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + MEASUREMENT_ID;
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', MEASUREMENT_ID, {allow_google_signals: false, allow_ad_personalization_signals: false});
    pageEvents();
  }

  function send(name, params){
    if(!loaded) return;
    gtag('event', name, params || {});
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
      send('view_item', {
        currency: CURRENCY, value: p.value,
        items: [{item_id: p.id, item_name: p.name, item_category: p.category, price: p.value}]
      });
    }
    if(/\/checkout(?:\.html)?$/i.test(location.pathname)) beginCheckout();
  }

  function beginCheckout(){
    if(viewedCheckout) return;
    const items = cartItems();
    if(!items.length) return;
    viewedCheckout = true;
    send('begin_checkout', {
      currency: CURRENCY, value: cartValue(items),
      items: items.map(function(i){
        return {item_id: String(i.id), item_variant: String(i.plan || ''), price: Number(i.bdt) || 0, quantity: Number(i.qty) || 1};
      })
    });
  }

  window.addEventListener('sos:track', function(e){
    const d = (e && e.detail) || {};
    switch(d.event){
      case 'sos_add_to_cart':
        send('add_to_cart', {
          currency: CURRENCY, value: Number(d.value_bdt) || 0,
          items: [{item_id: String(d.product_id || ''), item_variant: String(d.plan || ''), price: Number(d.value_bdt) || 0}]
        });
        break;
      case 'sos_order_submit':
        send('generate_lead', {
          currency: CURRENCY, value: Number(d.value_bdt) || 0,
          transaction_id: String(d.order_id || ''), order_kind: String(d.order_kind || ''),
          payment_method: String(d.payment_method || '')
        });
        break;
      case 'sos_whatsapp_click':
        send('whatsapp_click', {link_text: String(d.link_text || '').slice(0, 64)});
        break;
    }
  });

  // meta-pixel.js owns the notice; it fires sos:consent with 'granted' | 'denied'.
  window.addEventListener('sos:consent', function(e){
    const v = e && e.detail;
    if(v === 'granted'){
      if(loaded) gtag('consent', 'update', {analytics_storage: 'granted'});
      else loadGa();
    }
    else if(v === 'denied' && loaded) gtag('consent', 'update', {analytics_storage: 'denied'});
  });

  function start(){
    if(getConsent() === 'granted') loadGa();
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
