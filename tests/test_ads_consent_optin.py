"""Static regression gates for SaveOnSub measurement choice boundaries.

CEO decision 2026-11-12: no on-page cookie banner. Measurement is on by default,
disclosed on /privacy, with a persistent opt-out there. GPC / Do Not Track always
win. These checks supplement real-browser network inspection; no external
trackers or production systems are contacted.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AdsConsentChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pixel = (ROOT / "assets" / "meta-pixel.js").read_text(encoding="utf-8")
        cls.ga4 = (ROOT / "assets" / "ga4.js").read_text(encoding="utf-8")
        cls.privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
        cls.privacy_bn = (ROOT / "bn" / "privacy.html").read_text(encoding="utf-8")

    def test_no_banner(self):
        self.assertNotIn("sos-ads-consent", self.pixel)
        self.assertNotIn("showNotice", self.pixel)

    def test_gpc_and_dnt_always_win(self):
        for src in (self.pixel, self.ga4):
            self.assertIn("nav.globalPrivacyControl === true || nav.doNotTrack === '1'", src)

    def test_opt_out_blocks_pixel_and_ga(self):
        self.assertIn("function allowed(){ return getConsent() !== 'denied'; }", self.pixel)
        self.assertIn("if(loaded || !allowed()) return;", self.pixel)
        self.assertIn("if(!loaded || !window.fbq || !allowed()) return;", self.pixel)
        self.assertIn("if(!loaded || getConsent() === 'denied') return;", self.ga4)
        self.assertIn("gtag('consent', 'update', {analytics_storage: 'denied'})", self.ga4)

    def test_privacy_pages_offer_opt_out_and_opt_in(self):
        for page in (self.privacy, self.privacy_bn):
            self.assertIn("sosAdsOptOut()", page)
            self.assertIn("sosAdsOptIn()", page)


if __name__ == "__main__":
    unittest.main()
