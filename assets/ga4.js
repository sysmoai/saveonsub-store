/* SaveOnSub Google Analytics 4 bridge — maps first-party sos:track events to GA4.
 *
 * Property "SaveOnSub Website" (separate SaveOnSub GA account, Asia/Dhaka, BDT).
 * The Measurement ID is a public value, not a secret. Emptying it makes this
 * file inert (no network request).
 *
 * Consent: shares the cookie notice and choice (localStorage sos_ads_consent_v1)
 * shown by meta-pixel.js. Global Privacy Control / Do Not Track always win and
 * nothing is loaded. "Decline" means nothing is loaded; a later Decline stops
 * further sending and sets analytics_storage to denied. Ads signals and ad
 * personalization are always off.
 *
 * Event map:
 *   every page          → page_view (automatic)
 *   /p/<id>.html        → view_item
 *   sos_add_to_cart     → add_to_cart
 *   checkout with cart  → begin_checkout
 *   sos_order_submit    → generate_lead (value, transaction id = order id)
 *   sos_whatsapp_click  → contact
 * purchase is not sent from the browser: payment is confirmed by a human.
 */
(function(){
  'use strict';

  const MEASUREMENT_ID = 'G-YK7GRJ6X3X';
  const CONSENT_KEY = 'sos_ads_consent_v1';
  const CONSENT_MODE = 'notice'; // must match meta-pixel.js: 'notice' | 'opt-in'
  const CURRENCY = 'BDT';

  if(!/^G-[A-Z0-9]{6,12}$/.test(MEASUREMENT_ID)) return;

  const nav = navigator || {};
  if(nav.globalPrivacyControl === true || nav.doNotTrack === '1' || window.doNotTrack === '1') return;

  function getConsent(){ try { return localStorage.getItem(CONSENT_KEY) || ''; } catch(e){ return ''; } }

  let loaded = false;
  let stopped = false;
  let checkoutSent = false;

  window.dataLayer = window.dataLayer || [];
  function gtag(){ window.dataLayer.push(arguments); }

  function load(){
    if(loaded || stopped) return;
    loaded = true;
    gtag('consent', 'default', {
      analytics_storage: 'granted',
      ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied'
    });
    const s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(MEASUREMENT_ID);
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', MEASUREMENT_ID, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      currency: CURRENCY
    });
    pageEvents();
  }

  function stop(){
    stopped = true;
    if(loaded) gtag('consent', 'update', {analytics_storage: 'denied'});
  }

  function send(name, params){
    if(!loaded || stopped) return;
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
      send('view_item', {currency: CURRENCY, value: p.value,
        items: [{item_id: p.id, item_name: p.name, item_category: p.category}]});
    }
    if(/\/checkout(?:\.html)?$/i.test(location.pathname)) beginCheckout();
  }

  function beginCheckout(){
    if(checkoutSent) return;
    const items = cartItems();
    if(!items.length) return;
    checkoutSent = true;
    send('begin_checkout', {currency: CURRENCY, value: cartValue(items),
      items: items.map(function(i){ return {item_id: String(i.id), quantity: Number(i.qty) || 1}; })});
  }

  window.addEventListener('sos:track', function(e){
    const d = (e && e.detail) || {};
    switch(d.event){
      case 'sos_add_to_cart':
        send('add_to_cart', {currency: CURRENCY, value: Number(d.value_bdt) || 0,
          items: [{item_id: String(d.product_id || ''), item_variant: String(d.plan || '')}]});
        break;
      case 'sos_order_submit':
        send('generate_lead', {currency: CURRENCY, value: Number(d.value_bdt) || 0,
          transaction_id: String(d.order_id || ''), order_kind: String(d.order_kind || '')});
        break;
      case 'sos_whatsapp_click':
        send('contact', {link_text: String(d.link_text || '')});
        break;
    }
  });

  // Same notice as the Meta Pixel: meta-pixel.js fires sos:consent on a choice.
  window.addEventListener('sos:consent', function(e){
    const v = e && e.detail && e.detail.value;
    if(v === 'granted'){
      stopped = false;
      if(loaded) gtag('consent', 'update', {analytics_storage: 'granted'});
      else load();
    } else if(v === 'denied') stop();
  });

  function start(){
    const c = getConsent();
    if(c === 'denied') return;
    if(c === 'granted' || CONSENT_MODE === 'notice') load();
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
