#!/usr/bin/env python3
"""Add neutral, authority-safe social sharing metadata to strict SAVEONSUB L1 pages."""
from __future__ import annotations

import pathlib
import re

from build_public_info_v3 import DEST
from routes_v3 import DOMAIN

SOCIAL_IMAGE = f"{DOMAIN}/assets/icon-512.png"
OG_TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]*)">')
OG_DESC_RE = re.compile(r'<meta property="og:description" content="([^"]*)">')
OG_URL_RE = re.compile(r'<meta property="og:url" content="([^"]*)">')


def enhance_social_metadata() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    checked = 0
    changed = 0
    for path in sorted(DEST.rglob("*.html")):
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        if 'property="og:image"' in text and 'name="twitter:card"' in text:
            continue
        title = OG_TITLE_RE.search(text)
        desc = OG_DESC_RE.search(text)
        url = OG_URL_RE.search(text)
        if not title or not desc or not url or "</head>" not in text:
            raise RuntimeError(f"{path.relative_to(DEST)}: missing base OG metadata required for social enhancement")
        block = (
            f'<meta property="og:image" content="{SOCIAL_IMAGE}">'
            '<meta property="og:image:width" content="512">'
            '<meta property="og:image:height" content="512">'
            f'<meta property="og:image:alt" content="{title.group(1)}">'
            '<meta name="twitter:card" content="summary">'
            f'<meta name="twitter:title" content="{title.group(1)}">'
            f'<meta name="twitter:description" content="{desc.group(1)}">'
            f'<meta name="twitter:image" content="{SOCIAL_IMAGE}">'
            f'<meta name="twitter:image:alt" content="{title.group(1)}">'
        )
        new = text.replace("</head>", f"{block}</head>", 1)
        path.write_text(new, encoding="utf-8")
        changed += 1
    return {"social_pages_checked": checked, "social_pages_enhanced": changed}


def main() -> int:
    print("enhanced strict L1 social metadata:", enhance_social_metadata())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
