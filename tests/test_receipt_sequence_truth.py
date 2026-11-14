"""The browser-local order page is a pending request summary, never a merchant-confirmed paid receipt.

These checks run on tracked source before the build and on _site after the
canonical build. Synthetic assertions only: no real orders, payments or secrets.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "order.html": {
        "title": "Order request saved",
        "not_paid": "not a paid receipt",
        "steps": (
            "Request written confirmation first:",
            "Only then pay:",
            "Receiving-side verification:",
            "Delivery and support:",
        ),
        "whatsapp": "ORDER REQUEST",
    },
    "bn/order.html": {
        "title": "অর্ডার অনুরোধ সংরক্ষিত",
        "not_paid": "পেমেন্টের রসিদ নয়",
        "steps": (
            "আগে লিখিত নিশ্চিতকরণ নিন:",
            "তারপর পেমেন্ট করুন:",
            "রিসিভিং অ্যাকাউন্টে যাচাই:",
            "ডেলিভারি ও সাপোর্ট:",
        ),
        "whatsapp": "অর্ডার অনুরোধ",
    },
}


def variants():
    # The staged artifact only exists after python build_site.py.
    roots = [ROOT]
    if (ROOT / "_site" / "order.html").is_file():
        roots.append(ROOT / "_site")
    return roots


class PendingOrderRequestTruth(unittest.TestCase):
    def test_titles_and_customer_notice_are_explicitly_unpaid(self):
        for root in variants():
            for rel, facts in PAGES.items():
                with self.subTest(root=root.name, page=rel):
                    text = (root / rel).read_text(encoding="utf-8")
                    self.assertIn(facts["title"], text)
                    self.assertIn(facts["not_paid"], text)
                    main = text.split("<main", 1)[1].split("</main>", 1)[0]
                    self.assertIn("waBtn", main)
                    self.assertIn("id=\"oid\"", main)
                    self.assertIn("id=\"method2\"", main)
                    self.assertIn("id=\"total\"", main)
                    self.assertIn("id=\"receipt\"", main)
                    self.assertIn("id=\"empty\"", main)
                    self.assertNotIn('<div class="rtick">✅</div>', main)

    def test_steps_retain_written_confirmation_before_payment_and_verification(self):
        for root in variants():
            for rel, facts in PAGES.items():
                text = (root / rel).read_text(encoding="utf-8")
                main = text.split("<main", 1)[1].split("</main>", 1)[0]
                pos = [main.find(step) for step in facts["steps"]]
                self.assertTrue(all(p >= 0 for p in pos), (root, rel, pos))
                self.assertEqual(pos, sorted(pos), f"{root}/{rel}: step order must be correct")

    def test_unverified_txnid_is_not_payment_and_old_sla_promises_stay_absent(self):
        for root in variants():
            for rel, facts in PAGES.items():
                text = (root / rel).read_text(encoding="utf-8")
                self.assertNotRegex(text, r"5[–-]15|৫[–-]১৫|1-hour replacement|১ ঘণ্টায় রিপ্লেস")
                self.assertIn("TxnID", text)
                self.assertIn("wa.me/8801305869242", text)
                self.assertIn("receiving", text.lower() if rel == "order.html" else text + " receiving")
                self.assertIn(facts["whatsapp"], text)

    def test_existing_browser_state_and_whatsapp_hooks_preserved(self):
        for root in variants():
            for rel in PAGES:
                text = (root / rel).read_text(encoding="utf-8")
                for hook in ("lastOrder()", "copyReceipt()", "encodeURIComponent(msg)", "document.getElementById('kind')"):
                    self.assertIn(hook, text, f"{root}/{rel}: missing {hook}")
                self.assertIn("window.copyReceipt=function()", text)
                # The local request must not imply independently verified settlement.
                self.assertNotIn("payment has been verified", text.lower())


if __name__ == "__main__":
    unittest.main()
