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
import html as html_lib
import json
import re
from html.parser import HTMLParser
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


def plan_profiles() -> dict[str, dict]:
    """Actual raw restricted offers and exact provider-gated orderable plans."""
    raw = json.loads(PRICEBOOK.read_text(encoding="utf-8"))["approved_products"]
    effective = load_policy(PRICEBOOK)["approved_products"]
    profiles = {}
    for pid, rule in raw.items():
        restricted = [
            {"plan_id": p["plan_id"], "label": p["label"], "bdt": int(p["bdt"])}
            for p in (rule.get("plans") or []) if p.get("access_type") == "shared"
        ]
        if not restricted:
            continue
        allowed = {
            p["plan_id"]: (str(p["label"]), int(p["bdt"]))
            for p in (effective[pid].get("plans") or [])
        }
        profiles[pid] = {"restricted": restricted, "allowed": allowed}
    return profiles


def _stale_offer_copy(markup: str, offers: list[dict]) -> list[str]:
    """Catch a price+shared-plan sales claim without requiring a SKU ID or badge."""
    cleaned = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", markup,
                     flags=re.I | re.S)
    cleaned = html_lib.unescape(re.sub(r"<[^>]+>", " ", cleaned))
    cleaned = re.sub(r"\s+", " ", cleaned).casefold()
    issues = []
    for p in offers:
        label = re.sub(r"\s+", " ", str(p["label"])).strip().casefold()
        price = "৳" + format(int(p["bdt"]), ",")
        if not label:
            continue
        if (re.search(re.escape(label) + r".{0,70}" + re.escape(price), cleaned) or
                re.search(re.escape(price) + r".{0,50}" + re.escape(label), cleaned)):
            issues.append("restricted price+plan copy visible: " + str(p["plan_id"]))
    return issues


class _CartActions(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.actions: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "button":
            action = dict(attrs).get("onclick") or ""
            if "cartAdd" in action:
                self.actions.append(action)


def _cart_action_issues(pid: str, page_html: str,
                        allowed: dict[str, tuple[str, int]]) -> list[str]:
    parser = _CartActions()
    parser.feed(page_html)
    issues = []
    for action in parser.actions:
        m = re.fullmatch(r"\s*cartAdd\((.*)\)\s*;?\s*", action, flags=re.S)
        if not m:
            issues.append(f"{pid}: malformed cartAdd action")
            continue
        try:
            args = json.loads("[" + m.group(1) + "]")
        except (TypeError, ValueError):
            issues.append(f"{pid}: invalid cartAdd arguments")
            continue
        if len(args) != 5 or args[0] != pid or not isinstance(args[4], str):
            issues.append(f"{pid}: cartAdd missing correct product or stable plan ID")
            continue
        approved = allowed.get(args[4])
        if approved is None or args[1] != approved[0] or args[2] != approved[1]:
            issues.append(f"{pid}: cartAdd quotes an unapproved plan or amount")
    return issues


def validate_product_html(pid: str, html: str, held_ids: set[str],
                          restricted_offers: list[dict] | None = None,
                          allowed_plans: dict[str, tuple[str, int]] | None = None) -> list[str]:
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
    issues.extend(_stale_offer_copy(html, restricted_offers or []))
    issues.extend(_cart_action_issues(pid, html, allowed_plans or {}))
    return issues


def validate_price_list(html: str, locale: str,
                        offers: list[dict] | None = None) -> list[str]:
    disallowed = ("শেয়ার্ড অ্যাকাউন্ট (একাধিক ব্যবহারকারী)"
                  if locale == "bn" else "Shared account (multiple users)")
    issues = ([f"/{locale}/prices: shared-offer access descriptor remains"]
              if disallowed in html else [])
    issues.extend(f"/{locale}/prices: {issue}"
                  for issue in _stale_offer_copy(html, offers or []))
    return issues


def validate_public_catalog(js: str, restricted: dict[str, set[str]] | None = None) -> list[str]:
    issues = []
    if "SOS_COMMERCIAL_REVISION" not in js:
        issues.append("catalog.js missing governed revision marker")
    m = re.search(r"\bconst\s+CATALOG\s*=\s*(\{[^\n]*\});", js)
    if not m:
        return issues + ["catalog.js missing parseable governed CATALOG object"]
    try:
        products = json.loads(m.group(1)).get("products")
        if not isinstance(products, list):
            raise ValueError("products is not a list")
    except (TypeError, ValueError) as exc:
        return issues + [f"catalog.js malformed product data: {exc}"]
    restricted = restricted or {}
    seen = set()
    for product in products:
        pid = product.get("id")
        seen.add(pid)
        for plan in product.get("plans") or []:
            if plan.get("type") == "shared" or plan.get("access_type") == "shared":
                issues.append(f"catalog.js exposes shared access: {pid}")
            if plan.get("plan_id") in restricted.get(pid, set()):
                issues.append(f"catalog.js exposes held SKU ID: {pid}")
    missing = set(restricted) - seen
    if missing:
        issues.append(f"catalog.js missing {len(missing)} affected products")
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
