"""Tests for all_static_index.py (fixture site, no real build)."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import all_static_index as ai  # noqa: E402

SHELL = '<main><div class="grid g4" id="grid"></div>\n  <section id="bundles"><div id="bgrid"></div></section></main>'
PRODUCTS = {
    "chatgpt-plus": {"name": "🤖 ChatGPT Plus", "category": "AI Assistants"},
    "netflix": {"name": "Netflix", "category": "Entertainment"},
    "aips-business-package": {"name": "AIPS Business", "category": "Bundles"},
    "no-page": {"name": "No Page", "category": "Other"},
}


class AllIndex(unittest.TestCase):
    def setUp(self):
        self.site = Path(tempfile.mkdtemp())
        for d in ("p", "bn/p"):
            (self.site / d).mkdir(parents=True)
            for pid in ("chatgpt-plus", "netflix", "aips-business-package"):
                (self.site / d / f"{pid}.html").write_text("x")
        for rel in ("all.html", "bn/all.html"):
            (self.site / rel).write_text(SHELL)

    def tearDown(self):
        shutil.rmtree(self.site)

    def stage_all(self):
        for bn in (False, True):
            p = self.site / ("bn/all.html" if bn else "all.html")
            p.write_text(ai.stage(p.read_text(), ai.listed(PRODUCTS, self.site, bn), bn))

    def test_links_present_aips_and_pageless_excluded(self):
        self.stage_all()
        html = (self.site / "all.html").read_text()
        self.assertIn('href="p/chatgpt-plus"', html)
        self.assertIn('href="p/netflix"', html)
        self.assertNotIn("aips-", html)
        self.assertNotIn("no-page", html)
        self.assertIn("ChatGPT Plus</a>", html)  # emoji stripped
        self.assertIn("বিনোদন", (self.site / "bn/all.html").read_text())
        self.assertEqual(ai.check(self.site, PRODUCTS), [])

    def test_idempotent(self):
        self.stage_all()
        first = (self.site / "all.html").read_text()
        self.stage_all()
        self.assertEqual((self.site / "all.html").read_text(), first)

    def test_missing_index_fails(self):
        self.assertTrue(any("missing" in e for e in ai.check(self.site, PRODUCTS)))

    def test_planted_aips_link_fails(self):
        self.stage_all()
        p = self.site / "all.html"
        p.write_text(p.read_text().replace('href="p/netflix"', 'href="p/aips-business-package"'))
        self.assertTrue(ai.check(self.site, PRODUCTS))

    def test_price_in_index_fails(self):
        self.stage_all()
        p = self.site / "all.html"
        p.write_text(p.read_text().replace("Netflix</a>", "Netflix ৳499</a>"))
        self.assertTrue(any("prices" in e for e in ai.check(self.site, PRODUCTS)))


if __name__ == "__main__":
    unittest.main()
