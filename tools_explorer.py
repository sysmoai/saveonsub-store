#!/usr/bin/env python3
"""AI Tools Explorer: one discovery page for the wider AI-tool universe (build step).

Renders /tools from ops/seo/control/universe-families.json (written by
universe_registry.py). The Shop stays the only place with prices: a tool sold
by SaveOnSub links to its own product page; every other tool is labelled
"Not sold by SaveOnSub" with its official site and an availability question on
WhatsApp. Other business units' packages and service rows are never listed.

No price, discount, stock, warranty or delivery claim may appear on the page.
`--check` re-verifies the staged artifact.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

from site_config import SUPPORT_PHONE_DIGITS

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
FAMILIES = ROOT / "ops" / "seo" / "control" / "universe-families.json"
CATALOG = ROOT / "catalog.json"
BASE = "https://saveonsub.com"
URL = f"{BASE}/tools"
MARK = 'data-tools-explorer="2026-11-03"'
SHELL_FROM = "all.html"
TITLE = "AI Tools Explorer — Find the Right AI Tool | SAVEONSUB"
DESC = ("Browse AI tools by job: chat, image, video, voice, code, writing and productivity. "
        "See which tools SaveOnSub sells and visit official sites for the rest.")
FORBIDDEN = re.compile(r"৳|\$\s?\d|cheapest|lowest price|#1\b|lifetime|guarantee|instant delivery|in stock|warranty", re.I)
SKIP_FLAGS = {"other_unit_package", "service_candidate"}


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def listed(families: list[dict]) -> list[dict]:
    out = []
    for f in families:
        if not f.get("brand") or f.get("sos_only"):
            continue
        if f["family"].startswith("service:") or f.get("brand") == "AIPS" or "Setup Service" in f["brand"]:
            continue
        if f.get("capability_group") in (None, "Unmapped", "Bundles"):
            continue
        url = f.get("official_url") or ""
        if not f.get("sos_products") and not url.startswith("https://"):
            continue  # unverified tools stay internal until an official source is recorded
        out.append(f)
    return out


def card(f: dict, names: dict) -> str:
    name = esc(f["brand"])
    group = esc(f["capability_group"])
    provider = esc(f.get("provider") or "")
    if f.get("sos_products"):
        pid = f["sos_products"][0]
        action = (f'<span class="tos personal">Sold by SaveOnSub</span> '
                  f'<a class="btn btn-primary btn-sm" href="p/{esc(pid)}">See {esc(names.get(pid, pid))} plans</a>')
    else:
        msg = urllib.parse.quote(f"Hi! Is {f['brand']} available through SaveOnSub?")
        action = (f'<span class="tos">Not sold by SaveOnSub</span> '
                  f'<a href="{esc(f["official_url"])}" rel="noopener" target="_blank">Official site ↗</a> · '
                  f'<a href="https://wa.me/{SUPPORT_PHONE_DIGITS}?text={msg}" rel="noopener">Ask about availability</a>')
    return (f'<div class="pcard" data-group="{group}" data-name="{name.lower()}">'
            f'<h3 style="font-size:16px">{name}</h3><p class="sub" style="font-size:13px">{provider} · {group}</p>'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:13px">{action}</div></div>')


def render(shell: str, families: list[dict], names: dict) -> str:
    groups = sorted({f["capability_group"] for f in families})
    sold = sum(1 for f in families if f.get("sos_products"))
    options = "".join(f'<option value="{esc(g)}">{esc(g)}</option>' for g in groups)
    sections = "".join(
        f'<h2 class="mt3" style="font-size:22px" data-section="{esc(g)}">{esc(g)}</h2>'
        f'<div class="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px">'
        + "".join(card(f, names) for f in families if f["capability_group"] == g) + "</div>"
        for g in groups
    )
    main = (
        f'<main id="main" {MARK}><div class="wrap">'
        '<div class="crumbs"><a href="./">Home</a> › AI Tools Explorer</div>'
        '<h1 style="font-size:clamp(26px,4vw,38px)">AI Tools Explorer</h1>'
        f'<p class="sub mt2">{len(families)} AI tools grouped by the job they do. {sold} are sold by SaveOnSub '
        'with published plans; for the others we link the official site. Availability, plans and provider terms '
        'change often, so confirm on the official site before you pay anyone.</p>'
        '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:18px 0">'
        '<input id="tq" type="search" placeholder="Search tools" aria-label="Search tools" '
        'style="flex:1;min-width:200px;padding:10px;border-radius:10px;border:1px solid var(--line,#ccc)">'
        f'<select id="tg" aria-label="Filter by category" style="padding:10px;border-radius:10px">'
        f'<option value="">All categories</option>{options}</select>'
        '<label style="display:flex;align-items:center;gap:6px;font-size:14px;white-space:nowrap">'
        '<input id="ts" type="checkbox" style="width:auto;flex:none;margin:0"> Sold by SaveOnSub only</label>'
        '</div>'
        f'{sections}'
        '<p class="sub mt3" style="font-size:13px">Listing a tool here is not a claim of partnership with its provider. '
        'Not sure what you need? <a href="quiz">Take the Find My AI quiz</a> or <a href="all">see all products</a>.</p>'
        '</div></main>'
        '<script>(function(){var q=document.getElementById("tq"),g=document.getElementById("tg"),s=document.getElementById("ts");'
        'function f(){var t=(q.value||"").toLowerCase(),c=g.value,only=s.checked;'
        'document.querySelectorAll("[data-tools-explorer] .pcard").forEach(function(e){'
        'var ok=(!t||e.dataset.name.indexOf(t)>-1)&&(!c||e.dataset.group===c)&&(!only||e.querySelector(".personal"));'
        'e.style.display=ok?"":"none";});'
        'document.querySelectorAll("[data-section]").forEach(function(h){var n=h.nextElementSibling;'
        'var vis=[].some.call(n.children,function(x){return x.style.display!=="none";});h.style.display=n.style.display=vis?"":"none";});}'
        'q.addEventListener("input",f);g.addEventListener("change",f);s.addEventListener("change",f);})();</script>'
    )
    t = shell
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(TITLE)}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(DESC)}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(TITLE)}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(DESC)}">', t, count=1)
    t = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{URL}">', t, count=1)
    t = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{URL}">', t, count=1)
    t = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\s*', "", t)
    t = re.sub(r'<script type="application/ld\+json">.*?</script>', "", t, flags=re.S)
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "AI Tools Explorer",
          "url": URL, "description": DESC, "inLanguage": "en-BD"}
    t = t.replace("</head>", f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n</head>', 1)
    new, n = re.subn(r"<main\b[^>]*>.*?</main>", main.replace("\\", "\\\\"), t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit("[tools-explorer] <main> not found in shell")
    return new


def link_from_all() -> None:
    page = SITE / "all.html"
    text = page.read_text(encoding="utf-8")
    if MARK in text:
        return
    anchor = '<div class="crumbs"><a href="./">Home</a> › All Subscriptions</div>'
    if anchor not in text:
        raise SystemExit("[tools-explorer] all-products crumbs not found")
    link = (f'{anchor}<p {MARK} class="sub" style="margin:8px 0 0">Looking for a tool we do not sell? '
            '<a href="tools">Browse the AI Tools Explorer →</a></p>')
    page.write_text(text.replace(anchor, link, 1), encoding="utf-8")


def add_to_sitemap() -> None:
    sm = SITE / "sitemap.xml"
    text = sm.read_text(encoding="utf-8")
    if f"<loc>{URL}</loc>" not in text:
        text = text.replace("</urlset>", f"<url><loc>{URL}</loc><lastmod>2026-11-03</lastmod>"
                            "<changefreq>weekly</changefreq><priority>0.6</priority></url></urlset>", 1)
        sm.write_text(text, encoding="utf-8")


def check() -> list[str]:
    errors = []
    page = SITE / "tools.html"
    if not page.exists():
        return ["tools.html missing"]
    text = page.read_text(encoding="utf-8")
    body = re.search(r"<main\b.*?</main>", text, re.S).group(0)
    if FORBIDDEN.search(re.sub(r"<script.*?</script>", "", body, flags=re.S)):
        errors.append("tools.html: price/claim language on explorer page")
    if f'<link rel="canonical" href="{URL}">' not in text:
        errors.append("tools.html: canonical missing")
    if "aips" in body.lower():
        errors.append("tools.html: other business unit content listed")
    for href in re.findall(r'href="p/([^"]+)"', body):
        if not (SITE / "p" / f"{href}.html").exists():
            errors.append(f"tools.html: dead product link p/{href}")
    if f"<loc>{URL}</loc>" not in (SITE / "sitemap.xml").read_text(encoding="utf-8"):
        errors.append("sitemap.xml: /tools missing")
    if MARK not in (SITE / "all.html").read_text(encoding="utf-8"):
        errors.append("all.html: explorer link missing")
    return errors


def main(argv: list[str]) -> int:
    if not FAMILIES.exists():
        # The family file is derived from other business units' catalogs and is
        # kept out of the public repository until the CEO approves publishing it.
        print("[tools-explorer] SKIP — universe-families.json not present; /tools not staged")
        return 0
    if "--check" not in argv:
        families = listed(json.loads(FAMILIES.read_text(encoding="utf-8"))["families"])
        names = {p["id"]: p["name"] for p in json.loads(CATALOG.read_text(encoding="utf-8"))["products"]}
        shell = (SITE / SHELL_FROM).read_text(encoding="utf-8")
        (SITE / "tools.html").write_text(render(shell, families, names), encoding="utf-8")
        link_from_all()
        add_to_sitemap()
    errors = check()
    for e in errors:
        print("[tools-explorer] FAIL " + e)
    if errors:
        return 1
    print("[tools-explorer] PASS — explorer page staged, no prices, product links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
