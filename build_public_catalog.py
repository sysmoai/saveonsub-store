#!/usr/bin/env python3
"""Generate the browser catalog from the governed build-time projection.

The public JS keeps fields used by the storefront while stripping market-survey,
rank, proof and operational-promise fields that must not leak into customer-facing
runtime data.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from catalog_hold_gate import approved_plans, catalog_errors
from pricebook import load_policy

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "catalog.json"
OUT = ROOT / "assets" / "catalog.js"

DROP_KEYS = {
    "market",
    "market_survey",
    "keywords",
    "bestseller_rank",
    "order_count",
    "orders",
    "reviews",
    "review_count",
    "rating",
    "save_pct",
    "official_bdt",
    "compare_at",
    "supplier",
    "supplier_cost",
    "cost",
    "margin",
    "profit",
    "warranty",
    "delivery_slas",
    "delivery_sla",
    "replacement",
    "faq",
    "save_bdt", "official_usd", "price_source",
}


def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in DROP_KEYS}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    policy = load_policy(ROOT / 'ops' / 'PRICING-V2-2026-09-17.json')
    errors = catalog_errors(data, policy)
    if errors:
        raise SystemExit('[public-catalog] HOLD violation: ' + '; '.join(errors[:10]))
    public = scrub(data)
    # Public metadata is allowlisted; old FX anchors and historical pricing
    # precedence (including cross-business provenance) must not be shipped.
    meta = public.get("meta", {})
    if not isinstance(meta, dict):
        raise SystemExit("[public-catalog] malformed public metadata")
    public["meta"] = {
        key: meta[key]
        for key in ("brand", "currency", "commercial_revision", "pricing_review_rule")
        if key in meta
    }

    # Fail closed on price fields at ANY nested depth. A substring test for
    # just "bdt" misses e.g. "sale_price_bdt" in a future data extension.
    forbidden = {
        "bdt", "from_bdt", "price_bdt", "approved_price_bdt",
        "sale_price_bdt", "save_bdt", "official_bdt", "official_usd",
        "usd_anchor_rate", "price_precedence", "price_source",
    }

    def residual_price_fields(value, location="catalog"):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in forbidden:
                    yield f"{location}.{key}"
                yield from residual_price_fields(child, f"{location}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from residual_price_fields(child, f"{location}[{index}]")

    unlock = (policy.get("commercial_hold") or {}).get("status") == "SELECTIVE_UNLOCK"
    approved = approved_plans(policy) if unlock else {}
    # Under a CEO selective unlock, plan-level "bdt" is the one allowed price
    # field, and only on products whose plans catalog_errors() matched to the
    # pricebook. Everything else is still fail-closed.
    remaining = [
        loc for loc in residual_price_fields(public)
        if not (unlock and re.fullmatch(r"catalog\.products\[\d+\]\.plans\[\d+\]\.bdt", loc))
    ]
    if remaining:
        raise SystemExit(
            "[public-catalog] residual fixed-price fields; no JS written: "
            + ", ".join(remaining[:10])
        )
    for product in public["products"]:
        product.pop("held_plans", None)  # held plans are not advertised in the browser catalog
        if unlock and product.get("plans") and product.get("id") in approved:
            product["sellability"] = "approved"
        else:
            product["sellability"] = "inquiry_only"  # legacy status='live' is not sale permission
    revision = public.get("meta", {}).get("commercial_revision", "unknown")
    payload = json.dumps(public, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(
        "/* SAVEONSUB governed public catalog; generated during canonical build. */\n"
        f"const SOS_COMMERCIAL_REVISION = {json.dumps(revision)};\n"
        f"const CATALOG = {payload};\n",
        encoding="utf-8",
    )
    print(f"[public-catalog] wrote {OUT} revision={revision} products={len(public.get('products', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
