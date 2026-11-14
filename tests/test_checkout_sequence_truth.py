"""Checkout must tell the confirm-before-pay story without adding or removing a receiving instruction."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
NUM = "+880 1305-869242"
PAGES = ("checkout", "bn/checkout")


def box(rel):
    t = (SITE / f"{rel}.html").read_text(encoding="utf-8")
    return t[t.find('id="paybox"'): t.find("<!-- RIGHT")]


@unittest.skipUnless((SITE / "checkout.html").exists(), "run python build_site.py first")
class CheckoutSequence(unittest.TestCase):
    def test_whatsapp_confirmation_precedes_the_payment_number_and_payment_is_gated(self):
        for rel in PAGES:
            b = box(rel)
            self.assertLess(b.find("confirmWA()"), b.find("<details"), rel)
            self.assertLess(b.find("<details"), b.find(NUM), rel)
            self.assertNotIn("<details open", b, rel)

    def test_number_is_the_same_one_and_shown_once(self):
        for rel in PAGES:
            self.assertEqual(box(rel).count(NUM), 1, rel)
        # the same number as in the unchanged source pages
        for rel in PAGES:
            self.assertIn(NUM, (ROOT / f"{rel}.html").read_text(encoding="utf-8"))

    def test_inline_script_hooks_survive(self):
        for rel in PAGES:
            b = box(rel)
            for i in ("oid", "oid2", "paymethod", "payamount", "txn", "pb-bKash", "pb-Nagad", "pb-Rocket"):
                self.assertEqual(b.count(f'id="{i}"'), 1, f"{rel}: {i}")
            self.assertIn("setPay(", b)
            self.assertIn("copyText(OID", b)

    def test_no_automatic_settlement_or_screenshot_as_payment_claim(self):
        en, bn = box("checkout"), box("bn/checkout")
        self.assertIn("A TxnID or screenshot alone is not payment", en)
        self.assertIn("শুধু TxnID বা স্ক্রিনশট পেমেন্ট নয়", bn)
        self.assertIn("actual incoming credit in the authorized receiving account", en)
        self.assertIn("আসল ইনকামিং টাকা", bn)
        for t in (en, bn):
            visible = re.sub(r"<[^>]+>", " ", t).lower()
            self.assertNotRegex(visible, r"merchant|automatic|instant|settled automatically")

    def test_heading_has_no_time_promise(self):
        for rel in PAGES:
            t = (SITE / f"{rel}.html").read_text(encoding="utf-8")
            m = t[t.find("<main"): t.find("</main>")]
            self.assertNotIn("60 seconds", m)
            self.assertNotIn("৬০ সেকেন্ড", m)

    def test_existing_handoff_regression_still_passes_on_source(self):
        r = subprocess.run(["python", "-m", "unittest", "tests.test_checkout_wa_handoff"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
