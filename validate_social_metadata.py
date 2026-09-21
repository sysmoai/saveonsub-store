#!/usr/bin/env python3
"""Fail-closed validation for SaveOnSub Open Graph and Twitter metadata.

Run after technical_seo_hardening.py so canonical/og:url comparisons reflect
the final clean public URL graph.
"""
from __future__ import annotations

import html
import pathlib
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent / "_site"
IMAGE_URL = "https://saveonsub.com/assets/og-image.png"
IMAGE_ALT = "SaveOnSub — Verified Savings. Real Human Support."

REQUIRED_PROPERTY = {
    "og:site_name": "SaveOnSub",
    "og:title": None,
    "og:description": None,
    "og:type": None,
    "og:url": None,
    "og:locale": None,
    "og:image": IMAGE_URL,
    "og:image:width": "1200",
    "og:image:height": "630",
    "og:image:alt": IMAGE_ALT,
}
REQUIRED_NAME = {
    "twitter:card": "summary_large_image",
    "twitter:title": None,
    "twitter:description": None,
    "twitter:image": IMAGE_URL,
    "twitter:image:alt": IMAGE_ALT,
}


def attrs(tag: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r'''([:\w-]+)\s*=\s*(["'])(.*?)\2''', tag, flags=re.I | re.S):
        out[m.group(1).lower()] = html.unescape(m.group(3).strip())
    return out


def meta_values(text: str, key: str, attr: str) -> list[str]:
    key = key.lower()
    values: list[str] = []
    for tag in re.findall(r"<meta\b[^>]*>", text, flags=re.I | re.S):
        a = attrs(tag)
        if a.get(attr, "").lower() == key:
            values.append(a.get("content", "").strip())
    return values


def canonical(text: str) -> list[str]:
    values: list[str] = []
    for tag in re.findall(r"<link\b[^>]*>", text, flags=re.I | re.S):
        a = attrs(tag)
        if a.get("rel", "").lower() == "canonical":
            values.append(a.get("href", "").strip())
    return values


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"SOCIAL META ERROR — {error}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if not SITE.is_dir():
        fail(["_site missing; run the canonical build pipeline first"])

    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        fail(["no staged HTML pages found"])

    errors: list[str] = []
    for page in pages:
        rel = page.relative_to(SITE).as_posix()
        text = page.read_text(encoding="utf-8", errors="strict")

        if "saveonsub.com/assets/social/" in text:
            errors.append(f"{rel}: historical assets/social URL survived staging")

        can = canonical(text)
        if len(can) != 1 or not can[0]:
            errors.append(f"{rel}: expected exactly one canonical URL, got {can}")

        prop: dict[str, list[str]] = {
            key: meta_values(text, key, "property") for key in REQUIRED_PROPERTY
        }
        named: dict[str, list[str]] = {
            key: meta_values(text, key, "name") for key in REQUIRED_NAME
        }

        for key, expected in REQUIRED_PROPERTY.items():
            values = prop[key]
            if len(values) != 1:
                errors.append(f"{rel}: {key} count={len(values)} expected=1")
                continue
            if expected is not None and values[0] != expected:
                errors.append(f"{rel}: {key}={values[0]!r} expected={expected!r}")

        for key, expected in REQUIRED_NAME.items():
            values = named[key]
            if len(values) != 1:
                errors.append(f"{rel}: {key} count={len(values)} expected=1")
                continue
            if expected is not None and values[0] != expected:
                errors.append(f"{rel}: {key}={values[0]!r} expected={expected!r}")

        if len(can) == 1 and len(prop["og:url"]) == 1 and prop["og:url"][0] != can[0]:
            errors.append(
                f"{rel}: og:url/canonical mismatch "
                f"{prop['og:url'][0]!r} != {can[0]!r}"
            )

        if len(prop["og:title"]) == 1 and len(named["twitter:title"]) == 1:
            if prop["og:title"][0] != named["twitter:title"][0]:
                errors.append(f"{rel}: twitter:title differs from og:title")

        if len(prop["og:description"]) == 1 and len(named["twitter:description"]) == 1:
            if prop["og:description"][0] != named["twitter:description"][0]:
                errors.append(f"{rel}: twitter:description differs from og:description")

        if len(prop["og:title"]) == 1 and not prop["og:title"][0]:
            errors.append(f"{rel}: empty og:title")
        if len(prop["og:description"]) == 1 and not prop["og:description"][0]:
            errors.append(f"{rel}: empty og:description")
        if len(prop["og:type"]) == 1 and not prop["og:type"][0]:
            errors.append(f"{rel}: empty og:type")
        if len(prop["og:locale"]) == 1 and prop["og:locale"][0] not in {"en_BD", "bn_BD"}:
            errors.append(f"{rel}: unsupported og:locale={prop['og:locale'][0]!r}")

    sitemap = SITE / "sitemap.xml"
    if not sitemap.is_file():
        errors.append("sitemap.xml missing")
    else:
        sitemap_text = sitemap.read_text(encoding="utf-8", errors="strict")
        if "saveonsub.com/assets/social/" in sitemap_text:
            errors.append("sitemap.xml contains unpublished assets/social image URL")
        if "https://saveonsub.com/assets/og-image.png" not in sitemap_text:
            errors.append("sitemap.xml missing canonical homepage Open Graph image")

    image = SITE / "assets" / "og-image.png"
    if not image.is_file():
        errors.append("assets/og-image.png missing")
    else:
        try:
            from PIL import Image
            with Image.open(image) as im:
                if im.size != (1200, 630):
                    errors.append(f"assets/og-image.png size={im.size} expected=(1200, 630)")
        except Exception as exc:
            errors.append(f"assets/og-image.png could not be validated: {exc}")

    if errors:
        fail(errors)

    print(
        f"Social metadata validation OK — {len(pages)} HTML page(s), "
        "canonical OG/Twitter large-card parity and 1200x630 approved image enforced."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
