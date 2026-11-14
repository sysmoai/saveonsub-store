"""Phone UX guards on the staged site: floating buttons, refund cards, 44 px targets."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


@unittest.skipUnless((SITE / "refund.html").exists(), "run python build_site.py first")
class MobileUx(unittest.TestCase):
    def test_every_fab_label_is_wrapped_and_named(self):
        bad = []
        for p in SITE.rglob("*.html"):
            t = p.read_text(encoding="utf-8")
            for m in re.finditer(r'<(?:a|button)\b[^>]*class="fab [^"]*"[^>]*>(.*?)</(?:a|button)>', t, re.S):
                tag = m.group(0)
                if 'class="fab-t"' not in tag or "aria-label=" not in tag:
                    bad.append(str(p.relative_to(SITE)))
        self.assertFalse(bad[:5], bad[:5])

    def test_phone_css_rules_present(self):
        css = (SITE / "assets" / "style.css").read_text(encoding="utf-8")
        for needle in (".fab.fab-away", "width: 48px", ".tbl.tbl-stack", "min-height: 44px"):
            self.assertIn(needle, css)

    def test_anchor_jumps_clear_the_sticky_nav(self):
        """Tapping the sticky buy bar's 'Plans' (#plans) used to put the first plan card under the 63px nav."""
        css = (SITE / "assets" / "style.css").read_text(encoding="utf-8")
        m = re.search(r"html\s*\{[^}]*scroll-padding-top:\s*(\d+)px", css)
        self.assertTrue(m, "html needs scroll-padding-top")
        self.assertGreaterEqual(int(m.group(1)), 70)  # nav is 63px
        page = (SITE / "p" / "chatgpt-plus.html").read_text(encoding="utf-8")
        self.assertIn('href="#plans"', page)
        self.assertIn('id="plans"', page)

    def test_app_js_hides_fab_on_scroll(self):
        js = (SITE / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("fab-away", js)

    def test_refund_tables_stack_with_labels_and_same_text(self):
        for rel in ("refund.html", "bn/refund.html"):
            t = (SITE / rel).read_text(encoding="utf-8")
            self.assertIn("tbl-stack", t, rel)
            self.assertGreaterEqual(t.count("data-label="), 16, rel)
            self.assertIn("<th>", t, rel)  # header row kept for screen readers and desktop

    def test_wa_number_unchanged_on_fabs(self):
        for p in SITE.rglob("*.html"):
            t = p.read_text(encoding="utf-8")
            for num in re.findall(r'class="fab fab-wa"[^>]*wa\.me/(\d+)', t):
                self.assertEqual(num, "8801305869242", str(p))


if __name__ == "__main__":
    unittest.main()
