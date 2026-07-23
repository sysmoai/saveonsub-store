#!/usr/bin/env python3
"""SAVEONSUB brand assets v2 — 'Haor Teal' identity (unique to this brand).
Mark: price-tag tilted with ৳ — the 'honest price tag'. Run: python3 build_assets.py"""
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('assets', exist_ok=True)
BG = (6, 24, 26)          # Haor Deep #06181a
TEAL = (20, 212, 184)     # Taka Teal #14d4b8
TEAL2 = (46, 240, 210)    # bright #2ef0d2
SKY = (124, 199, 255)     # Meghna Sky #7cc7ff
AMBER = (255, 182, 72)    # Shondha Amber #ffb648
INK = (242, 251, 250)

def grad(draw, box, c1, c2):
    x0, y0, x1, y1 = box
    for i in range(max(1, x1 - x0)):
        t = i / max(1, x1 - x0 - 1)
        c = tuple(round(c1[j] + (c2[j] - c1[j]) * t) for j in range(3))
        draw.line([(x0 + i, y0), (x0 + i, y1)], fill=c)

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

# ---------- favicon.svg — the Honest Price Tag mark ----------
open('assets/favicon.svg', 'w').write(
"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#14d4b8"/><stop offset="1" stop-color="#7cc7ff"/></linearGradient></defs>
<rect width="64" height="64" rx="14" fill="#06181a"/>
<g transform="rotate(-12 32 32)">
<path d="M18 14 h20 a6 6 0 0 1 6 6 v24 a6 6 0 0 1 -6 6 h-20 a6 6 0 0 1 -6 -6 v-24 a6 6 0 0 1 6 -6 z" fill="none" stroke="url(#g)" stroke-width="4"/>
<circle cx="24" cy="22" r="3" fill="#ffb648"/>
<text x="30" y="44" font-family="Arial,Helvetica,sans-serif" font-size="24" font-weight="900" text-anchor="middle" fill="url(#g)">৳</text>
</g>
</svg>""")

# ---------- logo.svg — wordmark v2 ----------
open('assets/logo.svg', 'w').write(
"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 80">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#14d4b8"/><stop offset="1" stop-color="#7cc7ff"/></linearGradient></defs>
<rect width="460" height="80" rx="16" fill="#06181a"/>
<g transform="translate(14,14) rotate(-12 26 26)">
<path d="M12 6 h24 a5 5 0 0 1 5 5 v30 a5 5 0 0 1 -5 5 h-24 a5 5 0 0 1 -5 -5 v-30 a5 5 0 0 1 5 -5 z" fill="none" stroke="url(#g)" stroke-width="3.5"/>
<circle cx="17" cy="13" r="2.4" fill="#ffb648"/>
<text x="24" y="36" font-family="Arial,Helvetica,sans-serif" font-size="19" font-weight="900" text-anchor="middle" fill="url(#g)">৳</text>
</g>
<text x="78" y="52" font-family="Arial,Helvetica,sans-serif" font-size="33" font-weight="900" fill="#f2fbfa">SAVE<tspan fill="url(#g)">ON</tspan>SUB</text>
<text x="80" y="69" font-family="Arial,Helvetica,sans-serif" font-size="12.5" fill="#a3c9c4">সাবস্ক্রিপশনের সৎ দোকান</text>
</svg>""")

# ---------- apple-touch-icon.png ----------
img = Image.new('RGB', (180, 180), BG)
d = ImageDraw.Draw(img)
d.rounded_rectangle([40, 34, 140, 150], radius=16, outline=TEAL, width=9)
d.ellipse([56, 50, 74, 68], fill=AMBER)
d.text((90, 105), "৳", font=font(72), anchor="mm", fill=TEAL2)
img.save('assets/apple-touch-icon.png')

