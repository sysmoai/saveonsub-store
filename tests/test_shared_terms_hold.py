import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import shared_copy_check  # noqa: E402

POLICY = json.loads((ROOT / "ops" / "PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
# SOS-A3 (CEO 2026-11-12): these products publish no shared-access plan.
HELD = ["chatgpt-plus", "chatgpt-business", "chatgpt-pro", "claude-pro", "google-ai-plus", "perplexity-pro",
        "heygen", "grammarly", "otter", "writesonic", "netflix", "surfshark", "copilot-pro"]


class SharedTermsHold(unittest.TestCase):
    def test_held_products_publish_no_shared_plan(self):
        for pid in HELD:
            rule = POLICY["approved_products"][pid]
            shared = [p["plan_id"] for p in rule.get("plans") or [] if str(p.get("access_type", "")).startswith("shared")]
            self.assertEqual(shared, [], pid)
            if not rule.get("plans"):
                self.assertEqual(rule["mode"], "inquiry", pid)

    def test_personal_seat_label_needs_no_shared_disclosure(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d)
            (site / "p").mkdir()
            (site / "bn" / "p").mkdir(parents=True)
            (site / "p" / "demo.html").write_text('<button onclick="cartAdd(\'demo\',\'Personal seat\',100)">', encoding="utf-8")
            approved = {("demo", "Personal seat", 100)}
            self.assertEqual(shared_copy_check.page_issues(site, approved, set()), [])
            # A product that does sell a shared-type plan still needs the disclosure.
            self.assertTrue(shared_copy_check.page_issues(site, approved, {"demo"}))


if __name__ == "__main__":
    unittest.main()
