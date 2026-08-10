#!/usr/bin/env python3
"""Post-deploy smoke verification for the strict SAVEONSUB L1 public release."""
from __future__ import annotations

import argparse
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

from catalog_model import load_catalog

FORBIDDEN_HTML = [
    "৳",
    "add to cart",
    "buy now",
    "bkash",
    "nagad",
    "wa.me/",
    "api.whatsapp.com",
    '"@type":"offer"',
    '"@type": "offer"',
    '"@type":"aggregateoffer"',
    '"@type": "aggregateoffer"',
]


def fetch(base: str, path: str, attempts: int = 4) -> tuple[int, dict[str, str], str, str]:
    url = urllib.parse.urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SAVEONSUB-release-verifier/1.0"})
            with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as res:
                body = res.read(2_000_000).decode("utf-8", errors="replace")
                headers = {k.lower(): v for k, v in res.headers.items()}
                return res.status, headers, body, res.geturl()
        except Exception as exc:  # pragma: no cover - network-only path
            last = exc
            if attempt + 1 < attempts:
                time.sleep(2)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("SAVEONSUB_BASE_URL", "https://saveonsub.com"))
    parser.add_argument("--expected-sha", default=os.getenv("GITHUB_SHA", ""))
    args = parser.parse_args()

    expected_sha = args.expected_sha.strip().lower()
    require(bool(re.fullmatch(r"[0-9a-f]{40}", expected_sha)), "expected SHA must be a 40-character git SHA")

    status, headers, manifest, final_url = fetch(args.base_url, "/BUILD-MANIFEST.txt")
    require(status == 200, f"BUILD-MANIFEST status {status}")
    require(f"git_sha={expected_sha}" in manifest, "live BUILD-MANIFEST does not match expected git SHA")
    require("release_mode=L1_PUBLIC_INFO_ONLY" in manifest, "live release mode is not L1_PUBLIC_INFO_ONLY")
    require("public_prices=0" in manifest, "live artifact unexpectedly publishes prices")
    require("commerce_controls=0" in manifest, "live artifact unexpectedly exposes commerce controls")

    catalog = load_catalog()
    products = catalog.get("products", [])
    require(bool(products), "normalized catalog has no products")
    first_product = products[0]
    first_plan = (first_product.get("plans") or [None])[0]

    routes = ["/", "/bn.html", "/all.html", "/about.html", "/contact.html", "/faq.html"]
    for product in products[:5]:
        routes.append("/" + product["routes_v3"]["en"])
        routes.append("/" + product["routes_v3"]["bn"])
    if first_plan:
        routes.append("/" + first_plan["routes_v3"]["en"])
        routes.append("/" + first_plan["routes_v3"]["bn"])

    checked = 0
    for route in routes:
        status, page_headers, body, resolved = fetch(args.base_url, route)
        require(status == 200, f"{route}: HTTP {status}")
        lower = body.lower().replace(" ", "")
        for token in FORBIDDEN_HTML:
            token_cmp = token.lower().replace(" ", "")
            require(token_cmp not in lower, f"{route}: forbidden L1 token {token!r}")
        require("content-security-policy" in page_headers, f"{route}: CSP header missing")
        require(page_headers.get("x-content-type-options", "").lower() == "nosniff", f"{route}: nosniff header missing")
        checked += 1

    status, _, robots, _ = fetch(args.base_url, "/robots.txt")
    require(status == 200 and "Sitemap: https://saveonsub.com/sitemap.xml" in robots, "robots.txt invalid")
    status, _, sitemap, _ = fetch(args.base_url, "/sitemap.xml")
    require(status == 200, "sitemap.xml unavailable")
    require(first_product["routes_v3"]["en"] in sitemap, "sitemap missing product route")

    print(f"live verification passed: sha={expected_sha} routes={checked} base={final_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
