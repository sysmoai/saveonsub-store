"""Tests for listing-card price handling and site_seo_hygiene.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import commercial_truth_v2 as ct  # noqa: E402
import hold_content_price_guard as g  # noqa: E402
import site_seo_hygiene as h  # noqa: E402

CAT = ('<html><head><title>AI Video in Bangladesh — bKash | SAVEONSUB</title>'
       '<meta name="description" content="AI video from current price on the product page via bKash.">'
       '</head><body><h1>AI Video in <span>Bangladesh</span></h1>'
       '<p class="sub">we deliver the same tools from current price on the product page via bKash</p>'
       '<a class="pcard" href="../p/capcut-pro"><h3>CapCut Pro</h3><div class="price">From ৳249</div></a>'
       '<a class="pcard" href="../p/runway"><h3>Runway</h3><div class="price">From ৳499</div></a>'
       '</body></html>')


class ListingCards(unittest.TestCase):
    def test_link_card_keeps_only_approved_price(self):
        book = {"capcut-pro": {249}, "runway": {1}}
        out = g.sanitize(CAT, None, True, book)
        self.assertIn("From ৳249", out)
        self.assertNotIn("৳499", out)

    def test_card_access_label_discloses_shared(self):
        mixed = {"plans": [{"bdt": 499, "type": "shared"}, {"bdt": 2990, "type": "personal"}]}
        shared = {"plans": [{"bdt": 499, "type": "shared"}, {"bdt": 999, "type": "shared"}]}
        personal = {"plans": [{"bdt": 500, "type": "personal"}]}
        self.assertEqual(ct.card_price(mixed, False), ("From ৳499", "Shared and personal plans"))
        self.assertEqual(ct.card_price(shared, False)[1], "Shared account")
        self.assertEqual(ct.card_price(personal, False)[1], "Customer-specific")
        self.assertIn("শেয়ার্ড", ct.card_price(mixed, True)[1])


class Hygiene(unittest.TestCase):
    def test_category_rewrite(self):
        out = h.category(CAT, "c/ai-video.html", False)
        self.assertRegex(out, r"<title>AI Video Prices in Bangladesh: (CapCut Pro, Runway|Runway, CapCut Pro)</title>")
        self.assertRegex(out, r"Compare (CapCut Pro, Runway|Runway, CapCut Pro) in Bangladesh")
        self.assertNotIn("from current price", out)
        self.assertIn('"ItemList"', out)
        self.assertIn("From ৳249", out)

    def test_images_added_once(self):
        t = h.add_images("<html><head></head></html>", "https://saveonsub.com/og.png")
        self.assertEqual(h.add_images(t, "x"), t)
        self.assertIn('property="og:image"', t)


if __name__ == "__main__":
    unittest.main()
