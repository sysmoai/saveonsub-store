#!/usr/bin/env python3
"""Install the strict L1 response-header policy into the generated public artifact."""
from __future__ import annotations

from build_public_info_v3 import DEST

STRICT_HEADERS = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()
  Strict-Transport-Security: max-age=63072000; includeSubDomains
  Cross-Origin-Opener-Policy: same-origin
  X-Permitted-Cross-Domain-Policies: none
  Content-Security-Policy: default-src 'self'; script-src 'self'; script-src-attr 'none'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; manifest-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests

/sw.js
  Cache-Control: no-cache, no-store, must-revalidate
  Service-Worker-Allowed: /

/assets/site.webmanifest
  Cache-Control: public, max-age=86400
  Content-Type: application/manifest+json

/assets/*.png
  Cache-Control: public, max-age=604800
/assets/*.jpg
  Cache-Control: public, max-age=604800
/assets/*.svg
  Cache-Control: public, max-age=604800
/assets/*.ico
  Cache-Control: public, max-age=604800
/assets/*.woff2
  Cache-Control: public, max-age=604800

/assets/*.js
  Cache-Control: public, max-age=0, must-revalidate
/assets/*.css
  Cache-Control: public, max-age=0, must-revalidate
"""


def harden_security_headers() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    path = DEST / "_headers"
    prior = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    path.write_text(STRICT_HEADERS, encoding="utf-8")
    return {
        "strict_headers_written": 1,
        "strict_headers_changed": int(prior != STRICT_HEADERS),
    }


def main() -> int:
    print("hardened strict L1 headers:", harden_security_headers())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
