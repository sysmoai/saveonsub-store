#!/usr/bin/env python3
"""Compatibility-first normalized catalog model for SAVEONSUB v3.

This module reads the historical catalog.json and builds the active v3 model.
Historical fields are preserved only as explicitly quarantined audit data when
they are not valid public/commercial authority.

Important migration rules:
- existing product IDs and product URLs are permanent invariants;
- mutable prices never become part of identity or routes;
- raw legacy price/status/risk/proof fields never authorize commerce;
- provider, pricing, payment and launch authority come from protected registries;
- OpenAI/shared-account offerings are removed from the active v3 plan model;
- AIPS never supplies active SAVEONSUB price authority;
- unknown is never sellable.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
from collections import Counter, defaultdict
from typing import Any

from authority_model import (
    approved_price,
    commerce_launch_ready,
    load_authority,
    product_bundle_state,
    provider_plan_state,
    provider_product_state,
)
from media_registry import normalize_media
from routes_v3 import plan_label_slug, plan_path, product_path, slugify

ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_CATALOG = ROOT / "catalog.json"

KNOWN_PLAN_TYPES = {"personal", "shared", "official", "bundle"}
LEGACY_PROOF_KEYS = ("orders", "bestseller_rank", "market")
LEGACY_PLAN_PRICE_KEYS = ("bdt", "price_bdt", "price", "usd")
RISKY_FAQ_RE = re.compile(
    r"shared|seat|warranty|order|buy|price|৳|discount|resell|bkash|nagad|rocket|seller|customer|sold|#\s*1",
    re.I,
)


def source_digest(raw: dict[str, Any]) -> str:
    payload = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _plan_kind(plan: dict[str, Any]) -> str:
    explicit = str(plan.get("type") or "").strip().lower()
    if explicit in KNOWN_PLAN_TYPES:
        return explicit
    tos = str(plan.get("tos") or "").strip().lower()
    if tos.startswith("shared"):
        return "shared"
    if tos == "personal":
        return "personal"
    if tos == "official":
        return "official"
    if tos == "bundle":
        return "bundle"
    return "plan"


def _duration_key(plan: dict[str, Any]) -> str:
    return slugify(plan.get("duration") or "term", "term")


def _label_key(plan: dict[str, Any]) -> str:
    return plan_label_slug(plan.get("label") or _plan_kind(plan), _plan_kind(plan))


def _base_plan_id(product_id: str, plan: dict[str, Any]) -> str:
    return f"{product_id}--{_plan_kind(plan)}--{_duration_key(plan)}"


def _derived_plan_ids(product: dict[str, Any]) -> list[str]:
    plans = product.get("plans") or []
    base_counts = Counter(_base_plan_id(product["id"], p) for p in plans)
    label_group_counts: Counter[str] = Counter()
    ids: list[str] = []

    for plan in plans:
        persisted = str(plan.get("plan_id") or plan.get("id") or "").strip()
        if persisted:
            ids.append(persisted)
            continue

        base = _base_plan_id(product["id"], plan)
        if base_counts[base] == 1:
            ids.append(base)
            continue

        qualified = f"{base}--{_label_key(plan)}"
        label_group_counts[qualified] += 1
        if label_group_counts[qualified] == 1:
            ids.append(qualified)
        else:
            ids.append(f"{qualified}--{label_group_counts[qualified]:02d}")
    return ids


def _plan_slugs(product: dict[str, Any]) -> list[str]:
    plans = product.get("plans") or []
    candidates = [plan_label_slug(p.get("slug") or p.get("label") or _plan_kind(p), "plan") for p in plans]
    counts = Counter(candidates)
    used: defaultdict[str, int] = defaultdict(int)
    out: list[str] = []
    for candidate in candidates:
        if counts[candidate] == 1:
            out.append(candidate)
            continue
        used[candidate] += 1
        out.append(f"{candidate}-{used[candidate]}")
    return out


def _openai_surface(product: dict[str, Any]) -> bool:
    identity = f"{product.get('id','')} {product.get('name','')}".lower()
    return "chatgpt" in identity or "openai" in identity


def _looks_shared(plan: dict[str, Any]) -> bool:
    return (
        str(plan.get("type") or "").strip().lower() == "shared"
        or str(plan.get("tos") or "").strip().lower().startswith("shared")
        or "shared" in str(plan.get("label") or "").lower()
    )


def _quarantine_plan_reason(product: dict[str, Any], plan: dict[str, Any]) -> str | None:
    if _openai_surface(product) and _looks_shared(plan):
        return "provider_policy_openai_shared_account"
    return None


def _quarantine_product_fields(product: dict[str, Any]) -> None:
    proof = {key: copy.deepcopy(product[key]) for key in LEGACY_PROOF_KEYS if key in product}
    if proof:
        product["legacy_proof_v1"] = proof
        for key in proof:
            product.pop(key, None)

    price_source = str(product.get("price_source") or "")
    if re.search(r"(^|[-_])aips($|[-_])", price_source, re.I):
        product["legacy_price_source_v1"] = product.pop("price_source")

    faq = product.get("faq")
    if isinstance(faq, list):
        safe_faq = []
        removed_faq = []
        for entry in faq:
            text = f"{entry.get('q','')} {entry.get('a','')}" if isinstance(entry, dict) else str(entry)
            if RISKY_FAQ_RE.search(text):
                removed_faq.append(copy.deepcopy(entry))
            else:
                safe_faq.append(entry)
        if removed_faq:
            product["legacy_risky_faq_v1"] = removed_faq
            product["faq"] = safe_faq


def _quarantine_plan_prices(plan: dict[str, Any]) -> None:
    legacy_price = {key: copy.deepcopy(plan[key]) for key in LEGACY_PLAN_PRICE_KEYS if key in plan}
    if legacy_price:
        plan["legacy_price_v1"] = legacy_price
        for key in legacy_price:
            plan.pop(key, None)


def normalize_catalog(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a non-mutating active v3 model with unsafe legacy data quarantined."""
    normalized = copy.deepcopy(raw)
    authority = load_authority()
    commerce_ready = commerce_launch_ready(authority)
    normalized.setdefault("meta", {})

    precedence = list(normalized["meta"].get("price_precedence", []))
    safe_precedence = [s for s in precedence if not re.search(r"(^|[-_])aips($|[-_])", str(s), re.I)]
    if safe_precedence != precedence:
        normalized["meta"]["legacy_price_precedence_v1"] = precedence
        normalized["meta"]["price_precedence"] = safe_precedence

    normalized["meta"]["v3_model"] = {
        "version": 3,
        "source_sha256": source_digest(raw),
        "compatibility_mode": True,
        "commercial_default": "unknown",
        "commerce_launch_ready": commerce_ready,
        "public_price_authorized": authority["pricing"].get("public_price_authorized") is True,
        "payment_destinations_verified": authority["payment"].get("destinations_status") == "VERIFIED",
        "unsafe_legacy_fields_quarantined": True,
    }

    products = normalized.get("products", [])
    products_by_id = {str(p.get("id")): p for p in products if p.get("id")}

    for product in products:
        pid = str(product.get("id") or "").strip()
        if not pid:
            raise ValueError("product missing id")

        _quarantine_product_fields(product)

        active_plans = []
        quarantined_plans = []
        for original_index, plan in enumerate(product.get("plans") or [], 1):
            reason = _quarantine_plan_reason(product, plan)
            if reason:
                archived = copy.deepcopy(plan)
                archived["quarantine_reason_v3"] = reason
                archived["legacy_index_v1"] = original_index
                quarantined_plans.append(archived)
                continue
            active = plan
            _quarantine_plan_prices(active)
            active_plans.append(active)
        product["plans"] = active_plans
        if quarantined_plans:
            product["quarantined_plans_v3"] = quarantined_plans

        product["product_id"] = pid
        product["routes_v3"] = {
            "en": product_path(pid, "en"),
            "bn": product_path(pid, "bn"),
        }
        if isinstance(product.get("contains"), list) and product.get("contains"):
            product_state = product_bundle_state(product, products_by_id, authority)
        else:
            product_state = provider_product_state(product, authority)
        product["commercial_state_v3"] = product_state
        product["media_v3"] = normalize_media(product)

        plan_ids = _derived_plan_ids(product)
        plan_slugs = _plan_slugs(product)
        for index, plan in enumerate(product.get("plans") or []):
            plan_id = plan_ids[index]
            plan_slug = plan_slugs[index]
            if isinstance(product.get("contains"), list) and product.get("contains"):
                plan_state = product_state
            else:
                plan_state = provider_plan_state(product, plan, authority)
            price_record = approved_price(plan_id, authority)

            plan["plan_id_v3"] = plan_id
            plan["plan_slug_v3"] = plan_slug
            plan["product_id_v3"] = pid
            plan["commercial_state_v3"] = plan_state
            plan["price_v3"] = copy.deepcopy(price_record)
            plan["sellable_v3"] = bool(commerce_ready and plan_state == "allowed" and price_record)
            plan["routes_v3"] = {
                "en": plan_path(pid, plan_slug, "en"),
                "bn": plan_path(pid, plan_slug, "bn"),
            }
    return normalized


def load_raw_catalog(path: pathlib.Path | str = DEFAULT_CATALOG) -> dict[str, Any]:
    path = pathlib.Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(path: pathlib.Path | str = DEFAULT_CATALOG) -> dict[str, Any]:
    return normalize_catalog(load_raw_catalog(path))


def iter_plans(catalog: dict[str, Any]):
    for product in catalog.get("products", []):
        for plan in product.get("plans", []):
            yield product, plan
