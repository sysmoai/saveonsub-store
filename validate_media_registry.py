#!/usr/bin/env python3
"""Validate the internal SAVEONSUB v3 media registry and publication boundary."""
from __future__ import annotations

import pathlib

from catalog_model import load_catalog
from media_registry import (
    ALLOWED_ROLES,
    ALLOWED_SOURCES,
    ALLOWED_STATES,
    ALLOWED_TYPES,
    ALLOWED_VISIBILITY,
    load_media_registry,
)

ROOT = pathlib.Path(__file__).resolve().parent
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def text(value) -> str:
    return str(value or "").strip()


def main() -> int:
    registry = load_media_registry()
    catalog = load_catalog()
    products = {p["id"]: p for p in catalog.get("products", [])}
    plan_owner = {}
    for product in products.values():
        for plan in product.get("plans", []):
            plan_owner[plan["plan_id_v3"]] = product["id"]

    seen: set[str] = set()
    approved_public = 0
    drafts = 0
    for index, entry in enumerate(registry.get("entries", []), 1):
        if not isinstance(entry, dict):
            fail(f"entry {index}: must be an object")
            continue
        lowered_keys = {str(k).lower() for k in entry}
        if lowered_keys & {"token", "api_token", "api_key", "secret", "authorization", "password"}:
            fail(f"entry {index}: secret-like key is forbidden")

        media_id = text(entry.get("media_id"))
        product_id = text(entry.get("product_id"))
        plan_id = text(entry.get("plan_id"))
        kind = text(entry.get("kind") or entry.get("type")).lower()
        role = text(entry.get("role")).lower()
        provider = text(entry.get("provider") or entry.get("source")).lower()
        state = text(entry.get("state") or "draft").lower()
        visibility = text(entry.get("visibility") or "private").lower()
        source_id = text(entry.get("source_id") or entry.get("src") or entry.get("url"))

        if not media_id:
            fail(f"entry {index}: media_id required")
        elif media_id in seen:
            fail(f"entry {index}: duplicate media_id {media_id}")
        else:
            seen.add(media_id)
        if product_id not in products:
            fail(f"{media_id or index}: unknown product_id {product_id!r}")
        if plan_id:
            if plan_id not in plan_owner:
                fail(f"{media_id or index}: unknown plan_id {plan_id!r}")
            elif plan_owner[plan_id] != product_id:
                fail(f"{media_id or index}: plan belongs to {plan_owner[plan_id]}, not {product_id}")
        if kind not in ALLOWED_TYPES:
            fail(f"{media_id or index}: unsupported kind {kind!r}")
        if role not in ALLOWED_ROLES:
            fail(f"{media_id or index}: unsupported role {role!r}")
        if provider not in ALLOWED_SOURCES:
            fail(f"{media_id or index}: unsupported provider {provider!r}")
        if state not in ALLOWED_STATES:
            fail(f"{media_id or index}: unsupported state {state!r}")
        if visibility not in ALLOWED_VISIBILITY:
            fail(f"{media_id or index}: unsupported visibility {visibility!r}")
        if not source_id:
            fail(f"{media_id or index}: source_id/src required")

        if state == "draft":
            drafts += 1
        if state == "approved" and visibility == "public":
            approved_public += 1
            alt = entry.get("alt") if isinstance(entry.get("alt"), dict) else {}
            if not text(alt.get("en") or entry.get("alt")):
                fail(f"{media_id}: approved public media requires English alt text")
            if not text(alt.get("bn") or entry.get("alt_bn")):
                fail(f"{media_id}: approved public media requires Bangla alt text")
            if not text(entry.get("authority_ref")):
                fail(f"{media_id}: approved public media requires authority_ref")

            if kind in {"image", "graphic"}:
                width = entry.get("width")
                height = entry.get("height")
                if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
                    fail(f"{media_id}: approved public image/graphic requires positive width/height")
                delivery = text(entry.get("delivery_url") or entry.get("src") or entry.get("url"))
                if not delivery:
                    fail(f"{media_id}: approved public image/graphic requires delivery URL")
                if provider == "local" and delivery.startswith("/assets/"):
                    local = ROOT / delivery.lstrip("/")
                    if not local.is_file():
                        fail(f"{media_id}: local media file missing: {delivery}")
            if kind == "video" and provider not in {"local", "cloudflare_stream", "r2"}:
                fail(f"{media_id}: video provider {provider!r} is not supported")

    normalized_ids = []
    for product in products.values():
        normalized_ids.extend(item["media_id"] for item in product.get("media_v3", []))
    if len(normalized_ids) != len(set(normalized_ids)):
        fail("normalized public media contains duplicate media IDs")

    if errors:
        print(f"MEDIA REGISTRY INVALID: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL {message}")
        return 1

    print("media registry validation passed")
    print(f"registry entries: {len(registry.get('entries', []))}")
    print(f"approved public entries: {approved_public}")
    print(f"draft entries: {drafts}")
    print(f"normalized public media references: {len(normalized_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
