#!/usr/bin/env python3
"""Read-only, fail-closed checks for the current SaveOnSub EXEC-010 HOLD.

Historical status='live' preserves URLs but NEVER authorizes a quote, cart,
checkout, or published price. A future selective SKU unlock needs a separately
reviewed validator plus CEO source approval.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
CATALOG = ROOT / "catalog.json"
FORBIDDEN_PRODUCT_KEYS = {
    "from_bdt", "price_bdt", "approved_price_bdt", "sale_price_bdt",
    "save_pct", "official_bdt",
}


def catalog_errors(catalog: object, policy: object) -> list[str]:
    """Validate the governed HOLD projection; do not mutate either input."""
    errors: list[str] = []
    if not isinstance(policy, dict) or not isinstance(catalog, dict):
        return ["catalog/policy must be JSON objects"]
    revision = policy.get("revision")
    if not isinstance(revision, str) or not revision:
        errors.append("policy: missing revision")
    global_hold = policy.get("commercial_hold")
    if isinstance(global_hold, dict) and global_hold.get("status") == "SELECTIVE_UNLOCK":
        return errors + selective_unlock_errors(catalog, policy)
    if not isinstance(global_hold, dict) or global_hold.get("status") != "HOLD":
        errors.append("policy: non-HOLD requires a separate CEO-approved sellability validator; refusing fixed offers")
        return errors
    meta = catalog.get("meta")
    if not isinstance(meta, dict) or meta.get("commercial_revision") != revision:
        errors.append("catalog: pricing revision is missing or does not match policy")
    products = catalog.get("products")
    if not isinstance(products, list) or not products:
        return errors + ["catalog: products must be a nonempty list"]
    seen: set[str] = set()
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            errors.append(f"products[{index}]: expected object")
            continue
        pid = product.get("id")
        if not isinstance(pid, str) or not pid.strip() or pid in seen:
            errors.append(f"products[{index}]: missing/duplicate product id")
            continue
        seen.add(pid)
        plans = product.get("plans")
        if not isinstance(plans, list):
            errors.append(f"{pid}: plans must be a list, even in HOLD")
        elif plans:
            errors.append(f"{pid}: priced plans present during global HOLD")
        if product.get("request_price") is not True:
            errors.append(f"{pid}: HOLD requires request_price=true")
        if product.get("pricing_status") != "price-review-required":
            errors.append(f"{pid}: HOLD requires price-review-required status")
        if product.get("pricing_revision") != revision:
            errors.append(f"{pid}: pricing revision mismatch")
        if product.get("commercial_hold") != "EXEC-010":
            errors.append(f"{pid}: missing explicit EXEC-010 hold marker")
        if product.get("approved_sellable") is True:
            errors.append(f"{pid}: approved_sellable conflicts with HOLD")
        residual = FORBIDDEN_PRODUCT_KEYS.intersection(product)
        if residual:
            errors.append(f"{pid}: derived sale/discount fields forbidden in HOLD: {', '.join(sorted(residual))}")
    return errors


def approved_plans(policy: dict) -> dict[str, list[tuple[str, int]]]:
    """CEO pricebook: product id -> [(label, bdt)] for mode=fixed rules only."""
    out: dict[str, list[tuple[str, int]]] = {}
    for pid, rule in (policy.get("approved_products") or {}).items():
        if isinstance(rule, dict) and rule.get("mode") == "fixed" and rule.get("plans"):
            out[pid] = [(str(p["label"]), int(p["bdt"])) for p in rule["plans"]]
    return out


def selective_unlock_errors(catalog: dict, policy: dict) -> list[str]:
    """Sellability validator for a CEO-approved selective unlock.

    A product may carry priced plans only if every plan matches the founder's
    pricebook exactly (label and BDT); every other product stays inquiry-only.
    """
    errors: list[str] = []
    hold = policy.get("commercial_hold") or {}
    if not str(hold.get("authority", "")).strip():
        errors.append("policy: SELECTIVE_UNLOCK needs a recorded founder authority")
    revision = policy.get("revision")
    meta = catalog.get("meta")
    if not isinstance(meta, dict) or meta.get("commercial_revision") != revision:
        errors.append("catalog: pricing revision is missing or does not match policy")
    book = approved_plans(policy)
    products = catalog.get("products")
    if not isinstance(products, list) or not products:
        return errors + ["catalog: products must be a nonempty list"]
    seen: set[str] = set()
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            errors.append(f"products[{index}]: expected object")
            continue
        pid = product.get("id")
        if not isinstance(pid, str) or not pid.strip() or pid in seen:
            errors.append(f"products[{index}]: missing/duplicate product id")
            continue
        seen.add(pid)
        plans = product.get("plans")
        if not isinstance(plans, list):
            errors.append(f"{pid}: plans must be a list")
            continue
        residual = FORBIDDEN_PRODUCT_KEYS.intersection(product)
        if residual:
            errors.append(f"{pid}: derived sale/discount fields forbidden: {', '.join(sorted(residual))}")
        if plans:
            if pid not in book:
                errors.append(f"{pid}: priced plans without CEO approval")
                continue
            got = [(str(p.get("label")), int(p.get("bdt", -1))) for p in plans]
            if got != book[pid]:
                errors.append(f"{pid}: plans differ from the CEO pricebook")
            if product.get("request_price") is not False:
                errors.append(f"{pid}: approved product must not be request_price")
        elif product.get("request_price") is not True:
            errors.append(f"{pid}: unapproved product must be Price on Request")
    return errors


def refuse_legacy_generator(name: str) -> None:
    """Never run obsolete price-generating HTML/SEO entry points under EXEC-010."""
    raise SystemExit(
        f"{name} retired under the commercial HOLD: use build_site.py "
        "for governed, staging-only output; no unapproved price generation"
    )


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    errors = catalog_errors(catalog, policy)
    if errors:
        for error in errors[:30]:
            print("CATALOG HOLD BLOCKED: " + error)
        print(f"Catalog HOLD gate failed: {len(errors)} issue(s)")
        return 1
    sellable = sum(len(p.get("plans") or []) for p in catalog["products"])
    if sellable:
        print(f"Catalog gate passed (CEO SELECTIVE_UNLOCK): {sellable} approved plans, "
              f"{sum(1 for p in catalog['products'] if not p.get('plans'))} inquiry-only products")
        return 0
    print(f"Catalog HOLD gate passed: {len(catalog['products'])} inquiry-only products, 0 sellable plans")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
