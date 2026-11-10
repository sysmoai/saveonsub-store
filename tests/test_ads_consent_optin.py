"""Static regression gates for SaveOnSub measurement consent boundaries.

These checks supplement, but do not replace, real-browser network inspection.
No external trackers or production systems are contacted.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AdsConsentOptInTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pixel = (ROOT / "assets" / "meta-pixel.js").read_text(encoding="utf-8")
        cls.ga4 = (ROOT / "assets" / "ga4.js").read_text(encoding="utf-8")

    def test_pixel_not_loaded_without_explicit_grant(self):
        self.assertNotIn("CONSENT_MODE = 'notice'", self.pixel)
        self.assertIn("if(c === 'granted') loadPixel();", self.pixel)
        self.assertIn("if(loaded || getConsent() !== 'granted') return;", self.pixel)

    def test_pixel_events_require_current_grant(self):
        self.assertIn("if(!loaded || !window.fbq || getConsent() !== 'granted') return;", self.pixel)
        self.assertIn("if(loaded && window.fbq) window.fbq('consent', 'revoke');", self.pixel)

    def test_change_choice_revokes_until_new_approval(self):
        self.assertIn("localStorage.removeItem(CONSENT_KEY)", self.pixel)
        self.assertIn("announce('denied');", self.pixel)
        self.assertIn("else loadPixel();", self.pixel)

    def test_ga4_needs_grant_and_can_regrant_after_revocation(self):
        self.assertIn("if(getConsent() === 'granted') loadGa();", self.ga4)
        self.assertIn("if(loaded) gtag('consent', 'update', {analytics_storage: 'granted'});", self.ga4)
        self.assertIn("gtag('consent', 'update', {analytics_storage: 'denied'})", self.ga4)


if __name__ == "__main__":
    unittest.main()
