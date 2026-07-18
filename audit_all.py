#!/usr/bin/env python3
"""SAVEONSUB permanent harness: audits the ENTIRE store. Run after every change.
python3 audit_all.py  → exit 0 only if 0 gaps."""
import os, re, json, sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

issues = []
cat = json.load(open('catalog.json'))
ids = {p['id'] for p in cat['products']}

class V(HTMLParser):
    VOID = {'meta','br','img','input','hr','link'}
    def __init__(self): super().__init__(); self.stack=[]; self.errs=[]
    def handle_starttag(self,t,a):
        if t not in self.VOID: self.stack.append(t)
    def handle_endtag(self,t):
        if self.stack and self.stack[-1]==t: self.stack.pop()
        else: self.errs.append(t)

pages = []
for root, dirs, files in os.walk('.'):
    if '.git' in root: continue
    for f in files:
        if f.endswith('.html'): pages.append(os.path.join(root, f).replace('./',''))

NOINDEX_OK = {'checkout.html','404.html'}
for pg in sorted(pages):
    h = open(pg).read()
    v = V(); v.feed(h)
    if v.stack or v.errs: issues.append(f"{pg}: HTML {v.stack[:2]}{v.errs[:2]}")
    m = re.search(r'<title>(.*?)</title>', h)
    if not m: issues.append(f"{pg}: no title"); continue
    if len(m.group(1)) > 70: issues.append(f"{pg}: title {len(m.group(1))}ch")
    d = re.search(r'name="description" content="(.*?)"', h)
    if not d: issues.append(f"{pg}: no description")
    elif len(d.group(1)) > 165: issues.append(f"{pg}: desc {len(d.group(1))}ch")
    if h.count('<h1') != 1: issues.append(f"{pg}: h1×{h.count('<h1')}")
    if 'rel="canonical"' not in h and os.path.basename(pg) not in NOINDEX_OK: issues.append(f"{pg}: no canonical")
    if 'lang="en"' not in h and 'lang="bn"' not in h: issues.append(f"{pg}: no lang")
    if 'viewport' not in h: issues.append(f"{pg}: no viewport")
    if 'class="skip"' not in h and os.path.basename(pg) != 'offline.html': issues.append(f"{pg}: no skip-to-content link (a11y)")
    for i, s in enumerate(re.findall(r'application/ld\+json">(.*?)</script>', h, re.S)):
        try: json.loads(s)
        except Exception as e: issues.append(f"{pg}: JSON-LD#{i} invalid")
    if 'aggregateRating' in h: issues.append(f"{pg}: FAKE RATING — dishonest schema")
    # RICH-RESULTS required fields (Google) — parse each JSON-LD block
    for s in re.findall(r'application/ld\+json[^>]*>(.*?)</script>', h, re.S):
        try: dd = json.loads(s)
        except Exception: continue
        for obj in (dd if isinstance(dd, list) else [dd]):
            ty = obj.get('@type'); ty = ty[0] if isinstance(ty, list) else ty
            if ty == 'Product':
                if 'name' not in obj: issues.append(f"{pg}: Product schema no name")
                if not any(k in obj for k in ('offers','review','aggregateRating')): issues.append(f"{pg}: Product no offers")
                if 'image' not in obj: issues.append(f"{pg}: Product schema no image (Google rich-result)")
                of = obj.get('offers', {})
                if isinstance(of, dict) and of.get('@type') == 'AggregateOffer':
                    for k in ('lowPrice','priceCurrency'):
                        if k not in of: issues.append(f"{pg}: AggregateOffer no {k}")
                    for sub in of.get('offers', []):
                        if 'priceValidUntil' not in sub: issues.append(f"{pg}: Offer no priceValidUntil")
                        if 'hasMerchantReturnPolicy' not in sub: issues.append(f"{pg}: Offer no return policy")
            if ty == 'FAQPage':
                for q in obj.get('mainEntity', []):
                    if 'name' not in q or 'acceptedAnswer' not in q: issues.append(f"{pg}: FAQ item malformed")
            if ty == 'BreadcrumbList':
                for it in obj.get('itemListElement', []):
                    if 'position' not in it or 'name' not in it: issues.append(f"{pg}: Breadcrumb item malformed")
            if ty == 'Article':
                if 'image' not in obj: issues.append(f"{pg}: Article no image (Google rich-result)")
                if 'headline' not in obj: issues.append(f"{pg}: Article no headline")
                pub = obj.get('publisher', {})
                if 'logo' not in pub: issues.append(f"{pg}: Article publisher no logo")
    # link integrity
    base = os.path.dirname(pg)
    for l in set(re.findall(r'href="([^"#?]+)"', h)):
        if l.startswith(('http','mailto','tel',"'")) or any(c in l for c in ('${','+','`',"'")): continue  # skip JS-built links
        target = l.lstrip('/') or 'index.html' if l.startswith('/') else os.path.normpath(os.path.join(base, l))
        if not os.path.exists(target): issues.append(f"{pg}: DEAD LINK {l}")
    for l in set(re.findall(r'src="([^"]+)"', h)):
        if l.startswith('http'): continue
        target = l.lstrip('/') if l.startswith('/') else os.path.normpath(os.path.join(base, l))
        if not os.path.exists(target): issues.append(f"{pg}: DEAD SRC {l}")
    # numbers consistency
    if '01865385348' in h.replace('-','').replace(' ','') and '8801305869242' not in h.replace('-','').replace(' ','').replace('+',''):
        issues.append(f"{pg}: WhatsApp number malformed")

