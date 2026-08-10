#!/usr/bin/env python3
"""Validate CSP/header policy compatibility for the staged SAVEONSUB strict artifact."""
from __future__ import annotations

import json
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


class ScriptPolicyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.inline_event_attributes: list[tuple[str, str]] = []
        self.inline_executable_scripts = 0
        self.external_scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {str(k).lower(): str(v or "") for k, v in attrs}
        for key in a:
            if key.startswith("on"):
                self.inline_event_attributes.append((tag.lower(), key))
        if tag.lower() == "script":
            src = a.get("src", "")
            typ = a.get("type", "").lower()
            if src:
                self.external_scripts.append(src)
            elif typ != "application/ld+json":
                self.inline_executable_scripts += 1


def validate_headers() -> None:
    path = SITE / "_headers"
    if not path.is_file():
        fail("_headers missing from staged artifact")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    required = (
        "X-Content-Type-Options: nosniff",
        "X-Frame-Options: DENY",
        "Referrer-Policy: strict-origin-when-cross-origin",
        "Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        "Strict-Transport-Security: max-age=63072000; includeSubDomains",
        "Cross-Origin-Opener-Policy: same-origin",
        "X-Permitted-Cross-Domain-Policies: none",
        "default-src 'self'",
        "script-src 'self'",
        "script-src-attr 'none'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "upgrade-insecure-requests",
        "Cache-Control: no-cache, no-store, must-revalidate",
        "Service-Worker-Allowed: /",
    )
    for token in required:
        if token not in text:
            fail(f"_headers missing required policy token: {token}")

    csp_line = next((line.strip() for line in text.splitlines() if line.strip().startswith("Content-Security-Policy:")), "")
    if not csp_line:
        fail("Content-Security-Policy header missing")
    else:
        script_directive = next((part.strip() for part in csp_line.split(":", 1)[1].split(";") if part.strip().startswith("script-src ")), "")
        if "'unsafe-inline'" in script_directive:
            fail("script-src must not allow unsafe-inline")
        if "*" in script_directive:
            fail("script-src must not contain wildcard sources")

    if "/assets/*.js\n  Cache-Control: public, max-age=0, must-revalidate" not in text:
        fail("JavaScript HTTP cache must revalidate")
    if "/assets/*.css\n  Cache-Control: public, max-age=0, must-revalidate" not in text:
        fail("CSS HTTP cache must revalidate")


def validate_html() -> tuple[int, int, int]:
    pages = sorted(SITE.rglob("*.html"))
    inline_events = 0
    inline_scripts = 0
    external_scripts = 0
    for path in pages:
        rel = path.relative_to(SITE).as_posix()
        parser = ScriptPolicyParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        parser.close()
        inline_events += len(parser.inline_event_attributes)
        inline_scripts += parser.inline_executable_scripts
        external_scripts += len(parser.external_scripts)
        if parser.inline_event_attributes:
            fail(f"{rel}: inline event attributes violate script-src-attr 'none': {parser.inline_event_attributes[:5]}")
        if parser.inline_executable_scripts:
            fail(f"{rel}: executable inline script violates script-src 'self'")
        for src in parser.external_scripts:
            if not src.startswith("/"):
                fail(f"{rel}: external script must be same-origin root-relative: {src}")
    return len(pages), inline_events, inline_scripts


def main() -> int:
    if not SITE.is_dir():
        print("security policy blocked: _site missing")
        return 1
    validate_headers()
    pages, inline_events, inline_scripts = validate_html()
    if errors:
        print(f"SECURITY POLICY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "security_policy": "PASS",
        "pages_checked": pages,
        "inline_event_attributes": inline_events,
        "inline_executable_scripts": inline_scripts,
        "script_unsafe_inline": False,
        "script_src_attr_none": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
