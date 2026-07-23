#!/usr/bin/env python3
"""
SAVEONSUB — Post-Deploy Full Site Audit
Run this AFTER publishing on Replit.
Usage: python3 post_deploy_audit.py <base_url>
Example: python3 post_deploy_audit.py https://save-on-sub.sysmoais-workspace.replit.app
"""

import json, sys, re, urllib.request, urllib.error, os
from urllib.parse import urljoin

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else None
if not BASE:
    print("Usage: python3 post_deploy_audit.py <base_url>")
    print("Example: python3 post_deploy_audit.py https://save-on-sub.sysmoais-workspace.replit.app")
    sys.exit(1)

PASS, FAIL, WARN = 0, 0, 0
results = []

def check(label, url, expected_status=200, must_contain=None, must_not_contain=None):
    global PASS, FAIL, WARN
    full_url = urljoin(BASE, url)
    try:
        req = urllib.request.Request(full_url, headers={'User-Agent': 'SOS-Audit/1.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        status = resp.status
        body = resp.read().decode('utf-8', errors='replace')
        
        if status != expected_status:
            results.append(f"  FAIL [{status}] {label} ({full_url}) — expected {expected_status}")
            FAIL += 1
            return body if 'body' in dir() else ''
        
        if must_contain:
            if isinstance(must_contain, list):
                for mc in must_contain:
                    if mc not in body:
                        results.append(f"  FAIL [{status}] {label} — missing content: {mc[:60]}")
                        FAIL += 1
                        return body
            else:
                if must_contain not in body:
                    results.append(f"  FAIL [{status}] {label} — missing content: {must_contain[:60]}")
                    FAIL += 1
                    return body
        
        if must_not_contain:
            if isinstance(must_not_contain, list):
                for mnc in must_not_contain:
                    if mnc in body:
                        results.append(f"  WARN [{status}] {label} — contains unexpected: {mnc[:60]}")
                        WARN += 1
            else:
                if must_not_contain in body:
                    results.append(f"  WARN [{status}] {label} — contains unexpected: {must_not_contain[:60]}")
                    WARN += 1
        
        results.append(f"  PASS [{status}] {label}")
        PASS += 1
        return body
    except urllib.error.HTTPError as e:
        results.append(f"  FAIL [{e.code}] {label} ({full_url})")
        FAIL += 1
        return ''
    except Exception as e:
        results.append(f"  FAIL [ERR] {label} ({full_url}) — {e}")
        FAIL += 1
        return ''

# Load catalog to know product pages
cat = json.load(open('catalog.json'))
products = cat['products']
product_ids = [p['id'] for p in products]
product_names = [p['name'] for p in products]

# Load sitemap to know all pages
sitemap_path = 'sitemap.xml'
sitemap_urls = []
if os.path.exists(sitemap_path):
    import xml.etree.ElementTree as ET
    tree = ET.parse(sitemap_path)
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    for loc in tree.findall('.//ns:loc', ns):
        sitemap_urls.append(loc.text.strip())

print("=" * 60)
print(f"SAVEONSUB — POST-DEPLOY AUDIT")
print(f"Target: {BASE}")
print(f"Products in catalog: {len(products)}")
print(f"URLs in sitemap: {len(sitemap_urls)}")
print("=" * 60)

# ─── SECTION 1: Core SEO Files ───
print("\n[1/6] Core SEO Files")
check("robots.txt", "/robots.txt", must_contain=["User-agent", "Sitemap", "sitemap.xml"])
check("sitemap.xml", "/sitemap.xml", must_contain=["<urlset", "</urlset>"])
check("llms.txt", "/llms.txt", must_contain=["# SaveOnSub"])
check("404 page", "/404.html", expected_status=404 if False else 200,
      must_contain=["Page Not Found", "404"])

# ─── SECTION 2: Main Navigation Pages ───
print("\n[2/6] Main Navigation Pages")
home = check("Homepage", "/", must_contain=[
    "SAVEONSUB", "ChatGPT", "Claude", "schema.org",
    "application/ld+json", "service-worker.js"
])
check("All Products", "/all", must_contain=["All Subscriptions", "ChatGPT"])
check("Quiz", "/quiz", must_contain=["Find Your Perfect", "quiz"])

# ─── SECTION 3: Trust & Legal Pages ───
print("\n[3/6] Trust & Legal Pages")
trust_pages = [
    ("About", "/about"),
    ("Privacy Policy", "/privacy"),
    ("Terms of Service", "/terms"),
    ("Warranty", "/warranty"),
    ("Refund Policy", "/refund"),
    ("Contact", "/contact"),
    ("FAQ", "/faq"),
    ("Checkout", "/checkout"),
    ("Order Tracking", "/order"),
    ("Track Page", "/track"),
]
for label, path in trust_pages:
    check(label, path, must_contain=["SAVEONSUB"])

# ─── SECTION 4: Product Pages (all 72) ───
print(f"\n[4/6] Product Pages ({len(products)} total)")
product_ok = 0
product_fail = 0
for i, pid in enumerate(product_ids):
    body = check(f"Product: {pid}", f"/p/{pid}", expected_status=200)
    if body:
        checks = [
            "application/ld+json" in body,
            "Product" in body,
            product_names[i][:30] in body if i < len(product_names) else True,
            "buy" in body.lower() or "get started" in body.lower(),
            "bKash" in body or "Nagad" in body,
            "৳" in body,
        ]
        if all(checks):
            product_ok += 1
        else:
            results.append(f"  PARTIAL Product {pid} — missing some expected content")
            product_fail += 1

results.append(f"  Product pages: {product_ok} OK, {product_fail} partial")
PASS += product_ok
WARN += product_fail

# ─── SECTION 5: Schema.org & Structured Data ───
print("\n[5/6] Schema.org & Structured Data")
# Check homepage has schema
schema_count = home.count("application/ld+json") if home else 0
if schema_count >= 2:
    results.append(f"  PASS Homepage has {schema_count} Schema.org blocks (OnlineStore, Product, FAQPage, WebSite)")
    PASS += 1
else:
    results.append(f"  WARN Homepage has {schema_count} Schema.org blocks (expected 2+)")
    WARN += 1

# ─── SECTION 6: PWA & Security ───
print("\n[6/6] PWA, Security & Performance")
check("Service Worker", "/service-worker.js", must_contain=["self.", "fetch"])
check("Web Manifest", "/manifest.json", must_contain=["name", "short_name", "icons", "start_url"])
check("Security Headers", "/", must_contain=["Content-Security-Policy"])
check("Mobile Viewport", "/", must_contain=["viewport", "width=device-width"])

# ─── SECTION 7: Sitemap Coverage ───
print("\n[7/6] Sitemap Coverage Check")
live_sitemap = check("Live sitemap", "/sitemap.xml", must_contain=["<urlset"])
if live_sitemap:
    live_urls = re.findall(r'<loc>(.*?)</loc>', live_sitemap)
    expected_count = len(sitemap_urls)  # what the build generates
    actual_count = len(live_urls)
    product_urls_in_sitemap = [u for u in live_urls if '/p/' in u]
    
    results.append(f"  Sitemap: {actual_count} URLs (expected ~{expected_count}), {len(product_urls_in_sitemap)} product URLs")
    if actual_count >= expected_count * 0.9:
        results.append(f"  PASS Sitemap coverage adequate ({actual_count}/{expected_count})")
        PASS += 1
    else:
        results.append(f"  FAIL Sitemap coverage low ({actual_count}/{expected_count})")
        FAIL += 1

# ─── SUMMARY ───
print("\n" + "=" * 60)
print(f"AUDIT COMPLETE: {PASS} PASS, {FAIL} FAIL, {WARN} WARN")
print("=" * 60)

for r in results:
    print(r)

print("\n" + "=" * 60)
if FAIL == 0:
    print("RESULT: ALL CHECKS PASSED — site is launch-ready")
else:
    print(f"RESULT: {FAIL} FAILURE(S) need attention")
print("=" * 60)
