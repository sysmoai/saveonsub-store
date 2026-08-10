#!/usr/bin/env python3
"""Validate progressive, payload-free catalog discovery in strict SAVEONSUB L1."""
from __future__ import annotations

import json
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class DiscoveryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.discovery_sections: list[dict[str, str]] = []
        self.grids: list[dict[str, str]] = []
        self.cards = 0
        self.product_links: set[str] = set()
        self.categories: set[str] = set()
        self.statuses: set[str] = set()
        self.controls: dict[str, dict[str, str]] = {}
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []
        self.current_class = ""
        self.current_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        tag = tag.lower()
        classes = set(a.get("class", "").split())
        if tag == "html":
            self.lang = a.get("lang", "").lower()
        if tag == "section" and "data-discovery" in a:
            self.discovery_sections.append(a)
        if tag == "div" and a.get("id") == "catalog-grid":
            self.grids.append(a)
        if tag == "article" and "pcard" in classes:
            self.cards += 1
        if tag == "a" and a.get("href") and (a["href"].startswith("/p/") or a["href"].startswith("/bn/p/")):
            self.product_links.add(a["href"])
        for key in ("data-discovery-q", "data-discovery-category", "data-discovery-state", "data-discovery-sort", "data-discovery-clear", "data-discovery-count", "data-discovery-empty"):
            if key in a:
                self.controls[key] = a
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "link" and "stylesheet" in {x.lower() for x in a.get("rel", "").split()} and a.get("href"):
            self.stylesheets.append(a["href"])
        if tag in {"span", "h3"} and classes.intersection({"cat", "tos"}):
            self.current_class = "cat" if "cat" in classes else "tos"
            self.current_text = []

    def handle_endtag(self, tag: str) -> None:
        if self.current_class and tag.lower() in {"span", "h3"}:
            value = " ".join("".join(self.current_text).split())
            if value:
                (self.categories if self.current_class == "cat" else self.statuses).add(value)
            self.current_class = ""
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_class:
            self.current_text.append(data)


def parse(rel: str) -> DiscoveryParser:
    path = SITE / rel
    if not path.is_file():
        fail(f"discovery catalog page missing: {rel}")
        return DiscoveryParser()
    parser = DiscoveryParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    return parser


def validate_catalog(rel: str, language: str) -> None:
    parser = parse(rel)
    if parser.lang != language:
        fail(f"{rel}: language mismatch {parser.lang!r} != {language!r}")
    if len(parser.discovery_sections) != 1:
        fail(f"{rel}: expected one progressive discovery section")
    else:
        section = parser.discovery_sections[0]
        if "hidden" not in section:
            fail(f"{rel}: discovery controls must start hidden for progressive enhancement")
        if not section.get("aria-label", "").strip():
            fail(f"{rel}: discovery section needs localized aria-label")
    if len(parser.grids) != 1:
        fail(f"{rel}: expected one catalog-grid")
    if parser.cards != 72:
        fail(f"{rel}: expected 72 crawlable cards, found {parser.cards}")
    if len(parser.product_links) != 72:
        fail(f"{rel}: expected 72 distinct crawlable product links, found {len(parser.product_links)}")
    if len(parser.categories) != 13:
        fail(f"{rel}: expected 13 rendered categories, found {len(parser.categories)}")
    if not parser.statuses:
        fail(f"{rel}: provider-status labels missing from cards")

    required_controls = {
        "data-discovery-q",
        "data-discovery-category",
        "data-discovery-state",
        "data-discovery-sort",
        "data-discovery-clear",
        "data-discovery-count",
        "data-discovery-empty",
    }
    missing = required_controls - set(parser.controls)
    if missing:
        fail(f"{rel}: missing discovery controls: {sorted(missing)}")
    for key in ("data-discovery-q", "data-discovery-category", "data-discovery-state", "data-discovery-sort"):
        control = parser.controls.get(key, {})
        if control.get("aria-controls") != "catalog-grid":
            fail(f"{rel}: {key} must control catalog-grid")
    q = parser.controls.get("data-discovery-q", {})
    if q.get("type") != "search" or q.get("autocomplete") != "off":
        fail(f"{rel}: search control must be type=search autocomplete=off")
    count = parser.controls.get("data-discovery-count", {})
    if count.get("role") != "status" or count.get("aria-live") != "polite":
        fail(f"{rel}: result count must be a polite live status")
    clear = parser.controls.get("data-discovery-clear", {})
    if clear.get("type") != "button" or "disabled" not in clear:
        fail(f"{rel}: clear filter control must start disabled")
    if parser.scripts.count("/assets/discovery.js") != 1:
        fail(f"{rel}: discovery.js must load exactly once")
    if parser.stylesheets.count("/assets/discovery.css") != 1:
        fail(f"{rel}: discovery.css must load exactly once")


def validate_assets() -> None:
    js_path = SITE / "assets" / "discovery.js"
    css_path = SITE / "assets" / "discovery.css"
    if not js_path.is_file():
        fail("assets/discovery.js missing")
        return
    if not css_path.is_file():
        fail("assets/discovery.css missing")
        return
    js = js_path.read_text(encoding="utf-8", errors="replace")
    css = css_path.read_text(encoding="utf-8", errors="replace")
    required_js = (
        "querySelectorAll('.pcard')",
        "URLSearchParams(location.search)",
        "history.replaceState",
        "data-discovery-category",
        "data-discovery-state",
        "name-asc",
        "name-desc",
        "event.key==='/'",
        "root.hidden=false",
    )
    for token in required_js:
        if token not in js:
            fail(f"discovery.js missing behavior token: {token}")
    forbidden_js = ("fetch(", "XMLHttpRequest", "catalog.json", "assets/catalog.js", "localStorage", "sessionStorage")
    for token in forbidden_js:
        if token in js:
            fail(f"discovery.js must derive state from rendered cards, forbidden token: {token}")
    if ".pcard[hidden]" not in css or "focus-visible" not in css:
        fail("discovery.css must support hidden filtering and visible keyboard focus")

    sw_path = SITE / "sw.js"
    sw = sw_path.read_text(encoding="utf-8", errors="replace") if sw_path.is_file() else ""
    for asset in ("'/assets/discovery.js'", "'/assets/discovery.css'"):
        if asset not in sw:
            fail(f"service worker core missing discovery asset {asset}")


def main() -> int:
    if not SITE.is_dir():
        print("discovery quality blocked: _site missing")
        return 1
    validate_catalog("all.html", "en")
    validate_catalog("bn/all.html", "bn")
    validate_assets()
    if errors:
        print(f"DISCOVERY QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "discovery_quality": "PASS",
        "catalog_pages": 2,
        "products_per_catalog": 72,
        "categories_per_catalog": 13,
        "public_search_index_files": 0,
        "network_catalog_requests": 0,
        "commerce_data_used": 0,
        "pwa_discovery_assets": 2,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
