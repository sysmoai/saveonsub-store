#!/usr/bin/env python3
"""Submit live URLs to IndexNow (Bing, Yandex, Seznam...) after a CEO-approved deploy.

Not a build step. The key file /c17f09357d9ba41d3f98eb488be937c1.txt is public by design (IndexNow proves
site ownership by fetching it). Usage, after deploy only:
    python indexnow_submit.py                 # every <loc> in _site/sitemap.xml
    python indexnow_submit.py URL [URL ...]   # specific URLs
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KEY = "c17f09357d9ba41d3f98eb488be937c1"
HOST = "saveonsub.com"


def main(argv: list[str]) -> int:
    urls = argv or re.findall(r"<loc>(.*?)</loc>", (ROOT / "_site" / "sitemap.xml").read_text(encoding="utf-8"))
    urls = [u for u in urls if u.startswith(f"https://{HOST}/")][:10000]
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"https://{HOST}/{KEY}.txt",
                       "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8",
                                          "User-Agent": "saveonsub-indexnow/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"[indexnow] HTTP {r.status} for {len(urls)} URL(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
