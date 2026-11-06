"""Regression tests for product_rich_results.py (synthetic page, synthetic plans)."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import product_rich_results as r  # noqa: E402

PRODUCT = {"id": "demo", "name": "🎁 Demo AI", "category": "AI Assistants", "plans": [
    {"label": "Starter Shared (6–8 users)", "bdt": 499, "duration": "1 month", "type": "shared", "billing_unit": "month"},
    {"label": "Personal (your email)", "bdt": 2990, "duration": "1 month", "type": "personal", "billing_unit": "month"},
    {"label": "Yearly", "bdt": 9990, "duration": "1 year", "type": "personal", "billing_unit": "year"},
]}
PAGE = ('<html><head><title>Old</title><meta name="description" content="old">'
        '<meta property="og:image" content="https://saveonsub.com/assets/og.png"></head><body>'
        '<main id="main"><div class="wrap"><h1>Demo AI Price in Bangladesh</h1>'
        '<h2 class="mt3">Current public offer</h2><p>cards</p>'
        '<h2 class="mt3">Frequently asked questions</h2><h3>What is Demo AI?</h3><p>An assistant.</p>'
        '\n</div></main></body></html>')


def lds(t):
    return [json.loads(x) for x in re.findall(r'<script type="application/ld\+json" data-sos="[^"]+">(.*?)</script>', t, re.S)]


class RichResults(unittest.TestCase):
    def setUp(self):
        self.en = r.enrich(PAGE, "demo", PRODUCT, "2026-11-02", False)
        self.bn = r.enrich(PAGE, "demo", PRODUCT, "2026-11-02", True)

    def test_title_has_lowest_price_and_fits(self):
        for t in (self.en, self.bn):
            title = re.search(r"<title>(.*?)</title>", t).group(1)
            self.assertIn("৳499", title)
            self.assertLessEqual(len(title), r.TITLE_MAX)
            self.assertNotRegex(title, r.EMOJI)

    def test_offers_match_plans_exactly(self):
        prod = [x for x in lds(self.en) if x["@type"] == "Product"][0]
        self.assertEqual({o["price"] for o in prod["offers"]}, {"499", "2990", "9990"})
        self.assertTrue(all(o["priceCurrency"] == "BDT" for o in prod["offers"]))
        self.assertNotIn("aggregateRating", json.dumps(prod))

    def test_faq_jsonld_is_visible_and_includes_existing(self):
        faq = [x for x in lds(self.en) if x["@type"] == "FAQPage"][0]
        names = [q["name"] for q in faq["mainEntity"]]
        self.assertIn("What is Demo AI?", names)
        self.assertIn("How much is Demo AI in Bangladesh?", names)
        for n in names:
            self.assertIn(n, self.en)

    def test_yearly_plan_not_labelled_monthly(self):
        self.assertIn("৳9,990 / year", self.en)
        self.assertNotIn("৳9,990 / month", self.en)
        self.assertIn("৳9,990 / বছর", self.bn)

    def test_shared_plan_is_disclosed(self):
        self.assertIn("Shared account (multiple users)", self.en)
        self.assertIn("শেয়ার্ড অ্যাকাউন্ট", self.bn)

    def test_idempotent(self):
        again = r.enrich(self.en, "demo", PRODUCT, "2026-11-02", False)
        self.assertEqual(again.count('class="quick-answer"'), 1)
        self.assertEqual(len(lds(again)), 2)

    def test_no_forbidden_claims(self):
        for t in (self.en, self.bn):
            for sec in re.findall(r'<section data-sos=.*?</section>', t, re.S):
                self.assertIsNone(r.FORBIDDEN.search(re.sub(r"<[^>]+>", " ", sec)))

    def test_aips_and_inquiry_products_excluded(self):
        prods = {"aips-x": {"plans": [{"bdt": 1}]}, "q": {"plans": [], "request_price": True}, "ok": PRODUCT}
        self.assertEqual(list(r.priced(prods)), ["ok"])


if __name__ == "__main__":
    unittest.main()
