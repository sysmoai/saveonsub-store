"""/how-to-order must tell the same order story as home, product pages and refund terms."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
PAGES = {"how-to-order": "Confirm on WhatsApp before you pay", "bn/how-to-order": "পেমেন্টের আগে WhatsApp-এ নিশ্চিত করুন"}


def read(rel):
    return (SITE / f"{rel}.html").read_text(encoding="utf-8")


@unittest.skipUnless((SITE / "how-to-order.html").exists(), "run python build_site.py first")
class OrderSequence(unittest.TestCase):
    def main_text(self, rel):
        t = read(rel)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t[t.find("<main"):t.find("</main>")]))

    def test_written_confirmation_precedes_payment_then_verification_then_delivery(self):
        for rel, conf in PAGES.items():
            txt = self.main_text(rel)
            order = [txt.find(conf), txt.find("Send Money"), txt.find("মার্চেন্ট") if rel.startswith("bn/") else txt.find("merchant account"),
                     txt.find("ডেলিভারি ও সাপোর্ট") if rel.startswith("bn/") else txt.find("Delivery and support")]
            self.assertTrue(all(o >= 0 for o in order), (rel, order))
            self.assertEqual(order, sorted(order), rel)

    def test_no_minute_or_start_to_delivered_promise_anywhere_on_page(self):
        for rel in PAGES:
            t = read(rel)
            for bad in ("3 minutes", "৩ মিনিট", "3-Minute", "PT3M", "5–15", "৫–১৫", "start to delivered", "Instant products arrive"):
                self.assertNotIn(bad, t, f"{rel}: {bad}")

    def test_txn_id_or_screenshot_is_not_treated_as_payment(self):
        self.assertIn("A TxnID or screenshot alone is not payment", self.main_text("how-to-order"))
        self.assertIn("শুধু TxnID বা স্ক্রিনশট পেমেন্ট নয়", self.main_text("bn/how-to-order"))

    def test_payment_number_is_unchanged_and_shown_once(self):
        # same number the page showed before this change; the CEO-verified source decides any change
        self.assertEqual(self.main_text("how-to-order").count("+880 1305-869242"), 1)
        self.assertEqual(self.main_text("bn/how-to-order").count("+৮৮০ ১৩০৫-৮৬৯২৪২"), 1)

    def test_howto_schema_matches_visible_steps_and_has_no_total_time(self):
        for rel in PAGES:
            m = re.search(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "HowTo".*?)</script>', read(rel), re.S)
            self.assertIsNotNone(m, rel)
            d = json.loads(m.group(1))
            self.assertNotIn("totalTime", d)
            self.assertEqual(len(d["step"]), 5)
            self.assertEqual([s["position"] for s in d["step"]], [1, 2, 3, 4, 5])

    def test_links_in_page_body_are_clean(self):
        for rel in PAGES:
            t = read(rel)
            for href in re.findall(r'href="([^"]+)"', t[t.find("<main"):t.find("</main>")]):
                if href.startswith(("http", "mailto")):
                    continue
                self.assertNotIn(".html", href, f"{rel}: {href}")

    def test_home_and_product_pages_tell_the_same_story(self):
        home = read("index")
        self.assertIn("in writing before you pay", home)
        for rel, word in (("p/chatgpt-plus", "We verify, then activate"), ("bn/p/chatgpt-plus", "আমরা যাচাই করে অ্যাক্টিভেট করি")):
            self.assertIn(word, read(rel))


if __name__ == "__main__":
    unittest.main()
