"""Bangla buyer guidance on the three product pages: present once, no price/claim, no FAQ duplication."""
import re
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "_site"
MARK = 'data-bn-buyer-copy="1"'
PAGES = ("chatgpt-plus", "chatgpt-go", "google-ai-pro")


def block(slug):
    t = (SITE / "bn" / "p" / f"{slug}.html").read_text(encoding="utf-8")
    m = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S)
    return t, (m.group(0) if m else None)


@unittest.skipUnless((SITE / "bn" / "p" / "chatgpt-plus.html").exists(), "run python build_site.py first")
class BnBuyerCopy(unittest.TestCase):
    def test_exactly_one_block_on_each_of_the_three_pages_and_nowhere_else(self):
        for s in PAGES:
            t, b = block(s)
            self.assertEqual(t.count(MARK), 1, s)
            self.assertIsNotNone(b, s)
        others = [f for f in (SITE / "bn" / "p").glob("*.html") if f.stem not in PAGES]
        self.assertTrue(others)
        self.assertTrue(all(MARK not in f.read_text(encoding="utf-8") for f in others))

    def test_block_has_no_price_guarantee_or_provider_claim(self):
        for s in PAGES:
            _, b = block(s)
            txt = re.sub(r"<[^>]+>", " ", b)
            self.assertNotRegex(txt, r"[৳$]|[০-৯\d,]+\s*টাকা|[০-৯\d]+\s*TB|ক্রেডিট\s*[০-৯\d]", s)
            for bad in ("গ্যারান্টি", "আনলিমিটেড", "অনুমোদিত", "অফিসিয়াল রিসেলার", "সর্বনিম্ন", "একই দিনে", "ফেরত"):
                self.assertNotIn(bad, txt, f"{s}: {bad}")

    def test_no_new_faq_markup_or_schema(self):
        for s in PAGES:
            _, b = block(s)
            self.assertEqual(b.count("<details"), 1, s)  # optional tutorial only, not an FAQ
            self.assertNotIn("FAQ", b)
            self.assertNotIn("application/ld+json", b)
            self.assertNotIn("FAQPage", b)

    def test_links_are_clean_and_resolve(self):
        for s in PAGES:
            _, b = block(s)
            for href in re.findall(r'href="([^"]+)"', b):
                if href.startswith("https://wa.me/8801305869242"):
                    continue
                self.assertNotIn(".html", href)
                target = (SITE / "bn" / "p" / href).resolve()
                self.assertTrue(target.with_suffix(".html").exists() or target.is_dir(), f"{s}: dead {href}")

    def test_visible_part_is_short_and_has_cta_before_the_tutorial(self):
        for s in PAGES:
            _, b = block(s)
            head, tail = b.split("<details", 1)
            self.assertLess(len(re.sub(r"<[^>]+>", "", head)), 520, s)
            self.assertIn('href="https://wa.me/8801305869242?text=', head, s)
            self.assertNotRegex(head, r"wa\.me/(?!8801305869242)", s)
            self.assertIn("দশ মিনিটের", tail, s)

    def test_google_box_separates_official_list_from_offer_confirmation(self):
        t = (SITE / "bn" / "p" / "google-ai-pro.html").read_text(encoding="utf-8")
        a = t.index("১. Google-এর অফিসিয়াল প্ল্যানে যা আছে")
        b = t.index("২. ")
        self.assertLess(a, b)
        self.assertIn("এমন ধরে নেবেন না", t)
        en = (SITE / "p" / "google-ai-pro.html").read_text(encoding="utf-8")
        self.assertIn("Do not assume the whole list above applies", en)

    def test_google_lead_no_longer_asserts_every_feature_is_on_this_offer(self):
        t = (SITE / "bn" / "p" / "google-ai-pro.html").read_text(encoding="utf-8")
        self.assertNotIn("তাই প্রতিটি ফিচার আপনার নিজের", t)
        self.assertIn("পেমেন্টের আগে লিখিতভাবে নিশ্চিত করুন", t)
        en = (SITE / "p" / "google-ai-pro.html").read_text(encoding="utf-8")
        self.assertNotIn("so every feature shows up", en)


if __name__ == "__main__":
    unittest.main()
