"""V22: the floating WhatsApp button must carry a singly-encoded message.

commercial_truth_v2.sanitize_common() turns the legacy onclick button into an
anchor. The onclick URL is already percent-encoded, so encoding it again showed
customers "Hi!%20I%20want…" (href contained %2520) on 9 pages.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

from commercial_truth_v2 import sanitize_common

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ('<button class="fab fab-wa" onclick="location.href=\'https://wa.me/8801305869242'
          '?text=Hi!%20I%20want%20to%20order%20from%20SAVEONSUB\'" aria-label="WhatsApp">💬 WhatsApp</button>')


class WhatsAppFabEncoding(unittest.TestCase):
    def test_legacy_button_is_encoded_once(self):
        out = sanitize_common(LEGACY)
        href = re.search(r'<a class="fab fab-wa" href="([^"]+)"', out).group(1)
        self.assertNotIn("%25", href)
        self.assertEqual(unquote(href.split("?text=", 1)[1]), "Hi! I want to order from SAVEONSUB")

    def test_plain_text_message_still_encoded(self):
        out = sanitize_common(LEGACY.replace("Hi!%20I%20want%20to%20order%20from%20SAVEONSUB", "Hi there & more"))
        href = re.search(r'<a class="fab fab-wa" href="([^"]+)"', out).group(1)
        self.assertIn("Hi%20there%20%26%20more", href.replace("&amp;", "&"))

    def test_staged_site_has_no_double_encoded_whatsapp_link(self):
        site = ROOT / "_site"
        if not site.is_dir():
            self.skipTest("_site not built (pre-build phase); the unit tests above still run")
        bad = [p.relative_to(site).as_posix() for p in site.rglob("*.html")
               if re.search(r'wa\.me/\d+\?text=[^"\']*%25(?:20|21|3A)', p.read_text(encoding="utf-8", errors="ignore"))]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
