"""SOS-21: SKU-level orderability facts for shared/official plans in the BUILT site.

Reports (and pins invariants for) every plan across: browser cartAdd, legacy
checkout -> waOrder WhatsApp handoff, EN/BN product-page cart buttons, and the
server order API resolver. It does NOT change holds, prices or the catalog.

Needs a built _site (python build_site.py) and node; skipped otherwise, like the
other post-build tests. Set SOS_SHARED_REPORT=<path> to write the JSON report.
"""
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
NODE = shutil.which("node")
BUILT = (ROOT / "_site" / "assets" / "catalog.js").is_file()


def probe():
    out = subprocess.run(
        [NODE, "--import", "./tests/order-os/register.mjs", "tests/shared_orderability_probe.mjs"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out)["plans"]


@unittest.skipUnless(NODE and BUILT, "needs node and a built _site")
class SharedOrderabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = probe()
        report = os.environ.get("SOS_SHARED_REPORT")
        if report:
            Path(report).write_text(json.dumps(cls.rows, indent=1, ensure_ascii=False), encoding="utf-8")

    def test_no_half_states_between_cart_whatsapp_and_page_buttons(self):
        for r in self.rows:
            key = (r["product"], r["plan_id"])
            self.assertEqual(r["cart_add"], r["wa_handoff"], key)
            self.assertEqual(r["cart_add"], r["en_page_button"], key)
            self.assertEqual(r["cart_add"], r["bn_page_button"], key)

    def test_request_price_products_are_never_orderable(self):
        for r in self.rows:
            if r["request_price"]:
                self.assertFalse(r["cart_add"] or r["wa_handoff"] or r["server_api"], r)

    def test_held_plan_codes_are_not_orderable_anywhere(self):
        held = json.loads((ROOT / "ops/HELD-PLANS-2026-11-14.json").read_text(encoding="utf-8"))["held_plans"]
        for r in self.rows:
            self.assertNotIn(r["plan_id"], held.get(r["product"], []), r)

    def test_server_api_denies_every_shared_and_official_plan(self):
        for r in self.rows:
            if r["access_type"] in ("shared", "official"):
                self.assertFalse(r["server_api"], r)
            else:
                self.assertEqual(r["server_api"], r["access_type"] in ("personal", "team"), r)

    def test_every_orderable_plan_is_in_the_ceo_approved_effective_pricebook(self):
        import shared_copy_check
        approved = shared_copy_check.ceo_approved_shared()
        self.assertTrue(approved)
        for r in self.rows:
            if r["cart_add"]:
                self.assertIn((r["product"], r["label"], r["bdt"]), approved, r)

    def test_report_chatgpt_business_seven_seat_sku_facts(self):
        """Facts while the SKU exists: orderable by WhatsApp, not by the API. Passes if it was removed."""
        sku = [r for r in self.rows if (r["product"], r["plan_id"]) == ("chatgpt-business", "starter-shared-7-seats-1-month")]
        if not sku:
            return  # CEO removed this SKU permanently (18 Nov 2026); tests/test_removed_skus.py guards it
        r = sku[0]
        self.assertEqual("shared", r["access_type"])
        self.assertEqual(
            {"cart_add": True, "wa_handoff": True, "server_api": False, "en_page_button": True, "bn_page_button": True},
            {k: r[k] for k in ("cart_add", "wa_handoff", "server_api", "en_page_button", "bn_page_button")},
        )

    def test_shared_inventory_is_counted(self):
        shared = [r for r in self.rows if r["access_type"] == "shared"]
        official = [r for r in self.rows if r["access_type"] == "official"]
        print(f"\n[sos-21] shared plans orderable by cart+WhatsApp: {sum(r['wa_handoff'] for r in shared)}/{len(shared)}; "
              f"official: {sum(r['wa_handoff'] for r in official)}/{len(official)}; "
              f"server-API-orderable shared: {sum(r['server_api'] for r in shared)}")
        self.assertGreater(len(shared), 0)


if __name__ == "__main__":
    unittest.main()
