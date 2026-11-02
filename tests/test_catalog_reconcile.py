"""Synthetic regression tests for pricebook -> staged artifact reconciliation."""
import json
import tempfile
import unittest
from pathlib import Path

from apply_pricing_v2 import public_plan
from catalog_reconcile import reconcile

BASE = "https://saveonsub.com"


def page(pid: str, body: str) -> str:
    return (f'<link rel="canonical" href="{BASE}/{{loc}}{pid}">'
            f'<link rel="alternate" hreflang="en-bd" href="{BASE}/p/{pid}">'
            f'<link rel="alternate" hreflang="bn-bd" href="{BASE}/bn/p/{pid}">{body}')


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name)
        self.plans = [{"label": "Monthly", "bdt": 299, "duration": "month", "access_type": "personal"},
                      {"label": "Yearly", "bdt": 1499, "duration": "year", "access_type": "personal"}]
        self.policy = {"revision": "t", "approved_products": {
            "demo": {"mode": "fixed", "plans": self.plans},
            "held": {"mode": "inquiry", "plans": []}}}
        self.catalog = {"products": [{"id": "demo", "name": "Demo", "category": "AI Writing"}]}
        self.body = "৳299 / month ৳1,499 / year https://wa.me/8801305869242?text=Demo%20%E0%A7%B3299"
        self.write()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, js_plans=None):
        (self.site / "assets").mkdir(exist_ok=True)
        (self.site / "p").mkdir(exist_ok=True)
        (self.site / "bn" / "p").mkdir(parents=True, exist_ok=True)
        js = {"products": [{"id": "demo", "plans": js_plans if js_plans is not None
                            else [public_plan(p) for p in self.plans]}]}
        (self.site / "assets" / "catalog.js").write_text(
            "const CATALOG = " + json.dumps(js) + ";\n", encoding="utf-8")
        for loc, path in (("p/", self.site / "p" / "demo.html"), ("bn/p/", self.site / "bn" / "p" / "demo.html")):
            path.write_text(page("demo", self.body).replace("{loc}", loc), encoding="utf-8")
        (self.site / "sitemap.xml").write_text(
            f"<loc>{BASE}/p/demo</loc><loc>{BASE}/bn/p/demo</loc>", encoding="utf-8")

    def errors(self):
        return reconcile(self.policy, self.catalog, self.site)[0]

    def test_consistent_artifact_passes(self):
        self.assertEqual([], self.errors())

    def test_inquiry_entry_without_page_is_held(self):
        ledger = reconcile(self.policy, self.catalog, self.site)[2]
        self.assertEqual(["held"], ledger["summary"]["held_without_page"])

    def test_yearly_price_labelled_monthly_blocked(self):
        self.body = self.body.replace("৳1,499 / year", "৳1,499 / month")
        self.write()
        self.assertTrue(any("labelled per month" in e for e in self.errors()))

    def test_unapproved_price_blocked(self):
        self.body += " ৳199"
        self.write()
        self.assertTrue(any("unapproved price" in e for e in self.errors()))

    def test_whatsapp_prefill_and_number_checked(self):
        self.body = self.body.replace("8801305869242", "8801700000000").replace("%E0%A7%B3299", "%E0%A7%B3249")
        self.write()
        errs = self.errors()
        self.assertTrue(any("non-canonical number" in e for e in errs))
        self.assertTrue(any("prefill quotes unapproved" in e for e in errs))

    def test_catalog_js_drift_blocked(self):
        self.write(js_plans=[public_plan(self.plans[0])])
        self.assertTrue(any("catalog.js plans" in e for e in self.errors()))

    def test_fixed_price_without_page_blocked(self):
        self.policy["approved_products"]["ghost"] = {"mode": "fixed", "plans": self.plans[:1]}
        self.assertTrue(any("ghost" in e for e in self.errors()))

    def test_other_business_unit_must_stay_inquiry(self):
        self.policy["approved_products"]["aips-pack"] = {"mode": "fixed", "plans": self.plans[:1]}
        self.assertTrue(any("aips-pack" in e and "inquiry-only" in e for e in self.errors()))

    def test_period_unit_follows_duration(self):
        self.assertEqual(("1 year", "year"), (public_plan(self.plans[1])["duration"], public_plan(self.plans[1])["billing_unit"]))
        six = public_plan({"label": "6M", "bdt": 1, "duration": "6months"})
        self.assertEqual(("6 months", "6 months"), (six["duration"], six["billing_unit"]))
        with self.assertRaises(SystemExit):
            public_plan({"label": "x", "bdt": 1, "duration": "fortnight"})


if __name__ == "__main__":
    unittest.main()
