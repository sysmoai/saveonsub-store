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

    def test_breadcrumb_urls_are_locale_correct(self):
        for p in CATALOG.values():
            cat = s.slug(p["category"])
            en = json.loads(s.breadcrumb_ld(p, False).split(">", 1)[1].rsplit("<", 1)[0])
            bn = json.loads(s.breadcrumb_ld(p, True).split(">", 1)[1].rsplit("<", 1)[0])
            self.assertEqual([i["item"] for i in en["itemListElement"]],
                             [f"{s.BASE}/", f"{s.BASE}/all", f"{s.BASE}/c/{cat}", f"{s.BASE}/p/{p['id']}"])
            self.assertEqual([i["item"] for i in bn["itemListElement"]],
                             [f"{s.BASE}/bn", f"{s.BASE}/all", f"{s.BASE}/bn/c/{cat}", f"{s.BASE}/bn/p/{p['id']}"])
            self.assertEqual(bn["itemListElement"][0]["name"], "হোম")

    def test_section_links_stay_in_page_locale(self):
        import re
        for pid in ("netflix", "canva-pro", "bundle-dev", "cursor"):
            for bn in (False, True):
                sec = s.section_html(CATALOG[pid], CATALOG, COPY, bn)
                for href in re.findall(r'href="([^"]+)"', sec):
                    if href.startswith("http"):
                        continue
                    # relative to /p/ (EN) or /bn/p/ (BN): only siblings or ../c/<slug>
                    self.assertTrue(re.fullmatch(r"[a-z0-9-]+|\.\./c/[a-z0-9-]+|(\.\./)+blog/[a-z0-9-]+", href), href)

    @unittest.skipUnless((ROOT / "_site" / "p").exists(), "staged site not built")
    def test_staged_section_links_resolve_to_same_locale_pages(self):
        import re
        for base, prefix in ((ROOT / "_site" / "p", ""), (ROOT / "_site" / "bn" / "p", "bn/")):
            for page in base.glob("*.html"):
                t = page.read_text(encoding="utf-8")
                sec = re.search(rf"<section[^>]*{re.escape(s.MARK)}.*?</section>", t, re.S)
                self.assertIsNotNone(sec, page)
                for href in re.findall(r'href="([^"]+)"', sec.group(0)):
                    if href.startswith("http"):
                        continue
                    target = (page.parent / (href + ".html")).resolve()
                    self.assertTrue(target.exists(), f"{page}: {href}")
                    if "/_site/blog/" not in target.as_posix():
                        self.assertEqual(prefix == "bn/", "/_site/bn/" in target.as_posix(), f"{page}: {href}")


if __name__ == "__main__":
    unittest.main()


class BanglaGuides(unittest.TestCase):
    def test_sources_parse_and_have_no_claims(self):
        import bangla_guides as g
        products, guides = g.load()
        self.assertGreaterEqual(len(guides), 3)
        for meta in guides:
            self.assertTrue(all(p in products for p in meta["related"]), meta["slug"])
            html_out = g.md_to_html(meta["body"])
            self.assertIn("<h2", html_out)
            self.assertNotIn("৳", html_out)

    def test_faq_rows_have_four_fields_and_no_claims(self):
        for pid, rows in s.FAQS.items():
            self.assertIn(pid, CATALOG)
            for r in rows:
                self.assertEqual(4, len(r), pid)
                for x in r:
                    self.assertIsNone(s.FORBIDDEN.search(x), pid)
