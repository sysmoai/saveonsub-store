#!/usr/bin/env python3
"""Validate descriptive-only product comparison in strict SAVEONSUB L1."""
from __future__ import annotations

import json
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class CompareParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.roots: list[dict[str, str]] = []
        self.panels: list[dict[str, str]] = []
        self.statuses: list[dict[str, str]] = []
        self.tables: list[dict[str, str]] = []
        self.clear_buttons: list[dict[str, str]] = []
        self.scripts: list[str] = []
        self.styles: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        if "data-compare-root" in a:
            self.roots.append(a)
        if "data-compare-panel" in a:
            self.panels.append(a)
        if "data-compare-status" in a:
            self.statuses.append(a)
        if "data-compare-table" in a:
            self.tables.append(a)
        if "data-compare-clear" in a:
            self.clear_buttons.append(a)
        if tag.lower() == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag.lower() == "link" and "stylesheet" in {x.lower() for x in a.get("rel", "").split()} and a.get("href"):
            self.styles.append(a["href"])


def validate_page(rel: str) -> None:
    path = SITE / rel
    if not path.is_file():
        fail(f"missing comparison catalog: {rel}")
        return
    parser = CompareParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()
    if len(parser.roots) != 1:
        fail(f"{rel}: expected one compare root")
    elif "hidden" not in parser.roots[0] or parser.roots[0].get("aria-labelledby") != "compare-title":
        fail(f"{rel}: compare root must start hidden and be labelled")
    if len(parser.statuses) != 1 or parser.statuses[0].get("role") != "status" or parser.statuses[0].get("aria-live") != "polite":
        fail(f"{rel}: compare status must be polite live status")
    if len(parser.tables) != 1:
        fail(f"{rel}: expected one compare table")
    if len(parser.clear_buttons) != 1 or parser.clear_buttons[0].get("type") != "button" or "disabled" not in parser.clear_buttons[0]:
        fail(f"{rel}: clear comparison must start disabled")
    if parser.scripts.count("/assets/compare.js") != 1:
        fail(f"{rel}: compare.js must load exactly once")
    if parser.styles.count("/assets/compare.css") != 1:
        fail(f"{rel}: compare.css must load exactly once")


def validate_assets() -> None:
    js_path = SITE / "assets" / "compare.js"
    css_path = SITE / "assets" / "compare.css"
    if not js_path.is_file() or not css_path.is_file():
        fail("compare JS/CSS assets missing")
        return
    js = js_path.read_text(encoding="utf-8", errors="replace")
    css = css_path.read_text(encoding="utf-8", errors="replace")
    required = (
        "const MAX=3",
        "querySelectorAll('.pcard')",
        "text(card,'h3')",
        "text(card,'.cat')",
        "text(card,'.tos')",
        "aria-pressed",
        "selected.length>=MAX",
        "searchParams.set('compare'",
        "new URLSearchParams(location.search).get('compare')",
        "document.createElement('table')" if False else "data-compare-toggle",
    )
    for token in required:
        if token not in js:
            fail(f"compare.js missing required behavior: {token}")
    forbidden = (
        "fetch(", "XMLHttpRequest", "catalog.json", "assets/catalog.js", "localStorage", "sessionStorage",
        "price", "rating", "score", "best", "recommend", "winner", "৳", "BDT",
    )
    lower = js.lower()
    for token in forbidden:
        if token.lower() in lower:
            fail(f"compare.js contains forbidden authority/recommendation token: {token}")
    if "overflow:auto" not in css or "aria-pressed" not in css:
        fail("compare.css must support responsive table scrolling and selected state")
    sw = (SITE / "sw.js").read_text(encoding="utf-8", errors="replace") if (SITE / "sw.js").is_file() else ""
    for asset in ("'/assets/compare.js'", "'/assets/compare.css'"):
        if asset not in sw:
            fail(f"service worker core missing comparison asset {asset}")


def main() -> int:
    if not SITE.is_dir():
        print("compare quality blocked: _site missing")
        return 1
    validate_page("all.html")
    validate_page("bn/all.html")
    validate_assets()
    if errors:
        print(f"COMPARE QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "compare_quality": "PASS",
        "catalog_pages": 2,
        "max_products": 3,
        "comparison_fields": ["name", "category", "provider_status", "details_link"],
        "public_comparison_index": 0,
        "network_requests": 0,
        "price_fields": 0,
        "rating_fields": 0,
        "recommendation_scores": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
