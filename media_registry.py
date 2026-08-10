#!/usr/bin/env python3
"""Normalize product media for SAVEONSUB Evolution Architecture v3.

The reviewed internal registry is additive: current catalog media remains readable
for compatibility, while approved registry entries can become the long-term
source of gallery/video truth. Draft/private registry entries never reach public
normalized media. The module performs no network calls and uploads nothing.
"""
from __future__ import annotations

import copy
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_REGISTRY = ROOT / "data" / "media" / "media_registry.json"

ALLOWED_TYPES = {"image", "video", "document", "graphic"}
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
    "demo",
    "howto",
}
ALLOWED_STATES = {"draft", "reviewed", "approved", "retired"}
ALLOWED_VISIBILITY = {"public", "private"}


def _text(value: Any, fallback: str = "") -> str:
    return str(value).strip() if value not in (None, "") else fallback


def load_media_registry(path: pathlib.Path | str = DEFAULT_REGISTRY) -> dict[str, Any]:
    path = pathlib.Path(path)
    if not path.is_file():
        return {"schema": "saveonsub-media-registry-v1", "version": 1, "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "saveonsub-media-registry-v1":
        raise ValueError(f"unsupported media registry schema: {data.get('schema')!r}")
    if not isinstance(data.get("entries"), list):
        raise ValueError("media registry entries must be a list")
    return data


def _normalize_item(product: dict[str, Any], item: dict[str, Any], index: int) -> dict[str, Any]:
    pid = product["id"]
    media_type = _text(item.get("type") or item.get("kind"), "image").lower()
    source = _text(item.get("source") or item.get("provider"), "local").lower()
    role = _text(item.get("role"), "gallery").lower()
    state = _text(item.get("state"), "approved").lower()
    visibility = _text(item.get("visibility"), "public").lower()
    if media_type not in ALLOWED_TYPES:
        raise ValueError(f"{pid}: unsupported media type {media_type!r}")
    if source not in ALLOWED_SOURCES:
        raise ValueError(f"{pid}: unsupported media source {source!r}")
    if role not in ALLOWED_ROLES:
        raise ValueError(f"{pid}: unsupported media role {role!r}")
    if state not in ALLOWED_STATES:
        raise ValueError(f"{pid}: unsupported media state {state!r}")
    if visibility not in ALLOWED_VISIBILITY:
        raise ValueError(f"{pid}: unsupported media visibility {visibility!r}")

    src = _text(item.get("delivery_url") or item.get("src") or item.get("url"))
    source_id = _text(item.get("source_id") or item.get("id") or src)
    if source == "local" and not src:
        src = source_id
    if not source_id:
        raise ValueError(f"{pid}: media item {index} has no source_id/src/url")
    if state == "approved" and visibility == "public" and media_type in {"image", "graphic"} and not src:
        raise ValueError(f"{pid}: approved public image/graphic {source_id!r} has no delivery URL")

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
        "source_id": source_id,
        "src": src,
        "alt": {"en": alt_en, "bn": alt_bn},
        "caption": {"en": caption_en, "bn": caption_bn},
        "width": item.get("width"),
        "height": item.get("height"),
        "duration_seconds": item.get("duration_seconds"),
        "poster_media_id": item.get("poster_media_id"),
        "sort_order": int(item.get("sort_order", index)),
        "visibility": visibility,
        "state": state,
        "fallback": bool(item.get("fallback", False)),
        "authority_ref": item.get("authority_ref"),
        "legacy": copy.deepcopy(item),
    }


def _registry_items(product: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    pid = product["id"]
    out: list[dict[str, Any]] = []
    for raw in registry.get("entries", []):
        if not isinstance(raw, dict) or _text(raw.get("product_id")) != pid:
            continue
        item = _normalize_item(product, copy.deepcopy(raw), len(out) + 1)
        if item["state"] == "approved" and item["visibility"] == "public":
            out.append(item)
    return out


def normalize_media(product: dict[str, Any], registry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return approved public normalized media without mutating the product.

    Reviewed registry entries are read first. Legacy catalog shapes remain
    accepted during migration:
      * media: [ {...}, ... ]
      * gallery: [ {...}, ... ]
      * videos: [ {...}, ... ]

    If no approved public media exists, return the current product social card as
    a fallback-only image. Draft/private registry entries are never emitted.
    """
    registry = registry if registry is not None else load_media_registry()
    entries: list[dict[str, Any]] = _registry_items(product, registry)

    for key, forced_type in (("media", None), ("gallery", "image"), ("videos", "video")):
        value = product.get(key)
        if not isinstance(value, list):
            continue
        for raw in value:
            if isinstance(raw, str):
                raw = {"src": raw, "type": forced_type or "image", "role": "gallery", "state": "approved"}
            elif isinstance(raw, dict):
                raw = copy.deepcopy(raw)
                if forced_type and not raw.get("type"):
                    raw["type"] = forced_type
                raw.setdefault("state", "approved")
                raw.setdefault("visibility", "public")
            else:
                raise ValueError(f"{product.get('id')}: invalid {key} media item: {raw!r}")
            item = _normalize_item(product, raw, len(entries) + 1)
            if item["state"] == "approved" and item["visibility"] == "public":
                entries.append(item)

    if entries:
        ids = [item["media_id"] for item in entries]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{product['id']}: duplicate media_id in normalized public media")
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
        "source_id": f"/assets/social/{pid}.png",
        "src": f"/assets/social/{pid}.png",
        "alt": {"en": f"{name} — SAVEONSUB", "bn": f"{name} — SAVEONSUB"},
        "caption": {"en": "", "bn": ""},
        "width": 1200,
        "height": 630,
        "duration_seconds": None,
        "poster_media_id": None,
        "sort_order": 0,
        "visibility": "public",
        "state": "approved",
        "fallback": True,
        "authority_ref": None,
        "legacy": None,
    }]
