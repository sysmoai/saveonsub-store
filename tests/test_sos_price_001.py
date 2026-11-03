"""SOS-PRICE-001: CEO 2026-11-03 scoped ChatGPT Plus decision regression.

Commercial approval is distinct from provider permission, supplier invoice and fulfillment.
No production access or customer records are needed to test this source contract.
"""
import json
import unittest
from pathlib import Path

from apply_pricing_v2 import public_plan
from catalog_hold_gate import approved_plans

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"


class ChatGPTPlusScopedApprovalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.rule = cls.policy["approved_products"]["chatgpt-plus"]

    def test_personal_price_and_duration_are_ceo_approved(self):
        self.assertEqual("fixed", self.rule["mode"])
        self.assertEqual([("Personal (your email)", 3390, "1 month", "personal")],
                         [(p["label"], p["bdt"], p["duration"], p["access_type"])
                          for p in self.rule["plans"]])
        self.assertEqual("SOS-PRICE-001", self.rule["latest_ceo_amendment"]["decision_id"])
        projected = public_plan(self.rule["plans"][0])
        self.assertEqual((3390, "personal", "month"),
                         (projected["bdt"], projected["type"], projected["billing_unit"]))

    def test_shared_options_held_and_not_in_public_projection(self):
        self.assertEqual({499, 999}, {p["bdt"] for p in self.rule["held_plans"]})
        self.assertTrue(all(p["commercial_status"] == "HOLD"
                            and p["access_type"] == "shared"
                            and p["release_allowed"] is False
                            for p in self.rule["held_plans"]))
        self.assertEqual([("Personal (your email)", 3390)],
                         approved_plans(self.policy)["chatgpt-plus"])
        self.assertFalse(any(p["access_type"] == "shared" for p in self.rule["plans"]))

    def test_pricebook_total_counts_and_brand_isolation(self):
        plans = sum(len(rule.get("plans") or [])
                    for rule in self.policy["approved_products"].values()
                    if rule.get("mode") == "fixed")
        self.assertEqual(131, plans)
        self.assertEqual(plans, self.policy["commercial_hold"]["approved_sku_count"])
        self.assertEqual(133, self.policy["commercial_hold"]["previous_approved_plan_count"])
        self.assertTrue(all(rule["mode"] == "inquiry"
                            for pid, rule in self.policy["approved_products"].items()
                            if pid.startswith("aips-")))

    def test_financial_truth_gates_and_historical_price(self):
        amendment = self.rule["latest_ceo_amendment"]
        self.assertEqual("UNVERIFIED_INVOICE_REQUIRED", amendment["vat_invoice_status"])
        self.assertEqual("UNVERIFIED_TOTAL_EXPENSES_REQUIRED", amendment["unit_economics_status"])
        self.assertEqual("UNVERIFIED", amendment["provider_permission"])
        self.assertIn("2990", " ".join(amendment["changed_fields"]))
        self.assertEqual("REVIEW_NOT_PUBLISHED",
                         self.policy["commercial_hold"]["latest_scope_override"]["release_state"])

    def test_no_provider_resale_authorization_is_inferred(self):
        self.assertEqual("UNVERIFIED", self.rule["latest_ceo_amendment"]["provider_permission"])
        self.assertEqual("REVIEW_BRANCH_ONLY_NO_DEPLOY",
                         self.rule["latest_ceo_amendment"]["release_scope"])


if __name__ == "__main__":
    unittest.main()
