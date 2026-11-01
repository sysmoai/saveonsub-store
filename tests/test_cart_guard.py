"""T018-02: browser cart accepts only exact governed catalog plans."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")


def run(catalog):
    out = subprocess.run([NODE, str(HERE / "cart_guard_vm.cjs"), json.dumps(catalog)],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


@unittest.skipUnless(NODE, "node is required for the app.js VM test")
class CartGuardTest(unittest.TestCase):
    HOLD = {"products": [{"id": "chatgpt-plus", "request_price": True, "plans": []},
                         {"id": "demo", "request_price": False,
                          "plans": [{"label": "Demo — 1 Month", "bdt": 100}]}]}

    def test_hold_and_unknown_plans_never_reach_cart(self):
        r = run(self.HOLD)
        self.assertEqual(r["wrongPlan"], 0)
        self.assertEqual(r["holdPlan"], 0)
        self.assertEqual(r["staleRead"], 0)

    def test_exact_priced_plan_is_accepted_and_edited_price_rejected(self):
        r = run(self.HOLD)
        self.assertEqual(r["validPlan"], 1)
        self.assertEqual(r["editedPrice"], 1)

    def test_missing_catalog_fails_closed(self):
        r = run(None)
        self.assertEqual((r["wrongPlan"], r["holdPlan"], r["validPlan"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
