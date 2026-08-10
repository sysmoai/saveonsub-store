#!/usr/bin/env python3
"""Validate the strict SAVEONSUB mobile-navigation accessibility contract."""
from __future__ import annotations

import json
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class NavParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.navlinks: list[dict[str, str]] = []
        self.hamburgers: list[dict[str, str]] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        classes = set(a.get("class", "").split())
        if tag.lower() == "div" and "navlinks" in classes:
            self.navlinks.append(a)
        elif tag.lower() == "button" and "hamb" in classes:
            self.hamburgers.append(a)
        elif tag.lower() == "script" and a.get("src"):
            self.scripts.append(a["src"])


def validate_page(path: pathlib.Path) -> None:
    rel = path.relative_to(SITE).as_posix()
    parser = NavParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    parser.close()

    if len(parser.navlinks) != 1:
        fail(f"{rel}: expected one .navlinks, found {len(parser.navlinks)}")
    elif parser.navlinks[0].get("id") != "primary-nav":
        fail(f"{rel}: .navlinks must have id=primary-nav")

    if len(parser.hamburgers) != 1:
        fail(f"{rel}: expected one .hamb button, found {len(parser.hamburgers)}")
    else:
        button = parser.hamburgers[0]
        if button.get("aria-controls") != "primary-nav":
            fail(f"{rel}: hamburger aria-controls must target primary-nav")
        if button.get("aria-expanded") != "false":
            fail(f"{rel}: hamburger initial aria-expanded must be false")
        if not button.get("aria-label", "").strip():
            fail(f"{rel}: hamburger needs localized aria-label")
        if any(key.startswith("on") for key in button):
            fail(f"{rel}: hamburger must not depend on CSP-blocked inline event handlers")

    if parser.scripts.count("/assets/a11y.js") != 1:
        fail(f"{rel}: expected exactly one /assets/a11y.js script")


def validate_runtime() -> None:
    path = SITE / "assets" / "a11y.js"
    if not path.is_file():
        fail("assets/a11y.js missing")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    required = (
        "aria-controls",
        "aria-expanded",
        "classList.toggle('open')",
        "event.key!=='Escape'",
        "classList.remove('open')",
        "button.focus()",
        "DOMContentLoaded",
    )
    for token in required:
        if token not in text:
            fail(f"assets/a11y.js missing accessibility behavior token: {token}")

    sw = (SITE / "sw.js").read_text(encoding="utf-8", errors="replace") if (SITE / "sw.js").is_file() else ""
    if "'/assets/a11y.js'" not in sw:
        fail("service worker core does not include /assets/a11y.js")


def main() -> int:
    if not SITE.is_dir():
        print("navigation accessibility blocked: _site missing")
        return 1
    pages = sorted(SITE.rglob("*.html"))
    for path in pages:
        validate_page(path)
    validate_runtime()
    if errors:
        print(f"NAVIGATION ACCESSIBILITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "navigation_accessibility": "PASS",
        "pages_checked": len(pages),
        "nav_id_errors": 0,
        "aria_state_errors": 0,
        "inline_event_handlers": 0,
        "escape_behavior_errors": 0,
        "runtime_load_errors": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
