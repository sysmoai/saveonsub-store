/* SaveOnSub Meta Pixel bridge — maps first-party sos:track events to Meta.
 *
 * Fail-closed: if PIXEL_ID is emptied this file makes no network request and
 * shows nothing. Setting the ID (a public value, not a secret) turns it on.
 *
 * Choice (CEO, 2026-11-12: no on-page cookie banner): measurement is on by
 * default and disclosed on /privacy. Global Privacy Control / Do Not Track
 * always win, and the privacy page's opt-out (sosAdsOptOut) stops tracking in
 * this browser until the visitor opts back in (sosAdsOptIn).
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

  const PIXEL_ID = '2330425734478961'; // "SaveOnSub Website" dataset
  const CURRENCY = 'BDT';
  const CONSENT_KEY = 'sos_ads_consent_v1';

  if(!/^\d{6,20}$/.test(PIXEL_ID)) return;

  const nav = navigator || {};
  if(nav.globalPrivacyControl === true || nav.doNotTrack === '1' || window.doNotTrack === '1') return;

  function getConsent(){ try { return localStorage.getItem(CONSENT_KEY) || ''; } catch(e){ return ''; } }
  function setConsent(v){ try { localStorage.setItem(CONSENT_KEY, v); } catch(e){} }
  function allowed(){ return getConsent() !== 'denied'; }

  let loaded = false;
  let viewedCheckout = false;

  function loadPixel(){
    if(loaded || !allowed()) return;
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
    if(!loaded || !window.fbq || !allowed()) return;
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

  // ga4.js listens for this; it loads Google Analytics only after 'granted'.
  function announce(v){ try { window.dispatchEvent(new CustomEvent('sos:consent', {detail: v})); } catch(e){} }

  function start(){
    if(allowed()) loadPixel();
  }

  // The privacy page offers these two links. Opt-out persists in this browser.
  window.sosAdsOptOut = function(){
    setConsent('denied');
    if(loaded && window.fbq) window.fbq('consent', 'revoke');
    announce('denied');
  };
  window.sosAdsOptIn = function(){
    setConsent('granted');
    if(loaded && window.fbq) window.fbq('consent', 'grant');
    else loadPixel();
    announce('granted');
  };
  window.sosAdsConsentReset = window.sosAdsOptOut; // old privacy-page link

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
