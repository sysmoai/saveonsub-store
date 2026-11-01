"""Synthetic regression tests for issue #69 commercial HOLD."""
import copy
import unittest
from catalog_hold_gate import catalog_errors

class CatalogHoldGateTests(unittest.TestCase):
    def setUp(self):
        self.policy={"revision":"test", "commercial_hold":{"status":"HOLD"}}
        self.product={"id":"synthetic", "status":"live", "bestseller_rank":1,
                      "plans":[], "request_price":True,
                      "pricing_status":"price-review-required",
                      "pricing_revision":"test", "commercial_hold":"EXEC-010"}
        self.catalog={"meta":{"commercial_revision":"test"}, "products":[self.product]}

    def test_hold_allows_historical_live_status(self):
        self.assertEqual([], catalog_errors(self.catalog,self.policy))

    def test_stale_price_blocked(self):
        self.product["plans"]=[{"bdt":500}]
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_missing_hold_blocked(self):
        self.product.pop("commercial_hold")
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_duplicate_product_blocked(self):
        self.catalog["products"].append(copy.deepcopy(self.product))
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_malformed_plan_blocked(self):
        self.product["plans"]=None
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_approved_sellable_blocked(self):
        self.product["approved_sellable"]=True
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_revision_drift_blocked(self):
        self.product["pricing_revision"]="stale"
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_non_hold_policy_requires_new_review(self):
        self.policy["commercial_hold"]["status"]="APPROVED"
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_derived_price_blocked(self):
        self.product["from_bdt"]=499
        self.assertTrue(catalog_errors(self.catalog,self.policy))

    def test_real_review_catalog(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        catalog=json.loads((root/"catalog.json").read_text(encoding="utf-8"))
        policy=json.loads((root/"ops/PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
        self.assertEqual([],catalog_errors(catalog,policy))
        self.assertEqual(72,len(catalog["products"]))
        self.assertEqual(0,sum(len(p["plans"]) for p in catalog["products"]))

if __name__=="__main__":
    unittest.main()
