#!/usr/bin/env python3
"""Project the canonical private/raw catalog into the approved public pricing model.

This runs only in the build workspace. It does not rewrite the committed source
catalog. The staged public artifact and browser catalog are generated from this
projection, so legacy cheap/shared AI rows cannot silently return on a later build.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "catalog.json"
POLICY_PATH = ROOT / "ops" / "PRICING-V2-2026-09-17.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def public_plan(plan: dict) -> dict:
    access_type = plan.get("access_type", "personal")
    access_label = {
        "personal": "Customer-specific access",
        "team": "Team / Workspace access",
        "bundle": "Bundle",
        "service": "Setup / Service",
    }.get(access_type, "Confirm access method")
    out = {
        "label": plan["label"],
        "bdt": int(plan["bdt"]),
        "duration": plan.get("duration", "1 month"),
        "type": access_type,
        "access_label": access_label,
        "billing_unit": plan.get("billing_unit", "month"),
    }
    return out


def main() -> int:
    catalog = load(CATALOG_PATH)
    policy = load(POLICY_PATH)
    approved = policy.get("approved_products", {})
    ai_categories = set(policy.get("ai_categories", []))

    meta = catalog.setdefault("meta", {})
    meta["usd_anchor_rate"] = policy.get("fx_reference_bdt_per_usd", 124)
    meta["commercial_revision"] = policy["revision"]
    meta["pricing_review_rule"] = "Confirm exact provider tier, checkout amount, access method and availability before payment when a fixed price is not approved."
    meta.pop("delivery_slas", None)
    meta.pop("warranty", None)

    fixed = 0
    inquiry = 0
    untouched = 0
    seen_rules = set()

    for product in catalog.get("products", []):
        pid = str(product.get("id", "")).strip()
        category = str(product.get("category", "")).strip()
        rule = approved.get(pid)
        if rule is not None:
            seen_rules.add(pid)

        # Remove public-facing operational promises from every raw plan. Prices
        # for non-AI categories can remain, but SLA/warranty is always order-specific.
        for plan in product.get("plans", []) or []:
            for key in ("sla", "delivery", "delivery_sla", "warranty", "replacement", "save_pct", "official_bdt", "compare_at"):
                plan.pop(key, None)

        # Bundles are rebuilt only after every component access method is verified.
        # Legacy bundle rows included credential-shared AI components, so they are
        # inquiry-only in this release rather than silently repriced.
        is_bundle = category == "bundles" or pid.startswith("bundle-") or pid.startswith("aips-")

        if rule and rule.get("mode") != "inquiry" and rule.get("plans"):
            product["plans"] = [public_plan(p) for p in rule["plans"]]
            product["request_price"] = False
            product["pricing_status"] = "approved-fixed"
            product["pricing_revision"] = policy["revision"]
            product["commercial_note"] = "SaveOnSub local catalog price. Confirm current provider tier, access method and availability before payment."
            if rule.get("official_usd") is not None:
                product["official_usd"] = rule["official_usd"]
            fixed += 1
            continue

        # Every unapproved AI product, explicit inquiry rule, and legacy bundle is
        # fail-closed: keep the URL/indexing surface, but publish no stale fixed price
        # and no credential-shared cart action.
        if (rule and rule.get("mode") == "inquiry") or category in ai_categories or is_bundle:
            product["plans"] = []
            product["request_price"] = True
            product["pricing_status"] = "price-review-required"
            product["pricing_revision"] = policy["revision"]
            product["commercial_note"] = (rule or {}).get(
                "note",
                "Current fixed price is withheld until the exact provider tier, checkout amount, access method and availability are reconfirmed.",
            )
            inquiry += 1
            continue

        product["pricing_status"] = "existing-local-catalog"
        product["pricing_revision"] = policy["revision"]
        untouched += 1

    missing = sorted(set(approved) - seen_rules)
    # Missing optional rule IDs are a warning, not a reason to invent a matching
    # product. Every actual AI row is already fail-closed by category.
    if missing:
        print("[pricing-v2] optional rule ids not present in source catalog: " + ", ".join(missing))

    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"[pricing-v2] revision={policy['revision']} fixed={fixed} inquiry={inquiry} "
        f"existing-non-ai={untouched}; usd_reference={meta['usd_anchor_rate']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
