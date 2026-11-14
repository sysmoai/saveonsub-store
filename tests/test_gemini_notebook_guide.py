import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "ops" / "seo" / "guides" / "gemini-notebook-diye-porashona-bangla-guide.md"
PAGE = ROOT / "_site" / "blog" / "gemini-notebook-diye-porashona-bangla-guide.html"


class GeminiNotebookGuideSource(unittest.TestCase):
    def test_source_is_first_party_dated_and_hedged(self):
        text = SRC.read_text(encoding="utf-8")
        self.assertIn("https://support.google.com/gemininotebook/answer/16164461", text)
        self.assertIn("১৪ নভেম্বর ২০২৬", text)
        self.assertIn("14 Nov 2026", text)
        # facts that were NOT read must not be asserted
        self.assertIn("Country availability for Bangladesh, pricing and plan limits were not read", text)
        self.assertNotRegex(text, r"৳|\bfree forever\b|সম্পূর্ণ ফ্রি")

    def test_cta_is_a_no_number_question(self):
        text = SRC.read_text(encoding="utf-8")
        for key in ("cta", "cta_prefill"):
            line = re.search(rf"^{key}: (.*)$", text, re.M).group(1)
            self.assertNotRegex(line, r"[0-9০-৯]|৳|price|দাম", key)

    def test_bangladesh_availability_is_not_claimed(self):
        body = SRC.read_text(encoding="utf-8").split("---", 2)[2]
        self.assertIn("বাংলাদেশ সেখানে আছে কি না, এই গাইড তা নিশ্চিত করে না", body)


@unittest.skipUnless(PAGE.exists(), "run python build_site.py first")
class GeminiNotebookGuidePage(unittest.TestCase):
    def test_page_metadata_and_listing(self):
        html = PAGE.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        self.assertLessEqual(len(title), 60)
        self.assertIn("FAQPage", html)
        self.assertIn('data-guide-cta="whatsapp"', html)
        self.assertIn("https://wa.me/8801305869242?text=", html)
        self.assertEqual((ROOT / "_site" / "sitemap.xml").read_text(encoding="utf-8").count("gemini-notebook-diye-porashona-bangla-guide"), 1)
        self.assertEqual((ROOT / "_site" / "blog" / "index.html").read_text(encoding="utf-8").count("gemini-notebook-diye-porashona-bangla-guide"), 1)

    def test_internal_links_resolve(self):
        html = PAGE.read_text(encoding="utf-8")
        for slug in ("gemini-banglay-kivabe-byabohar-korben", "bangla-prompt-guide-porashona-freelancing-byabsha"):
            self.assertIn(f'href="{slug}"', html.replace("./", ""))
            self.assertTrue((ROOT / "_site" / "blog" / f"{slug}.html").exists(), slug)


if __name__ == "__main__":
    unittest.main()
