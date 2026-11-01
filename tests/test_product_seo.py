"""Regression tests for product_seo_enrich.py (synthetic HTML + real copy file)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import product_seo_enrich as s  # noqa: E402

CATALOG = {p["id"]: p for p in json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))["products"]}
COPY = json.loads(s.COPY.read_text(encoding="utf-8"))["products"]

PAGE = (
    '<html><head><title>🎁 Old Title — Current Price Confirmation | SAVEONSUB</title>'
    '<meta name="description" content="old"><meta property="og:title" content="old"></head><body>'
    '<main id="main"><div class="wrap"><h1 style="x">🎁 {name} Price in Bangladesh</h1>'
    '<div class="notice mt3">SaveOnSub is an independent store.</div>\n</div></main></body></html>'
)


class ProductSeo(unittest.TestCase):
    def test_every_catalog_product_has_copy_or_contents(self):
        for pid, p in CATALOG.items():
            self.assertTrue(s.what_text(p, COPY, CATALOG, False), pid)
            self.assertTrue(s.what_text(p, COPY, CATALOG, True), pid)

    def test_copy_has_no_commercial_claims(self):
        for pid, (en, bn) in COPY.items():
            self.assertIsNone(s.FORBIDDEN.search(en), pid)
            self.assertIsNone(s.FORBIDDEN.search(bn), pid)

    def test_titles_short_and_emoji_free(self):
        for p in CATALOG.values():
            for bn in (False, True):
                t = s.make_title(s.clean_name(p["name"]), bn)
                self.assertLessEqual(len(t), s.TITLE_MAX, t)
                self.assertIsNone(s.EMOJI.search(t), t)

    def test_enrich_adds_section_breadcrumb_and_no_price(self):
        for pid in ("chatgpt-plus", "bundle-research", "netflix"):
            p = CATALOG[pid]
            for bn in (False, True):
                out = s.enrich(PAGE.format(name=p["name"]), p, CATALOG, COPY, bn)
                self.assertIn(s.MARK, out)
                self.assertIn('"BreadcrumbList"', out)
                self.assertNotIn("৳", out)
                self.assertNotIn("Current Price Confirmation", out)
                self.assertIsNone(s.EMOJI.search(out.split("<h1")[1].split("</h1>")[0]))
                # idempotent: a second pass adds nothing
                self.assertEqual(out, s.enrich(out, p, CATALOG, COPY, bn))

    def test_missing_governed_body_fails_closed(self):
        with self.assertRaises(SystemExit):
            s.enrich("<html><head><title>x</title></head><body><main></main></body></html>",
                     CATALOG["netflix"], CATALOG, COPY, False)


if __name__ == "__main__":
    unittest.main()
