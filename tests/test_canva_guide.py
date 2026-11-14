"""Mission 3: the Canva Free-vs-Pro Bangla buyer guide (needs a built _site)."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote

ROOT = Path(__file__).resolve().parent.parent
SLUG = "canva-free-naki-pro-bangladesh-bangla-guide"
PAGE = ROOT / "_site" / "blog" / f"{SLUG}.html"


class CanvaGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.main = re.search(r"<main\b.*?</main>", cls.html, re.S).group(0)
        cls.text = re.sub(r"<[^>]+>", " ", cls.main)

    def test_metadata(self):
        title = re.search(r"<title>(.*?)</title>", self.html).group(1)
        self.assertLessEqual(len(title), 60)
        self.assertIn(f'rel="canonical" href="https://saveonsub.com/blog/{SLUG}"', self.html)
        self.assertEqual(self.html.count("<h1"), 1)
        self.assertIn('hreflang="bn-bd"', self.html)

    def test_structured_data(self):
        kinds = [json.loads(b)["@type"] for b in re.findall(r'application/ld\+json">(.*?)</script>', self.html, re.S)]
        self.assertEqual(kinds, ["Article", "FAQPage"])
        faq = [json.loads(b) for b in re.findall(r'application/ld\+json">(.*?)</script>', self.html, re.S)][1]
        self.assertEqual(len(faq["mainEntity"]), 4)
        for q in faq["mainEntity"]:
            self.assertIn(q["name"], self.text)  # every FAQ answer is visible on the page

    def test_cta_is_a_question_not_an_offer(self):
        href = re.search(r'data-guide-cta="whatsapp".*?href="([^"]+)"', self.html, re.S).group(1).replace("&amp;", "&")
        u = urlsplit(href)
        self.assertEqual((u.netloc, u.path), ("wa.me", "/8801305869242"))
        msg = unquote(parse_qs(u.query)["text"][0])
        self.assertNotRegex(msg, r"[0-9০-৯]")  # no price, no number promise
        cta = re.search(r'data-guide-cta="whatsapp"><p>(.*?)</p>', self.html, re.S).group(1)
        self.assertIn("পাসওয়ার্ড", cta)
        self.assertNotRegex(cta, r"[0-9০-৯]|৳|ছাড়|অফার|সস্তা")

    def test_no_sellable_claims(self):
        for bad in ("৳", "শেয়ার্ড", "সস্তা", "গ্যারান্টি", "SaveOnSub", "SAVEONSUB", "সবচেয়ে কম"):
            self.assertNotIn(bad, self.text)
        self.assertIn("লগইন কারও সঙ্গে ভাগ করবেন না", self.text)

    def test_provider_facts_are_dated_and_hedged(self):
        self.assertIn("১৪ নভেম্বর ২০২৬", self.text)
        self.assertIn("নিজের চেকআউটে", self.text)
        self.assertNotIn("Canva Teams-এ", self.text)

    def test_links_resolve(self):
        for href in re.findall(r'href="(\.\./bn/p/[a-z0-9-]+|[a-z0-9-]+)"', self.main):
            self.assertTrue((PAGE.parent / (href + ".html")).resolve().exists(), href)

    def test_listed_once(self):
        self.assertEqual((ROOT / "_site" / "sitemap.xml").read_text(encoding="utf-8").count(f"/blog/{SLUG}<"), 1)
        guides = [p for p in (ROOT / "ops/seo/guides").glob("*.md") if "canva" in p.name]
        self.assertEqual(len(guides), 1)  # no second Canva guide


if __name__ == "__main__":
    unittest.main()
