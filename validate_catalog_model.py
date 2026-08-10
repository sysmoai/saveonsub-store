#!/usr/bin/env python3
"""Validate the additive SAVEONSUB v3 catalog compatibility model.

This validator is intentionally strict about identity, route uniqueness, media
references and legacy-field preservation. It does not change public output.
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

from catalog_model import iter_plans, load_raw_catalog, normalize_catalog, source_digest

ROOT = pathlib.Path(__file__).resolve().parent

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def compare_legacy_dict(raw: dict, normalized: dict, scope: str, added_keys: set[str]) -> None:
    for key, value in raw.items():
        if key in added_keys:
            continue
        if key not in normalized:
            fail(f"{scope}: legacy key disappeared: {key}")
        elif normalized[key] != value and key != "plans":
            fail(f"{scope}: legacy value changed for key {key}")


def main() -> int:
    raw = load_raw_catalog()
    before = source_digest(raw)
    normalized = normalize_catalog(raw)
    after = source_digest(raw)

    if before != after:
        fail("normalize_catalog mutated the raw input")

    raw_products = raw.get("products", [])
    products = normalized.get("products", [])
    if len(raw_products) != len(products):
        fail(f"product count changed: {len(raw_products)} -> {len(products)}")

    raw_plan_count = sum(len(p.get("plans", [])) for p in raw_products)
    plan_count = sum(len(p.get("plans", [])) for p in products)
    if raw_plan_count != plan_count:
        fail(f"plan count changed: {raw_plan_count} -> {plan_count}")

    product_ids = [p.get("id") for p in products]
    if len(set(product_ids)) != len(product_ids):
        dupes = sorted(k for k, v in Counter(product_ids).items() if v > 1)
        fail(f"duplicate product IDs: {dupes}")

    plan_ids: list[str] = []
    plan_routes_en: list[str] = []
    plan_routes_bn: list[str] = []
    media_ids: list[str] = []
    product_routes_en: list[str] = []
    product_routes_bn: list[str] = []
    unknown_commercial = 0
    fallback_media = 0

    raw_by_id = {p["id"]: p for p in raw_products}
    for product in products:
        pid = product["id"]
        raw_product = raw_by_id[pid]
        compare_legacy_dict(
            raw_product,
            product,
            f"product {pid}",
            {"product_id", "routes_v3", "commercial_state_v3", "media_v3"},
        )

        expected_en = f"p/{pid}.html"
        expected_bn = f"bn/p/{pid}.html"
        if product["routes_v3"]["en"] != expected_en:
            fail(f"{pid}: existing EN product route changed")
        if product["routes_v3"]["bn"] != expected_bn:
            fail(f"{pid}: existing BN product route changed")
        product_routes_en.append(product["routes_v3"]["en"])
        product_routes_bn.append(product["routes_v3"]["bn"])

        raw_plans = raw_product.get("plans", [])
        normalized_plans = product.get("plans", [])
        if len(raw_plans) != len(normalized_plans):
            fail(f"{pid}: plan count changed")
        for idx, plan in enumerate(normalized_plans):
            raw_plan = raw_plans[idx]
            compare_legacy_dict(
                raw_plan,
                plan,
                f"{pid} plan {idx + 1}",
                {"plan_id_v3", "plan_slug_v3", "product_id_v3", "commercial_state_v3", "routes_v3"},
            )
            plan_id = str(plan.get("plan_id_v3") or "")
            if not plan_id:
                fail(f"{pid} plan {idx + 1}: missing plan_id_v3")
            plan_ids.append(plan_id)
            if plan.get("product_id_v3") != pid:
                fail(f"{pid} plan {idx + 1}: wrong product_id_v3")
            plan_routes_en.append(plan["routes_v3"]["en"])
            plan_routes_bn.append(plan["routes_v3"]["bn"])
            if plan.get("commercial_state_v3") == "unknown":
                unknown_commercial += 1

        for media in product.get("media_v3", []):
            media_id = str(media.get("media_id") or "")
            if not media_id:
                fail(f"{pid}: normalized media missing media_id")
            media_ids.append(media_id)
            if media.get("product_id") != pid:
                fail(f"{pid}: media {media_id} points at wrong product")
            if media.get("fallback"):
                fallback_media += 1
            if media.get("source") == "local":
                src = str(media.get("src") or "")
                if not src.startswith("/"):
                    fail(f"{pid}: local media must use root-relative src: {src}")
                else:
                    local = ROOT / src.lstrip("/")
                    if not local.is_file():
                        fail(f"{pid}: local media does not exist: {src}")

    for name, values in (
        ("plan IDs", plan_ids),
        ("EN plan routes", plan_routes_en),
        ("BN plan routes", plan_routes_bn),
        ("media IDs", media_ids),
        ("EN product routes", product_routes_en),
        ("BN product routes", product_routes_bn),
    ):
        duplicates = sorted(k for k, v in Counter(values).items() if v > 1)
        if duplicates:
            fail(f"duplicate {name}: {duplicates[:10]}")

    # New plan routes may not collide with any existing HTML path.
    existing_html = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.glob("**/*.html")
        if "_site" not in p.parts and ".git" not in p.parts
    }
    collisions = sorted((set(plan_routes_en) | set(plan_routes_bn)) & existing_html)
    if collisions:
        fail(f"new plan routes collide with existing HTML: {collisions[:10]}")

    # Fail closed: legacy status labels are never enough to authorize commerce.
    for _, plan in iter_plans(normalized):
        if plan.get("commercial_state_v3") not in {"allowed", "direct_provider_only", "blocked", "unknown"}:
            fail(f"invalid commercial_state_v3: {plan.get('commercial_state_v3')}")

    if errors:
        print(f"V3 CATALOG MODEL INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    summary = {
        "products": len(products),
        "plans": plan_count,
        "unique_plan_ids_v3": len(set(plan_ids)),
        "unique_plan_routes_en": len(set(plan_routes_en)),
        "unique_plan_routes_bn": len(set(plan_routes_bn)),
        "normalized_media_items": len(media_ids),
        "fallback_media_items": fallback_media,
        "plans_defaulting_commercial_unknown": unknown_commercial,
        "legacy_source_sha256": before,
        "legacy_product_routes_preserved": True,
        "legacy_input_mutated": False,
    }
    print("V3 catalog compatibility model valid")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
