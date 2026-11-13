"""Tests for motion_polish.py and category_copy_polish.py (string fixtures, no build)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import category_copy_polish as cc  # noqa: E402
import motion_polish as mp  # noqa: E402


class MotionHome(unittest.TestCase):
    def test_home_gets_fx_rail_facts_without_prices(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "index.html"
            f.write_text('<header class="hero" id="main"><h1>ChatGPT and more. Pay in taka.</h1>'
                         '<div class="price">From ৳499</div></header><section>x</section>', encoding="utf-8")
            text, changed = mp.home(f, False, [("chatgpt-plus", "ChatGPT Plus"), ("canva-pro", "Canva <Pro>")], 13)
        self.assertTrue(changed)
        self.assertIn('class="hero-fx"', text)
        self.assertIn('<span class="hl">Pay in taka.</span>', text)
        self.assertIn('href="p/chatgpt-plus"', text)
        self.assertIn("Canva &lt;Pro&gt;", text)
        self.assertIn('data-count="2"', text)
        rail = text[text.index('class="brandrail"'):text.index('class="factband"')]
        self.assertNotIn("৳", rail)
        self.assertIn('tabindex="-1"', rail)  # loop copy is not a second tab stop

    def test_bn_facts_use_bengali_digits(self):
        self.assertIn(">৬৭<", mp.facts(67, 13, True))


class CategoryCopy(unittest.TestCase):
    PAGE = ('<h1>AI Assistants</h1>\n  <p class="sub mt2">Official plans need a card at ~৳2,200/mo.</p>\n'
            '  <p class="sub" style="font-size:14px">🏷️ Honest labels: <span class="tos official">official</span>'
            ' <span class="tos shared-med">shared·covered</span></p>\n'
            '<div class="grid"><a class="pcard" href="../p/x"><div class="price">থেকে ৳499</div></a></div>')

    def test_intro_and_legend_replaced_cards_kept(self):
        out, n = cc.process(self.PAGE, "ai-assistants", False)
        self.assertGreaterEqual(n, 2)
        self.assertNotIn("2,200", out)
        self.assertNotIn("shared·covered", out)
        self.assertIn('class="pcard"', out)
        self.assertIn(cc.MARK, out)

    def test_bn_price_word_order(self):
        out, _ = cc.process(self.PAGE, "ai-assistants", True)
        self.assertIn('<div class="price">৳499 থেকে</div>', out)

    def test_idempotent(self):
        once, _ = cc.process(self.PAGE, "ai-assistants", False)
        self.assertEqual(cc.process(once, "ai-assistants", False), (once, 0))


if __name__ == "__main__":
    unittest.main()
