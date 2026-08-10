#!/usr/bin/env python3
"""Validate the SAVEONSUB v3 active catalog + legacy quarantine model."""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter

from catalog_model import iter_plans, load_raw_catalog, normalize_catalog, source_digest

ROOT = pathlib.Path(__file__).resolve().parent
errors: list[str] = []
PROOF_KEYS = {"orders", "bestseller_rank", "market"}
PRICE_KEYS = {"bdt", "price_bdt", "price", "usd"}


def fail(message: str) -> None:
    errors.append(message)


def looks_openai_shared(product: dict, plan: dict) -> bool:
    identity = f"{product.get('id','')} {product.get('name','')}".lower()
    openai = "chatgpt" in identity or "openai" in identity
    shared = (
        str(plan.get("type") or "").lower() == "shared"
        or str(plan.get("tos") or "").lower().startswith("shared")
        or "shared" in str(plan.get("label") or "").lower()
    )
    return openai and shared


def plan_signature(plan: dict) -> tuple:
    return (
        str(plan.get("type") or ""),
        str(plan.get("label") or ""),
        str(plan.get("duration") or ""),
        str(plan.get("tos") or ""),
    )


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
    active_plan_count = sum(len(p.get("plans", [])) for p in products)
    quarantined_count = sum(len(p.get("quarantined_plans_v3", [])) for p in products)
    if raw_plan_count != active_plan_count + quarantined_count:
        fail(
            f"plan accounting mismatch: raw={raw_plan_count} active={active_plan_count} quarantined={quarantined_count}"
        )

    precedence = normalized.get("meta", {}).get("price_precedence", [])
    if any(re.search(r"(^|[-_])aips($|[-_])", str(s), re.I) for s in precedence):
        fail("active normalized price precedence still references AIPS")

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
    fallback_media = 0
    state_counts: Counter[str] = Counter()
    sellable_count = 0
    priced_count = 0

    raw_by_id = {p["id"]: p for p in raw_products}
    for product in products:
        pid = product["id"]
        raw_product = raw_by_id[pid]

        expected_en = f"p/{pid}.html"
        expected_bn = f"bn/p/{pid}.html"
        if product["routes_v3"]["en"] != expected_en:
            fail(f"{pid}: existing EN product route changed")
        if product["routes_v3"]["bn"] != expected_bn:
            fail(f"{pid}: existing BN product route changed")
        product_routes_en.append(product["routes_v3"]["en"])
        product_routes_bn.append(product["routes_v3"]["bn"])

        archived_proof = product.get("legacy_proof_v1", {})
        for key in PROOF_KEYS:
            if key in raw_product:
                if key in product:
                    fail(f"{pid}: legacy proof key remained active: {key}")
                if archived_proof.get(key) != raw_product.get(key):
                    fail(f"{pid}: legacy proof key not preserved in quarantine: {key}")

        raw_price_source = str(raw_product.get("price_source") or "")
        if re.search(r"(^|[-_])aips($|[-_])", raw_price_source, re.I):
            if "price_source" in product:
                fail(f"{pid}: AIPS price source remained active")
            if product.get("legacy_price_source_v1") != raw_product.get("price_source"):
                fail(f"{pid}: AIPS price source not preserved in legacy quarantine")

        raw_plans = raw_product.get("plans", [])
        expected_active_raw = [p for p in raw_plans if not looks_openai_shared(raw_product, p)]
        expected_quarantined_raw = [p for p in raw_plans if looks_openai_shared(raw_product, p)]
        active_plans = product.get("plans", [])
        quarantined_plans = product.get("quarantined_plans_v3", [])
        if len(active_plans) != len(expected_active_raw):
            fail(f"{pid}: active plan count mismatch")
        if len(quarantined_plans) != len(expected_quarantined_raw):
            fail(f"{pid}: quarantined plan count mismatch")

        for archived, raw_plan in zip(quarantined_plans, expected_quarantined_raw):
            if plan_signature(archived) != plan_signature(raw_plan):
                fail(f"{pid}: quarantined plan identity changed")
            if archived.get("quarantine_reason_v3") != "provider_policy_openai_shared_account":
                fail(f"{pid}: quarantined OpenAI/shared plan missing reason")

        for idx, (plan, raw_plan) in enumerate(zip(active_plans, expected_active_raw), 1):
            if looks_openai_shared(raw_product, raw_plan):
                fail(f"{pid}: prohibited OpenAI/shared plan remained active")

            legacy_price = plan.get("legacy_price_v1", {})
            for key in PRICE_KEYS:
                if key in raw_plan:
                    if key in plan:
                        fail(f"{pid} plan {idx}: legacy price field remained active: {key}")
                    if legacy_price.get(key) != raw_plan.get(key):
                        fail(f"{pid} plan {idx}: legacy price field not preserved: {key}")

            for key, value in raw_plan.items():
                if key in PRICE_KEYS:
                    continue
                if key not in plan:
                    fail(f"{pid} plan {idx}: non-price legacy key disappeared: {key}")
                elif plan[key] != value:
                    fail(f"{pid} plan {idx}: non-price legacy value changed: {key}")

            plan_id = str(plan.get("plan_id_v3") or "")
            if not plan_id:
                fail(f"{pid} plan {idx}: missing plan_id_v3")
            plan_ids.append(plan_id)
            if plan.get("product_id_v3") != pid:
                fail(f"{pid} plan {idx}: wrong product_id_v3")
            plan_routes_en.append(plan["routes_v3"]["en"])
            plan_routes_bn.append(plan["routes_v3"]["bn"])

            state = plan.get("commercial_state_v3")
            if state not in {"allowed", "direct_provider_only", "blocked", "unknown"}:
                fail(f"{pid} / {plan_id}: invalid commercial state {state!r}")
            state_counts[str(state)] += 1
            if plan.get("price_v3") is not None:
                priced_count += 1
            if plan.get("sellable_v3") is True:
                sellable_count += 1
                if state != "allowed" or not plan.get("price_v3"):
                    fail(f"{pid} / {plan_id}: sellable without allowed state + approved price")

            identity = f"{pid} {product.get('name','')}".lower()
            if ("chatgpt" in identity or "openai" in identity) and state not in {"direct_provider_only", "blocked"}:
                fail(f"{pid} / {plan_id}: retained OpenAI plan is not direct-provider-only/blocked")

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
                elif not (ROOT / src.lstrip("/")).is_file():
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

    existing_html = {
        p.relative_to(ROOT).as_posix()
        for p in ROOT.glob("**/*.html")
        if "_site" not in p.parts and "_preview_v3" not in p.parts and ".git" not in p.parts
    }
    collisions = sorted((set(plan_routes_en) | set(plan_routes_bn)) & existing_html)
    if collisions:
        fail(f"new plan routes collide with existing HTML: {collisions[:10]}")

    meta = normalized.get("meta", {}).get("v3_model", {})
    if meta.get("public_price_authorized") is not True and priced_count:
        fail(f"{priced_count} plan(s) have price_v3 while public pricing is unauthorized")
    if meta.get("commerce_launch_ready") is not True and sellable_count:
        fail(f"{sellable_count} plan(s) are sellable while commerce launch is not ready")

    if errors:
        print(f"V3 CATALOG MODEL INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    summary = {
        "products": len(products),
        "legacy_plans": raw_plan_count,
        "active_plans": active_plan_count,
        "quarantined_plans": quarantined_count,
        "unique_plan_ids_v3": len(set(plan_ids)),
        "unique_plan_routes_en": len(set(plan_routes_en)),
        "unique_plan_routes_bn": len(set(plan_routes_bn)),
        "normalized_media_items": len(media_ids),
        "fallback_media_items": fallback_media,
        "commercial_state_counts": dict(sorted(state_counts.items())),
        "approved_price_records_in_effect": priced_count,
        "sellable_plans": sellable_count,
        "legacy_source_sha256": before,
        "legacy_product_routes_preserved": True,
        "legacy_input_mutated": False,
        "unsafe_legacy_fields_quarantined": True,
    }
    print("V3 active catalog + quarantine model valid")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
