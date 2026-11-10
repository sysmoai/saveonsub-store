#!/usr/bin/env python3
"""Motion and visual polish for the staged site (build step, after a11y_polish.py).

The site read as flat on first open (CEO, 10 Nov 2026). This step adds markup
hooks that ``assets/style.css`` (block "motion v1") and ``assets/app.js``
(scroll reveal, count-up, trust-bar rotation, scroll progress) animate:

- EN/BN home: animated aurora behind the hero, a highlighted phrase in the h1,
  a scrolling rail of the products we list (names and links only, no prices)
  and a facts band whose numbers are counted from the staged catalog.
- every page: ``sw.js`` cache name follows the CSS/JS content, so returning
  visitors get the new look on their next view instead of a stale cache.

Nothing here adds a price, a claim or a URL. All motion stops under
``prefers-reduced-motion``. ``--check`` re-verifies without writing.
"""
from __future__ import annotations

import hashlib
import html
import re
import sys
from pathlib import Path

import product_rich_results as rr

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
MARK = "motion-v1-2026-11-10"
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
FX = '<div class="hero-fx" aria-hidden="true"><i></i><i></i><i></i><span class="hero-grid"></span></div>'
HIGHLIGHT = {False: "Pay in taka.", True: "BDT-তে পেমেন্ট করুন।"}


def products() -> list[tuple[str, str]]:
    items = rr.priced(rr.load_catalog(SITE))
    return [(pid, rr.clean_name(p["name"])) for pid, p in items.items() if not pid.startswith("aips-")]


def rail(items: list[tuple[str, str]], bn: bool) -> str:
    prefix = "p/" if not bn else "bn/p/"
    chips = "".join(f'<a class="rchip" href="{prefix}{pid}">{html.escape(name)}</a>' for pid, name in items)
    label = "যেসব সাবস্ক্রিপশন আমরা দিই" if bn else "Subscriptions we offer"
    # second copy is for the seamless loop only, so it is hidden from assistive tech
    dup = re.sub(r'<a class="rchip"', '<a class="rchip" tabindex="-1"', chips)
    return (f'<section class="brandrail" data-sos="{MARK}" aria-label="{label}"><div class="rtrack">'
            f'<div class="rset">{chips}</div><div class="rset" aria-hidden="true">{dup}</div></div></section>')


def facts(n: int, cats: int, bn: bool) -> str:
    if bn:
        rows = [(n, "টি সাবস্ক্রিপশন, টাকায় নির্দিষ্ট দাম"), (cats, "টি ক্যাটাগরি"),
                (3, "টি লোকাল পেমেন্ট: বিকাশ, নগদ, রকেট"), (None, "বাংলা ও ইংরেজিতে হোয়াটসঅ্যাপ সাপোর্ট")]
    else:
        rows = [(n, "subscriptions with fixed taka prices"), (cats, "categories to browse"),
                (3, "local payment methods: bKash, Nagad, Rocket"), (None, "WhatsApp support in Bangla and English")]
    cells = []
    for num, text in rows:
        if num is None:
            big = '<b class="fnum">💬</b>'
        else:
            shown = str(num).translate(BN_DIGITS) if bn else str(num)
            big = f'<b class="fnum" data-count="{num}"{" data-bn=1" if bn else ""}>{shown}</b>'
        cells.append(f'<div class="fcell">{big}<span>{text}</span></div>')
    return f'<section class="factband" data-sos="{MARK}"><div class="wrap fgrid">{"".join(cells)}</div></section>'


def home(path: Path, bn: bool, items: list[tuple[str, str]], cats: int) -> tuple[str, bool]:
    text = path.read_text(encoding="utf-8")
    if MARK in text:
        return text, False
    text = re.sub(r'(<header class="hero"[^>]*>)', lambda m: m.group(1) + FX, text, count=1)
    hl = HIGHLIGHT[bn]
    text = re.sub(r"(<h1>[^<]*?)" + re.escape(hl), lambda m: m.group(1) + f'<span class="hl">{hl}</span>', text,
                  count=1)
    text = text.replace("</header>", "</header>" + rail(items, bn) + facts(len(items), cats, bn), 1)
    return text, True


def sw_version(text: str) -> str:
    digest = hashlib.sha256()
    for name in ("assets/style.css", "assets/app.js", "assets/catalog.js"):
        f = SITE / name
        if f.is_file():
            digest.update(f.read_bytes())
    return re.sub(r"const CACHE = '[^']*';", f"const CACHE = 'sos-{digest.hexdigest()[:12]}';", text, count=1)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not SITE.is_dir():
        print("[motion-polish] FAIL — _site missing; run build_site.py first")
        return 1
    items = products()
    cats = len(list((SITE / "c").glob("*.html")))
    done = 0
    if not check:
        for rel, bn in (("index.html", False), ("bn.html", True)):
            new, changed = home(SITE / rel, bn, items, cats)
            if changed:
                (SITE / rel).write_text(new, encoding="utf-8")
                done += 1
        sw = SITE / "sw.js"
        if sw.is_file():
            sw.write_text(sw_version(sw.read_text(encoding="utf-8")), encoding="utf-8")
    errors = []
    for rel in ("index.html", "bn.html"):
        t = (SITE / rel).read_text(encoding="utf-8")
        for need in ('class="hero-fx"', 'class="brandrail"', 'class="factband"', 'class="hl"'):
            if need not in t:
                errors.append(f"{rel}: {need} missing")
        for sec in re.findall(r'<section class="(?:brandrail|factband)".*?</section>', t, re.S):
            if "৳" in sec:
                errors.append(f"{rel}: price inside a motion section")
    sw = SITE / "sw.js"
    if sw.is_file() and sw_version(sw.read_text(encoding="utf-8")) != sw.read_text(encoding="utf-8"):
        errors.append("sw.js cache name does not follow the current CSS/JS")
    if errors:
        print("[motion-polish] FAIL — " + "; ".join(errors))
        return 1
    if check:
        print(f"[motion-polish] PASS — hero motion, product rail ({len(items)}), facts band on EN/BN home; sw cache current")
    else:
        print(f"[motion-polish] {done} home page(s) upgraded; product rail {len(items)} names; sw cache versioned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
