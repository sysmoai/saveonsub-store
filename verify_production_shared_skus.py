#!/usr/bin/env python3
"""Read-only production acceptance gate for every unverified shared-access SKU.

Unlike spot-checks of the original five explicit HOLDS, this derives the complete
restricted inventory from the canonical CEO pricebook, so future shared SKUs
cannot silently skip post-deployment verification. It never submits an order,
touches an account, or writes any production state.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

from pricebook import load_policy

ROOT = Path(__file__).resolve().parent
PRICEBOOK = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
CATALOG = ROOT / "catalog.json"


def restricted_inventory() -> dict[str, set[str]]:
    raw = json.loads(PRICEBOOK.read_text(encoding="utf-8"))["approved_products"]
    governed = load_policy(PRICEBOOK)["approved_products"]
    existing = {p["id"] for p in json.loads(CATALOG.read_text(encoding="utf-8"))["products"]}
    restricted = {}
    for pid, rule in raw.items():
        shared = {p["plan_id"] for p in (rule.get("plans") or [])
                  if p.get("access_type") == "shared"}
        if not shared:
            continue
        if not re.fullmatch(r"[a-z0-9-]+", pid) or pid not in existing:
            raise ValueError(f"Unmapped shared SKU product: {pid}")
        effective_rule = governed[pid]
        held = {p["plan_id"] for p in (effective_rule.get("held_plans") or [])}
        active = {p["plan_id"] for p in (effective_rule.get("plans") or [])}
        if not shared <= held or shared & active:
            raise ValueError(f"Shared rights guard missing for: {pid}")
        restricted[pid] = shared
    if not restricted:
        raise ValueError("Shared inventory unexpectedly empty; cannot certify release")
    return restricted


def validate_product_html(pid: str, html: str, held_ids: set[str]) -> list[str]:
    issues = []
    if 'data-held-plans="1"' not in html:
        issues.append(f"{pid}: missing visible held-plan notice")
    if f"/p/{pid}" not in html:
        issues.append(f"{pid}: product route/content mismatch")
    for plan_id in sorted(held_ids):
        if plan_id in html:
            issues.append(f"{pid}: restricted SKU still present in HTML: {plan_id}")
    if re.search(r'class=["\'][^"\']*\btos\s+shared\b', html):
        issues.append(f"{pid}: shared plan access badge still present")
    return issues


def validate_price_list(html: str, locale: str) -> list[str]:
    disallowed = ("শেয়ার্ড অ্যাকাউন্ট (একাধিক ব্যবহারকারী)"
                  if locale == "bn" else "Shared account (multiple users)")
    return ([f"/{locale}/prices: shared-offer access descriptor remains"]
            if disallowed in html else [])


def validate_public_catalog(js: str) -> list[str]:
    issues = []
    if "SOS_COMMERCIAL_REVISION" not in js:
        issues.append("catalog.js missing governed revision marker")
    if re.search(r'"type"\s*:\s*"shared"', js):
        issues.append("catalog.js still contains orderable shared-access plans")
    return issues


def fetch_text(url: str) -> str:
    req = Request(url, headers={
        "User-Agent": "SaveOnSub-Release-Verification/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    with urlopen(req, timeout=25) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status} for {url}")
        return response.read().decode("utf-8", errors="replace")


def verify_one(base: str, pid: str, locale: str, ids: set[str]) -> list[str]:
    path = f"/bn/p/{pid}" if locale == "bn" else f"/p/{pid}"
    url = base + path
    try:
        return [f"{path}: {issue}" for issue in validate_product_html(
            pid, fetch_text(url), ids)]
    except Exception as exc:
        return [f"{path}: fetch/validation error: {type(exc).__name__}: {exc}"]


def verify_production(base: str = "https://saveonsub.com") -> int:
    base = base.rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("Production verification requires HTTPS")
    restricted = restricted_inventory()
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        jobs = [pool.submit(verify_one, base, pid, locale, ids)
                for pid, ids in sorted(restricted.items())
                for locale in ("en", "bn")]
        for task in concurrent.futures.as_completed(jobs):
            failures.extend(task.result())

    for locale, path in (("en", "/prices"), ("bn", "/bn/prices")):
        try:
            failures.extend(validate_price_list(fetch_text(base + path), locale))
        except Exception as exc:
            failures.append(f"{path}: fetch/validation error: {type(exc).__name__}: {exc}")

    try:
        failures.extend(validate_public_catalog(fetch_text(base + "/assets/catalog.js")))
    except Exception as exc:
        failures.append(f"/assets/catalog.js: fetch/validation error: {type(exc).__name__}: {exc}")

    if failures:
        print("[shared-release] FAIL: " + str(len(failures)) + " problem(s)")
        for issue in failures[:50]:
            print("  " + issue)
        if len(failures) > 50:
            print("  ... " + str(len(failures) - 50) + " more")
        return 1

    print("[shared-release] PASS: " + str(len(restricted)) +
          " product groups, " + str(sum(map(len, restricted.values()))) +
          " shared SKUs held across EN/BN, price listings and browser catalog")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://saveonsub.com")
    args = parser.parse_args()
    return verify_production(args.base_url)


if __name__ == "__main__":
    raise SystemExit(main())
