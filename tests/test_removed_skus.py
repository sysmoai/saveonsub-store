"""Permanently removed SKUs must not come back (CEO decision, 18 Nov 2026).

chatgpt-business / starter-shared-7-seats-1-month (BDT 699, 'Starter Shared (7 seats)')
was permanently removed and will not be offered again. This guard fails if it
reappears in the pricebook, the built catalog or any built product page.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOVED = [("chatgpt-business", "starter-shared-7-seats-1-month", "Starter Shared (7 seats)")]


class RemovedSkuTest(unittest.TestCase):
    def test_not_in_pricebook(self):
        policy = json.loads((ROOT / "ops/PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
        for pid, plan_id, label in REMOVED:
            plans = policy["approved_products"].get(pid, {}).get("plans", [])
            self.assertNotIn(plan_id, [p.get("plan_id") for p in plans])
            self.assertNotIn(label, [p.get("label") for p in plans])

    def test_not_in_committed_catalog(self):
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        for p in catalog["products"]:
            for pl in p.get("plans", []):
                for pid, plan_id, label in REMOVED:
                    self.assertFalse(p["id"] == pid and pl.get("plan_id") == plan_id)

    def test_not_in_built_site(self):
        site = ROOT / "_site"
        if not (site / "assets" / "catalog.js").is_file():
            self.skipTest("needs a built _site")
        for pid, plan_id, label in REMOVED:
            for rel in ("assets/catalog.js", f"p/{pid}.html", f"bn/p/{pid}.html"):
                text = (site / rel).read_text(encoding="utf-8")
                self.assertNotIn(plan_id, text, rel)
                self.assertNotIn(label, text, rel)


if __name__ == "__main__":
    unittest.main()
