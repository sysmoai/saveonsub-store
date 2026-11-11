"""Tests for cross_unit_quarantine.py (fixture site, no real build)."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cross_unit_quarantine as q  # noqa: E402

CAT = {"meta": {}, "products": [{"id": "netflix"}, {"id": "bundle-dev"}, {"id": "aips-business-package"}]}
REDIRECTS = "/p/aips-* /all 301\n/bn/p/aips-* /bn/all 301\n/modes/aips-* /all 301\n"
BUNDLES = ('<html><head><script type="application/ld+json">{"@type": "ItemList", "numberOfItems": 2, '
           '"itemListElement": [{"@type": "ListItem", "position": 1, "url": "https://saveonsub.com/p/aips-business-package"}, '
           '{"@type": "ListItem", "position": 2, "url": "https://saveonsub.com/p/bundle-dev"}]}</script></head><body>'
           '<a class="pcard" href="../p/aips-business-package"><h3>AIPS</h3></a>'
           '<a class="pcard" href="../p/bundle-dev"><h3>Dev</h3></a></body></html>')
MODES = ('<div class="pcard" style="padding:28px"><h3>Dev</h3><div class="ctas"><a href="modes/bundle-dev">V</a></div></div>'
         '<div class="pcard" style="padding:28px"><h3>Biz</h3><div class="ctas"><a href="modes/aips-business-package">V</a></div></div>'
         "<script>const MODE_MAP = {team: 'aips-business-package'};</script>")


class Quarantine(unittest.TestCase):
    def setUp(self):
        self.site = Path(tempfile.mkdtemp())
        for d in ("p", "bn/p", "modes", "c", "assets"):
            (self.site / d).mkdir(parents=True, exist_ok=True)
        for d in ("p", "bn/p", "modes"):
            (self.site / d / "aips-business-package.html").write_text("other unit")
        (self.site / "p" / "bundle-dev.html").write_text("ok")
        (self.site / "assets" / "catalog.js").write_text("/* x */\nconst CATALOG = " + json.dumps(CAT) + ";\n")
        (self.site / "c" / "bundles.html").write_text(BUNDLES)
        (self.site / "modes.html").write_text(MODES)
        (self.site / "all.html").write_text('<title>All 3 Products</title>{"numberOfItems":3,"itemListOrder":"x"} 3 subscriptions')
        (self.site / "sitemap.xml").write_text("<urlset>\n  <url><loc>https://saveonsub.com/p/aips-business-package</loc></url>\n"
                                               "  <url><loc>https://saveonsub.com/p/bundle-dev</loc></url>\n</urlset>")
        (self.site / "llms.txt").write_text("- Dev https://saveonsub.com/p/bundle-dev\n- AIPS https://saveonsub.com/p/aips-business-package\n")
        (self.site / "_redirects").write_text(REDIRECTS)

    def tearDown(self):
        shutil.rmtree(self.site)

    def test_unstaged_site_fails(self):
        errors = q.check(self.site)
        self.assertTrue(any("other-unit file" in e for e in errors))
        self.assertTrue(any("still references" in e for e in errors))

    def test_stage_removes_files_links_and_entries(self):
        self.assertEqual(q.stage(self.site), 3)
        self.assertEqual(q.check(self.site), [])
        bundles = (self.site / "c" / "bundles.html").read_text()
        self.assertIn('href="../p/bundle-dev"', bundles)
        self.assertIn('"position": 1, "url": "https://saveonsub.com/p/bundle-dev"', bundles)
        self.assertIn('"numberOfItems": 1', bundles)
        modes = (self.site / "modes.html").read_text()
        self.assertIn("modes/bundle-dev", modes)
        self.assertIn("team: 'bundle-dev'", modes)
        self.assertIn("bundle-dev", (self.site / "sitemap.xml").read_text())
        self.assertIn("bundle-dev", (self.site / "llms.txt").read_text())
        cat = (self.site / "assets" / "catalog.js").read_text()
        self.assertNotIn("aips-", cat)
        self.assertIn('"netflix"', cat)

    def test_counts_follow_catalog(self):
        q.stage(self.site)
        t = (self.site / "all.html").read_text()
        self.assertIn("All 2 Products", t)
        self.assertIn('"numberOfItems":2,', t)
        self.assertIn("2 subscriptions", t)

    def test_idempotent(self):
        q.stage(self.site)
        snap = {p: p.read_text() for p in self.site.rglob("*") if p.is_file()}
        q.stage(self.site)
        self.assertEqual(snap, {p: p.read_text() for p in self.site.rglob("*") if p.is_file()})

    def test_missing_redirect_fails(self):
        q.stage(self.site)
        (self.site / "_redirects").write_text("/home /index.html 301\n")
        self.assertTrue(any("_redirects" in e for e in q.check(self.site)))


if __name__ == "__main__":
    unittest.main()
