"""Regression tests for conversion_upgrade.py (synthetic product + home pages)."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import conversion_upgrade as cu  # noqa: E402

PLANS = [{"label": "Starter Shared", "bdt": 499, "type": "shared", "billing_unit": "month"},
         {"label": "Personal", "bdt": 3390, "type": "personal", "billing_unit": "month"}]
PRODUCT = {"id": "demo", "name": "Demo AI", "category": "AI Assistants", "plans": PLANS}
OTHER = {"id": "other", "name": "Other Tool", "category": "AI Video",
         "plans": [{"label": "Personal", "bdt": 990, "type": "personal"}]}
PRODUCTS = {"demo": PRODUCT, "other": OTHER}
PAGE = ('<html><body><main id="main" data-commercial-truth="x"><div class="wrap">'
        '<div style="display:flex"><span style="font-size:46px">✨</span><div><h1>Demo AI Price</h1></div></div>'
        '<div class="grid mt2" style="grid-template-columns:1fr;gap:10px"><div class="pcard">plans</div></div>'
        '<section class="mt3"><h2 style="font-size:22px">Confirm the access model before payment</h2><p>x</p></section>'
        '<section><h2 class="mt3" style="font-size:22px">Related tools</h2><ul><li><a href="other">Other Tool</a></li></ul>'
        '<p>More</p></section></div></main>'
        '<a class="fab fab-wa" href="https://wa.me/8801305869242?text=demo%20%E0%A7%B3499">WA</a></body></html>')


def upgrade(text=PAGE, bn=False):
    return cu.upgrade_product(text, PRODUCT, PRODUCTS, {"demo", "other"},
                              {"usd": 20, "url": "https://example.com/pricing"}, "2026-11-02", bn)


class ProductUpgrade(unittest.TestCase):
    def test_blocks_present(self):
        t = upgrade()
        self.assertIn('class="ptile"', t)
        self.assertNotIn("font-size:46px", t)
        self.assertIn("Demo AI key facts", t)
        self.assertIn("Compare plans", t)
        self.assertIn("How ordering works", t)
        self.assertIn('id="plans"', t)
        self.assertIn('class="buybar"', t)
        self.assertIn('<body class="has-buybar">', t)

    def test_idempotent(self):
        once = upgrade()
        self.assertEqual(upgrade(once), once)

    def test_only_own_prices_inside_main(self):
        t = upgrade()
        main = re.search(r"<main\b.*?</main>", t, re.S).group(0)
        amounts = {int(a.replace(",", "")) for a in re.findall(r"৳\s?([0-9][0-9,]*)", main)}
        self.assertLessEqual(amounts, {499, 3390})
        self.assertIn('href="../p/other"', main)

    def test_buybar_reuses_existing_prefill(self):
        t = upgrade()
        self.assertEqual(t.count("text=demo%20%E0%A7%B3499"), 2)

    def test_no_forbidden_claims(self):
        bn_page = PAGE.replace("Confirm the access model before payment", "অ্যাক্সেস আগে নিশ্চিত করুন")
        self.assertEqual(cu.check_text("p", upgrade()), [])
        self.assertEqual(cu.check_text("bn/p", upgrade(bn_page, bn=True)), [])

    def test_missing_anchor_fails_closed(self):
        with self.assertRaises(SystemExit):
            upgrade(PAGE.replace("Confirm the access model before payment", "Changed"))


class HomeUpgrade(unittest.TestCase):
    HOME = ('<html><body><div class="trustbar"><div class="wrap">'
            '<span>🏷️ <b>Every plan clearly labeled</b>: Customer-specific · Team / Workspace · Bundle · Setup / Service</span>'
            '</div></div><header class="hero"><h1>Choose the right subscription. Pay in BDT. Know the access model first.</h1>'
            '<p class="sub">Compare AI, productivity, streaming and other subscriptions. Old.</p>'
            '<div class="pcard"><span class="icon">✨</span><h3>Demo AI</h3><div class="price">From ৳499</div>'
            '<a class="btn" href="p/demo.html">View</a></div></header><footer>f</footer></body></html>')

    def test_home(self):
        t = cu.upgrade_home(self.HOME, PRODUCTS, {"demo", "other"}, False)
        self.assertIn("Shared · Personal", t)
        self.assertIn("Pay in taka.</h1>", t)
        self.assertIn('class="ptile"', t)
        self.assertIn('"FAQPage"', t)
        self.assertEqual(cu.upgrade_home(t, PRODUCTS, {"demo", "other"}, False), t)
        # FAQ JSON-LD matches the visible questions
        for q, _ in cu.HOME_FAQ[False]:
            self.assertIn(f"<summary>{q}</summary>", t)


if __name__ == "__main__":
    unittest.main()
