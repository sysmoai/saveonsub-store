#!/usr/bin/env python3
"""Validate deterministic same-category exploration on strict SAVEONSUB L1 product pages."""
from __future__ import annotations

import json
import pathlib
from html.parser import HTMLParser

from catalog_model import load_catalog
from enhance_related_v3 import MAX_PEERS, peers_for
from routes_v3 import slugify

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class RelatedParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_related = False
        self.related_depth = 0
        self.section_attrs: dict[str, str] | None = None
        self.links: list[str] = []
        self.text_parts: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        self.depth += 1
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        if tag.lower() == "section" and "data-related-tools" in a:
            if self.in_related:
                fail("nested related-tools section")
            self.in_related = True
            self.related_depth = self.depth
            self.section_attrs = a
        elif self.in_related and tag.lower() == "a" and a.get("href"):
            self.links.append(a["href"])

    def handle_endtag(self, tag: str) -> None:
        if self.in_related and self.depth == self.related_depth and tag.lower() == "section":
            self.in_related = False
        self.depth = max(0, self.depth - 1)

    def handle_data(self, data: str) -> None:
        if self.in_related:
            self.text_parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.text_parts).split())


def expected_links(product: dict, products: list[dict], language: str) -> tuple[str, list[str]]:
    bn = language == "bn"
    prefix = "/bn" if bn else ""
    category = str(product.get("category") or "")
    category_link = f"{prefix}/c/{slugify(category)}.html"
    peer_links = [f"{prefix}/p/{p['id']}.html" for p in peers_for(products, product)]
    return category_link, peer_links


def validate_page(product: dict, products: list[dict], language: str) -> tuple[int, int]:
    bn = language == "bn"
    rel = f"bn/p/{product['id']}.html" if bn else f"p/{product['id']}.html"
    path = SITE / rel
    if not path.is_file():
        fail(f"missing product page: {rel}")
        return 0, 0
    parser = RelatedParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    attrs = parser.section_attrs
    if attrs is None:
        fail(f"{rel}: missing same-category exploration section")
        return 0, 0

    category = str(product.get("category") or "")
    peers = peers_for(products, product)
    category_link, peer_links = expected_links(product, products, language)
    if attrs.get("data-related-category") != category:
        fail(f"{rel}: related category mismatch")
    if attrs.get("data-related-count") != str(len(peers)):
        fail(f"{rel}: related count mismatch")
    if parser.links.count(category_link) != 1:
        fail(f"{rel}: expected exactly one category link {category_link}")

    actual_peer_links = [link for link in parser.links if link.startswith("/bn/p/" if bn else "/p/")]
    if actual_peer_links != peer_links:
        fail(f"{rel}: peer links are not deterministic/catalog-derived: {actual_peer_links} != {peer_links}")
    if len(actual_peer_links) > MAX_PEERS:
        fail(f"{rel}: peer count exceeds {MAX_PEERS}")
    if (f"/bn/p/{product['id']}.html" if bn else f"/p/{product['id']}.html") in actual_peer_links:
        fail(f"{rel}: self-link present in related tools")

    text = parser.text().lower()
    forbidden = ("best", "recommended", "recommendation", "winner", "ranking", "score", "rating", "top pick", "৳", "bdt", "price")
    for token in forbidden:
        if token in text:
            fail(f"{rel}: related section contains ranking/commerce token: {token}")
    required_label = "একই ক্যাটাগরি" if bn else "same category"
    if peers and required_label.lower() not in text:
        fail(f"{rel}: peers are not explicitly labeled same-category")
    if not peers:
        zero_copy = "এই ক্যাটাগরিতে বর্তমানে অন্য কোনো টুল নেই" if bn else "there are currently no other tools in this category"
        if zero_copy.lower() not in text:
            fail(f"{rel}: single-product category needs explicit no-peer copy")
    return 1, len(peer_links)


def main() -> int:
    if not SITE.is_dir():
        print("related quality blocked: _site missing")
        return 1
    catalog = load_catalog()
    products = catalog.get("products", [])
    pages = 0
    peer_links = 0
    zero_peer_pages = 0
    for product in products:
        peers = peers_for(products, product)
        if not peers:
            zero_peer_pages += 2
        for language in ("en", "bn"):
            checked, links = validate_page(product, products, language)
            pages += checked
            peer_links += links
    if errors:
        print(f"RELATED QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "related_quality": "PASS",
        "product_pages_checked": pages,
        "max_peers_per_page": MAX_PEERS,
        "same_category_peer_links": peer_links,
        "zero_peer_pages": zero_peer_pages,
        "ranking_terms": 0,
        "recommendation_terms": 0,
        "price_fields": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
