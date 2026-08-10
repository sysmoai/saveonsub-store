#!/usr/bin/env python3
"""Resolve protected SAVEONSUB authority records for v3 generators/backend.

Legacy catalog fields may describe historical plans, market research or old
pricing, but they do not authorize commerce. This module is the compatibility
firewall between that legacy data and the v3 public/runtime model.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent
CONTROL = ROOT / "docs" / "control"
PROVIDER_FILE = CONTROL / "provider_eligibility.json"
PRICING_FILE = CONTROL / "pricing_authority.json"
PAYMENT_FILE = CONTROL / "payment_authority.json"
CONTACT_FILE = CONTROL / "contact_authority.json"
LEGAL_FILE = CONTROL / "legal_authority.json"
LAUNCH_FILE = CONTROL / "launch_state.json"

VALID_COMMERCIAL_STATES = {"allowed", "direct_provider_only", "blocked", "unknown"}


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_authority() -> dict[str, Any]:
    return {
        "provider": _load(PROVIDER_FILE),
        "pricing": _load(PRICING_FILE),
        "payment": _load(PAYMENT_FILE),
        "contact": _load(CONTACT_FILE),
        "legal": _load(LEGAL_FILE),
        "launch": _load(LAUNCH_FILE),
    }


def provider_product_state(product: dict[str, Any], authority: dict[str, Any] | None = None) -> str:
    authority = authority or load_authority()
    registry = authority["provider"]
    record = registry.get("records", {}).get(str(product.get("id", "")), {})
    state = str(record.get("state") or registry.get("default_state") or "unknown").lower()
    return state if state in VALID_COMMERCIAL_STATES else "unknown"


def provider_plan_state(product: dict[str, Any], plan: dict[str, Any], authority: dict[str, Any] | None = None) -> str:
    authority = authority or load_authority()
    registry = authority["provider"]
    record = registry.get("records", {}).get(str(product.get("id", "")), {})
    product_state = provider_product_state(product, authority)
    plan_type = str(plan.get("type") or "").lower()
    tos = str(plan.get("tos") or "").lower()
    looks_shared = plan_type == "shared" or tos.startswith("shared") or "shared" in str(plan.get("label") or "").lower()

    if looks_shared and record.get("shared_plan_state"):
        state = str(record["shared_plan_state"]).lower()
        return state if state in VALID_COMMERCIAL_STATES else "blocked"
    return product_state


def product_bundle_state(product: dict[str, Any], products_by_id: dict[str, dict[str, Any]], authority: dict[str, Any] | None = None) -> str:
    """Fail-close a bundle when any known component cannot be SAVEONSUB commerce."""
    authority = authority or load_authority()
    contains = product.get("contains")
    if not isinstance(contains, list) or not contains:
        return provider_product_state(product, authority)
    component_states = []
    for product_id in contains:
        component = products_by_id.get(str(product_id))
        if not component:
            component_states.append("unknown")
        else:
            component_states.append(provider_product_state(component, authority))
    if any(state in {"blocked", "direct_provider_only"} for state in component_states):
        return "blocked"
    if any(state == "unknown" for state in component_states):
        return "unknown"
    return "allowed" if component_states and all(state == "allowed" for state in component_states) else "unknown"


def approved_price(plan_id: str, authority: dict[str, Any] | None = None) -> dict[str, Any] | None:
    authority = authority or load_authority()
    pricing = authority["pricing"]
    if pricing.get("public_price_authorized") is not True:
        return None
    record = pricing.get("active_prices", {}).get(plan_id)
    if not isinstance(record, dict):
        return None
    if record.get("status") != "approved":
        return None
    amount = record.get("amount_bdt")
    if not isinstance(amount, int) or amount < 0:
        return None
    if not record.get("authority_ref"):
        return None
    return record


def payment_ready(authority: dict[str, Any] | None = None) -> bool:
    authority = authority or load_authority()
    payment = authority["payment"]
    return payment.get("destinations_status") == "VERIFIED" and bool(payment.get("destinations"))


def commerce_launch_ready(authority: dict[str, Any] | None = None) -> bool:
    authority = authority or load_authority()
    launch = authority["launch"]
    return (
        launch.get("state") in {"L2_LIMITED_COMMERCE", "L3_FULL_APPROVED_COMMERCE"}
        and launch.get("commerce_authorized") is True
        and launch.get("payment_instructions_authorized") is True
        and payment_ready(authority)
    )
