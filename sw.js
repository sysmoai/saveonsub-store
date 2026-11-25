/* SAVEONSUB service worker — offline resilience for BD mobile networks */
const CACHE = 'sos-b0f5b73b8439';
const CORE = ['/', '/index.html', '/all.html', '/offline.html',
  '/assets/style.css', '/assets/app.js', '/assets/catalog.js',
  '/assets/favicon.svg', '/assets/icon-192.png', '/assets/site.webmanifest'];
// Only these responses are safe to persist: a 404/5xx body written into the
// cache would be replayed offline instead of offline.html.
const cacheable = r => r && r.ok && r.type === 'basic';
// Network-first (cache only as the offline fallback).
const FRESH = new Set(['/assets/catalog.js', '/assets/app.js']);
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE).catch(()=>{})).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  // Price-governing scripts must match the page they run on. A stale
  // catalog.js next to a fresh page makes the cart guard refuse the new
  // price, so the first "Add to cart" after a price release did nothing.
  const fresh = FRESH.has(new URL(req.url).pathname);
  if (req.mode === 'navigate' || fresh) {
    // network-first for pages (fresh prices), fall back to cache, then offline page
    e.respondWith(fetch(req).then(r => {
      if (cacheable(r)) { const cp=r.clone(); caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{}); }
      return r;
    }).catch(() => caches.match(req).then(r => r || (fresh ? Response.error() : caches.match('/offline.html')))));
  } else {
    // stale-while-revalidate: serve instantly, but always refresh in the
    // background so a price/catalog change lands on the next view rather
    // than never. Pure cache-first pinned stale prices indefinitely.
    e.respondWith(caches.match(req).then(hit => {
      const net = fetch(req).then(res => {
        if (cacheable(res)) { const cp=res.clone(); caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{}); }
        return res;
      });
      return hit || net;
    }));
  }
});
