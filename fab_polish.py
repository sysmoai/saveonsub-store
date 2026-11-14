#!/usr/bin/env python3
"""Floating-button polish for the staged site (build step, after commercial_truth_v2.py).

Problem (CEO review of the /warranty phone screenshot, 13 Nov 2026): the two
floating buttons (WhatsApp at the right, Find-My-AI quiz at the left) are wide
labelled pills. On a phone they sit on top of cards and body text.

Fix: on phones the buttons become 48 px round icon buttons that slide away while
the reader scrolls down and in the footer (CSS + a few lines in assets/app.js).
This step only wraps the visible label in ``<span class="fab-t">`` so CSS can hide
it on phones; the accessible name still comes from the existing ``aria-label``.
Hrefs, numbers and prefilled messages are not touched. ``--check`` re-verifies.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
FAB = re.compile(r'(<(?P<tag>a|button)\b[^>]*\bclass="fab (?:fab-wa|fab-quiz)"[^>]*>)(?P<icon>[^<\s]+) (?P<label>[^<]+)(</(?P=tag)>)')


def wrap(m: re.Match) -> str:
    return f'{m.group(1)}<span aria-hidden="true">{m.group("icon")}</span><span class="fab-t"> {m.group("label")}</span>{m.group(5)}'


def pages():
    return sorted(SITE.rglob("*.html"))


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not SITE.is_dir():
        print("[fab] FAIL — _site missing; run build_site.py")
        return 1
    changed = bad = 0
    for p in pages():
        t = p.read_text(encoding="utf-8")
        if 'class="fab ' not in t:
            continue
        new = FAB.sub(wrap, t)
        if check:
            if new != t:
                bad += 1
                print(f"[fab] FAIL — unwrapped label in {p.relative_to(SITE)}")
        elif new != t:
            p.write_text(new, encoding="utf-8")
            changed += 1
    if bad:
        return 1
    print(f"[fab] PASS — {'checked' if check else f'{changed} page(s) updated'}; labels wrapped for phone icon mode")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
