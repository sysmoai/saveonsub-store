"""Synthetic regression tests for issue #69 commercial HOLD."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from catalog_hold_gate import catalog_errors
import build_public_catalog

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


    def test_legacy_home_and_seo_generators_fail_without_side_effects(self):
        root = Path(__file__).resolve().parents[1]
        for filename in ("build_home.py", "build_seo.py"):
            with self.subTest(file=filename), tempfile.TemporaryDirectory() as tmp:
                result = subprocess.run(
                    [sys.executable, str(root / filename)],
                    cwd=tmp, capture_output=True, text=True, timeout=20
                )
                self.assertNotEqual(0, result.returncode)
                self.assertIn("retired under the commercial HOLD", result.stdout + result.stderr)
                self.assertEqual([], list(Path(tmp).iterdir()))

    def test_public_js_prunes_legacy_metadata_and_requires_inquiry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ops").mkdir()
            (root / "assets").mkdir()
            (root / "ops" / "PRICING-V2-2026-09-17.json").write_text(json.dumps(self.policy))
            example = copy.deepcopy(self.catalog)
            example["meta"].update({
                "brand": "SAVEONSUB", "currency": "BDT",
                "price_precedence": ["aips-live-jul26"], "usd_anchor_rate": 124
            })
            (root / "catalog.json").write_text(json.dumps(example))
            target = root / "assets" / "catalog.js"
            with patch.object(build_public_catalog, "ROOT", root), \
                 patch.object(build_public_catalog, "SRC", root / "catalog.json"), \
                 patch.object(build_public_catalog, "OUT", target):
                self.assertEqual(0, build_public_catalog.main())
            content = target.read_text(encoding="utf-8")
            self.assertIn('"sellability":"inquiry_only"', content)
            self.assertIn('"brand":"SAVEONSUB"', content)
            for banned in ("aips-live-jul26", "price_precedence", "usd_anchor_rate", '"bdt":'):
                self.assertNotIn(banned, content)

    def test_nested_bdt_field_cannot_overwrite_previous_safe_js(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ops").mkdir()
            (root / "assets").mkdir()
            (root / "ops" / "PRICING-V2-2026-09-17.json").write_text(json.dumps(self.policy))
            bad = copy.deepcopy(self.catalog)
            bad["products"][0]["extension"] = {"sale_price_bdt": 499}
            (root / "catalog.json").write_text(json.dumps(bad))
            target = root / "assets" / "catalog.js"
            target.write_text("previous-safe-output", encoding="utf-8")
            with patch.object(build_public_catalog, "ROOT", root), \
                 patch.object(build_public_catalog, "SRC", root / "catalog.json"), \
                 patch.object(build_public_catalog, "OUT", target):
                with self.assertRaisesRegex(SystemExit, "residual fixed-price fields"):
                    build_public_catalog.main()
            self.assertEqual("previous-safe-output", target.read_text(encoding="utf-8"))

    def test_rejected_non_hold_source_does_not_write_public_js(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ops").mkdir()
            (root / "assets").mkdir()
            (root / "ops" / "PRICING-V2-2026-09-17.json").write_text(json.dumps(self.policy))
            bad = copy.deepcopy(self.catalog)
            bad["products"][0]["plans"] = [{"bdt": 499}]
            (root / "catalog.json").write_text(json.dumps(bad))
            target = root / "assets" / "catalog.js"
            with patch.object(build_public_catalog, "ROOT", root), \
                 patch.object(build_public_catalog, "SRC", root / "catalog.json"), \
                 patch.object(build_public_catalog, "OUT", target):
                with self.assertRaises(SystemExit):
                    build_public_catalog.main()
            self.assertFalse(target.exists())

if __name__=="__main__":
    unittest.main()
