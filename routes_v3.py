#!/usr/bin/env python3
"""Stable route helpers for SAVEONSUB Evolution Architecture v3.

This module is additive. Existing product/category URLs are invariants and must
not be changed by v3 work. Plan routes are new and remain non-public until their
generator is explicitly enabled. Mutable commercial values such as prices must
never become part of permanent route identity.
"""
from __future__ import annotations

import re
import unicodedata

DOMAIN = "https://saveonsub.com"

PRICE_TOKEN_RE = re.compile(
    r"(?i)(?:৳|\b(?:bdt|tk)\.?\s*)\s*[0-9][0-9,]*(?:\.[0-9]+)?"
)


def strip_price_tokens(value: object) -> str:
    """Remove explicit BDT/Tk price tokens before making stable IDs/slugs."""
    text = str(value or "")
    text = PRICE_TOKEN_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip(" -–—|·,()[]{}")
    return text


def slugify(value: object, fallback: str = "item") -> str:
    """Return a conservative ASCII URL slug."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback


def plan_label_slug(value: object, fallback: str = "plan") -> str:
    """Make a plan slug after removing mutable price tokens."""
    return slugify(strip_price_tokens(value), fallback)


def product_path(product_id: str, language: str = "en") -> str:
    if language == "bn":
        return f"bn/p/{product_id}.html"
    if language != "en":
        raise ValueError(f"unsupported language: {language}")
    return f"p/{product_id}.html"


def product_url(product_id: str, language: str = "en") -> str:
    return f"{DOMAIN}/{product_path(product_id, language)}"


def plan_path(product_id: str, plan_slug: str, language: str = "en") -> str:
    plan_slug = plan_label_slug(plan_slug, "plan")
    if language == "bn":
        return f"bn/p/{product_id}/{plan_slug}.html"
    if language != "en":
        raise ValueError(f"unsupported language: {language}")
    return f"p/{product_id}/{plan_slug}.html"


def plan_url(product_id: str, plan_slug: str, language: str = "en") -> str:
    return f"{DOMAIN}/{plan_path(product_id, plan_slug, language)}"
