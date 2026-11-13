#!/usr/bin/env python3
"""Make the refund-policy table readable on phones (build step, after fab_polish.py).

At 320-414 px the shared ``.tbl`` wrapper scrolls sideways and the "What you get"
and "Timeline" columns are hidden off-screen, which is the part a buyer needs.
This step marks the table of /refund and /bn/refund as ``tbl-stack`` and copies each
header text into a ``data-label`` on the cells; CSS (assets/style.css, max-width
600px) then shows every row as a card with the label above each cell. Desktop and
tablet keep the normal table. Text is copied, never edited; ``--check`` re-verifies.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
PAGES = ("refund.html", "bn/refund.html")
TBL = re.compile(r'<div class="tbl([^"]*)"([^>]*)><table>(.*?)</table></div>', re.S)
ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL = re.compile(r"<t([hd])\b[^>]*>(.*?)</t\1>", re.S)
TAGS = re.compile(r"<[^>]+>")


def text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAGS.sub("", s))).strip()


def convert(m: re.Match) -> str:
    rows = ROW.findall(m.group(3))
    if not rows:
        return m.group(0)
    heads = [text(c[1]) for c in CELL.findall(rows[0]) if c[0] == "h"]
    if not heads:
        return m.group(0)
    out = [f'<tr>{"".join(f"<th>{h}</th>" for h in heads)}</tr>']
    for r in rows[1:]:
        cells = CELL.findall(r)
        tds = []
        for i, (_k, inner) in enumerate(cells):
            lab = html.escape(heads[i] if i < len(heads) else "", quote=True)
            empty = ' data-empty="1"' if text(inner) in ("—", "-", "–") else ""
            tds.append(f'<td data-label="{lab}"{empty}>{inner}</td>')
        out.append(f'<tr>{"".join(tds)}</tr>')
    cls = m.group(1) if "tbl-stack" in m.group(1) else m.group(1) + " tbl-stack"
    return f'<div class="tbl{cls}"{m.group(2)}><table>{"".join(out)}</table></div>'


def main(argv: list[str]) -> int:
    check = "--check" in argv
    bad = 0
    for rel in PAGES:
        f = SITE / rel
        if not f.exists():
            print(f"[policy-tables] FAIL — {rel} missing")
            return 1
        t = f.read_text(encoding="utf-8")
        new = TBL.sub(convert, t)
        if "tbl-stack" not in new or new.count("data-label=") < 4:
            print(f"[policy-tables] FAIL — no stacked table in {rel}")
            return 1
        if check:
            if new != t:
                bad += 1
                print(f"[policy-tables] FAIL — not converted: {rel}")
        else:
            f.write_text(new, encoding="utf-8")
    if bad:
        return 1
    print("[policy-tables] PASS — refund tables stack as cards on phones (text unchanged)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
