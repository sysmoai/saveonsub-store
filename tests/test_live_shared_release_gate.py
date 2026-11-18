"""Offline synthetic validation of the live shared-SKU release acceptance gate."""
import unittest
from pathlib import Path
from unittest.mock import patch

import verify_production_shared_skus as gate


ROOT = Path(__file__).resolve().parents[1]


class LiveSharedReleaseGate(unittest.TestCase):
    def test_current_inventory_all_shared_are_held_by_effective_policy(self):
        inventory = gate.restricted_inventory()
        self.assertEqual(43, len(inventory))
        self.assertEqual(57, sum(map(len, inventory.values())))

    def test_approved_personal_card_with_held_notice_passes(self):
        html = '<link rel="canonical" href="https://saveonsub.com/p/demo">' + \
               '<div data-held-plans="1">Shared unavailable</div>' + \
               '<button onclick="cartAdd(\'demo\',\'Personal\',100,\'Demo\',\'personal-id\')"></button>'
        self.assertEqual([], gate.validate_product_html("demo", html, {"shared-id"}))

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
                return 'const SOS_COMMERCIAL_REVISION="v2"; const CATALOG={"products":[]};'
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

    def test_manual_deploy_invokes_gate_after_live_smoke(self):
        workflow = (ROOT / ".github/workflows/canonical-deploy-manual.yml").read_text(encoding="utf-8")
        pos = workflow.index("      - name: Verify canonical production")
        self.assertIn("python verify_production_shared_skus.py --base-url https://saveonsub.com",
                      workflow[pos:])


if __name__ == "__main__":
    unittest.main()
