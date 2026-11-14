import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "_site" / "p" / "canva-pro.html"


def _plan():
    book = json.loads((ROOT / "ops" / "PRICING-V2-2026-09-17.json").read_text(encoding="utf-8"))
    return next(p for p in book["approved_products"]["canva-pro"]["plans"]
                if p["plan_id"] == "team-seat-your-login-1-month")


class CanvaTeamSeatLabel(unittest.TestCase):
    def test_team_seat_is_not_labelled_shared_and_price_is_unchanged(self):
        plan = _plan()
        self.assertEqual(plan["access_type"], "team")  # CEO 2026-11-14: "it is not shared"
        self.assertEqual(plan["bdt"], 299)
        self.assertEqual(plan["duration"], "1 month")

    @unittest.skipUnless(PAGE.exists(), "run python build_site.py first")
    def test_built_page_has_no_shared_label_for_team_seat(self):
        html = PAGE.read_text(encoding="utf-8")
        self.assertNotIn("Shared account (multiple users)", html)
        self.assertIn("Team / Workspace access", html)


if __name__ == "__main__":
    unittest.main()
