#!/usr/bin/env python3
"""Validate protected authority boundaries for SAVEONSUB v3."""
from __future__ import annotations

import json
import pathlib
import re

import site_config
from authority_model import load_authority
from catalog_model import load_catalog

ROOT = pathlib.Path(__file__).resolve().parent
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def main() -> int:
    authority = load_authority()
    contact = authority["contact"]
    payment = authority["payment"]
    pricing = authority["pricing"]
    legal = authority["legal"]
    provider = authority["provider"]
    launch = authority["launch"]

    if contact.get("whatsapp", {}).get("status") != "PENDING_OWNER_INPUT":
        fail("WhatsApp status is not fail-closed pending owner input")
    if contact.get("whatsapp", {}).get("value") is not None:
        fail("an unverified WhatsApp value is present")
    if site_config.WHATSAPP_NUMBER is not None or site_config.WHATSAPP_URL is not None:
        fail("site_config exposes an unverified WhatsApp destination")

    if payment.get("destinations_status") != "PENDING_OWNER_INPUT":
        fail("payment destinations are not pending owner input")
    if payment.get("destinations"):
        fail("payment destination values exist before verification")
    if site_config.PAYMENT_DESTINATIONS:
        fail("site_config exposes payment destinations")

    if pricing.get("public_price_authorized") is not False:
        fail("public price authority unexpectedly enabled")
    if pricing.get("active_prices"):
        fail("active price registry is not empty while authority is unverified")
    if pricing.get("legacy_catalog_prices_operational") is not False:
        fail("legacy catalog prices are treated as operational")

    if legal.get("legal_operator", {}).get("name") is not None:
        fail("legal operator populated without primary evidence")
    if site_config.LEGAL_OPERATOR_PUBLIC is not None:
        fail("site_config exposes an unverified legal operator")

    if site_config.COMMERCE_UI_ENABLED:
        fail("commerce UI enabled before protected authority resolution")
    if launch.get("commerce_authorized") is True:
        fail("launch control has commerce authorized before protected authority resolution")

    for pid in ("chatgpt-plus", "chatgpt-pro", "chatgpt-go", "chatgpt-business"):
        record = provider.get("records", {}).get(pid)
        if not record:
            fail(f"missing OpenAI provider record for {pid}")
            continue
        if record.get("state") != "direct_provider_only":
            fail(f"{pid} is not direct_provider_only")
        if record.get("shared_plan_state") != "blocked":
            fail(f"{pid} shared plan state is not blocked")

    normalized = load_catalog()
    if any(plan.get("sellable_v3") for p in normalized.get("products", []) for plan in p.get("plans", [])):
        fail("a plan normalizes to sellable before authority resolution")
    if any(plan.get("price_v3") for p in normalized.get("products", []) for plan in p.get("plans", [])):
        fail("a plan has an effective v3 public price before authority resolution")

    # High-risk runtime/template surfaces must not carry the stale number.
    stale = re.compile(r"(?:\+?880[ -]?1305[ -]?869242|8801305869242|01305869242)")
    for rel in ("site_config.py", "templates.py", "assets/app.js", "commerce-worker/src/index.js"):
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        if stale.search(text):
            fail(f"stale SAVEONSUB contact appears in authority/runtime source: {rel}")

    if errors:
        print(f"AUTHORITY BOUNDARY INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    state_counts = {}
    for product in normalized.get("products", []):
        for plan in product.get("plans", []):
            state = plan.get("commercial_state_v3", "unknown")
            state_counts[state] = state_counts.get(state, 0) + 1
    print(json.dumps({
        "authority_boundary_valid": True,
        "commerce_ui_enabled": site_config.COMMERCE_UI_ENABLED,
        "public_price_authorized": pricing.get("public_price_authorized"),
        "payment_destinations_status": payment.get("destinations_status"),
        "whatsapp_status": contact.get("whatsapp", {}).get("status"),
        "legal_operator_status": legal.get("legal_operator", {}).get("status"),
        "v3_commercial_state_counts": dict(sorted(state_counts.items())),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
