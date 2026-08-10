#!/usr/bin/env python3
"""Normalize product media for SAVEONSUB Evolution Architecture v3.

Current products do not yet have a first-class media model. This module accepts
future catalog media entries while preserving today's generated social card as a
safe local fallback. It performs no network calls and uploads nothing.
"""
from __future__ import annotations

import copy
from typing import Any

ALLOWED_TYPES = {"image", "video", "document"}
ALLOWED_SOURCES = {"local", "cloudflare_images", "cloudflare_stream", "r2"}
ALLOWED_ROLES = {
    "hero",
    "gallery",
    "screenshot",
    "feature",
    "comparison",
    "plan",
    "thumbnail",
    "poster",
    "social",
    "download",
}


def _text(value: Any, fallback: str = "") -> str:
    return str(value).strip() if value not in (None, "") else fallback


def _normalize_local_item(product: dict[str, Any], item: dict[str, Any], index: int) -> dict[str, Any]:
    pid = product["id"]
    media_type = _text(item.get("type"), "image").lower()
    source = _text(item.get("source"), "local").lower()
    role = _text(item.get("role"), "gallery").lower()
    if media_type not in ALLOWED_TYPES:
        raise ValueError(f"{pid}: unsupported media type {media_type!r}")
    if source not in ALLOWED_SOURCES:
        raise ValueError(f"{pid}: unsupported media source {source!r}")
    if role not in ALLOWED_ROLES:
        raise ValueError(f"{pid}: unsupported media role {role!r}")

    src = _text(item.get("src") or item.get("url") or item.get("id"))
    if not src:
        raise ValueError(f"{pid}: media item {index} has no src/url/id")

    media_id = _text(item.get("media_id") or item.get("id"), f"{pid}-media-{index:02d}")
    alt = item.get("alt")
    if isinstance(alt, dict):
        alt_en = _text(alt.get("en"), product.get("name", pid))
        alt_bn = _text(alt.get("bn"), alt_en)
    else:
        alt_en = _text(alt, product.get("name", pid))
        alt_bn = _text(item.get("alt_bn"), alt_en)

    caption = item.get("caption")
    if isinstance(caption, dict):
        caption_en = _text(caption.get("en"))
        caption_bn = _text(caption.get("bn"), caption_en)
    else:
        caption_en = _text(caption)
        caption_bn = _text(item.get("caption_bn"), caption_en)

    return {
        "media_id": media_id,
        "product_id": pid,
        "plan_id": item.get("plan_id"),
        "type": media_type,
        "source": source,
        "role": role,
        "src": src,
        "alt": {"en": alt_en, "bn": alt_bn},
        "caption": {"en": caption_en, "bn": caption_bn},
        "width": item.get("width"),
        "height": item.get("height"),
        "sort_order": int(item.get("sort_order", index)),
        "visibility": _text(item.get("visibility"), "public"),
        "fallback": bool(item.get("fallback", False)),
        "legacy": copy.deepcopy(item),
    }


def normalize_media(product: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized media entries without mutating the product.

    Future accepted catalog shapes:
      * media: [ {...}, ... ]
      * gallery: [ {...}, ... ]
      * videos: [ {...}, ... ]

    If none exist, return the current product social card as a fallback-only
    image. The fallback is not treated as evidence that a real ecommerce gallery
    exists.
    """
    entries: list[dict[str, Any]] = []
    for key, forced_type in (("media", None), ("gallery", "image"), ("videos", "video")):
        value = product.get(key)
        if not isinstance(value, list):
            continue
        for raw in value:
            if isinstance(raw, str):
                raw = {"src": raw, "type": forced_type or "image", "role": "gallery"}
            elif isinstance(raw, dict):
                raw = copy.deepcopy(raw)
                if forced_type and not raw.get("type"):
                    raw["type"] = forced_type
            else:
                raise ValueError(f"{product.get('id')}: invalid {key} media item: {raw!r}")
            entries.append(_normalize_local_item(product, raw, len(entries) + 1))

    if entries:
        return sorted(entries, key=lambda x: (x["sort_order"], x["media_id"]))

    pid = product["id"]
    name = _text(product.get("name"), pid)
    return [{
        "media_id": f"{pid}-social-fallback",
        "product_id": pid,
        "plan_id": None,
        "type": "image",
        "source": "local",
        "role": "social",
        "src": f"/assets/social/{pid}.png",
        "alt": {"en": f"{name} — SAVEONSUB", "bn": f"{name} — SAVEONSUB"},
        "caption": {"en": "", "bn": ""},
        "width": 1200,
        "height": 630,
        "sort_order": 0,
        "visibility": "public",
        "fallback": True,
        "legacy": None,
    }]
