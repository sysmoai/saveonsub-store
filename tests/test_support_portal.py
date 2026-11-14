"""support_portal.py: noindex, inert-by-default, no prices/claims, separation of AI training, safe JS."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


def main_text(rel):
    h = (SITE / rel).read_text(encoding="utf-8")
    m = re.search(r"<main.*?</main>", h, re.S)
    return h, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(0)))


class SupportPortal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (SITE / "bn" / "refund.html").exists():
            raise unittest.SkipTest("build _site first")
        subprocess.run([sys.executable, str(ROOT / "support_portal.py")], check=True, capture_output=True)

    def test_noindex_and_not_in_sitemap(self):
        for rel in ("bn/support.html", "support.html"):
            h, _ = main_text(rel)
            self.assertRegex(h, r'name="robots" content="noindex,nofollow')
        sm = SITE / "sitemap.xml"
        if sm.exists():
            self.assertNotRegex(sm.read_text(encoding="utf-8"), r"/support<")

    def test_inert_until_configured_and_config_untouched(self):
        cfg = (ROOT / "assets" / "order-config.js").read_text()
        self.assertIn('apiBase: ""', cfg)
        js = (ROOT / "assets" / "support-portal.js").read_text()
        self.assertIn("if (!live)", js)
        self.assertIn("el.disabled = true", js)

    def test_ai_training_is_separate_and_unpriced(self):
        for rel in ("bn/support.html", "support.html"):
            h, t = main_text(rel)
            self.assertIn('value="ai_training_inquiry"', h)
            self.assertNotRegex(t, r"৳|BDT|Tk\b|\$\d")
            self.assertNotRegex(t.lower(), r"guarantee|গ্যারান্টি|within \d+ (minutes|hours)|merchant")
        _, bn = main_text("bn/support.html")
        self.assertIn("আলাদা, ঐচ্ছিক সার্ভিস", bn)
        self.assertIn("ট্র্যাকিং কোড নেই", bn)

    def test_secrets_are_never_persisted_or_put_in_urls(self):
        js = (ROOT / "assets" / "support-portal.js").read_text()
        for bad in ("localStorage", "sessionStorage", "document.cookie", "innerHTML", "eval("):
            self.assertNotIn(bad, js)
        self.assertIn('"x-ticket-token"', js)
        self.assertIn('credentials: "omit"', js)

    def test_mobile_friendly_controls(self):
        h, _ = main_text("bn/support.html")
        self.assertIn('name="viewport"', h)
        self.assertIn("min-height:44px", h)
        self.assertIn('lang="bn"', h)

    def test_check_mode_passes(self):
        r = subprocess.run([sys.executable, str(ROOT / "support_portal.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
