/* SAVEONSUB service worker — offline resilience for BD mobile networks */
const CACHE = 'sos-v1';
const CORE = ['/', '/index.html', '/all.html', '/offline.html',
  '/assets/style.css', '/assets/app.js', '/assets/catalog.js',
  '/assets/favicon.svg', '/assets/icon-192.png', '/assets/site.webmanifest'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE).catch(()=>{})).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    // network-first for pages (fresh prices), fall back to cache, then offline page
    e.respondWith(fetch(req).then(r => { const cp=r.clone(); caches.open(CACHE).then(c=>c.put(req,cp)); return r; })
      .catch(() => caches.match(req).then(r => r || caches.match('/offline.html'))));
  } else {
    // cache-first for static assets
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => {
      const cp=res.clone(); caches.open(CACHE).then(c=>c.put(req,cp)); return res;
    }).catch(()=>r)));
  }
});
