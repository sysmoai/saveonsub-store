#!/usr/bin/env python3
"""Make staged SaveOnSub logo references cache-safe.

Cloudflare can retain a previously cached static asset at a stable custom-domain
URL even after a Pages deployment changes the origin object. Production HTML
therefore references a content-addressed copy of the approved logo instead of
the mutable /assets/logo.svg path.

Run only after stage_deploy.py. The original asset remains in _site for backward
compatibility, but current staged HTML must reference the immutable filename.
"""
from __future__ import annotations

import hashlib
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
ASSETS = SITE / "assets"
SOURCE = ASSETS / "logo.svg"
BRAND_LOCK = 'data-brand-lock="2026-08-19-approved"'


def main() -> int:
    if not SITE.is_dir() or not SOURCE.is_file():
        print("CACHE-SAFE BRAND ERROR — run stage_deploy.py first")
        return 1

    raw = SOURCE.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print("CACHE-SAFE BRAND ERROR — staged logo is not UTF-8 SVG")
        return 1

    if BRAND_LOCK not in text:
        print("CACHE-SAFE BRAND ERROR — staged logo is not the approved brand-locked asset")
        return 1

    digest = hashlib.sha256(raw).hexdigest()
    immutable_name = f"logo-{digest[:16]}.svg"
    immutable = ASSETS / immutable_name
    shutil.copy2(SOURCE, immutable)

    changed = 0
    token = "assets/logo.svg"
    replacement = f"assets/{immutable_name}"
    for page in SITE.rglob("*.html"):
        old = page.read_text(encoding="utf-8", errors="strict")
        new = old.replace(token, replacement)
        if new != old:
            page.write_text(new, encoding="utf-8")
            changed += 1

    # Current HTML must never point at the mutable logo URL after this pass.
    stale = []
    referenced = 0
    for page in SITE.rglob("*.html"):
        body = page.read_text(encoding="utf-8", errors="strict")
        if token in body:
            stale.append(page.relative_to(SITE).as_posix())
        if replacement in body:
            referenced += 1

    if stale:
        print(f"CACHE-SAFE BRAND ERROR — {len(stale)} HTML page(s) still reference {token}")
        for path in stale[:20]:
            print(f"  {path}")
        return 1
    if referenced == 0:
        print("CACHE-SAFE BRAND ERROR — immutable logo is not referenced by staged HTML")
        return 1
    if immutable.read_bytes() != raw:
        print("CACHE-SAFE BRAND ERROR — immutable logo bytes changed during copy")
        return 1

    print(f"cache-safe approved logo: /assets/{immutable_name}")
    print(f"logo_sha256={digest}")
    print(f"rewrote {changed} HTML file(s); immutable logo referenced by {referenced} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
