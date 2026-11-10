#!/usr/bin/env python3
"""Stage /prices and /bn/prices: every CEO-approved plan on one page (build step).

Runs after product_rich_results.py and before hold_content_price_guard.py.
Plans come only from the staged governed catalog (_site/assets/catalog.js),
so no price can appear here that is not in the pricebook. Each product is a
listing card (<div class="pcard">) whose prices precede its product link, the
shape hold_content_price_guard already accepts for listing cards: a price is
kept only when it is approved for the product the card links to.

Also adds the pages to sitemap.xml and links each priced product page to them.
`--check` re-verifies without writing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import product_rich_results as rr

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
BASE = rr.BASE
MARK = "prices-page-2026-11-06"


def card(pid: str, p: dict, bn: bool) -> str:
    rows = "".join(
        f'<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;padding:6px 0;'
        f'border-top:1px solid var(--line,rgba(127,127,127,.2))"><span>{rr.esc(pl.get("label", "Plan"))}'
        f'<br><small style="color:var(--muted)">{rr.access_text(pl, bn)}</small></span>'
        f'<div class="price">{rr.price_text(pl, bn)}</div></div>'
        for pl in p["plans"])
    more = "বিস্তারিত ও অর্ডার" if bn else "Details and order"
    return (f'<div class="pcard"><h3 style="font-size:17px;margin:0 0 4px">{rr.esc(rr.clean_name(p["name"]))}</h3>'
            f'{rows}<div class="ctas"><a class="btn btn-ghost btn-sm" href="p/{pid}">{more}</a></div></div>')


def page(template: str, products: dict[str, dict], policy: dict, bn: bool) -> str:
    url = f"{BASE}{'/bn' if bn else ''}/prices"
    latest = max((rr.approved_on(pid, policy) for pid in products), default="")
    n = len(products)
    if bn:
        title = "AI সাবস্ক্রিপশনের দাম বাংলাদেশে — প্রাইস লিস্ট | SAVEONSUB"
        desc = (f"ChatGPT, Gemini, Claude, Canva, Netflix সহ {n}টি সাবস্ক্রিপশনের বর্তমান দাম টাকায়, "
                "অ্যাক্সেস টাইপসহ। bKash, Nagad বা Rocket-এ পেমেন্ট।")
        h1 = "AI ও ডিজিটাল সাবস্ক্রিপশনের দাম — বাংলাদেশ"
        intro = (f"SaveOnSub-এর সব দাম এক তালিকায় (সর্বশেষ হালনাগাদ {latest})। "
                 "শেয়ার্ড প্ল্যানে একাধিক ব্যবহারকারী একই অ্যাকাউন্ট ব্যবহার করেন; কাজ বা গোপন তথ্যের জন্য "
                 "কাস্টমার-নির্দিষ্ট প্ল্যান নিন। পেমেন্টের আগে WhatsApp-এ চূড়ান্ত দাম নিশ্চিত করা হয়।")
    else:
        title = "AI Subscription Prices in Bangladesh (BDT) | SAVEONSUB"
        desc = (f"Current BDT prices for {n} subscriptions incl. ChatGPT, Gemini, Claude, Canva and Netflix, "
                "with access type. Pay by bKash, Nagad or Rocket.")
        h1 = "AI and digital subscription prices in Bangladesh"
        intro = (f"Every SaveOnSub price in one list (last updated {latest}). "
                 "On a shared plan several people use one account; choose a customer-specific plan for work or "
                 "private data. The final price is confirmed on WhatsApp before payment.")
    by_cat: dict[str, list[str]] = {}
    for pid, p in products.items():
        by_cat.setdefault(p.get("category", "Other"), []).append(card(pid, p, bn))
    sections = "".join(
        f'<h2 class="mt3" style="font-size:20px">{rr.esc(cat)}</h2>'
        f'<div class="grid mt2" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">'
        f'{"".join(cards)}</div>' for cat, cards in by_cat.items())
    main = (f'<main id="main" data-sos="{MARK}"><div class="wrap"><h1>{h1}</h1><p>{intro}</p>'
            f'{sections}</div></main>')
    t = re.sub(r"<main\b.*?</main>", lambda _m: main, template, count=1, flags=re.S)
    t = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', "", t, flags=re.S)
    t = rr.set_title(t, title)
    for attr, name, val in (("name", "description", desc), ("property", "og:title", title),
                            ("property", "og:description", desc), ("property", "og:url", url)):
        t = rr.set_meta(t, attr, name, val)
    t = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', t)
    for lang, href in (("en-bd", "/prices"), ("bn-bd", "/bn/prices"), ("x-default", "/prices")):
        t = re.sub(rf'hreflang="{lang}" href="[^"]*"', f'hreflang="{lang}" href="{BASE}{href}"', t)
    items = [{"@type": "ListItem", "position": i + 1, "url": f"{BASE}{'/bn' if bn else ''}/p/{pid}",
              "name": rr.clean_name(p["name"])} for i, (pid, p) in enumerate(products.items())]
    ld = rr.jsonld({"@context": "https://schema.org", "@type": "ItemList", "@id": url + "#list",
                    "name": title, "numberOfItems": n, "itemListElement": items})
    return t.replace("</head>", ld + "</head>", 1)


def add_sitemap(site: Path, date: str) -> None:
    sm = site / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    if f"<loc>{BASE}/prices</loc>" in s:
        return
    alt = "".join(f'<xhtml:link rel="alternate" hreflang="{lang}" href="{BASE}{href}"/>'
                  for lang, href in (("en-bd", "/prices"), ("bn-bd", "/bn/prices"), ("x-default", "/prices")))
    entry = "".join(f"  <url><loc>{BASE}{p}</loc><lastmod>{date}</lastmod><changefreq>weekly</changefreq>"
                    f"<priority>0.9</priority>{alt}</url>\n" for p in ("/prices", "/bn/prices"))
    sm.write_text(s.replace("</urlset>", entry + "</urlset>", 1), encoding="utf-8")


def link_from_products(site: Path, products: dict[str, dict]) -> None:
    for pid in products:
        for path, bn in ((site / "p" / f"{pid}.html", False), (site / "bn" / "p" / f"{pid}.html", True)):
            if not path.exists():
                continue
            t = path.read_text(encoding="utf-8")
            if 'href="../prices"' in t:
                continue
            label = "সব প্রোডাক্টের দাম একসাথে" if bn else "All prices in one list"
            link = f' <a href="../prices" style="font-size:13px">{label} →</a>'
            t = re.sub(r'(<section data-sos="%s" class="quick-answer".*?)(</p></section>)' % rr.MARK,
                       lambda m: m.group(1) + link + m.group(2), t, count=1, flags=re.S)
            path.write_text(t, encoding="utf-8")


def check(site: Path, products: dict[str, dict]) -> list[str]:
    errors = []
    for rel, bn in (("prices.html", False), ("bn/prices.html", True)):
        path = site / rel
        if not path.exists():
            errors.append(f"{rel}: missing")
            continue
        t = path.read_text(encoding="utf-8")
        cards = t.count('class="pcard"')
        if cards != len(products):
            errors.append(f"{rel}: {cards} cards != {len(products)} priced products")
        for m in re.finditer(r'<div class="pcard">(.*?)href="p/([a-z0-9-]+)"', t, re.S):
            allowed = {int(pl["bdt"]) for pl in products.get(m.group(2), {}).get("plans", [])}
            shown = {int(x.replace(",", "")) for x in re.findall(r"৳([\d,]+)", m.group(1))}
            if not shown or shown != allowed:
                errors.append(f"{rel}: {m.group(2)} shows {sorted(shown)} != approved {sorted(allowed)}")
        if f'<link rel="canonical" href="{BASE}{"/bn" if bn else ""}/prices">' not in t:
            errors.append(f"{rel}: canonical")
    sm = (site / "sitemap.xml").read_text(encoding="utf-8")
    for p in ("/prices", "/bn/prices"):
        if f"<loc>{BASE}{p}</loc>" not in sm:
            errors.append(f"sitemap.xml: {p} missing")
    return errors


def main(argv: list[str]) -> int:
    if not (SITE / "assets" / "catalog.js").exists():
        raise SystemExit("[prices-page] _site missing; run the build first")
    policy = json.loads(rr.POLICY.read_text(encoding="utf-8"))
    products = rr.priced(rr.load_catalog(SITE))
    if "--check" not in argv:
        for bn in (False, True):
            src = SITE / ("bn/about.html" if bn else "about.html")
            out = SITE / ("bn/prices.html" if bn else "prices.html")
            out.write_text(page(src.read_text(encoding="utf-8"), products, policy, bn), encoding="utf-8")
        add_sitemap(SITE, max((rr.approved_on(pid, policy) for pid in products), default=""))
        link_from_products(SITE, products)
        print("[prices-page] staged /prices and /bn/prices")
    errors = check(SITE, products)
    if errors:
        print("\n".join(errors[:60]), file=sys.stderr)
        raise SystemExit(f"[prices-page] FAIL — {len(errors)} issue(s)")
    print(f"[prices-page] PASS — {len(products)} product cards per locale, prices == pricebook, sitemap entries present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
