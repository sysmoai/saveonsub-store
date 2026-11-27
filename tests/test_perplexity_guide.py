"""Weekly SEO cycle 2026-11-23: the Perplexity Free-vs-Pro Bangla guide (needs a built _site)."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote

ROOT = Path(__file__).resolve().parent.parent
SLUG = "perplexity-free-naki-pro-bangla-guide"
PAGE = ROOT / "_site" / "blog" / f"{SLUG}.html"


@unittest.skipUnless(PAGE.exists(), "run python build_site.py first")
class PerplexityGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.main = re.search(r"<main\b.*?</main>", cls.html, re.S).group(0)
        cls.text = re.sub(r"<[^>]+>", " ", cls.main)

    def test_metadata(self):
        title = re.search(r"<title>(.*?)</title>", self.html).group(1)
        self.assertLessEqual(len(title), 60)
        desc = re.search(r'<meta name="description" content="([^"]*)"', self.html).group(1)
        self.assertLessEqual(len(desc), 160)
        self.assertIn(f'rel="canonical" href="https://saveonsub.com/blog/{SLUG}"', self.html)
        self.assertEqual(self.html.count("<h1"), 1)
        self.assertIn('hreflang="bn-bd"', self.html)

    def test_structured_data(self):
        blocks = [json.loads(b) for b in re.findall(r'application/ld\+json">(.*?)</script>', self.html, re.S)]
        self.assertEqual([b["@type"] for b in blocks], ["Article", "FAQPage"])
        self.assertEqual(blocks[0]["datePublished"], "2026-11-23")
        self.assertEqual(len(blocks[1]["mainEntity"]), 4)
        for q in blocks[1]["mainEntity"]:
            self.assertIn(q["name"], self.text)

    def test_no_price_and_no_sellable_claims(self):
        # The provider price could not be read on 2026-11-23, so the guide must not state any.
        self.assertNotRegex(self.text, r"\$\s*\d|৳|টাকা")
        for bad in ("শেয়ার্ড", "সস্তা", "গ্যারান্টি", "SaveOnSub", "SAVEONSUB", "সবচেয়ে কম"):
            self.assertNotIn(bad, self.text)
        self.assertIn("লগইন কারও সঙ্গে ভাগ করবেন না", self.text)

    def test_facts_are_dated_with_first_party_links(self):
        self.assertIn("২৩ নভেম্বর ২০২৬", self.text)
        self.assertIn("নিজের চেকআউটে", self.text)
        for url in ("https://www.perplexity.ai/help-center/en/articles/10352901-what-is-perplexity-pro",
                    "https://www.perplexity.ai/help-center/en/articles/10352895-how-does-perplexity-work"):
            self.assertIn(f'href="{url}"', self.main)

    def test_cta_is_a_question_not_an_offer(self):
        href = re.search(r'data-guide-cta="whatsapp".*?href="([^"]+)"', self.html, re.S).group(1).replace("&amp;", "&")
        u = urlsplit(href)
        self.assertEqual((u.netloc, u.path), ("wa.me", "/8801305869242"))
        self.assertNotRegex(unquote(parse_qs(u.query)["text"][0]), r"[0-9০-৯]")


class WeeklyHygiene(unittest.TestCase):
    def test_how_to_order_titles_fit(self):
        for rel in ("how-to-order.html", "bn/how-to-order.html"):
            page = ROOT / "_site" / rel
            if page.exists():
                title = re.search(r"<title>(.*?)</title>", page.read_text(encoding="utf-8")).group(1)
                self.assertLessEqual(len(title), 60, rel)

    def test_bn_all_has_its_own_description(self):
        a, b = ROOT / "_site" / "bn" / "all.html", ROOT / "_site" / "subscriptions.html"
        if a.exists() and b.exists():
            get = lambda p: re.search(r'<meta name="description" content="([^"]*)"', p.read_text(encoding="utf-8")).group(1)
            self.assertNotEqual(get(a), get(b))


if __name__ == "__main__":
    unittest.main()
