#!/usr/bin/env python3
"""Readability polish for staged blog pages (build step, after hold_content_price_guard).

hold_content_price_guard replaces any taka amount that is not a page's own approved
price with the phrase "current price on the product page". In table cells that
produced "current price on the product page from current price on the product
page". This step turns whole-cell placeholders into "See product page" and
removes doubled placeholders. It never adds a number, claim or price.
`--check` verifies the staged artifact without writing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
PH = "current price on the product page"
CELL = re.compile(rf"(<t[dh][^>]*>)\s*(?:<b>)?\s*(?:[Ff]rom\s+)?{PH}(?:\s+(?:from\s+)?{PH})*\s*(?:</b>)?\s*(</t[dh]>)")
DOUBLE = re.compile(rf"(?:[Ff]rom\s+)?{PH}\s+(?:from\s+)?{PH}")
FROM_PH = re.compile(rf"\b[Ff]rom\s+{PH}")


def polish(text: str) -> str:
    text = CELL.sub(r"\1See product page\2", text)
    text = DOUBLE.sub("the price on the product page", text)
    return text


# Claims removed from the shared-vs-personal guide on 10 Nov 2026 (gap T59): they
# contradicted the product pages (shared users can see activity) or promised SLAs.
BANNED = re.compile(r"bulletproof|zero risk|stays private|Private per-user|replaces in 1h|1-hour hiccup|"
                    r"Google is tolerant|most tolerant|officially supported", re.I)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    bad = []
    changed = 0
    for path in sorted((SITE / "blog").glob("*.html")):
        text = path.read_text(encoding="utf-8")
        new = polish(text)
        if BANNED.search(new):
            bad.append(f"{path.name} (banned claim: {BANNED.search(new).group(0)})")
        if check:
            if CELL.search(text) or DOUBLE.search(text):
                bad.append(path.name)
        elif new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    if bad:
        print("[blog-polish] FAIL — doubled/cell placeholders or banned claims: " + ", ".join(bad))
        return 1
    print(f"[blog-polish] PASS — {changed} blog page(s) polished; no doubled price placeholders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
