"""R13: prevent historical provider USD catalog anchors leaking into HOLD pages.

Only generated product body presentation is changed. This does not validate
the vendor tier, current price, seller authorization or production deployment.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import commercial_truth_v2 as ct  # noqa: E402
import build_site  # noqa: E402

PRODUCTS = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))["products"]


class ProviderReferenceHygieneR13(unittest.TestCase):
    def test_all_catalog_provider_refs_have_no_unverified_numeric_usd(self):
        reviewed = 0
        for product in PRODUCTS:
            if not product.get("official_url"):
                continue
            for bn in (False, True):
                with self.subTest(id=product["id"],bn=bn):
                    body = ct.product_main(product, bn)
                    self.assertNotIn("provider list reference:", body)
                    self.assertNotRegex(body, r"(?i)\$\s*[0-9]+(?:\.[0-9]+)?")
                    self.assertIn("href=", body)
                    reviewed += 1
        self.assertGreaterEqual(reviewed, 100)

    def test_deepseek_held_html_keeps_provider_link_without_usd2(self):
        product = next(p for p in PRODUCTS if p["id"] == "deepseek")
        for bn in (False, True):
            with self.subTest(bn=bn):
                body = ct.product_main(product, bn)
                self.assertIn("https://chat.deepseek.com/", body)
                self.assertNotIn("$2", body)
                self.assertNotIn("cartAdd", body)
                self.assertIn("PRICE ON REQUEST" if not bn else "মূল্য অনুরোধসাপেক্ষ", body)

    def test_unverified_synthetic_price_cannot_be_presented_as_official(self):
        fake = {"id": "r13-synthetic", "name": "Unverified Plan",
                "category": "AI Assistants", "plans": [], "request_price": True,
                "official_url": "https://example.com/", "official_usd": 999999}
        for bn in (False, True):
            body = ct.product_main(fake, bn)
            self.assertNotIn("$999999", body)
            self.assertIn("https://example.com/", body)
            self.assertNotIn("cartAdd", body)

    def test_final_commercial_rewrite_precedes_product_seo_and_claim_guards(self):
        steps = build_site.STEPS
        self.assertLess(steps.index("commercial_truth_v2.py"),
                        steps.index("product_seo_enrich.py"))
        self.assertLess(steps.index("product_seo_enrich.py"),
                        steps.index("hold_content_price_guard.py"))


if __name__ == "__main__":
    unittest.main()
