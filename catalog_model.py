#!/usr/bin/env python3
"""Compatibility-first normalized catalog model for SAVEONSUB v3.

This module reads the existing catalog.json and enriches a deep copy with
stable-enough v3 identifiers, routes, media and fail-closed commerce metadata.
It deliberately does not rewrite catalog.json and is safe to run in CI.

Important migration rule:
- existing product IDs and product URLs are permanent invariants;
- derived plan IDs are provisional migration identities until persisted in the
  reviewed v3 plan registry/source;
- a missing explicit commercial eligibility state normalizes to UNKNOWN, never
  to sellable.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
from collections import Counter, defaultdict
from typing import Any

from media_registry import normalize_media
from routes_v3 import plan_path, product_path, slugify

ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_CATALOG = ROOT / "catalog.json"

KNOWN_PLAN_TYPES = {"personal", "shared", "official", "bundle"}
COMMERCIAL_STATES = {"allowed", "direct_provider_only", "blocked", "unknown"}


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
    return slugify(plan.get("label") or _plan_kind(plan), _plan_kind(plan))


def _base_plan_id(product_id: str, plan: dict[str, Any]) -> str:
    return f"{product_id}--{_plan_kind(plan)}--{_duration_key(plan)}"


def _derived_plan_ids(product: dict[str, Any]) -> list[str]:
    """Derive deterministic migration IDs for the legacy plan array.

    Most plans resolve to <product>--<kind>--<duration>. If multiple legacy
    plans share that semantic key, a stable label qualifier is added; only an
    exact duplicate label requires a final ordinal. Once v3 IDs are persisted,
    generators will prefer the persisted ID and this derivation becomes a
    compatibility fallback only.
    """
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
    candidates = [slugify(p.get("slug") or p.get("label") or _plan_kind(p), "plan") for p in plans]
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


def _commercial_state(product: dict[str, Any], plan: dict[str, Any] | None = None) -> str:
    values = []
    if plan:
        values += [plan.get("commercial_state"), plan.get("eligibility")]
    values += [product.get("commercial_state"), product.get("eligibility")]
    for value in values:
        normalized = str(value or "").strip().lower()
        if normalized in COMMERCIAL_STATES:
            return normalized
    return "unknown"


def normalize_catalog(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copy normalized model while preserving all legacy fields."""
    normalized = copy.deepcopy(raw)
    normalized.setdefault("meta", {})
    normalized["meta"]["v3_model"] = {
        "version": 1,
        "source_sha256": source_digest(raw),
        "compatibility_mode": True,
        "commercial_default": "unknown",
    }

    for product in normalized.get("products", []):
        pid = str(product.get("id") or "").strip()
        if not pid:
            raise ValueError("product missing id")
        product["product_id"] = pid
        product["routes_v3"] = {
            "en": product_path(pid, "en"),
            "bn": product_path(pid, "bn"),
        }
        product["commercial_state_v3"] = _commercial_state(product)
        product["media_v3"] = normalize_media(product)

        plan_ids = _derived_plan_ids(product)
        plan_slugs = _plan_slugs(product)
        for index, plan in enumerate(product.get("plans") or []):
            plan_id = plan_ids[index]
            plan_slug = plan_slugs[index]
            plan["plan_id_v3"] = plan_id
            plan["plan_slug_v3"] = plan_slug
            plan["product_id_v3"] = pid
            plan["commercial_state_v3"] = _commercial_state(product, plan)
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
