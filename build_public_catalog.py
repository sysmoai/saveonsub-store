#!/usr/bin/env python3
"""Generate the browser catalog from the governed build-time projection.

The public JS keeps fields used by the storefront while stripping market-survey,
rank, proof and operational-promise fields that must not leak into customer-facing
runtime data.
"""
from __future__ import annotations

import json
from pathlib import Path

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
}


def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in DROP_KEYS}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    public = scrub(data)
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
