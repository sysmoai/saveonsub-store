import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import shared_copy_check  # noqa: E402
from pricebook import load_policy  # noqa: E402

POLICY = load_policy(ROOT / "ops" / "PRICING-V2-2026-09-17.json")  # effective: held plans removed


class SharedPlanDisclosure(unittest.TestCase):
    def test_every_shared_type_product_needs_disclosure(self):
        pids = shared_copy_check.approved_shared_type_pids()
        for pid, rule in POLICY["approved_products"].items():
            has_shared = any(str(p.get("access_type", "")).startswith("shared") for p in rule.get("plans") or [])
            self.assertEqual(pid in pids, has_shared and rule.get("mode") == "fixed", pid)

    def test_personal_seat_label_needs_no_shared_disclosure(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d)
            (site / "p").mkdir()
            (site / "bn" / "p").mkdir(parents=True)
            (site / "p" / "demo.html").write_text('<button onclick="cartAdd(\'demo\',\'Personal seat\',100)">', encoding="utf-8")
            approved = {("demo", "Personal seat", 100)}
            self.assertEqual(shared_copy_check.page_issues(site, approved, set()), [])
            self.assertTrue(shared_copy_check.page_issues(site, approved, {"demo"}))


if __name__ == "__main__":
    unittest.main()