# ---------- PWA icons 192 & 512 (maskable-safe: mark centered with padding) ----------
def pwa_icon(sz):
    im = Image.new('RGB', (sz, sz), BG)
    dd = ImageDraw.Draw(im)
    # keep art inside the 80% safe zone so Android maskable crop never clips it
    m = int(sz*0.26); w = int(sz*0.055)
    dd.rounded_rectangle([m, m*0.9, sz-m, sz-m*0.78], radius=int(sz*0.09), outline=TEAL, width=max(3,w))
    dd.ellipse([m+int(sz*0.04), m*0.9+int(sz*0.04), m+int(sz*0.13), m*0.9+int(sz*0.13)], fill=AMBER)
    dd.text((sz//2, int(sz*0.56)), "৳", font=font(int(sz*0.34)), anchor="mm", fill=TEAL2)
    im.save(f'assets/icon-{sz}.png')
pwa_icon(192); pwa_icon(512)

# ---------- og-image.png 1200×630 ----------
og = Image.new('RGB', (1200, 630), BG)
d = ImageDraw.Draw(og)
grad(d, (0, 0, 1200, 8), TEAL, SKY)
grad(d, (0, 622, 1200, 630), SKY, TEAL)
d.rounded_rectangle([70, 180, 240, 400], radius=24, outline=TEAL, width=10)
d.ellipse([98, 210, 128, 240], fill=AMBER)
d.text((155, 320), "৳", font=font(110), anchor="mm", fill=TEAL2)
d.text((690, 210), "SAVEONSUB", font=font(92), anchor="mm", fill=INK)
d.text((690, 292), "সাবস্ক্রিপশনের সৎ দোকান — honest BD prices", font=font(34), anchor="mm", fill=(163, 201, 196))
d.text((690, 380), "ChatGPT ৳350 · Netflix ৳349 · Canva ৳299", font=font(44), anchor="mm", fill=TEAL2)
d.text((690, 460), "bKash / Nagad · 5–15 min · 1-hour warranty · pay-after-testing", font=font(28), anchor="mm", fill=(163, 201, 196))
d.text((690, 545), "saveonsub.com", font=font(36), anchor="mm", fill=SKY)
og.save('assets/og-image.png')

# ---------- per-product social cards (1200×630) — distinct OG image + Product schema image ----------
import json as _pj, re as _pre
_cat = _pj.load(open('catalog.json'))
os.makedirs('assets/social', exist_ok=True)
LBL = {"official":("OFFICIAL",TEAL2),"personal":("PERSONAL ACCOUNT",SKY),
       "shared-low":("SHARED · LOW RISK",AMBER),"shared-med":("SHARED · WARRANTY-COVERED",AMBER)}
def _wrap(dr, text, fnt, maxw):
    words=text.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if dr.textlength(t, font=fnt) <= maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines[:2]
_made=0
for _p in _cat['products']:
    nm=_pre.sub(r'^[^\w৳]+','',_p['name']).strip()  # strip leading emoji
    frm=min(pl['bdt'] for pl in _p['plans'])
    lbl=None
    for pl in _p['plans']:
        tos=pl.get('tos','')
        if tos in LBL: lbl=LBL[tos]; break
    im=Image.new('RGB',(1200,630),BG); dr=ImageDraw.Draw(im)
    grad(dr,(0,0,1200,8),TEAL,SKY); grad(dr,(0,622,1200,630),SKY,TEAL)
    # brand mark row (Latin-safe: DejaVu has no ৳/Bengali glyphs, so use 'Tk' + English tagline)
    dr.rounded_rectangle([70,60,146,164],radius=14,outline=TEAL,width=7)
    dr.ellipse([84,78,106,100],fill=AMBER)
    dr.text((108,128),"Tk",font=font(34),anchor="mm",fill=TEAL2)
    dr.text((176,90),"SAVEONSUB",font=font(40),anchor="lm",fill=INK)
    dr.text((178,136),"Bangladesh's honest subscription store",font=font(24),anchor="lm",fill=(163,201,196))
    # product name (wrapped, up to 2 lines)
    y=258
    for ln in _wrap(dr,nm,font(70),1060):
        dr.text((70,y),ln,font=font(70),anchor="lm",fill=INK); y+=82
    # price + category
    pr=f"from Tk {frm:,}"
    dr.text((70,y+22),pr,font=font(62),anchor="lm",fill=TEAL2)
    catw=dr.textlength(pr,font=font(62))
    dr.text((70+catw+26,y+34),f"· {_p['category']}",font=font(30),anchor="lm",fill=(163,201,196))
    # honest label chip
    if lbl:
        txt,col=lbl; cw=dr.textlength(txt,font=font(26))
        dr.rounded_rectangle([70,y+82,70+cw+40,y+128],radius=12,outline=col,width=3)
        dr.text((90,y+105),txt,font=font(26),anchor="lm",fill=col)
    # footer (two safe rows — no overlap)
    dr.text((70,548),"bKash · Nagad · Rocket  ·  5–15 min delivery  ·  1-hour warranty",font=font(27),anchor="lm",fill=(163,201,196))
    dr.text((70,590),"saveonsub.com",font=font(30),anchor="lm",fill=SKY)
    im.save(f"assets/social/{_p['id']}.png"); _made+=1
print(f"OK per-product social cards: {_made}")

# ---------- manifest (installable PWA: full icon set, shortcuts, categories) ----------
import json as _json
_manifest = {
  "name": "SAVEONSUB — Premium Subscriptions at BD Prices",
  "short_name": "SAVEONSUB",
  "description": "Premium subscriptions at honest BD prices, paid with bKash/Nagad/Rocket.",
  "start_url": "/?utm_source=pwa",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#06181a",
  "theme_color": "#06181a",
  "lang": "en-BD",
  "dir": "ltr",
  "categories": ["shopping", "business", "productivity"],
  "icons": [
    {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
    {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    {"src": "/assets/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}
  ],
  "shortcuts": [
    {"name": "All Products", "url": "/all.html", "description": "Browse the full catalog"},
    {"name": "Find My AI (Quiz)", "url": "/quiz.html", "description": "60-second product finder"},
    {"name": "Track Order", "url": "/track.html", "description": "Check your order status"}
  ]
}
open('assets/site.webmanifest', 'w').write(_json.dumps(_manifest, ensure_ascii=False))

# ---------- service worker (offline-first shell, network-first for HTML) ----------
SW = r'''/* SAVEONSUB service worker — offline resilience for BD mobile networks */
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
'''
open('sw.js', 'w').write(SW)

# ---------- offline.html (self-contained; renders with no network) ----------
OFFLINE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offline — SAVEONSUB</title>
<meta name="description" content="You are offline. SAVEONSUB works again the moment your connection returns.">
<link rel="canonical" href="https://saveonsub.com/offline.html">
<meta name="robots" content="noindex,follow">
<meta name="theme-color" content="#06181a">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<style>
  html,body{margin:0;height:100%;background:#06181a;color:#eaf6f3;
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans Bengali",sans-serif}
  .wrap{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;
    text-align:center;padding:32px;box-sizing:border-box}
  .mark{font-size:64px;line-height:1;margin-bottom:8px}
  h1{font-size:26px;margin:12px 0 6px;color:#2ef0d2}
  p{max-width:440px;color:#a3c9c4;font-size:15.5px;line-height:1.6;margin:6px 0}
  .bn{color:#7cc7ff;margin-top:4px}
  .btns{display:flex;gap:12px;flex-wrap:wrap;justify-content:center;margin-top:22px}
  a.btn{display:inline-flex;align-items:center;gap:6px;padding:12px 20px;border-radius:12px;
    font-weight:800;text-decoration:none;font-size:15px}
  .primary{background:linear-gradient(90deg,#14d4b8,#7cc7ff);color:#06181a}
  .ghost{border:1.5px solid #14406a;color:#7cc7ff}
  .wa{background:#25d366;color:#04231a}
</style>
</head>
<body>
<div class="wrap">
  <div class="mark">📴</div>
  <h1>You're offline</h1>
  <p>No internet right now — but SAVEONSUB is installed and will work the second your connection is back.</p>
  <p class="bn">ইন্টারনেট নেই। সংযোগ ফিরলেই আবার সব চলবে।</p>
  <div class="btns">
    <a class="btn primary" href="/index.html">↻ Try again</a>
    <a class="btn ghost" href="/all.html">Browse cached catalog</a>
    <a class="btn wa" href="https://wa.me/8801305869242?text=Hi!">💬 WhatsApp us</a>
  </div>
</div>
</body>
</html>'''
open('offline.html', 'w').write(OFFLINE)

for f_ in ['assets/favicon.svg','assets/logo.svg','assets/apple-touch-icon.png','assets/icon-192.png','assets/icon-512.png','assets/og-image.png','assets/site.webmanifest','sw.js','offline.html']:
    print(f"OK {f_}: {os.path.getsize(f_)} bytes")
