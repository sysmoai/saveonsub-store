#!/usr/bin/env python3
"""Validate preview-only SAVEONSUB v3 plan pages.

The preview is deliberately not deployable. This check proves the route tree is
complete and fail-closed before any plan page can be considered for public use.
"""
from __future__ import annotations

import json
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
    expected_plans = sum(len(p.get("plans", [])) for p in catalog.get("products", []))
    en_files = sorted(PREVIEW.glob("p/*/*.html"))
    bn_files = sorted(PREVIEW.glob("bn/p/*/*.html"))

    if len(en_files) != expected_plans:
        fail(f"EN preview plan pages: expected {expected_plans}, found {len(en_files)}")
    if len(bn_files) != expected_plans:
        fail(f"BN preview plan pages: expected {expected_plans}, found {len(bn_files)}")

    expected_ids = {
        plan["plan_id_v3"]
        for product in catalog.get("products", [])
        for plan in product.get("plans", [])
    }
    found_en: set[str] = set()
    found_bn: set[str] = set()

    forbidden = {
        "cartAdd(": "cart handler",
        '"@type": "Offer"': "Offer schema",
        '"@type":"Offer"': "Offer schema",
        '"@type": "AggregateOffer"': "AggregateOffer schema",
        '"@type":"AggregateOffer"': "AggregateOffer schema",
        "catalog.json": "raw catalog reference",
        "aips-live.json": "internal AIPS reference",
    }

    for language, files, found in (("en", en_files, found_en), ("bn", bn_files, found_bn)):
        for path in files:
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(PREVIEW).as_posix()
            if '<meta name="robots" content="noindex,follow">' not in text:
                fail(f"{rel}: missing noindex,follow")
            if 'data-v3-preview="true"' not in text:
                fail(f"{rel}: missing preview marker")
            if '<link rel="canonical" href="https://saveonsub.com/' not in text:
                fail(f"{rel}: missing canonical")
            if "hreflang=" not in text:
                fail(f"{rel}: missing hreflang")
            if "data-plan-id=" not in text:
                fail(f"{rel}: missing plan ID")
            match = re.search(r'data-plan-id="([^"]+)"', text)
            if match:
                plan_id = match.group(1)
                if plan_id in found:
                    fail(f"{rel}: duplicate {language} plan ID {plan_id}")
                found.add(plan_id)
            for needle, description in forbidden.items():
                if needle in text:
                    fail(f"{rel}: contains forbidden {description}")
            # Preview plan pages must not leak current BDT sell prices.
            if re.search(r"৳\s*[0-9]", text):
                fail(f"{rel}: contains a BDT price")
            # They must not include an active commerce form/button.
            if re.search(r"<(form|button)\b", text, re.I):
                fail(f"{rel}: contains active form/button control")

    if found_en != expected_ids:
        missing = sorted(expected_ids - found_en)
        extra = sorted(found_en - expected_ids)
        fail(f"EN plan ID parity mismatch missing={missing[:5]} extra={extra[:5]}")
    if found_bn != expected_ids:
        missing = sorted(expected_ids - found_bn)
        extra = sorted(found_bn - expected_ids)
        fail(f"BN plan ID parity mismatch missing={missing[:5]} extra={extra[:5]}")

    manifest_path = PREVIEW / "manifest.json"
    if not manifest_path.is_file():
        fail("preview manifest missing")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("preview_only") is not True:
            fail("preview manifest is not marked preview_only")
        if manifest.get("public_deploy_excluded") is not True:
            fail("preview manifest is not marked deploy-excluded")
        if manifest.get("plans") != expected_plans:
            fail("preview manifest plan count mismatch")

    if errors:
        print(f"V3 PREVIEW INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    print(json.dumps({
        "v3_preview_valid": True,
        "plans": expected_plans,
        "en_plan_pages": len(en_files),
        "bn_plan_pages": len(bn_files),
        "prices_exposed": 0,
        "cart_controls": 0,
        "offer_schema": 0,
        "robots": "noindex,follow",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
