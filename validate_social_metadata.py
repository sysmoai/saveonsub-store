#!/usr/bin/env python3
"""Validate authority-safe social preview metadata on every strict SAVEONSUB L1 page."""
from __future__ import annotations

import json
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
DOMAIN = "https://saveonsub.com"
EXPECTED_IMAGE = f"{DOMAIN}/assets/icon-512.png"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta_property: dict[str, list[str]] = {}
        self.meta_name: dict[str, list[str]] = {}
        self.canonical = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag.lower() == "meta":
            if a.get("property"):
                self.meta_property.setdefault(a["property"].lower(), []).append(a.get("content", ""))
            if a.get("name"):
                self.meta_name.setdefault(a["name"].lower(), []).append(a.get("content", ""))
        elif tag.lower() == "link":
            rel = {x.lower() for x in a.get("rel", "").split()}
            if "canonical" in rel:
                self.canonical = a.get("href", "")


def one(mapping: dict[str, list[str]], key: str, rel: str) -> str:
    values = mapping.get(key, [])
    if len(values) != 1:
        fail(f"{rel}: expected exactly one {key}, found {len(values)}")
        return values[0] if values else ""
    return values[0]


def validate_page(path: pathlib.Path) -> None:
    rel = path.relative_to(SITE).as_posix()
    parser = MetaParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()

    og_title = one(parser.meta_property, "og:title", rel)
    og_desc = one(parser.meta_property, "og:description", rel)
    og_url = one(parser.meta_property, "og:url", rel)
    og_image = one(parser.meta_property, "og:image", rel)
    og_width = one(parser.meta_property, "og:image:width", rel)
    og_height = one(parser.meta_property, "og:image:height", rel)
    og_alt = one(parser.meta_property, "og:image:alt", rel)
    twitter_card = one(parser.meta_name, "twitter:card", rel)
    twitter_title = one(parser.meta_name, "twitter:title", rel)
    twitter_desc = one(parser.meta_name, "twitter:description", rel)
    twitter_image = one(parser.meta_name, "twitter:image", rel)
    twitter_alt = one(parser.meta_name, "twitter:image:alt", rel)

    if not og_title.strip() or not og_desc.strip():
        fail(f"{rel}: social title/description cannot be empty")
    if og_url != parser.canonical:
        fail(f"{rel}: og:url must equal canonical")
    if og_image != EXPECTED_IMAGE or twitter_image != EXPECTED_IMAGE:
        fail(f"{rel}: social image must use neutral SAVEONSUB icon")
    if og_width != "512" or og_height != "512":
        fail(f"{rel}: social image dimensions must be 512x512")
    if og_alt != og_title or twitter_alt != og_title:
        fail(f"{rel}: social image alt must match visible page title metadata")
    if twitter_card != "summary":
        fail(f"{rel}: twitter:card must be summary for square neutral icon")
    if twitter_title != og_title or twitter_desc != og_desc:
        fail(f"{rel}: Twitter and Open Graph title/description must stay aligned")


def main() -> int:
    if not SITE.is_dir():
        print("social metadata blocked: _site missing")
        return 1
    image = SITE / "assets" / "icon-512.png"
    if not image.is_file():
        fail("neutral social image assets/icon-512.png is missing")
    pages = sorted(SITE.rglob("*.html"))
    for path in pages:
        validate_page(path)
    if errors:
        print(f"SOCIAL METADATA BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "social_metadata": "PASS",
        "pages_checked": len(pages),
        "social_image": "/assets/icon-512.png",
        "og_errors": 0,
        "twitter_errors": 0,
        "cross_brand_social_images": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
