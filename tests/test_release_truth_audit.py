"""Tests for link_hygiene.py and release_truth_audit.py (fixture site, no real build).

Every audit check has a negative case: the audit must FAIL on a planted defect.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import link_hygiene as lh  # noqa: E402
import release_truth_audit as ra  # noqa: E402

B = "https://saveonsub.com"


def page(url: str, body: str = "", title: str = "T", alts: dict | None = None, extra_head: str = "") -> str:
    tags = "".join(f'<link rel="alternate" hreflang="{k}" href="{v}">' for k, v in (alts or {}).items())
    return (f'<html><head><title>{title}</title><link rel="canonical" href="{url}">{tags}{extra_head}'
            f'</head><body>{body}</body></html>')


class FixtureSite(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.site = self.tmp / "_site"
        (self.site / "p").mkdir(parents=True)
        (self.site / "bn").mkdir()
        offer = ('<script type="application/ld+json">{"@type":"Product","offers":{"@type":"Offer",'
                 '"price":"499","priceCurrency":"BDT"}}</script>')
        files = {
            "index.html": page(B + "/", '<a href="p/a.html">A</a> <a href="https://wa.me/8801305869242">WA</a>',
                               "Home"),
            "about.html": page(B + "/about", '<a href="index.html">home</a>', "About",
                               {"en-bd": B + "/about", "bn-bd": B + "/about", "x-default": B + "/about"}),
            "bn/about.html": page(B + "/bn/about", '<a href="../about.html">EN</a>', "আমাদের সম্পর্কে",
                                  {"bn-bd": B + "/bn/about", "en-bd": B + "/about", "x-default": B + "/about"}),
            "p/a.html": page(B + "/p/a", '<p>৳499 / month</p><a href="../../refund.html">refund</a>', "A", None,
                             offer),
            "refund.html": page(B + "/refund", "", "Refund"),
        }
        for rel, text in files.items():
            (self.site / rel).write_text(text, encoding="utf-8")
        (self.site / "sitemap.xml").write_text(
            "".join(f"<url><loc>{B}{u}</loc></url>" for u in ("/", "/about", "/bn/about", "/p/a", "/refund")),
            encoding="utf-8")
        self.old = (lh.SITE, ra.SITE)
        lh.SITE = ra.SITE = self.site

    def tearDown(self):
        lh.SITE, ra.SITE = self.old
        shutil.rmtree(self.tmp)

    def fix(self):
        self.assertEqual(lh.main([]), 0)

    # link_hygiene ---------------------------------------------------------
    def test_check_fails_before_and_passes_after(self):
        self.assertEqual(lh.main(["--check"]), 1)
        self.fix()
        self.assertEqual(lh.main(["--check"]), 0)
        idx = (self.site / "index.html").read_text()
        self.assertIn('href="p/a"', idx)
        self.assertIn('href="./"', (self.site / "about.html").read_text())
        self.assertIn(f'hreflang="bn-bd" href="{B}/bn/about"', (self.site / "about.html").read_text())

    def test_missing_target_and_external_untouched(self):
        (self.site / "x.html").write_text(page(B + "/x", '<a href="nope.html">n</a>'
                                               '<a href="https://www.adobe.com/a.html">ext</a>'), encoding="utf-8")
        self.fix()
        text = (self.site / "x.html").read_text()
        self.assertIn('href="nope.html"', text)
        self.assertIn('https://www.adobe.com/a.html', text)

    # release_truth_audit: clean fixture passes -----------------------------
    def test_clean_site_passes(self):
        self.fix()
        self.assertEqual(ra.audit(), [])

    # negative cases -------------------------------------------------------
    def assertFails(self, prefix: str):
        errors = ra.audit()
        self.assertTrue(any(e.startswith(prefix) for e in errors), errors)

    def test_private_file_staged_fails(self):
        self.fix()
        (self.site / "catalog.json").write_text("{}")
        self.assertFails("private-files")

    def test_private_cost_json_staged_fails(self):
        self.fix()
        (self.site / "ops").mkdir()
        (self.site / "ops" / "costs.json").write_text("{}")
        self.assertFails("private-files")

    def test_wrong_whatsapp_number_fails(self):
        self.fix()
        (self.site / "refund.html").write_text(page(B + "/refund", '<a href="https://wa.me/8801314773344">x</a>'))
        self.assertFails("whatsapp")

    def test_dead_internal_link_fails(self):
        self.fix()
        (self.site / "refund.html").write_text(page(B + "/refund", '<a href="/p/missing">x</a>'))
        self.assertFails("links")

    def test_sitemap_noindex_page_fails(self):
        self.fix()
        (self.site / "refund.html").write_text(
            page(B + "/refund", "", "Refund", None, '<meta name="robots" content="noindex">'))
        self.assertFails("sitemap")

    def test_duplicate_title_fails(self):
        self.fix()
        (self.site / "refund.html").write_text(page(B + "/refund", "", "A"))
        self.assertFails("canonical")

    def test_non_reciprocal_hreflang_fails(self):
        (self.site / "about.html").write_text(page(B + "/about", "", "About", {"en-bd": B + "/about"}))
        self.assertFails("hreflang")

    def test_offer_price_not_visible_fails(self):
        self.fix()
        text = (self.site / "p" / "a.html").read_text().replace("৳499", "current price")
        (self.site / "p" / "a.html").write_text(text)
        self.assertFails("schema")

    def test_fake_rating_fails(self):
        self.fix()
        (self.site / "refund.html").write_text(page(
            B + "/refund", "", "Refund", None,
            '<script type="application/ld+json">{"@type":"AggregateRating","ratingValue":5}</script>'))
        self.assertFails("schema")

    def test_aips_product_page_with_price_fails(self):
        self.fix()
        (self.site / "p" / "aips-pack.html").write_text(page(B + "/p/aips-pack", "<p>৳1,990</p>", "Pack"))
        self.assertFails("aips")

    def test_manifest_written(self):
        self.fix()
        out = self.tmp / "m.json"
        self.assertEqual(ra.audit(out), [])
        import json
        data = json.loads(out.read_text())
        self.assertEqual(data["sitemap"], 5)
        row = next(r for r in data["rows"] if r["page_id"] == "p/a.html")
        self.assertEqual((row["intent"], row["index"], row["offers"]), ("product", True, 1))


if __name__ == "__main__":
    unittest.main()
