"""Every priced product page shows support/refund terms before payment, with no invented promise."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
MARK = 'data-coverage-block="1"'


def catalog():
    t = (SITE / "assets" / "catalog.js").read_text(encoding="utf-8")
    i = t.index("const CATALOG = ") + len("const CATALOG = ")
    return {p["id"]: p for p in json.JSONDecoder().raw_decode(t[i:])[0]["products"]}


@unittest.skipUnless((SITE / "p" / "chatgpt-plus.html").exists(), "run python build_site.py first")
class CoverageDisclosure(unittest.TestCase):
    def test_every_priced_product_page_has_one_block_in_both_languages(self):
        cat = catalog()
        n = 0
        for d in ("p", "bn/p"):
            for f in (SITE / d).glob("*.html"):
                p = cat.get(f.stem)
                if p and p.get("plans"):
                    t = f.read_text(encoding="utf-8")
                    self.assertEqual(t.count(MARK), 1, str(f))
                    self.assertIn("refund.html", t)
                    self.assertIn("warranty.html", t)
                    n += 1
        self.assertGreaterEqual(n, 100)

    def test_no_invented_period_or_guarantee(self):
        cfg = json.loads((ROOT / "ops/seo/control/coverage-periods.json").read_text(encoding="utf-8"))
        t = (SITE / "p" / "chatgpt-plus.html").read_text(encoding="utf-8")
        blk = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)
        self.assertIn("confirmed in writing for your order before you pay", blk) if not cfg else None
        self.assertNotRegex(blk, r"\b\d+\s*(day|days|hour|hours|month)\b")
        for bad in ("guarantee", "lifetime", "official reseller", "authorized"):
            self.assertNotIn(bad, blk.lower())

    def test_shared_products_get_provider_disclosure_personal_only_do_not(self):
        cat = catalog()
        t = (SITE / "p" / "chatgpt-plus.html").read_text(encoding="utf-8")
        self.assertIn("not provided or endorsed by ChatGPT Plus", t)
        bn = (SITE / "bn/p" / "chatgpt-plus.html").read_text(encoding="utf-8")
        self.assertIn("ChatGPT Plus দেয় না বা অনুমোদন করে না", bn)
        personal_only = [i for i, p in cat.items() if p.get("plans") and not any(x.get("type") == "shared" for x in p["plans"])]
        self.assertTrue(personal_only)
        pt = (SITE / "p" / f"{personal_only[0]}.html").read_text(encoding="utf-8")
        self.assertNotIn("not provided or endorsed by", pt)

    def test_whatsapp_cta_uses_official_number_only(self):
        t = (SITE / "p" / "google-ai-pro.html").read_text(encoding="utf-8")
        blk = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)
        self.assertIn("https://wa.me/8801305869242", blk)
        self.assertEqual(len(re.findall(r"wa\.me/(\d+)", blk)), 1)


if __name__ == "__main__":
    unittest.main()
