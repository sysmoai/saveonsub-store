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

    def test_every_refund_row_is_on_support_terms_verbatim(self):
        cell = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
        for refund, support in (("refund.html", "warranty.html"), ("bn/refund.html", "bn/warranty.html")):
            rows = [c for r in re.findall(r"<tr>(.*?)</tr>", self.page(refund), re.S) if len(c := cell.findall(r)) >= 2]
            self.assertGreaterEqual(len(rows), 8, refund)
            sup = self.page(support)
            for sit, out in [r[:2] for r in rows]:
                self.assertIn(sit.strip(), sup, f"{refund} situation missing on {support}: {sit[:50]}")
                self.assertIn(out.strip(), sup, f"{refund} outcome missing on {support}: {out[:50]}")

    def test_order_receipt_page_has_no_rewrite_artifacts(self):
        t = self.page("order.html")
        self.assertNotIn("support terms support terms", t)
        self.assertNotIn("নিশ্চিত করা হয়ে ডেলিভারি", t)

    def test_internal_links_resolve(self):
        for rel in ("warranty.html", "bn/warranty.html", "order.html"):
            base = (SITE / rel).parent
            for href in re.findall(r'href="([^"#?:]+)"', self.page(rel)):
                if href.startswith(("http", "mailto", "tel")) or href.startswith("assets/") or href.startswith("../assets/"):
                    continue
                target = (base / href)
                ok = target.exists() or (target.with_suffix(".html")).exists() or (target / "index.html").exists() or href in ("./", "../bn")
                self.assertTrue(ok or (SITE / (href.rstrip("/") + ".html")).exists(), f"{rel}: broken link {href}")

    def test_no_new_timing_promise(self):
        """Any hour/day figure on support terms must already be in the CEO-approved refund page."""
        timing = re.compile(r"\b\d+\s*(?:-|\s)?(?:hour|hr|minute|min|day)s?\b|[০-৯]+\s*(?:ঘণ্টা|মিনিট|দিন)")
        for support, refund in (("warranty.html", "refund.html"), ("bn/warranty.html", "bn/refund.html")):
            main = re.search(r"(?s)<main.*?</main>", self.page(support)).group(0)
            ref_main = re.search(r"(?s)<main.*?</main>", self.page(refund)).group(0)
            allowed = set(m.group(0) for m in timing.finditer(ref_main))
            extra = set(m.group(0) for m in timing.finditer(main)) - allowed
            self.assertFalse(extra, f"{support} has timing not on the refund page: {extra}")

    def test_official_whatsapp_only(self):
        for rel in ("warranty.html", "bn/warranty.html"):
            nums = set(re.findall(r"wa\.me/(\d+)", self.page(rel)))
            self.assertEqual(nums, {"8801305869242"}, rel)


if __name__ == "__main__":
    unittest.main()
