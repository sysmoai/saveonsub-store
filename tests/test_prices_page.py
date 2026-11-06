"""Regression tests for prices_page.py (synthetic template + plans)."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import hold_content_price_guard as g  # noqa: E402
import prices_page as pp  # noqa: E402

TEMPLATE = ('<html><head><title>About</title><link rel="canonical" href="https://saveonsub.com/about">'
            '<link rel="alternate" hreflang="en-bd" href="https://saveonsub.com/about">'
            '<script type="application/ld+json">{"@type":"AboutPage"}</script></head>'
            '<body><main id="main"><div class="wrap">old</div></main></body></html>')
PRODUCTS = {"demo": {"name": "Demo AI", "category": "AI Assistants", "plans": [
    {"label": "Personal", "bdt": 2990, "type": "personal", "billing_unit": "month"},
    {"label": "Yearly", "bdt": 9990, "type": "personal", "billing_unit": "year"}]}}
POLICY = {"approved_at": "2026-11-02", "approved_products": {"demo": {"approved_on": "2026-11-02"}}}


class PricesPage(unittest.TestCase):
    def test_page_shape(self):
        t = pp.page(TEMPLATE, PRODUCTS, POLICY, False)
        self.assertIn('<link rel="canonical" href="https://saveonsub.com/prices">', t)
        self.assertNotIn("AboutPage", t)
        self.assertIn('"ItemList"', t)
        self.assertIn("৳9,990 / year", t)

    def test_guard_keeps_approved_and_masks_others(self):
        t = pp.page(TEMPLATE, PRODUCTS, POLICY, False)
        book = {"demo": {2990, 9990}}
        self.assertEqual(g.sanitize(t, None, True, book), t)
        bad = pp.page(TEMPLATE, {"demo": {**PRODUCTS["demo"], "plans": [
            {"label": "X", "bdt": 111, "type": "personal"}]}}, POLICY, False)
        self.assertNotIn("৳111", g.sanitize(bad, None, True, book))

    def test_bn(self):
        t = pp.page(TEMPLATE, PRODUCTS, POLICY, True)
        self.assertIn("https://saveonsub.com/bn/prices", t)
        self.assertTrue(re.search(r"৳2,990 / মাস", t))


if __name__ == "__main__":
    unittest.main()
