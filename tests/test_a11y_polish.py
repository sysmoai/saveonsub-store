"""Tests for a11y_polish.py (fixture site, no real build)."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import a11y_polish as ap  # noqa: E402


class A11yPolish(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.site = self.tmp / "_site"
        (self.site / "bn").mkdir(parents=True)
        (self.site / "a.html").write_text(
            '<h2>Plans &amp; <b>prices</b></h2><div class="tbl"><table></table></div>'
            '<div class="tbl wide" id="x"><table></table></div>', encoding="utf-8")
        (self.site / "bn" / "b.html").write_text('<div class="tbl"><table></table></div>', encoding="utf-8")
        (self.site / "c.html").write_text('<div class="tblx"></div><div class="card"></div>', encoding="utf-8")
        self.old = ap.SITE
        ap.SITE = self.site

    def tearDown(self):
        ap.SITE = self.old
        shutil.rmtree(self.tmp)

    def test_check_fails_before_fix_and_passes_after(self):
        self.assertEqual(ap.main(["--check"]), 1)
        self.assertEqual(ap.main([]), 0)
        self.assertEqual(ap.main(["--check"]), 0)

    def test_labels_and_attributes(self):
        ap.main([])
        a = (self.site / "a.html").read_text(encoding="utf-8")
        self.assertEqual(a.count('tabindex="0" role="region"'), 2)
        self.assertIn('aria-label="Plans &amp; prices"', a)
        self.assertIn('<div class="tbl wide" id="x" tabindex="0"', a)
        b = (self.site / "bn" / "b.html").read_text(encoding="utf-8")
        self.assertIn('aria-label="তুলনার টেবিল"', b)

    def test_idempotent_and_ignores_other_classes(self):
        ap.main([])
        once = (self.site / "a.html").read_text(encoding="utf-8")
        ap.main([])
        self.assertEqual(once, (self.site / "a.html").read_text(encoding="utf-8"))
        self.assertNotIn("tabindex", (self.site / "c.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
