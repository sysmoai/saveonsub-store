#!/usr/bin/env python3
"""Stage a crawlable A-Z product index on /all and /bn/all (build step, SOS-P1-013).

The product grid on /all is drawn by JavaScript, so the initial HTML had no
<a href> to any product page. This step adds a plain, server-rendered list of
links, grouped by category, below the grid. It shows names only (no prices, no
availability claims), skips other business units (aips-*) and any product
without a staged page. Runs after prices_page.py, before link_hygiene.py.
`--check` re-verifies without writing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import product_rich_results as rr
from prices_page import BN_CAT

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
MARK = "all-static-index-2026-11-12"
ANCHOR = '<section id="bundles"'
BLOCK = re.compile(r'<section id="all-index"[^>]*data-mark="' + MARK + r'".*?</section>\n(?:  )?', re.S)


def listed(products: dict[str, dict], site: Path, bn: bool) -> dict[str, list[tuple[str, str]]]:
    groups: dict[str, list[tuple[str, str]]] = {}
    for pid, p in products.items():
        if pid.startswith("aips-"):
            continue
        if not (site / ("bn/p" if bn else "p") / f"{pid}.html").exists():
            continue
        groups.setdefault(p.get("category") or "Other", []).append((rr.clean_name(p["name"]), pid))
    return {c: sorted(v, key=lambda t: t[0].lower()) for c, v in sorted(groups.items())}


def block(groups: dict[str, list[tuple[str, str]]], bn: bool) -> str:
    title = "সব প্রোডাক্ট (A–Z)" if bn else "All products A–Z"
    parts = []
    for cat, items in groups.items():
        label = BN_CAT.get(cat, cat) if bn else cat
        links = "".join(f'<li><a href="p/{rr.esc(pid)}" style="color:var(--green2,#14d4b8)">{rr.esc(name)}</a></li>' for name, pid in items)
        parts.append(f'<div><h3 style="font-size:15px;margin:14px 0 6px">{rr.esc(label)}</h3>'
                     f'<ul style="list-style:none;padding:0;margin:0;display:grid;gap:4px">{links}</ul></div>')
    return (f'<section id="all-index" data-mark="{MARK}" aria-labelledby="all-index-h" style="padding:40px 0 10px">'
            f'<h2 id="all-index-h" style="font-size:20px">{title}</h2>'
            f'<div class="grid g4 mt2">{"".join(parts)}</div></section>\n')


def stage(html: str, groups, bn: bool) -> str:
    html = BLOCK.sub("", html)
    if ANCHOR not in html:
        raise SystemExit("[all-index] bundles section anchor not found")
    return html.replace(ANCHOR, block(groups, bn) + "  " + ANCHOR, 1)


def check(site: Path, products: dict[str, dict]) -> list[str]:
    errors = []
    for bn in (False, True):
        rel = "bn/all.html" if bn else "all.html"
        html = (site / rel).read_text(encoding="utf-8")
        m = BLOCK.search(html)
        if not m:
            errors.append(f"{rel}: static product index missing")
            continue
        hrefs = re.findall(r'href="p/([a-z0-9-]+)(?:\.html)?"', m.group(0))
        want = sorted(pid for items in listed(products, site, bn).values() for _n, pid in items)
        if sorted(hrefs) != want:
            errors.append(f"{rel}: index links {len(hrefs)} != staged product pages {len(want)}")
        if any(h.startswith("aips-") for h in hrefs):
            errors.append(f"{rel}: cross-unit aips-* link in index")
        if "৳" in m.group(0):
            errors.append(f"{rel}: index must not show prices")
    return errors


def main(argv: list[str]) -> int:
    if not (SITE / "assets" / "catalog.js").exists():
        raise SystemExit("[all-index] _site missing; run the build first")
    products = rr.load_catalog(SITE)
    if "--check" not in argv:
        for bn in (False, True):
            path = SITE / ("bn/all.html" if bn else "all.html")
            path.write_text(stage(path.read_text(encoding="utf-8"), listed(products, SITE, bn), bn), encoding="utf-8")
        print("[all-index] staged A-Z product index on /all and /bn/all")
    errors = check(SITE, products)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(f"[all-index] FAIL — {len(errors)} issue(s)")
    n = sum(len(v) for v in listed(products, SITE, False).values())
    print(f"[all-index] PASS — {n} crawlable product links per locale, no aips-*, no prices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
