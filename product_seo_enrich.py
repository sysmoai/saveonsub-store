#!/usr/bin/env python3
"""Product-page SEO enrichment for the staged site (build step).

Runs after commercial_truth_v2.py has written the governed product bodies and
before the HOLD/claims guards, so every guard still checks the final HTML.

Per product page (EN /p and BN /bn/p) it:
- sets a short, emoji-free title (<= 60 chars) and a product-specific meta
  description built from ops/seo/PRODUCT-COPY-*.json;
- strips decorative emoji from the H1;
- adds unique crawlable sections: "What is X", an official-price reference
  (official provider link only, no numeric price, never a SaveOnSub price),
  and related-product internal links (same category, bundles, contents);
- adds BreadcrumbList JSON-LD where it is missing.

It never adds a SaveOnSub price, discount, ranking, speed, guarantee or
credential-sharing claim. `--check` re-verifies the staged artifact.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
CATALOG = ROOT / "catalog.json"
COPY = ROOT / "ops" / "seo" / "PRODUCT-COPY-2026-11-01.json"
FAQ = ROOT / "ops" / "seo" / "PRODUCT-FAQ-2026-11-01.json"
GUIDES = ROOT / "ops" / "seo" / "guides"
BASE = "https://saveonsub.com"
MARK = 'data-product-seo="product-seo-2026-11-01"'
TITLE_MAX = 60
DESC_MAX = 160

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]+"
)
FORBIDDEN = re.compile(
    r"৳|US\$\s?\d|\btaka\b|cheapest|lowest price|\#1\b|lifetime|guarantee|shared account|instant delivery",
    re.I,
)


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", EMOJI.sub("", name or "")).strip()


def slug(cat: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (cat or "").lower()).strip("-")


def fit(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:—- ")
    return cut + "…"


def make_title(name: str, bn: bool) -> str:
    brand = " | SAVEONSUB"
    if bn:
        # "দাম" keeps long bundle names from sharing the EN title verbatim.
        options = [f"{name} দাম বাংলাদেশে{brand}", f"{name} বাংলাদেশে{brand}", f"{name} দাম{brand}", f"{name}{brand}"]
    else:
        options = [f"{name} Price in Bangladesh{brand}", f"{name} in Bangladesh{brand}", f"{name}{brand}"]
    for opt in options:
        if len(opt) <= TITLE_MAX:
            return opt
    return fit(name, TITLE_MAX - len(brand)) + brand


def what_text(p: dict, copy: dict, products: dict, bn: bool) -> str:
    entry = copy.get(p["id"])
    if entry:
        return entry[1] if bn else entry[0]
    parts = [clean_name(products[c]["name"]) for c in p.get("contains") or [] if c in products]
    if parts:
        joined = ", ".join(parts)
        return (f"এই বান্ডেলে একসাথে রয়েছে: {joined}। প্রতিটি টুলের বিস্তারিত নিচের লিংকে দেখুন।" if bn
                else f"This bundle groups {joined} in one order. See each included tool's page below for what it does.")
    return ""


def make_desc(name: str, what: str, bn: bool) -> str:
    tail = (" মূল্য ও অ্যাক্সেস WhatsApp-এ নিশ্চিত করুন।" if bn
            else " Confirm BDT price and access on WhatsApp.")
    lead = what.split("। ")[0] if bn else what.split(". ")[0]
    lead = lead.rstrip("।.") + ("।" if bn else ".")
    if not lead.lower().startswith(name.lower()[:6]):
        lead = f"{name}: {lead}"
    room = DESC_MAX - len(tail)
    if len(lead) > room:
        end = "।" if bn else "."
        cut = max(lead.rfind(sep, 0, room - 1) for sep in (", ", "; ", " with ", " and "))
        lead = (lead[:cut].rstrip(",; ") + end) if cut > 40 else fit(lead, room)
    return lead + tail


def related(p: dict, products: dict, bn: bool) -> list[tuple[str, str]]:
    out: list[str] = []
    for c in p.get("contains") or []:
        out.append(c)
    for b in p.get("bundles") or []:
        out.append(b)
    for q in products.values():
        if q["category"] == p["category"] and q["id"] != p["id"]:
            out.append(q["id"])
    seen, links = set(), []
    for pid in out:
        if pid in seen or pid == p["id"] or pid not in products:
            continue
        seen.add(pid)
        links.append((pid, clean_name(products[pid]["name"])))
        if len(links) >= 8:
            break
    return links


def load_faq() -> dict:
    return json.loads(FAQ.read_text(encoding="utf-8"))["products"] if FAQ.exists() else {}


def load_guides() -> dict:
    """product id -> [(slug, title)] from the Bangla guide sources."""
    out: dict = {}
    for path in sorted(GUIDES.glob("*.md")) if GUIDES.exists() else []:
        head = path.read_text(encoding="utf-8").split("---")[1]
        meta = dict(l.split(":", 1) for l in head.strip().splitlines() if ":" in l)
        rel = [x.strip() for x in meta.get("related", "").strip().strip("[]").split(",") if x.strip()]
        for pid in rel:
            out.setdefault(pid, []).append((meta["slug"].strip(), meta["title"].strip()))
    return out


FAQS = load_faq()
GUIDE_LINKS = load_guides()


def faq_html(pid: str, bn: bool) -> str:
    rows = FAQS.get(pid) or []
    if not rows:
        return ""
    items = "".join(
        f'<h3 class="mt2" style="font-size:17px">{esc(r[2] if bn else r[0])}</h3><p>{esc(r[3] if bn else r[1])}</p>'
        for r in rows
    )
    return f'<h2 class="mt3" style="font-size:22px">{"সাধারণ প্রশ্ন" if bn else "Frequently asked questions"}</h2>{items}'


def guide_html(pid: str, bn: bool) -> str:
    rows = GUIDE_LINKS.get(pid) or []
    if not rows:
        return ""
    up = "../../" if bn else "../"
    lis = "".join(f'<li><a href="{up}blog/{esc(slug)}">{esc(title)}</a></li>' for slug, title in rows)
    return f'<h2 class="mt3" style="font-size:22px">{"বাংলা গাইড" if bn else "Bangla guides"}</h2><ul>{lis}</ul>'


def section_html(p: dict, products: dict, copy: dict, bn: bool) -> str:
    name = clean_name(p["name"])
    what = what_text(p, copy, products, bn)
    parts = [f'<section class="mt3" {MARK}>']
    if what:
        parts.append(f'<h2 style="font-size:22px">{esc(name)} {"কী?" if bn else "— what is it?"}</h2><p>{esc(what)}</p>')
    url = p.get("official_url")
    # No numeric provider price here: catalog official_usd is not per-SKU
    # date/region verified, so the section links to the official page only.
    if url and not p.get("contains"):
        if bn:
            parts.append(
                f'<h2 class="mt3" style="font-size:22px">বাংলাদেশে {esc(name)}-এর দাম কত?</h2>'
                f'<p>প্রোভাইডারের বর্তমান মূল্য ও আপনার দেশে প্ল্যান পাওয়া যায় কিনা <a href="{esc(url)}" target="_blank" rel="noopener nofollow">প্রোভাইডারের অফিসিয়াল ওয়েবসাইটে দেখুন ↗</a>। '
                f'প্রোভাইডার দেশ, ট্যাক্স ও প্ল্যান অনুযায়ী মূল্য বদলাতে পারে। SaveOnSub-এর বর্তমান টাকায় মূল্য ও অ্যাক্সেস পদ্ধতি পেমেন্টের আগে লিখিতভাবে নিশ্চিত করা হয়।</p>'
            )
        else:
            parts.append(
                f'<h2 class="mt3" style="font-size:22px">How much is {esc(name)} in Bangladesh?</h2>'
                f'<p>Check the provider\'s current price and whether the plan is offered in your country on the <a href="{esc(url)}" target="_blank" rel="noopener nofollow">official provider website ↗</a>. '
                f'Provider prices can vary by country, tax and plan. SaveOnSub confirms its current BDT price and the exact access method in writing before any payment.</p>'
            )
    parts.append(faq_html(p["id"], bn))
    parts.append(guide_html(p["id"], bn))
    links = related(p, products, bn)
    if links:
        lis = "".join(f'<li><a href="{esc(pid)}">{esc(n)}</a></li>' for pid, n in links)
        cat = esc(p["category"])
        heading = "সম্পর্কিত টুল" if bn else "Related tools"
        cat_link = f'<a href="../c/{slug(p["category"])}">{cat}</a>'
        more = f'<p>{"আরও দেখুন: " if bn else "More in "}{cat_link}</p>'
        parts.append(f'<h2 class="mt3" style="font-size:22px">{heading}</h2><ul>{lis}</ul>{more}')
    parts.append("</section>")
    return "".join(parts)


def breadcrumb_ld(p: dict, bn: bool) -> str:
    name = clean_name(p["name"])
    prefix = "/bn" if bn else ""
    # /bn/all canonicalises to /all, so the indexable All Products target is /all.
    items = [
        ("হোম" if bn else "Home", f"{BASE}{'/bn' if bn else '/'}"),
        ("সব প্রোডাক্ট" if bn else "All Products", f"{BASE}/all"),
        (p["category"], f"{BASE}{prefix}/c/{slug(p['category'])}"),
        (name, f"{BASE}{prefix}/p/{p['id']}"),
    ]
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)
        ],
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def set_title(text: str, title: str) -> str:
    return re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", text, count=1, flags=re.S)


def set_meta(text: str, attr: str, name: str, content: str) -> str:
    pat = re.compile(rf'<meta\s+{attr}=["\']{re.escape(name)}["\'][^>]*>', re.I)
    tag = f'<meta {attr}="{esc(name)}" content="{esc(content)}">'
    return pat.sub(tag, text, count=1) if pat.search(text) else text.replace("</head>", tag + "\n</head>", 1)


def enrich(text: str, p: dict, products: dict, copy: dict, bn: bool) -> str:
    name = clean_name(p["name"])
    title = make_title(name, bn)
    what = what_text(p, copy, products, bn) or name
    desc = make_desc(name, what, bn)
    text = set_title(text, title)
    text = set_meta(text, "name", "description", desc)
    text = set_meta(text, "property", "og:title", title)
    text = set_meta(text, "property", "og:description", desc)
    text = set_meta(text, "name", "twitter:title", title)
    text = set_meta(text, "name", "twitter:description", desc)
    text = re.sub(r"(<h1\b[^>]*>)(.*?)(</h1>)", lambda m: m.group(1) + clean_name(m.group(2)) + m.group(3), text, count=1, flags=re.S)
    if MARK not in text:
        sec = section_html(p, products, copy, bn)
        text, n = re.subn(r'(<div class="notice mt3">[^<]*</div>\s*</div></main>)', sec + r"\1", text, count=1)
        if n == 0:
            raise SystemExit(f"[product-seo] governed product body not found for {p['id']} ({'bn' if bn else 'en'})")
    if '"BreadcrumbList"' not in text:
        text = text.replace("</head>", breadcrumb_ld(p, bn) + "\n</head>", 1)
    return text


def pages(products: dict):
    for pid, p in products.items():
        for path, bn in ((SITE / "p" / f"{pid}.html", False), (SITE / "bn" / "p" / f"{pid}.html", True)):
            if path.exists():
                yield path, p, bn


def check(products: dict) -> list[str]:
    errors = []
    for path, p, bn in pages(products):
        t = path.read_text(encoding="utf-8")
        rel = path.relative_to(SITE)
        title = html.unescape((re.search(r"<title>(.*?)</title>", t, re.S) or [None, ""])[1])
        desc_m = re.search(r'<meta name="description" content="([^"]*)"', t)
        desc = html.unescape(desc_m.group(1)) if desc_m else ""
        h1 = (re.search(r"<h1\b[^>]*>(.*?)</h1>", t, re.S) or [None, ""])[1]
        if not title or len(title) > TITLE_MAX:
            errors.append(f"{rel}: title length {len(title)} > {TITLE_MAX}")
        if EMOJI.search(title) or EMOJI.search(h1):
            errors.append(f"{rel}: emoji in title/H1")
        if not desc or len(desc) > DESC_MAX:
            errors.append(f"{rel}: description length {len(desc)}")
        if MARK not in t:
            errors.append(f"{rel}: product SEO section missing")
        if '"BreadcrumbList"' not in t:
            errors.append(f"{rel}: BreadcrumbList missing")
        sec = re.search(rf"<section[^>]*{re.escape(MARK)}.*?</section>", t, re.S)
        if sec and FORBIDDEN.search(re.sub(r"<[^>]+>", " ", sec.group(0))):
            errors.append(f"{rel}: forbidden commercial claim inside SEO section")
        for href in re.findall(r'href="([^"]+)"', sec.group(0)) if sec else []:
            if href.startswith("http"):
                continue
            target = (path.parent / (href + ".html")).resolve()
            if not target.exists():
                errors.append(f"{rel}: SEO section link target missing: {href}")
            elif "/_site/blog/" not in target.as_posix() and ("/_site/bn/" in target.as_posix()) != bn:
                errors.append(f"{rel}: SEO section link crosses locale: {href}")
    return errors


def main(argv: list[str]) -> int:
    if not SITE.exists():
        raise SystemExit("[product-seo] _site missing; run the build first")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    products = {p["id"]: p for p in catalog["products"] if p.get("id")}
    copy = json.loads(COPY.read_text(encoding="utf-8"))["products"]
    for pid, (en, bn) in copy.items():
        if FORBIDDEN.search(en) or FORBIDDEN.search(bn):
            raise SystemExit(f"[product-seo] forbidden claim in copy for {pid}")
    if "--check" not in argv:
        n = 0
        for path, p, bn in pages(products):
            path.write_text(enrich(path.read_text(encoding="utf-8"), p, products, copy, bn), encoding="utf-8")
            n += 1
        print(f"[product-seo] enriched {n} product pages")
    errors = check(products)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(f"[product-seo] FAIL — {len(errors)} issue(s)")
    print("[product-seo] PASS — titles, descriptions, H1, unique sections, same-locale link targets and breadcrumbs verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
