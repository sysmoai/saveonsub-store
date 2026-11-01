"""T018-01/03/04: policy audit and shared-offer check fail closed."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import audit_policy  # noqa: E402
import shared_copy_check  # noqa: E402

HOLD_POLICY = {"commercial_hold": {"status": "HOLD"}, "ai_categories": ["ai-assistants"],
               "approved_products": {"google-ai-pro": {"mode": "inquiry", "plans": []},
                                     "chatgpt-plus": {"mode": "inquiry", "plans": []}}}


def product(pid, plans=(), request_price=True, category="ai-assistants"):
    return {"id": pid, "category": category, "plans": list(plans), "request_price": request_price}


class PolicyAuditTest(unittest.TestCase):
    def catalog(self, *extra):
        return {"products": [product("google-ai-pro"), product("chatgpt-plus"), *extra]}

    def test_repository_catalog_and_policy_pass(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "ops/PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
        self.assertEqual(audit_policy.audit(catalog, policy), [])

    def test_repository_catalog_is_hold(self):
        products = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))["products"]
        self.assertTrue(all(p.get("request_price") and not p.get("plans") for p in products))

    def test_priced_product_during_hold_fails(self):
        bad = product("netflix", [{"label": "Mobile", "bdt": 349}], False, "entertainment")
        self.assertTrue(audit_policy.audit(self.catalog(bad), HOLD_POLICY))

    def test_locked_skus_cannot_be_priced_even_without_hold(self):
        policy = dict(HOLD_POLICY, commercial_hold={})
        catalog = {"products": [product("google-ai-pro", [{"label": "1m", "bdt": 3390}], False), product("chatgpt-plus")]}
        self.assertTrue(any("google-ai-pro" in x for x in audit_policy.audit(catalog, policy)))

    def test_request_price_outside_allowlist_fails_without_hold(self):
        policy = dict(HOLD_POLICY, commercial_hold={})
        issues = audit_policy.audit(self.catalog(product("netflix", category="entertainment")), policy)
        self.assertTrue(any("allowlist" in x for x in issues))

    def test_cost_fields_fail(self):
        policy = json.loads(json.dumps(HOLD_POLICY))
        policy["approved_products"]["chatgpt-plus"]["purchase_cost"] = 1
        self.assertTrue(any("cost/margin" in x for x in audit_policy.audit(self.catalog(), policy)))


class SharedOfferTest(unittest.TestCase):
    def test_shared_labels_and_types_are_detected(self):
        products = [product("envato", [{"label": "Shared", "bdt": 1}]),
                    product("spotify", [{"label": "Family slot (your account)", "bdt": 1}]),
                    product("netflix", [{"label": "1 Screen (private profile)", "bdt": 1}]),
                    product("x", [{"label": "Plan", "bdt": 1, "type": "shared-low"}]),
                    product("ok", [{"label": "Pro — 1 Month", "bdt": 1, "type": "personal"}])]
        self.assertEqual(len(shared_copy_check.shared_plans(products)), 4)

    def test_repository_catalog_has_no_shared_plan(self):
        products = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))["products"]
        self.assertEqual(shared_copy_check.shared_plans(products), [])


if __name__ == "__main__":
    unittest.main()
