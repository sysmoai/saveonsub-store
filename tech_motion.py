#!/usr/bin/env python3
"""AI-tech look and motion v3 for the staged site (build step, after motion_polish.py).

CEO, 13 Nov 2026: the site should look best-in-class, with motion that reads as
AI and advanced tech, and work well on every device. This step only adds markup
hooks; ``assets/style.css`` (block "motion v3") and ``assets/app.js`` animate them:

- EN/BN home: a ``<canvas class="neural-fx">`` inside the hero backdrop. app.js
  draws a slow neural network (nodes, links and data pulses). It starts after the
  page is idle, caps pixel density, uses fewer nodes on phones, pauses when the
  hero is off screen or the tab is hidden, and never runs under
  ``prefers-reduced-motion`` or Save-Data.
- every page: emoji icons in category tiles, product cards and the "why" cards
  become one consistent set of line icons (inline SVG, no requests) or the
  product monogram chip used elsewhere on the site.

Nothing here adds or changes a price, claim, URL, heading or link target.
``--check`` re-verifies without writing.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from conversion_upgrade import initials

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
MARK = "motion-v3-2026-11-13"
CANVAS = '<canvas class="neural-fx" aria-hidden="true" data-sos="%s"></canvas>' % MARK


def svg(body: str) -> str:
    return ('<svg class="ico" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            f'{body}</svg>')


ICONS = {
    # category slug -> icon
    "ai-assistants": svg('<rect x="6" y="6" width="12" height="12" rx="2.5"/><path d="M9.5 9.5h5v5h-5z"/>'
                         '<path d="M9 2.5v3.5M15 2.5v3.5M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/>'),
    "ai-image-design": svg('<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.8"/>'
                           '<path d="m4 18 5.5-5 3.5 3 3-2.5L20 17"/>'),
    "ai-video": svg('<rect x="2.5" y="5" width="14" height="14" rx="3"/><path d="m16.5 10 5-3v10l-5-3"/>'
                    '<path d="m8 9.5 4 2.5-4 2.5z"/>'),
    "ai-voice-music": svg('<path d="M3 12h1.5M6.5 8v8M10 4.5v15M13.5 7.5v9M17 10v4M20.5 12H21"/>'),
    "ai-code-dev": svg('<path d="m8.5 7-5 5 5 5M15.5 7l5 5-5 5M13.5 4.5l-3 15"/>'),
    "ai-writing": svg('<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16z"/><path d="m13.5 6.5 4 4M14 20h6"/>'),
    "workspace-productivity": svg('<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/>'
                                  '<rect x="3.5" y="13.5" width="7" height="7" rx="2"/><path d="M17 13.5v7M13.5 17h7"/>'),
    "entertainment": svg('<rect x="2.5" y="5" width="19" height="13" rx="3"/><path d="M8 21h8M10.5 9.5l4 2-4 2z"/>'),
    "vpn-security": svg('<path d="M12 3 4.5 6v5.5c0 4.6 3.1 8 7.5 9.5 4.4-1.5 7.5-4.9 7.5-9.5V6z"/><path d="m8.8 12 2.2 2.2 4.4-4.4"/>'),
    "bundles": svg('<path d="m12 3 8.5 4.5L12 12 3.5 7.5z"/><path d="m3.5 12 8.5 4.5 8.5-4.5M3.5 16.5 12 21l8.5-4.5"/>'),
    "education": svg('<path d="M2.5 9 12 4.5 21.5 9 12 13.5z"/><path d="M6.5 11v5c3 2.5 8 2.5 11 0v-5M21.5 9v5"/>'),
    "gaming": svg('<path d="M7 7h10a4.5 4.5 0 0 1 4.4 5.4l-1 4.4a2.2 2.2 0 0 1-3.8 1L14.5 15h-5l-2.1 2.8a2.2 2.2 0 0 1-3.8-1l-1-4.4A4.5 4.5 0 0 1 7 7z"/>'
                  '<path d="M7.5 10v3M6 11.5h3M15.5 11h.01M17.5 13h.01"/>'),
    "lifestyle": svg('<path d="M12 20.5s-8-4.6-8-10.4A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 8 2.5c0 5.8-8 10.4-8 10.4z"/>'),
    # "why" cards and facts band
    "taka": svg('<circle cx="12" cy="12" r="9"/><path d="M8.5 7.5c1.6 0 2.5.8 2.5 2.3V16c0 .8.6 1.4 1.4 1.4 2 0 3.6-1.7 3.6-3.9M8 11h6"/>'),
    "tag": svg('<path d="M3.5 12.3V4.5a1 1 0 0 1 1-1h7.8l8.2 8.2a1.4 1.4 0 0 1 0 2l-6.6 6.6a1.4 1.4 0 0 1-2 0z"/><circle cx="8" cy="8" r="1.5"/>'),
    "chat": svg('<path d="M20.5 11.5a8 8 0 0 1-11.7 7.1L3.5 20l1.4-5A8 8 0 1 1 20.5 11.5z"/><path d="M8.5 11.5h.01M12.5 11.5h.01M16.5 11.5h.01"/>'),
    "doc": svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>'),
}
WHY = {"৳": "taka", "🏷️": "tag", "💬": "chat", "📄": "doc"}


def hue(name: str) -> int:
    return (sum(ord(c) * (i + 1) for i, c in enumerate(name)) * 37) % 360


def upgrade(text: str, home: bool) -> str:
    # category tiles: emoji -> line icon chosen by the tile's own link target
    def cat(m: re.Match) -> str:
        slug = m.group(2)
        icon = ICONS.get(slug)
        return f'{m.group(1)}<span class="icon ico-wrap">{icon}</span>' if icon else m.group(0)
    text = re.sub(r'(<a class="cattile" href="[^"]*?c/([a-z0-9-]+)(?:\.html)?">)<span class="icon">[^<]*</span>', cat, text)
    # product cards: emoji -> the same monogram chip used on product pages
    def card(m: re.Match) -> str:
        name = html.unescape(m.group(2))
        return (f'{m.group(1)}<span class="ptile" style="--h:{hue(name)}" aria-hidden="true">'
                f'{html.escape(initials(name))}</span><h3>{m.group(2)}</h3>')
    text = re.sub(r'(<a class="pcard" href="[^"]*">)<span class="icon">[^<]*</span><h3>([^<]*)</h3>', card, text)
    # "why" cards
    for emo, key in WHY.items():
        text = text.replace(f'<span style="font-size:24px">{emo}</span>', f'<span class="ico-wrap">{ICONS[key]}</span>')
    text = text.replace('<b class="fnum">💬</b>', f'<b class="fnum fico">{ICONS["chat"]}</b>')
    if home and MARK not in text:
        text = re.sub(r'(<div class="hero-fx" aria-hidden="true">)', lambda m: m.group(1) + CANVAS, text, count=1)
    return text


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not SITE.is_dir():
        print("[tech-motion] FAIL — _site missing; run build_site.py first")
        return 1
    homes = {SITE / "index.html", SITE / "bn.html"}
    changed = 0
    errors: list[str] = []
    for f in sorted(SITE.rglob("*.html")):
        old = f.read_text(encoding="utf-8")
        new = upgrade(old, f in homes)
        if new != old:
            if check:
                errors.append(f"{f.relative_to(SITE)} not upgraded")
            else:
                # safety: the step must not change any price, link target or heading text
                for pat in (r"৳\s?[\d,০-৯]+", r'href="[^"]*"', r"<h[1-3][^>]*>[^<]*"):
                    if re.findall(pat, old) != re.findall(pat, new):
                        errors.append(f"{f.relative_to(SITE)}: {pat} changed")
                f.write_text(new, encoding="utf-8")
                changed += 1
    for f in homes:
        if MARK not in f.read_text(encoding="utf-8"):
            errors.append(f"{f.name}: neural canvas missing")
    left = sum(len(re.findall(r'class="cattile"[^>]*><span class="icon">[^<]', f.read_text(encoding="utf-8")))
               for f in SITE.rglob("*.html"))
    if left:
        errors.append(f"{left} category tile(s) still use emoji")
    if errors:
        print("[tech-motion] FAIL — " + "; ".join(errors[:12]))
        return 1
    print(f"[tech-motion] {'PASS' if check else 'OK'} — neural hero on EN/BN home; line icons; {changed} page(s) upgraded")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
