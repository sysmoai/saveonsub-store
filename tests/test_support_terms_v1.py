"""Staged /warranty pages must match Refund V1 and carry no broken rename artifacts."""
import re
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "_site"


@unittest.skipUnless((SITE / "warranty.html").exists(), "run python build_site.py first")
class SupportTermsV1(unittest.TestCase):
    def page(self, rel):
        return (SITE / rel).read_text(encoding="utf-8")

    def test_no_rename_artifacts(self):
        for rel in ("warranty.html", "bn/warranty.html"):
            t = self.page(rel)
            for bad in ("Support terms & Support Terms", "A support terms", "সাপোর্ট শর্ত ও সাপোর্ট শর্ত",
                        "selected offer-এর written terms"):
                self.assertNotIn(bad, t, f"{bad!r} in {rel}")

    def test_single_h1_and_refund_link(self):
        for rel in ("warranty.html", "bn/warranty.html"):
            t = self.page(rel)
            self.assertEqual(len(re.findall(r"<h1\b", t)), 1, rel)
            self.assertIn('href="refund"', t, rel)

    def test_same_outcomes_as_refund_v1(self):
        en, bn = self.page("warranty.html"), self.page("bn/warranty.html")
        self.assertIn("refund for the unused days", en)
        self.assertIn("covered period shown on your product", en)
        self.assertIn("অব্যবহৃত দিনের রিফান্ড", bn)
        self.assertIn("কভারের সময়ের মধ্যে", bn)

    def test_no_new_timing_promise(self):
        for rel in ("warranty.html", "bn/warranty.html"):
            main = re.search(r"(?s)<main.*?</main>", self.page(rel)).group(0)
            self.assertIsNone(re.search(r"\b\d+\s*(?:-|\s)?(?:hour|hr|minute|min|day)s?\b|[০-৯]+\s*(?:ঘণ্টা|মিনিট|দিন)", main), rel)

    def test_official_whatsapp_only(self):
        for rel in ("warranty.html", "bn/warranty.html"):
            nums = set(re.findall(r"wa\.me/(\d+)", self.page(rel)))
            self.assertEqual(nums, {"8801305869242"}, rel)


if __name__ == "__main__":
    unittest.main()
