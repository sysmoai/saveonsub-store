"""SOS-PRICE-001 REV2: CEO-approved 3-plan SaveOnSub ChatGPT Plus regression.

The CEO commercial decision does not grant vendor permission to share accounts.
The site must describe shared access clearly, with exact provider restriction,
privacy risk and no personal/team authorization claims.
"""
import json
import unittest
from pathlib import Path

from apply_pricing_v2 import public_plan
from catalog_hold_gate import approved_plans
from commercial_truth_v2 import product_main
from catalog_reconcile import plan_status

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"

EXPECTED = [
    ("Starter Shared (6–8 users)", 499, "1 month", "shared"),
    ("Premium Shared (2–3 users)", 999, "1 month", "shared"),
    ("Personal (your email)", 3390, "1 month", "personal"),
]


class ChatGPTPlusCEOApprovalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.rule = cls.policy["approved_products"]["chatgpt-plus"]
        cls.projections = [public_plan(p) for p in cls.rule["plans"]]

    def test_three_ceo_approved_prices_and_duration(self):
        self.assertEqual("fixed", self.rule["mode"])
        self.assertEqual(EXPECTED, [
            (p["label"], p["bdt"], p["duration"], p["access_type"])
            for p in self.rule["plans"]])
        self.assertEqual("SOS-PRICE-001-REV2",
                         self.rule["latest_ceo_amendment"]["decision_id"])
        self.assertEqual([499, 999, 3390],
                         [p["bdt"] for p in self.projections])
        self.assertTrue(all(p["billing_unit"] == "month" for p in self.projections))

    def test_shared_prices_active_in_public_projection_without_hold(self):
        self.assertNotIn("held_plans", self.rule)
        self.assertEqual([
            ("Starter Shared (6–8 users)", 499),
            ("Premium Shared (2–3 users)", 999),
            ("Personal (your email)", 3390),
        ], approved_plans(self.policy)["chatgpt-plus"])
        self.assertEqual(["shared", "shared", "personal"],
                         [p["type"] for p in self.projections])
        self.assertEqual(3,
                         self.policy["commercial_hold"]["latest_scope_override"]["active_plans"])
        self.assertEqual(0,
                         self.policy["commercial_hold"]["latest_scope_override"]["held_plans"])

    def test_totals_and_business_unit_scope(self):
        count = sum(len(rule.get("plans") or [])
                    for rule in self.policy["approved_products"].values()
                    if rule.get("mode") == "fixed")
        self.assertEqual(133, count)
        self.assertEqual(count, self.policy["commercial_hold"]["approved_sku_count"])
        self.assertEqual(131, self.policy["commercial_hold"]["previous_approved_plan_count"])
        self.assertEqual(77, len(self.policy["approved_products"]))
        self.assertTrue(all(rule["mode"] == "inquiry"
                            for pid, rule in self.policy["approved_products"].items()
                            if pid.startswith("aips-")))

    def test_earlier_hold_decision_retained_as_superseded_history(self):
        history = self.rule["decision_history"]
        self.assertTrue(any(h.get("disposition") == "SUPERSEDED_BY_CEO_CORRECTION"
                            and h.get("superseded_by") == "SOS-PRICE-001-REV2"
                            for h in history))
        self.assertIn("2990", " ".join(history[-1].get("changed_fields", [])))

    def test_vendor_restriction_and_financial_evidence_separate(self):
        amendment = self.rule["latest_ceo_amendment"]
        self.assertEqual("CONFLICTED_PROVIDER_ACCOUNT_SHARING_POLICY",
                         amendment["provider_permission"])
        self.assertEqual("UNVERIFIED_INVOICE_REQUIRED",
                         amendment["vat_invoice_status"])
        self.assertEqual("UNVERIFIED_TOTAL_EXPENSES_REQUIRED",
                         amendment["unit_economics_status"])
        self.assertEqual("REVIEW_BRANCH_ONLY_NO_DEPLOY",
                         amendment["release_scope"])
        self.assertEqual(["CONFLICTED_PROVIDER_TERMS_REVIEW",
                          "CONFLICTED_PROVIDER_TERMS_REVIEW",
                          "UNKNOWN_VERIFY_ACTIVATION_METHOD"],
                         [plan_status(p) for p in self.rule["plans"]])

    def test_customer_facing_en_bn_prices_and_policy_warning(self):
        product = {
            "id": "chatgpt-plus", "name": "ChatGPT Plus",
            "category": "AI Assistants",
            "plans": self.projections, "request_price": False,
            "official_url": "https://chatgpt.com/",
        }
        en = product_main(product, False)
        bn = product_main(product, True)
        for page in (en, bn):
            for amount in ("৳499", "৳999", "৳3,390"):
                self.assertIn(amount, page)
            self.assertEqual(3, page.count("cartAdd("))
            self.assertIn('data-provider-policy-disclosure="account-sharing"', page)
            self.assertIn("https://help.openai.com/en/articles/10471989-openai-account-sharing-policy", page)
        self.assertIn("OpenAI does not permit sharing individual accounts", en)
        self.assertIn("এটি OpenAI অনুমোদিত individual বা Team seat নয়", bn)
        self.assertIn('class="tos shared"', en)
        self.assertIn('class="tos personal"', en)
        self.assertNotIn("This listing is not a credential-sharing offer", en)
        self.assertNotIn("7-day guarantee", en)

    def test_review_only_no_publication(self):
        self.assertEqual("REVIEW_NOT_PUBLISHED",
                         self.policy["commercial_hold"]["latest_scope_override"]["release_state"])


if __name__ == "__main__":
    unittest.main()
