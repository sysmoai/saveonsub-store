#!/usr/bin/env python3
"""Accessibility polish for the staged site (build step, after link_hygiene.py).

axe-core (WCAG 2 A/AA) over all 242 staged pages on 10 Nov 2026 found two
repeatable defects that a build step can fix without touching copy or prices:

- ``scrollable-region-focusable``: wide comparison tables sit in a
  horizontally scrolling ``<div class="tbl">``. Keyboard users could not reach
  the hidden columns. Each such wrapper now gets ``tabindex="0"``,
  ``role="region"`` and an ``aria-label`` taken from the nearest heading above
  it (fallback "Comparison table" / "তুলনার টেবিল").
- ``link-in-text-block`` is fixed in ``assets/style.css`` (links inside running
  text are underlined), not here.

``--check`` re-verifies without writing.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
TBL = re.compile(r'<div class="(tbl(?:\s[^"]*)?)"(?![^>]*\btabindex=)([^>]*)>')
HEADING = re.compile(r"<h[1-4][^>]*>(.*?)</h[1-4]>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")


def label_for(text: str, pos: int, bn: bool) -> str:
    heads = HEADING.findall(text[:pos])
    if heads:
        words = re.sub(r"\s+", " ", html.unescape(TAGS.sub("", heads[-1]))).strip()
        if words:
            return words[:80]
    return "তুলনার টেবিল" if bn else "Comparison table"


def process(page: Path) -> tuple[str, int]:
    text = page.read_text(encoding="utf-8")
    bn = page.relative_to(SITE).as_posix().startswith("bn")
    out, last, n = [], 0, 0
    for m in TBL.finditer(text):
        lab = html.escape(label_for(text, m.start(), bn), quote=True)
        out.append(text[last:m.start()])
        out.append(f'<div class="{m.group(1)}"{m.group(2)} tabindex="0" role="region" aria-label="{lab}">')
        last = m.end()
        n += 1
    out.append(text[last:])
    return "".join(out), n


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not SITE.is_dir():
        print("[a11y-polish] FAIL — _site missing; run build_site.py first")
        return 1
    total = pages = 0
    for page in sorted(SITE.rglob("*.html")):
        new, n = process(page)
        if n:
            total += n
            pages += 1
            if not check:
                page.write_text(new, encoding="utf-8")
    if check:
        if total:
            print(f"[a11y-polish] FAIL — {total} scrollable table(s) on {pages} page(s) not keyboard-focusable")
            return 1
        print("[a11y-polish] PASS — every scrollable table is a focusable, labelled region")
        return 0
    print(f"[a11y-polish] {total} scrollable table(s) on {pages} page(s) made focusable, labelled regions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