# catalog completeness: page + sitemap + llms per product
sm = open('sitemap.xml').read(); ll = open('llms.txt').read()
for pid in ids:
    if not os.path.exists(f"p/{pid}.html"): issues.append(f"catalog: no page for {pid}")
    if not os.path.exists(f"assets/social/{pid}.png"): issues.append(f"social card missing for {pid}")
    if not os.path.exists(f"bn/p/{pid}.html"): issues.append(f"Bangla page missing for {pid}")
    if 'SpeakableSpecification' not in open(f"p/{pid}.html").read(): issues.append(f"{pid}: no speakable schema (voice/GEO)")
    if f"/bn/p/{pid}.html" not in sm: issues.append(f"sitemap: missing bn/{pid}")
    if f"/p/{pid}.html" not in sm: issues.append(f"sitemap: missing {pid}")
    if f"/p/{pid}.html" not in ll: issues.append(f"llms.txt: missing {pid}")
# sitemap URLs all exist
t = ET.parse('sitemap.xml'); ns = {'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
for u in t.getroot():
    p = u.find('s:loc', ns).text.replace('https://saveonsub.com/','') or 'index.html'
    if not os.path.exists(p): issues.append(f"sitemap: dead {p}")
# robots + core files
for f in ['robots.txt','llms.txt','sitemap.xml','assets/style.css','assets/app.js','assets/catalog.js','404.html']:
    if not os.path.exists(f): issues.append(f"missing core file {f}")
# security headers present in _headers
_hdr = open('_headers').read()
for _sec in ['Content-Security-Policy','Strict-Transport-Security','X-Content-Type-Options','frame-ancestors']:
    if _sec not in _hdr: issues.append(f"_headers missing {_sec}")
if "script-src 'self'" not in _hdr: issues.append("_headers CSP missing script-src self restriction")
# catalog.js freshness vs catalog.json
cj = open('assets/catalog.js').read()
if str(cat['products'][0]['plans'][0]['bdt']) not in cj: issues.append("catalog.js stale — rerun build_catalog.py")
# a11y/perf: dark color-scheme declared + reduced-motion + focus states in CSS
_css = open('assets/style.css').read()
if 'color-scheme' not in _css: issues.append("style.css missing color-scheme (dark form controls / no flash)")
if 'prefers-reduced-motion' not in _css: issues.append("style.css missing reduced-motion support")
if ':focus' not in _css: issues.append("style.css missing focus states (keyboard a11y)")

# HOMEPAGE DRIFT: bestseller prices on index must match catalog
idx=open('index.html').read()
for p in cat['products']:
    if p.get('bestseller_rank',0)>0:
        f=min(pl['bdt'] for pl in p['plans'])
        if f"৳{f:,}" not in idx and f"৳{f}" not in idx:
            issues.append(f"HOMEPAGE DRIFT: {p['id']} from-price ৳{f} not on index")
for f in ['blog/index.html','_headers','_redirects','build_all.sh','README.md','build_home.py','contact.html','track.html','students.html','offers.html','sitemap.html','bn.html',
          'sw.js','offline.html','assets/icon-192.png','assets/icon-512.png','order.html','bn/faq.html','bn/how-to-order.html']:
    if not os.path.exists(f): issues.append(f"missing {f}")
# order receipt must be reachable from checkout + save/read order via app.js
if "location.href='order.html'" not in open('checkout.html').read(): issues.append("checkout does not route to order.html")
if 'function saveOrder' not in open('assets/app.js').read(): issues.append("app.js missing saveOrder")
# PWA integrity: manifest must reference the icons that exist; SW must be registered site-wide
_mf = open('assets/site.webmanifest').read()
for _ic in ['icon-192.png','icon-512.png']:
    if _ic not in _mf: issues.append(f"manifest missing {_ic}")
if 'maskable' not in _mf: issues.append("manifest missing maskable icon (Android install)")
if "register('/sw.js')" not in open('assets/app.js').read(): issues.append("app.js does not register service worker")
if 'function suggestBangla' not in open('assets/app.js').read(): issues.append("app.js missing Bangla language auto-suggest")
if "caches.match('/offline.html')" not in open('sw.js').read(): issues.append("sw.js missing offline fallback")
if 'blog/index.html' not in open('sitemap.xml').read(): issues.append("blog index not in sitemap")
# guides must funnel to products (>=3 product links each) for internal equity + conversion
for _g in glob.glob('blog/*.html') if 'glob' in dir() else __import__('glob').glob('blog/*.html'):
    if _g.endswith('index.html'): continue
    _pl = len(set(re.findall(r'href="\.\./p/([^"]+)\.html"', open(_g).read())))
    if _pl < 3: issues.append(f"{_g}: only {_pl} product links (need >=3 for funnel)")
# IMAGE SITEMAP: namespace present + every image:loc that's a local asset exists
_smx = open('sitemap.xml').read()
if 'sitemap-image/1.1' not in _smx: issues.append("sitemap missing image namespace")
for _il in re.findall(r'<image:loc>(.*?)</image:loc>', _smx):
    _lp = _il.replace('https://saveonsub.com/','')
    if not os.path.exists(_lp): issues.append(f"image sitemap: dead image {_lp}")
if _smx.count('<image:image>') < len(ids): issues.append(f"image sitemap: only {_smx.count('<image:image>')} images for {len(ids)} products")
# hreflang annotations in sitemap (EN↔BN pairs)
if 'www.w3.org/1999/xhtml' not in _smx: issues.append("sitemap missing xhtml namespace for hreflang")
_bncount = _smx.count('hreflang="bn-bd"')
if _bncount < len(ids): issues.append(f"sitemap: only {_bncount} bn-bd alternates for {len(ids)} products")
# category pages exist + in sitemap
import re as _re
for _c in cat['categories']:
    if any(p['category']==_c for p in cat['products']):
        _cs=_re.sub(r"[^a-z0-9]+","-",_c.lower()).strip("-")
        if not os.path.exists(f"c/{_cs}.html"): issues.append(f"missing category page c/{_cs}.html")
        if f"/c/{_cs}.html" not in open('sitemap.xml').read(): issues.append(f"category {_cs} not in sitemap")
        if not os.path.exists(f"bn/c/{_cs}.html"): issues.append(f"missing Bangla category page bn/c/{_cs}.html")
        if f"/bn/c/{_cs}.html" not in open('sitemap.xml').read(): issues.append(f"Bangla category {_cs} not in sitemap")
# INTERNAL LINKING: every product page must link to its category landing page (equity + UX)
for _pp in cat['products']:
    _pcs = _re.sub(r"[^a-z0-9]+","-",_pp['category'].lower()).strip("-")
    if f'c/{_pcs}.html' not in open(f"p/{_pp['id']}.html").read(): issues.append(f"{_pp['id']}: EN page doesn't link its category")
    if f'c/{_pcs}.html' not in open(f"bn/p/{_pp['id']}.html").read(): issues.append(f"{_pp['id']}: BN page doesn't link its category")
# all.html (shop hub) must link every category landing page (crawlable equity + nav)
_allh = open('all.html').read()
for _c in cat['categories']:
    if any(p['category']==_c for p in cat['products']):
        _acs = _re.sub(r"[^a-z0-9]+","-",_c.lower()).strip("-")
        if f'c/{_acs}.html' not in _allh: issues.append(f"all.html doesn't link category {_acs}")
# ENTITY CONSISTENCY (AIO): one brand name, one phone, everywhere
ll2 = open('llms.txt').read()
if 'Q&A for AI assistants' not in ll2: issues.append("llms.txt missing AIO Q&A section")
import datetime as _dt
if _dt.date.today().isoformat() not in ll2 and 'answers current as of' in ll2:
    pass  # stamp exists; rebuilt date may differ from audit date — only flag if no stamp
if 'answers current as of' not in ll2: issues.append("llms.txt missing freshness stamp")
if 'বাংলা প্রশ্নোত্তর' not in ll2: issues.append("llms.txt missing Bangla AIO section")
# ENTITY: both homepages carry an Organization/OnlineStore with the verifiable family sameAs
for _hp in ['index.html','bn.html']:
    _h = open(_hp).read()
    if '"OnlineStore"' not in _h and '"Organization"' not in _h: issues.append(f"{_hp}: no Organization schema")
    if 'github.com/sysmoai' not in _h: issues.append(f"{_hp}: Organization missing sameAs family links")
    if '"founder"' not in _h: issues.append(f"{_hp}: Organization missing founder entity")
for pg2 in ['index.html','all.html','about.html','faq.html']:
    h2 = open(pg2).read()
    if 'SaveOnSub' in h2.replace('SAVEONSUB',''): issues.append(f"{pg2}: inconsistent brand casing")
    if '8801305869242' not in h2.replace('-','').replace(' ',''): issues.append(f"{pg2}: WhatsApp entity missing")
print(f"AUDITED: {len(pages)} pages, {len(ids)} products, sitemap, robots, llms, assets")
if issues:
    print(f"❌ {len(issues)} GAPS:"); [print(" -", i) for i in issues[:25]]
    sys.exit(1)
print("✅ 0 GAPS — store is launch-clean")
