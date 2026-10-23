#!/usr/bin/env python3
"""Fail-closed check that no credential-shared offer is sellable or promoted.

Checks (fails, never rewrites):
  * catalog.json and the staged browser catalog contain no shared-type plan
    (label or access type: shared, family slot, private profile, screen, seat);
  * no staged product page carries a shared plan card, cart action or priced
    Offer for a shared plan, and no shared promo copy ("Shared seats work the
    same as personal", "SHARED · LOW RISK", ...).

Cautionary copy that warns about sharing risk is allowed.
Usage: python3 shared_copy_check.py [SITE_DIR]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SHARED_LABEL = re.compile(r"shared|family slot|private profile|\bscreens?\b|\bseats?\b|শেয়ার্ড|শেয়ার্ড", re.I)
SHARED_TYPE = re.compile(r"^shared", re.I)
SHARED_PROMO = re.compile(
    r"Shared seats work the same as personal|SHARED · (?:LOW RISK|WARRANTY COVERED|POLICY RISK)"
    r"|শেয়ার্ড · (?:কম ঝুঁকি|ওয়ারেন্টিসহ)|শেয়ার্ড · (?:কম ঝুঁকি|ওয়ারেন্টিসহ)"
    r"|shared account bangladesh|cheapest shared|শেয়ার্ড [০-৯\d]+ টাকা",
    re.I,
)


def shared_plans(products: list[dict]) -> list[str]:
    out = []
    for product in products:
        for plan in product.get("plans") or []:
            label = str(plan.get("label", ""))
            kind = str(plan.get("type") or plan.get("access_type") or "")
            if SHARED_LABEL.search(label) or SHARED_TYPE.search(kind):
                out.append(f"{product.get('id')}: {label} ({kind or 'untyped'})")
    return out


def public_catalog_products(site: Path) -> list[dict]:
    js = site / "assets" / "catalog.js"
    if not js.exists():
        return []
    m = re.search(r"const CATALOG = (\{.*\});\s*$", js.read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1)).get("products", []) if m else []


def page_issues(site: Path) -> list[str]:
    issues = []
    pages = sorted((site / "p").glob("*.html")) + sorted((site / "bn" / "p").glob("*.html"))
    for path in pages:
        rel = path.relative_to(site).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'onclick="cartAdd\(([^)]*)\)"', text):
            if SHARED_LABEL.search(m.group(1)):
                issues.append(f"{rel}: shared plan cart action {m.group(1)[:80]}")
        for m in re.finditer(r'"@type"\s*:\s*"Offer"[^{}]*"name"\s*:\s*"([^"]*)"', text):
            if SHARED_LABEL.search(m.group(1)):
                issues.append(f"{rel}: shared Offer {m.group(1)[:80]}")
        for m in SHARED_PROMO.finditer(text):
            issues.append(f"{rel}: shared promo copy {m.group(0)!r}")
    return issues


def main(argv: list[str]) -> int:
    site = Path(argv[1]) if len(argv) > 1 else ROOT / "_site"
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    issues = [f"catalog.json: {x}" for x in shared_plans(catalog.get("products", []))]
    if site.is_dir():
        issues += [f"assets/catalog.js: {x}" for x in shared_plans(public_catalog_products(site))]
        issues += page_issues(site)
    if issues:
        print(f"[shared-copy] FAIL — {len(issues)} shared offer(s)/promo(s):")
        for x in issues[:60]:
            print("  " + x)
        return 1
    print("[shared-copy] PASS — no sellable or promoted credential-shared offer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
