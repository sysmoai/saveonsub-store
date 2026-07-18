#!/usr/bin/env python3
"""SAVEONSUB launch preflight — deploy-readiness checks BEYOND correctness (audit_all.py).
Run: python3 deploy_preflight.py   → exit 0 only if launch-ready.
Complements the harness: this catches launch-day footguns (wrong domain, placeholders,
localhost refs, inconsistent contact numbers, Emon-gated prices leaking live)."""
import os, re, json, sys, glob

DOMAIN = "https://saveonsub.com"
WA_SALES = "8801305869242"      # customer support / WhatsApp
BKASH = "8801305869242"        # merchant send-money number
fails, warns, notes = [], [], []

html_files = [f for f in glob.glob('**/*.html', recursive=True) if '.git' not in f]

# 1) Canonical + absolute URLs must all use the one https domain (no http, localhost, staging)
BAD_HOSTS = re.compile(r'https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|staging|test|example\.com|saveonsub\.pages\.dev)')
for f in html_files:
    h = open(f).read()
    if BAD_HOSTS.search(h): fails.append(f"{f}: references a non-production host")
    for m in re.findall(r'<link rel="canonical" href="([^"]+)"', h):
        if not m.startswith(DOMAIN): fails.append(f"{f}: canonical not on {DOMAIN} → {m}")
    if 'http://saveonsub.com' in h: fails.append(f"{f}: insecure http:// canonical/link")

# 2) No placeholder / dev leftovers in shipped pages
# Case-SENSITIVE code tokens (avoid matching the HTML placeholder="" attr or words like "financial")
CODE_TOKENS = ['TODO:', 'FIXME', 'CHANGEME', 'Lorem ipsum', 'lorem ipsum', 'coming soon']
BROKEN_PRICE = re.compile(r'৳\s*(NaN|undefined|null|None|Infinity)', re.I)
STANDALONE_BAD = re.compile(r'>\s*(NaN|undefined)\s*<')  # a bad value rendered as visible text
for f in html_files:
    h = open(f).read()
    for p in CODE_TOKENS:
        if p in h: fails.append(f"{f}: contains dev token '{p}'")
    if BROKEN_PRICE.search(h): fails.append(f"{f}: BROKEN PRICE render (৳NaN/undefined)")
    if STANDALONE_BAD.search(h): fails.append(f"{f}: renders a NaN/undefined value as text")

# 3) Contact-number consistency (one sales number, one merchant number, everywhere)
for f in html_files:
    h = open(f).read().replace('-', '').replace(' ', '')
    # any wa.me link must point to the sales number
    for wanum in re.findall(r'wa\.me/(\d+)', h):
        if wanum != WA_SALES: fails.append(f"{f}: wa.me points to {wanum}, expected {WA_SALES}")
    # merchant number only appears at checkout; if present elsewhere it's fine but must be the right one
    for mnum in re.findall(r'\+?8801\d{9}', h):
        if mnum.lstrip('+') not in (WA_SALES, BKASH):
            warns.append(f"{f}: unknown BD phone number {mnum}")

# 4) Emon-gated: no 'proposed-new' price may ship live without confirmation
cat = json.load(open('catalog.json'))
proposed = [p['id'] for p in cat['products'] if p.get('price_source') == 'proposed-new']
if proposed:
    warns.append(f"{len(proposed)} product(s) still on 'proposed-new' pricing (Emon must confirm before/at launch): {', '.join(proposed[:8])}{'…' if len(proposed)>8 else ''}")

# 5) robots.txt ↔ sitemap agreement + canonical domain
robots = open('robots.txt').read()
if f"Sitemap: {DOMAIN}/sitemap.xml" not in robots: fails.append("robots.txt sitemap line missing/wrong domain")
if 'Disallow: /checkout.html' not in robots: warns.append("robots.txt no longer disallows /checkout.html")
sm = open('sitemap.xml').read()
if DOMAIN not in sm: fails.append("sitemap.xml domain mismatch")

# 6) Deploy artifact inventory
deploy_files = [f for f in glob.glob('**/*', recursive=True)
                if os.path.isfile(f) and not f.endswith(('.py', '.sh', '.md'))
                and '.git' not in f and not f.startswith('_BACKUPS')]
total_bytes = sum(os.path.getsize(f) for f in deploy_files)
big = sorted(((os.path.getsize(f), f) for f in deploy_files), reverse=True)[:3]
notes.append(f"deploy artifact: {len(deploy_files)} files, {total_bytes/1024/1024:.2f} MB total")
notes.append("largest: " + ", ".join(f"{f} ({b//1024}KB)" for b, f in big))
for must in ['index.html', '404.html', '_headers', '_redirects', 'robots.txt', 'sitemap.xml', 'sw.js', 'offline.html', 'assets/style.css']:
    if not os.path.exists(must): fails.append(f"deploy: missing required file {must}")
# Build-source files that must NOT ship (expose internal price_source/proposed prices/survey sourcing)
SOURCE_LEAKS = ['catalog.json']
for s in SOURCE_LEAKS:
    if s in deploy_files:
        blocked = f"/{s}" in open('_redirects').read() if os.path.exists('_redirects') else False
        if not blocked:
            warns.append(f"deploy: {s} is a build source (not used at runtime — site reads assets/catalog.js) and exposes internal pricing/sourcing; exclude from deploy or block in _redirects")

# 7) Every canonical target actually exists on disk (self-referential integrity)
for f in html_files:
    h = open(f).read()
    m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if m:
        rel = m.group(1).replace(DOMAIN + '/', '').replace(DOMAIN, '') or 'index.html'
        if rel and not os.path.exists(rel) and not rel.endswith('/'):
            fails.append(f"{f}: canonical {m.group(1)} has no file on disk")

# ---- report ----
print("=" * 60)
print("SAVEONSUB — LAUNCH PREFLIGHT")
print("=" * 60)
for n in notes: print("  •", n)
print(f"\nHTML pages scanned: {len(html_files)}")
if warns:
    print(f"\n⚠️  {len(warns)} WARNING(S) — review, not blocking:")
    for w in warns: print("   -", w)
if fails:
    print(f"\n❌ {len(fails)} BLOCKER(S) — must fix before deploy:")
    for x in fails: print("   -", x)
    print("\nRESULT: NOT launch-ready.")
    sys.exit(1)
print("\n✅ RESULT: LAUNCH-READY — no blockers. Warnings (if any) are Emon-decisions.")
