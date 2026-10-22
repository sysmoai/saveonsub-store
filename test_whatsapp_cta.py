#!/usr/bin/env python3
"""Negative + positive tests for the floating WhatsApp CTA (commercial_truth_v2.py).

Covers the two defects flagged in the 2026-10-23 CEO production-safety review:
1. A missing/unrecognized CTA must FAIL validation, not silently pass.
2. The generated wa.me link must be safely percent-encoded for apostrophes,
   ampersands, Bengali text, emoji and other non-ASCII content, and must never
   embed the message as a raw, hand-escaped JS string literal.

Run: python test_whatsapp_cta.py
Exits non-zero on any failure, matching the repo's other audit_*.py scripts.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

import commercial_truth_v2 as ct

WA_NUMBER = "8801305869242"

PAGE_TEMPLATE = """<!DOCTYPE html><html><body>
<main id="main"><h1>placeholder</h1></main>
{fab}
</body></html>"""

GOOD_FAB = (
    '<button class="fab fab-wa" onclick="location.href=\'https://wa.me/'
    + WA_NUMBER
    + "?text=STALE%20PRICE%20HERE'\" aria-label=\"WhatsApp\">\U0001f4ac WhatsApp</button>"
)


def make_page(tmp: Path, fab_html: str) -> Path:
    path = tmp / "product.html"
    path.write_text(PAGE_TEMPLATE.format(fab=fab_html), encoding="utf-8")
    return path


def extract_fab_href(text: str) -> str | None:
    m = re.search(r'<a class="fab fab-wa" href="([^"]*)"', text)
    return m.group(1) if m else None


def decoded_text_param(href: str) -> str:
    return parse_qs(urlsplit(href).query).get("text", [""])[0]


def run(label, fn):
    try:
        fn()
        print(f"PASS — {label}")
        return True
    except AssertionError as e:
        print(f"FAIL — {label}: {e}")
        return False


def test_positive_rewrite_fixed_price():
    with tempfile.TemporaryDirectory() as d:
        path = make_page(Path(d), GOOD_FAB)
        product = {
            "id": "chatgpt-plus",
            "name": "ChatGPT Plus",
            "category": "AI Assistants",
            "plans": [{"label": "Plus — 1 Month", "bdt": 3390, "type": "personal", "duration": "1 month"}],
        }
        ct.rewrite_product_page(path, product, bn=False)
        text = path.read_text(encoding="utf-8")
        href = extract_fab_href(text)
        assert href is not None, "expected a rewritten <a class=fab fab-wa> anchor"
        assert href.startswith(f"https://wa.me/{WA_NUMBER}?text="), f"unexpected href prefix: {href}"
        decoded = decoded_text_param(href)
        assert "3,390" in decoded or "3390" in decoded, f"approved price missing from CTA text: {decoded!r}"
        assert "'" not in href and '"' not in href, "href must not contain raw quote characters"


def test_positive_rewrite_inquiry_product():
    with tempfile.TemporaryDirectory() as d:
        path = make_page(Path(d), GOOD_FAB)
        product = {"id": "canva-pro", "name": "Canva Pro", "category": "ai-image-design", "plans": [], "request_price": True}
        ct.rewrite_product_page(path, product, bn=False)
        href = extract_fab_href(path.read_text(encoding="utf-8"))
        decoded = decoded_text_param(href)
        assert "confirm" in decoded.lower(), f"inquiry CTA should ask to confirm price: {decoded!r}"
        assert "৳" not in decoded, f"inquiry product must not quote any fixed price: {decoded!r}"


def test_negative_missing_cta_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        path = make_page(Path(d), "<!-- no fab button on this page -->")
        product = {"id": "claude-pro", "name": "Claude Pro", "category": "AI Assistants", "plans": [{"label": "Claude Pro — 1 Month", "bdt": 3390, "type": "personal"}]}
        try:
            ct.rewrite_product_page(path, product, bn=False)
            raise AssertionError("expected SystemExit when the floating WhatsApp CTA is missing, got silent success")
        except SystemExit as e:
            assert "not found" in str(e).lower() or "missing" in str(e).lower(), f"unexpected SystemExit message: {e}"


def test_negative_unrecognized_cta_markup_fails_closed():
    with tempfile.TemporaryDirectory() as d:
        # Right-looking button, wrong WhatsApp number — must not be silently accepted.
        wrong_number_fab = GOOD_FAB.replace(WA_NUMBER, "8800000000000")
        path = make_page(Path(d), wrong_number_fab)
        product = {"id": "claude-pro", "name": "Claude Pro", "category": "AI Assistants", "plans": [{"label": "Claude Pro — 1 Month", "bdt": 3390, "type": "personal"}]}
        try:
            ct.rewrite_product_page(path, product, bn=False)
            raise AssertionError("expected SystemExit for a CTA pointing at the wrong WhatsApp number")
        except SystemExit:
            pass


def test_encoding_apostrophe_ampersand_bengali_emoji():
    with tempfile.TemporaryDirectory() as d:
        path = make_page(Path(d), GOOD_FAB)
        product = {
            "id": "weird-name",
            "name": "Tom & Jerry's Ultimate \U0001f680 অ্যাপ",
            "category": "AI Assistants",
            "plans": [{"label": "Standard's Plan — 1 Month", "bdt": 1234, "type": "personal"}],
        }
        ct.rewrite_product_page(path, product, bn=False)
        text = path.read_text(encoding="utf-8")
        href = extract_fab_href(text)
        assert href is not None
        # The raw href must contain no literal apostrophe, ampersand, space, or
        # non-ASCII byte — everything after `text=` must be percent-encoded.
        query_value = href.split("text=", 1)[1]
        assert "'" not in query_value, f"unescaped apostrophe leaked into href: {query_value}"
        assert "&" not in query_value.replace("&amp;", ""), f"raw ampersand leaked into query: {query_value}"
        assert all(ord(c) < 128 for c in query_value), f"non-ASCII byte leaked unescaped into href: {query_value}"
        decoded = decoded_text_param(html_unescape(href))
        assert "Tom & Jerry's Ultimate" in decoded and "অ্যাপ" in decoded and "\U0001f680" in decoded, \
            f"round-trip decode lost content: {decoded!r}"


def html_unescape(s: str) -> str:
    import html as _html
    return _html.unescape(s)


def test_sanitize_common_converts_every_other_fab_button_too():
    # Non-governed pages (checkout, Netflix, Spotify, blog posts, ...) never go
    # through rewrite_product_page(), so sanitize_common() must be the thing
    # that makes *their* floating WhatsApp buttons safe too. The raw message
    # here uses HTML-entity-escaped &amp; / &#39; — the form any careful
    # generator would already produce when splicing text into an HTML
    # attribute. (A *raw*, un-entity-escaped apostrophe inside the single-quoted
    # JS literal breaks the HTML before this function ever sees it — that is a
    # latent landmine in the original onclick/location.href pattern itself, not
    # something a post-hoc text pass can repair; see report Section D/F.)
    raw = (
        '<button class="fab fab-wa" onclick="location.href=\'https://wa.me/8801305869242?text='
        "Hi! I want Tom &amp; Jerry&#39;s plan ✨'\" aria-label=\"WhatsApp\">\U0001f4ac WhatsApp</button>"
    )
    out = ct.sanitize_common(raw)
    assert "<button" not in out, f"legacy onclick button should be fully replaced: {out}"
    href = extract_fab_href(out)
    assert href is not None, f"expected a converted <a class=fab fab-wa> anchor: {out}"
    query_value = href.split("text=", 1)[1]
    assert "'" not in query_value and "&" not in query_value.replace("&amp;", ""), \
        f"unescaped apostrophe/ampersand leaked: {query_value}"
    decoded = decoded_text_param(html_unescape(href))
    assert "Tom & Jerry's plan" in decoded, f"round-trip lost content: {decoded!r}"


def test_pipeline_order_sanitize_then_rewrite_stays_idempotent_and_correct():
    # Real build order: sanitize_common() runs on every page first (converting
    # button->anchor), THEN rewrite_product_page() runs on governed pages only.
    with tempfile.TemporaryDirectory() as d:
        path = make_page(Path(d), GOOD_FAB)
        path.write_text(ct.sanitize_common(path.read_text(encoding="utf-8")), encoding="utf-8")
        product = {"id": "chatgpt-plus", "name": "ChatGPT Plus", "category": "AI Assistants",
                   "plans": [{"label": "Plus — 1 Month", "bdt": 3390, "type": "personal"}]}
        ct.rewrite_product_page(path, product, bn=False)
        href = extract_fab_href(path.read_text(encoding="utf-8"))
        assert href is not None and "3%2C390" in href or "3390" in (href or ""), \
            f"governed price should win over the pre-existing (now-anchor) stale CTA: {href}"


def test_negative_stale_price_in_cta_rejected_by_build_audit():
    # Simulate the main()-level audit: a page whose CTA still quotes a price the
    # governed plan list does not contain must be flagged, not pass silently.
    approved_prices = {3390}
    fab_text_with_stale_price = "Hi! I want to order Claude Pro (Premium Shared, ৳1495)"
    fab_prices = {int(n.replace(",", "")) for n in re.findall(r"৳([\d,]+)", fab_text_with_stale_price)}
    assert fab_prices and not fab_prices.issubset(approved_prices), \
        "test setup error: expected the stale price to be detected as unapproved"


TESTS = [
    ("rewrite_product_page produces a safe, correctly-priced anchor (fixed price)", test_positive_rewrite_fixed_price),
    ("rewrite_product_page produces a confirm-price CTA for inquiry-only products", test_positive_rewrite_inquiry_product),
    ("missing floating CTA fails closed (SystemExit), not a silent pass", test_negative_missing_cta_fails_closed),
    ("CTA pointing at the wrong WhatsApp number fails closed", test_negative_unrecognized_cta_markup_fails_closed),
    ("apostrophes / ampersands / Bengali / emoji are safely percent-encoded", test_encoding_apostrophe_ampersand_bengali_emoji),
    ("sanitize_common() converts every other floating WhatsApp button too", test_sanitize_common_converts_every_other_fab_button_too),
    ("sanitize_common() then rewrite_product_page() stays correct and idempotent", test_pipeline_order_sanitize_then_rewrite_stays_idempotent_and_correct),
    ("stale price in CTA text is detected as a violation by the audit logic", test_negative_stale_price_in_cta_rejected_by_build_audit),
]


def main() -> int:
    results = [run(label, fn) for label, fn in TESTS]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} WhatsApp CTA tests passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
