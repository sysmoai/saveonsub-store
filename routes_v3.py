#!/usr/bin/env python3
"""Stable route helpers for SAVEONSUB Evolution Architecture v3.

This module is additive. Existing product/category URLs are invariants and must
not be changed by v3 work. Plan routes are new and remain non-public until their
generator is explicitly enabled.
"""
from __future__ import annotations

import re
import unicodedata

DOMAIN = "https://saveonsub.com"


def slugify(value: object, fallback: str = "item") -> str:
    """Return a conservative ASCII URL slug.

    Product IDs are already canonical and should not be passed through this
    function when constructing existing product URLs.
    """
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback


def product_path(product_id: str, language: str = "en") -> str:
    if language == "bn":
        return f"bn/p/{product_id}.html"
    if language != "en":
        raise ValueError(f"unsupported language: {language}")
    return f"p/{product_id}.html"


def product_url(product_id: str, language: str = "en") -> str:
    return f"{DOMAIN}/{product_path(product_id, language)}"


def plan_path(product_id: str, plan_slug: str, language: str = "en") -> str:
    plan_slug = slugify(plan_slug, "plan")
    if language == "bn":
        return f"bn/p/{product_id}/{plan_slug}.html"
    if language != "en":
        raise ValueError(f"unsupported language: {language}")
    return f"p/{product_id}/{plan_slug}.html"


def plan_url(product_id: str, plan_slug: str, language: str = "en") -> str:
    return f"{DOMAIN}/{plan_path(product_id, plan_slug, language)}"
