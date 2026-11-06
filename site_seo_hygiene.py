#!/usr/bin/env python3
"""Site-wide SEO hygiene for the staged site (build step).

Runs after hold_content_price_guard.py, before the final audits. Adds no price.

- Category pages (/c, /bn/c): replaces the generic EN title and the EN/BN meta
  descriptions (which the price guard had left reading "from current price on
  the product page") with copy naming the products listed on the page, removes
  that leftover phrase from body copy outside the price cards, and adds an
  ItemList JSON-LD of the listed products when missing.
- Every indexable page without og:image / twitter:image gets the site default.
- Indexable SaveOnSub pages that self-canonicalise but were missing from
  sitemap.xml are added (SEO-006). /modes and /os stay out (ISO-001, CEO).

`--check` re-verifies without writing.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
BASE = "https://saveonsub.com"
MARK = "seo-hygiene-2026-11-06"
LEFTOVER = "current price on the product page"
TITLE_MAX = 60
DESC_MAX = 160
SITEMAP_ADD = ("bn/about", "bn/contact", "bn/offers", "bn/quiz", "bn/students")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]+")
CARD = re.compile(r'<a class="pcard" href="(?:\.\./|/)?(?:bn/)?p/([a-z0-9-]+)"[^>]*>.*?<h3>(.*?)</h3>', re.S)


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def clean(name: str) -> str:
    return re.sub(r"\s+", " ", EMOJI.sub("", html.unescape(re.sub(r"<[^>]+>", "", name)))).strip()


def set_title(t: str, title: str) -> str:
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", t, count=1, flags=re.S)
    return set_meta(t, "property", "og:title", title)


def set_meta(t: str, attr: str, name: str, content: str) -> str:
    pat = re.compile(rf'<meta\s+{attr}="{re.escape(name)}"[^>]*>')
    tag = f'<meta {attr}="{name}" content="{esc(content)}">'
    return pat.sub(lambda _m: tag, t) if pat.search(t) else t.replace("</head>", tag + "\n</head>", 1)


def fit_names(prefix: str, names: list[str], suffix: str, limit: int) -> str | None:
    for k in range(min(3, len(names)), 0, -1):
        s = prefix + ", ".join(names[:k]) + suffix
        if len(s) <= limit:
            return s
    return None


def catalog_order() -> dict[str, int]:
    try:
        m = re.search(r"const CATALOG = (\{.*?\});\s*$", (SITE / "assets" / "catalog.js").read_text(encoding="utf-8"), re.S | re.M)
        return {p["id"]: i for i, p in enumerate(json.loads(m.group(1))["products"])}
    except (OSError, AttributeError, ValueError, KeyError):
        return {}


def category(t: str, rel: str, bn: bool) -> str:
    cards = []
    for pid, name in CARD.findall(t):
        if pid.startswith("aips-") or pid in {c[0] for c in cards}:
            continue
        cards.append((pid, clean(name)))
    order = catalog_order()
    named = sorted(cards, key=lambda c: order.get(c[0], 999))  # flagship products first
    names = [n.split(" (")[0].replace(" — ", " ").strip() for _, n in named]
    if not names:
        return t
    h1 = clean((re.search(r"<h1\b[^>]*>(.*?)</h1>", t, re.S) or [None, ""])[1])
    cat = re.split(r"\s+(?:in|—)\s+", h1)[0].strip() or "Subscriptions"
    more = len(names) - 3
    if bn:
        desc = f"বাংলাদেশে {', '.join(names[:3])}" + (f" সহ {len(names)}টি" if more > 0 else "") + \
               " সাবস্ক্রিপশনের টাকায় দাম, শেয়ার্ড বা পার্সোনাল অ্যাক্সেস তুলনা করুন। bKash, Nagad বা Rocket-এ পেমেন্ট।"
    else:
        pre = f"{cat} Prices in Bangladesh: "
        title = None
        for k in range(min(3, len(names)), 0, -1):  # most names first; brand only if it still fits
            for tail, limit in ((" | SAVEONSUB", TITLE_MAX), ("", 65)):
                cand = pre + ", ".join(names[:k]) + tail
                if title is None and len(cand) <= limit:
                    title = cand
        if title:
            t = set_title(t, title)
        desc = f"Compare {', '.join(names[:3])}" + (f" and {more} more" if more > 0 else "") + \
               " in Bangladesh: taka prices, shared or personal access, bKash/Nagad/Rocket payment."
    if len(desc) > DESC_MAX:
        desc = desc[:DESC_MAX - 1].rsplit(" ", 1)[0] + "…"
    t = set_meta(t, "name", "description", desc)
    t = set_meta(t, "property", "og:description", desc)
    t = set_meta(t, "name", "twitter:description", desc) if 'name="twitter:description"' in t else t

    # leftover guard phrase outside price cards
    def body_fix(seg: str) -> str:
        seg = re.sub(rf"\s+(?:from|From)\s+{LEFTOVER}", "", seg)
        return seg.replace(f" {LEFTOVER}", "")
    parts = re.split(r'(<div class="price">[^<]*</div>)', t)
    t = "".join(p if p.startswith('<div class="price">') else body_fix(p) for p in parts)

    if '"ItemList"' not in t:
        url = f"{BASE}/{rel[:-5]}"
        pre = f"{BASE}{'/bn' if bn else ''}/p/"
        ld = {"@context": "https://schema.org", "@type": "ItemList", "@id": url + "#products",
              "name": clean(h1), "numberOfItems": len(cards),
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": pre + pid, "name": n}
                                  for i, (pid, n) in enumerate(cards)]}
        raw = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        t = t.replace("</head>", f'<script type="application/ld+json" data-sos="{MARK}">{raw}</script>\n</head>', 1)
    return t


def default_image(site: Path) -> str | None:
    m = re.search(r'<meta property="og:image" content="([^"]+)"', (site / "index.html").read_text(encoding="utf-8"))
    return m.group(1) if m else None


def indexable(t: str) -> bool:
    return not re.search(r'<meta name="robots" content="[^"]*noindex', t)


def add_images(t: str, img: str) -> str:
    if 'property="og:image"' not in t:
        t = t.replace("</head>", f'<meta property="og:image" content="{esc(img)}">\n</head>', 1)
    if 'name="twitter:image"' not in t:
        t = t.replace("</head>", f'<meta name="twitter:image" content="{esc(img)}">\n</head>', 1)
    if 'name="twitter:card"' not in t:
        t = t.replace("</head>", '<meta name="twitter:card" content="summary_large_image">\n</head>', 1)
    return t


def sitemap_add(site: Path) -> None:
    sm = site / "sitemap.xml"
    s = sm.read_text(encoding="utf-8")
    add = ""
    for path in SITEMAP_ADD:
        page = site / f"{path}.html"
        if not page.exists() or f"<loc>{BASE}/{path}</loc>" in s:
            continue
        t = page.read_text(encoding="utf-8")
        if not indexable(t) or f'<link rel="canonical" href="{BASE}/{path}">' not in t:
            continue
        add += f"  <url><loc>{BASE}/{path}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>\n"
    if add:
        sm.write_text(s.replace("</urlset>", add + "</urlset>", 1), encoding="utf-8")


def check(site: Path) -> list[str]:
    errors = []
    for path in sorted((site / "c").glob("*.html")) + sorted((site / "bn" / "c").glob("*.html")):
        rel = path.relative_to(site).as_posix()
        t = path.read_text(encoding="utf-8")
        outside = re.sub(r'<div class="price">[^<]*</div>', "", t)
        if LEFTOVER in outside:
            errors.append(f"{rel}: '{LEFTOVER}' outside price cards")
        title = html.unescape((re.search(r"<title>(.*?)</title>", t, re.S) or [None, ""])[1])
        if len(title) > 65:
            errors.append(f"{rel}: title {len(title)}")
        if '"ItemList"' not in t:
            errors.append(f"{rel}: no ItemList")
    for path in site.rglob("*.html"):
        rel = path.relative_to(site).as_posix()
        if rel.startswith("tests/"):
            continue
        t = path.read_text(encoding="utf-8", errors="replace")
        if indexable(t) and 'property="og:image"' not in t:
            errors.append(f"{rel}: no og:image")
    sm = (site / "sitemap.xml").read_text(encoding="utf-8")
    for p in SITEMAP_ADD:
        if (site / f"{p}.html").exists() and f"<loc>{BASE}/{p}</loc>" not in sm:
            errors.append(f"sitemap.xml: {p} missing")
    if re.search(r"<loc>[^<]*/(?:modes|os)\b", sm):
        errors.append("sitemap.xml: /modes or /os listed (ISO-001 is a CEO decision)")
    return errors


def main(argv: list[str]) -> int:
    if not (SITE / "index.html").exists():
        raise SystemExit("[seo-hygiene] _site missing; run the build first")
    if "--check" not in argv:
        img = default_image(SITE)
        n_cat = n_img = 0
        for path in sorted((SITE / "c").glob("*.html")) + sorted((SITE / "bn" / "c").glob("*.html")):
            path.write_text(category(path.read_text(encoding="utf-8"), path.relative_to(SITE).as_posix(),
                                     path.parts[-3] == "bn"), encoding="utf-8")
            n_cat += 1
        for path in SITE.rglob("*.html"):
            if path.relative_to(SITE).as_posix().startswith("tests/") or not img:
                continue
            t = path.read_text(encoding="utf-8", errors="replace")
            if indexable(t):
                new = add_images(t, img)
                if new != t:
                    path.write_text(new, encoding="utf-8")
                    n_img += 1
        sitemap_add(SITE)
        print(f"[seo-hygiene] {n_cat} category pages rewritten; social image tags added on {n_img} pages")
    errors = check(SITE)
    if errors:
        print("\n".join(errors[:60]), file=sys.stderr)
        raise SystemExit(f"[seo-hygiene] FAIL — {len(errors)} issue(s)")
    print("[seo-hygiene] PASS — category titles/descriptions/ItemList, og:image everywhere, sitemap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
