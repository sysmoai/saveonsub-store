"""Regression tests for the EXEC-010 HOLD content price guard (synthetic HTML only)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import hold_content_price_guard as g  # noqa: E402


class SanitizeRemovesSaleprices(unittest.TestCase):
    def test_plain_sale_price_replaced_and_comma_kept(self):
        out = g.sanitize("Bundles: Student ৳449, Research ৳600/mo, Business ৳1,299.")
        self.assertEqual("Bundles: Student price on request, Research price on request, Business price on request.", out)
        self.assertEqual([], g.residues(out))

    def test_google_ai_pro_headline_rewritten(self):
        html = '<h1>Google AI Pro at <span class="grad-text">৳500</span> — how is it possible?</h1>'
        out = g.sanitize(html)
        self.assertNotIn("৳500", out)
        self.assertIn("honest explainer", out)

    def test_shared_chatgpt_seat_is_never_advertised(self):
        html = ("Via SAVEONSUB: shared seat ৳499/month or personal account ৳2,990/month, paid with bKash/Nagad."
                '<td><a href="../p/chatgpt-plus">Shared seat (6–8 users)</a></td><td>৳499/mo</td>')
        out = g.sanitize(html)
        self.assertNotIn("৳", out)
        self.assertIn("does not sell shared ChatGPT seats", out)
        self.assertIn("not offered (HOLD)", out)
        self.assertNotIn("shared seat price on request", out.lower())

    def test_bangla_digits_free_text_untouched(self):
        self.assertEqual("দাম জানতে WhatsApp করুন", g.sanitize("দাম জানতে WhatsApp করুন"))


class OfficialAndMarketFactsPreserved(unittest.TestCase):
    def test_official_provider_prices_kept(self):
        cases = [
            "Officially $20/month (~৳2,200)",
            "Spotify Individual ৳219 · Student ৳109 · Duo ৳299 · Family ৳379",
            "৳219/month individual, ৳109 student, ৳299 duo, ৳379 family",
            "Spotify BD student is ৳109 official",
            "Google lists it at ৳2,500/month in Bangladesh.",
            "BD market (surveyed) ৳1,299–13,000",
            'opts:[["low","Under ৳500"],["mid","৳500 – ৳1,000"],["high","৳1,000+"]]',
            '"Lifetime ChatGPT ৳999" (no such thing exists)',
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(text, g.sanitize(text))
                self.assertEqual([], g.residues(text))

    def test_official_word_only_protects_its_own_amount(self):
        out = g.sanitize("No ads → slot ৳129 or official ৳219")
        self.assertEqual("No ads → slot price on request or official ৳219", out)


class GateFailsClosed(unittest.TestCase):
    def test_residue_detected(self):
        self.assertTrue(g.residues("<p>We sell it at ৳500 on your own Gmail</p>"))

    def test_check_mode_fails_on_temp_site(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "blog").mkdir()
            (site / "blog" / "x.html").write_text("<p>Canva ৳299/mo</p>", encoding="utf-8")
            old = g.SITE
            g.SITE = site
            try:
                self.assertEqual(1, g.main(["--check"]))
                self.assertEqual(0, g.main([]))
                self.assertEqual(0, g.main(["--check"]))
                expected = g.UNLOCK_REPLACEMENT if g.unlock_book() is not None else g.REPLACEMENT
                self.assertIn(expected, (site / "blog" / "x.html").read_text(encoding="utf-8"))
            finally:
                g.SITE = old


if __name__ == "__main__":
    unittest.main()
