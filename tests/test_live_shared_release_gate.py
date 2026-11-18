"""Offline synthetic validation of the live shared-SKU release acceptance gate."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import apply_pricing_v2
import verify_production_shared_skus as gate


ROOT = Path(__file__).resolve().parents[1]


class LiveSharedReleaseGate(unittest.TestCase):
    def test_shared_only_inquiry_projection_carries_held_notice_metadata(self):
        """The 16 shared-only product groups must not lose their HOLD notice."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ops").mkdir()
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps({"products": [
                {"id": "demo", "category": "ai-assistants", "plans": []}
            ]}), encoding="utf-8")
            policy_path = root / "ops" / "PRICING-V2-2026-09-17.json"
            policy_path.write_text(json.dumps({
                "revision": "fixture",
                "ai_categories": ["ai-assistants"],
                "commercial_hold": {
                    "status": "SELECTIVE_UNLOCK", "authority": "synthetic",
                    "approved_sku_count": 1
                },
                "approved_products": {"demo": {"mode": "fixed", "plans": [
                    {"plan_id": "shared-demo", "label": "Demo Shared",
                     "bdt": 10, "access_type": "shared"}
                ]}}
            }), encoding="utf-8")
            (root / "ops" / "HELD-PLANS-2026-11-14.json").write_text(
                json.dumps({"held_plans": {"demo": ["shared-demo"]}}),
                encoding="utf-8")
            with patch.object(apply_pricing_v2, "CATALOG_PATH", catalog_path), \
                 patch.object(apply_pricing_v2, "POLICY_PATH", policy_path):
                self.assertEqual(0, apply_pricing_v2.main())
            product = json.loads(catalog_path.read_text(encoding="utf-8"))["products"][0]
            self.assertEqual([], product["plans"])
            self.assertTrue(product["request_price"])
            self.assertEqual("shared-demo", product["held_plans"][0]["plan_id"])

    def test_current_inventory_all_shared_are_held_by_effective_policy(self):
        inventory = gate.restricted_inventory()
        self.assertEqual(43, len(inventory))
        self.assertEqual(57, sum(map(len, inventory.values())))

    def test_approved_personal_card_with_held_notice_passes(self):
        html = '<link rel="canonical" href="https://saveonsub.com/p/demo">' + \
               '<div data-held-plans="1">Shared unavailable</div>' + \
               '<button onclick="cartAdd(&quot;demo&quot;,&quot;Personal&quot;,100,&quot;Demo&quot;,&quot;personal-id&quot;)"></button>'
        self.assertEqual([], gate.validate_product_html("demo", html, {"shared-id"}, [], {"personal-id": ("Personal", 100)}))

    def test_old_shared_sku_is_never_accepted(self):
        html = '<link rel="canonical" href="https://saveonsub.com/p/demo">' + \
               '<div data-held-plans="1"></div>' + \
               '<button onclick="cartAdd(\'demo\',\'Shared\',1,\'Demo\',\'shared-id\')"></button>'
        issues = gate.validate_product_html("demo", html, {"shared-id"})
        self.assertTrue(any("restricted SKU" in x for x in issues))

    def test_missing_notice_or_wrong_product_fails_closed(self):
        issues = gate.validate_product_html("demo", '<h1>unrelated</h1>', {"shared-id"})
        self.assertTrue(any("missing visible held-plan notice" in x for x in issues))
        self.assertTrue(any("route/content mismatch" in x for x in issues))

    def test_shared_plan_badge_fails_closed(self):
        html = '<link href="/p/demo"><div data-held-plans="1"></div>' + \
               '<span class="tos shared">Shared account</span>'
        self.assertTrue(gate.validate_product_html("demo", html, {"shared-id"}))

    def test_price_list_denies_unverified_shared_plan_descriptor(self):
        self.assertEqual([], gate.validate_price_list("Individual account only", "en"))
        self.assertEqual([], gate.validate_price_list("নিজের অ্যাকাউন্ট", "bn"))
        self.assertTrue(gate.validate_price_list("Shared account (multiple users)", "en"))
        self.assertTrue(gate.validate_price_list("শেয়ার্ড অ্যাকাউন্ট (একাধিক ব্যবহারকারী)", "bn"))

    def test_browser_catalog_denies_shared_type(self):
        self.assertEqual([], gate.validate_public_catalog(
            'const SOS_COMMERCIAL_REVISION="v2"; const CATALOG={"products":[]};'))
        self.assertTrue(gate.validate_public_catalog(
            'const SOS_COMMERCIAL_REVISION="v2"; const CATALOG={"type":"shared"};'))
        self.assertTrue(gate.validate_public_catalog('const CATALOG={};'))

    def test_synthetic_full_release_pass_and_failure(self):
        def good_fetch(url):
            if url.endswith("catalog.js"):
                return 'const SOS_COMMERCIAL_REVISION="v2"; const CATALOG={"products":[{"id":"demo","plans":[]}]};'
            if url.endswith("/prices"):
                return "Individual access"
            if url.endswith("/p/demo"):
                return '<link href="/p/demo"><div data-held-plans="1"></div>'
            raise ValueError("Unexpected URL " + url)

        with patch.object(gate, "restricted_inventory", return_value={"demo": {"shared-id"}}), \
             patch.object(gate, "fetch_text", side_effect=good_fetch):
            self.assertEqual(0, gate.verify_production())

        def stale_fetch(url):
            if url.endswith("/p/demo"):
                return '<link href="/p/demo"><div data-held-plans="1"></div> shared-id'
            return good_fetch(url)

        with patch.object(gate, "restricted_inventory", return_value={"demo": {"shared-id"}}), \
             patch.object(gate, "fetch_text", side_effect=stale_fetch):
            self.assertEqual(1, gate.verify_production())

    def test_stale_shared_price_copy_fails_even_without_plan_id_or_badge(self):
        markup = ('<link href="/p/demo"><div data-held-plans="1"></div>'
                  '<div>Standard Shared — ৳1,199 · Add to cart</div>')
        offers = [{"plan_id": "restricted-plan", "label": "Standard Shared", "bdt": 1199}]
        issues = gate.validate_product_html("demo", markup, {"restricted-plan"}, offers)
        self.assertTrue(any("restricted price+plan copy" in issue for issue in issues))
        self.assertTrue(gate.validate_price_list("Standard Shared — ৳1,199", "en", offers))

    def test_personal_cart_action_requires_exact_authorized_label_and_amount(self):
        markup = ('<link href="/p/demo"><div data-held-plans="1"></div>'
                  '<button onclick="cartAdd(&quot;demo&quot;,&quot;Personal&quot;,100,&quot;Demo&quot;,&quot;personal-id&quot;)"></button>')
        self.assertEqual([], gate.validate_product_html(
            "demo", markup, {"restricted-id"}, [], {"personal-id": ("Personal", 100)}))
        issues = gate.validate_product_html(
            "demo", markup.replace(",100,", ",1,"), {"restricted-id"}, [],
            {"personal-id": ("Personal", 100)})
        self.assertTrue(any("unapproved plan or amount" in x for x in issues))
        unexpected = gate.validate_product_html("demo", markup, {"restricted-id"}, [], {})
        self.assertTrue(unexpected)

    def test_catalog_must_include_each_restricted_product(self):
        js = 'const SOS_COMMERCIAL_REVISION="v2"; const CATALOG={"products":[]};'
        self.assertTrue(gate.validate_public_catalog(js, {"demo": {"restricted-id"}}))

    def test_staged_gate_accepts_synthetic_safe_build_and_denies_stale_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            for folder in ("p", "bn/p", "assets"):
                (site / folder).mkdir(parents=True, exist_ok=True)
            safe_markup = '<link href="/p/demo"><div data-held-plans="1"></div>'
            for relative in ("p/demo.html", "bn/p/demo.html"):
                (site / relative).write_text(safe_markup, encoding="utf-8")
            for relative in ("prices.html", "bn/prices.html"):
                (site / relative).write_text("Personal only", encoding="utf-8")
            (site / "assets/catalog.js").write_text(
                'const SOS_COMMERCIAL_REVISION="v2"; const CATALOG={"products":[{"id":"demo","plans":[]}]};',
                encoding="utf-8")
            profiles = {"demo": {"restricted": [
                {"plan_id": "restricted-id", "label": "Standard Shared", "bdt": 1199}
            ], "allowed": {}}}
            with patch.object(gate, "restricted_inventory", return_value={"demo": {"restricted-id"}}), \
                 patch.object(gate, "plan_profiles", return_value=profiles):
                self.assertEqual(0, gate.verify_staged_site(site))
                (site / "bn/p/demo.html").write_text(
                    safe_markup + "<p>Standard Shared ৳1,199</p>", encoding="utf-8")
                self.assertEqual(1, gate.verify_staged_site(site))

    def test_manual_deploy_checks_staged_artifact_before_publish(self):
        workflow = (ROOT / ".github/workflows/canonical-deploy-manual.yml").read_text(
            encoding="utf-8")
        self.assertLess(workflow.index("python verify_production_shared_skus.py --site-dir _site"),
                        workflow.index("wrangler pages deploy"))
        self.assertIn("if python verify_production_shared_skus.py --base-url", workflow)

    def test_manual_deploy_invokes_gate_after_live_smoke(self):
        workflow = (ROOT / ".github/workflows/canonical-deploy-manual.yml").read_text(encoding="utf-8")
        pos = workflow.index("      - name: Verify canonical production")
        self.assertIn("python verify_production_shared_skus.py --base-url https://saveonsub.com",
                      workflow[pos:])


if __name__ == "__main__":
    unittest.main()
