/* SaveOnSub measurement/attribution layer — no external tracker by itself.
 * Captures only page/referrer-host/UTM context in sessionStorage, emits
 * dataLayer events for a future GA4/GTM integration, and appends source context
 * to WhatsApp order/support messages so conversions can be attributed today.
 */
(function(){
  'use strict';

  const KEY = 'sos_session_attribution_v1';
  const MAX = 64;

  function clean(v){
    return String(v || '').replace(/[\r\n|]/g, ' ').trim().slice(0, MAX);
  }
  function refHost(){
    try { return document.referrer ? clean(new URL(document.referrer).hostname) : ''; }
    catch(e){ return ''; }
  }
  function currentAttribution(){
    let a = null;
    try { a = JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch(e){}
    if(!a){
      const q = new URLSearchParams(location.search);
      a = {
        landing: clean(location.pathname || '/'),
        referrer: refHost(),
        utm_source: clean(q.get('utm_source')),
        utm_medium: clean(q.get('utm_medium')),
        utm_campaign: clean(q.get('utm_campaign'))
      };
      try { sessionStorage.setItem(KEY, JSON.stringify(a)); } catch(e){}
    }
    return a;
  }

  const ATTR = currentAttribution();
  window.dataLayer = window.dataLayer || [];

  function track(name, extra){
    const payload = Object.assign({
      event: 'sos_' + name,
      page_path: clean(location.pathname || '/'),
      landing_path: ATTR.landing,
      referrer_host: ATTR.referrer,
      utm_source: ATTR.utm_source,
      utm_medium: ATTR.utm_medium,
      utm_campaign: ATTR.utm_campaign
    }, extra || {});
    window.dataLayer.push(payload);
    try { window.dispatchEvent(new CustomEvent('sos:track', {detail: payload})); } catch(e){}
  }
  window.sosTrack = track;

  function attributionLine(){
    const parts = ['source=' + clean(location.pathname || '/')];
    if(ATTR.landing && ATTR.landing !== location.pathname) parts.push('landing=' + ATTR.landing);
    if(ATTR.referrer) parts.push('ref=' + ATTR.referrer);
    if(ATTR.utm_source) parts.push('utm_source=' + ATTR.utm_source);
    if(ATTR.utm_medium) parts.push('utm_medium=' + ATTR.utm_medium);
    if(ATTR.utm_campaign) parts.push('utm_campaign=' + ATTR.utm_campaign);
    return '[SOS attribution: ' + parts.join(' | ') + ']';
  }

  function enrichWhatsAppHref(href){
    try {
      const u = new URL(href, location.href);
      if(u.hostname !== 'wa.me' && !u.hostname.endsWith('.wa.me')) return href;
      const line = attributionLine();
      let text = u.searchParams.get('text') || '';
      if(!text.includes('[SOS attribution:')){
        text = text ? (text + '\n\n' + line) : line;
        u.searchParams.set('text', text);
      }
      return u.toString();
    } catch(e){ return href; }
  }

  // Dynamic helper links used by checkout/order flows.
  if(typeof window.waLink === 'function'){
    const originalWaLink = window.waLink;
    window.waLink = function(text){ return enrichWhatsAppHref(originalWaLink(text)); };
  }
  if(typeof window.waOrder === 'function'){
    const originalWaOrder = window.waOrder;
    window.waOrder = function(extra){ return enrichWhatsAppHref(originalWaOrder(extra)); };
  }
  if(typeof window.cartAdd === 'function'){
    const originalCartAdd = window.cartAdd;
    window.cartAdd = function(id, planLabel, bdt, name){
      track('add_to_cart', {product_id: clean(id), plan: clean(planLabel), value_bdt: Number(bdt) || 0});
      return originalCartAdd.apply(this, arguments);
    };
  }

  document.addEventListener('click', function(e){
    const a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if(a){
      const href = a.getAttribute('href') || '';
      if(/https?:\/\/wa\.me\//i.test(href)){
        const enriched = enrichWhatsAppHref(a.href);
        if(enriched !== a.href) a.href = enriched;
        track('whatsapp_click', {link_text: clean(a.textContent)});
      } else if(/checkout\.html|\/checkout(?:$|[?#])/i.test(href)){
        track('checkout_start', {link_text: clean(a.textContent)});
      }
    }
  }, true);

  track('page_view_ready');
})();
