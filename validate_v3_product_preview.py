#!/usr/bin/env python3
"""Validate preview-only v3 ecommerce product pages."""
from __future__ import annotations

import pathlib
import re

from catalog_model import load_catalog

ROOT = pathlib.Path(__file__).resolve().parent
PREVIEW = ROOT / "_preview_v3"

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def main() -> int:
    catalog = load_catalog()
    products = catalog.get("products", [])
    en_files = sorted(PREVIEW.glob("p/*.html"))
    bn_files = sorted(PREVIEW.glob("bn/p/*.html"))
    if len(en_files) != len(products):
        fail(f"EN product previews expected {len(products)}, found {len(en_files)}")
    if len(bn_files) != len(products):
        fail(f"BN product previews expected {len(products)}, found {len(bn_files)}")

    by_id = {p["id"]: p for p in products}
    forbidden = ("cartAdd(", '"@type": "Offer"', '"@type":"Offer"', "AggregateOffer", "catalog.json", "aips-live.json")

    for language, files in (("en", en_files), ("bn", bn_files)):
        for path in files:
            pid = path.stem
            product = by_id.get(pid)
            rel = path.relative_to(PREVIEW).as_posix()
            if not product:
                fail(f"{rel}: product missing from catalog model")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if '<meta name="robots" content="noindex,follow">' not in text:
                fail(f"{rel}: missing noindex,follow")
            if 'data-v3-preview="true"' not in text:
                fail(f"{rel}: missing preview marker")
            expected_canonical = f'https://saveonsub.com/{product["routes_v3"][language]}'
            if f'<link rel="canonical" href="{expected_canonical}">' not in text:
                fail(f"{rel}: canonical does not preserve current public product URL")
            if re.search(r"৳\s*[0-9]", text):
                fail(f"{rel}: exposes BDT price")
            if re.search(r"<(form|button)\b", text, re.I):
                fail(f"{rel}: contains active form/button commerce control")
            for needle in forbidden:
                if needle in text:
                    fail(f"{rel}: contains forbidden token {needle}")

            plan_ids = re.findall(r'data-plan-id="([^"]+)"', text)
            expected_plan_ids = [p["plan_id_v3"] for p in product.get("plans", [])]
            if plan_ids != expected_plan_ids:
                fail(f"{rel}: plan identity/order mismatch")

            hrefs = re.findall(r'class="v3-link" href="([^"]+)"', text)
            if len(hrefs) != len(expected_plan_ids):
                fail(f"{rel}: expected {len(expected_plan_ids)} plan links, found {len(hrefs)}")
            for href in hrefs:
                target = path.parent / href
                if not target.is_file():
                    fail(f"{rel}: plan link target missing: {href}")

            media_ids = re.findall(r'data-media-id="([^"]+)"', text)
            expected_media_ids = [m["media_id"] for m in product.get("media_v3", [])]
            if media_ids != expected_media_ids:
                fail(f"{rel}: media registry/order mismatch")

    if errors:
        print(f"V3 PRODUCT PREVIEW INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    print(
        f"v3 product preview valid: products={len(products)} EN={len(en_files)} BN={len(bn_files)} "
        f"commerce_controls=0 prices=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
