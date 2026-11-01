"""Round 08 source-of-truth safety checks; no network calls or deploy actions."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def fact(name):
    return json.loads((ROOT / "ops" / name).read_text(encoding="utf-8"))


class ProviderFactsNovemberSafetyTests(unittest.TestCase):
    def test_all_five_have_review_scope_and_dated_first_party_sources(self):
        names = (
            "CHATGPT-COHORT-FACTS-2026-09-07.json",
            "DESIGN-COHORT-FACTS-2026-09-08.json",
            "ENTERTAINMENT-COHORT-FACTS-2026-09-09.json",
            "GOOGLE-AI-COHORT-FACTS-2026-09-04.json",
            "RUNWAY-COHORT-FACTS-2026-09-09.json",
        )
        for name in names:
            with self.subTest(file=name):
                f = fact(name)
                self.assertEqual(f["verified_on"], f["verification_scope"]["current_fact_recheck_on"])
                self.assertTrue(f["verification_scope"]["first_party_sources"])
                self.assertIn("Historical", f["verification_scope"]["limitation"])

    def test_canva_price_is_sourced_not_hardcoded_to_old_180(self):
        f = fact("DESIGN-COHORT-FACTS-2026-09-08.json")
        code = (ROOT / "design_cohort.py").read_text(encoding="utf-8")
        self.assertEqual(f["canva"]["official_reference"]["pro_yearly_usd"], 144)
        self.assertNotIn("US$180", code)
        self.assertIn("CANVA_PRO_YEARLY_USD", code)
        self.assertIn('VERIFIED = FACTS["verified_on"]', code)

    def test_unverified_google_student_offer_is_not_advertised(self):
        f = fact("GOOGLE-AI-COHORT-FACTS-2026-09-04.json")
        source = (ROOT / "google_ai_cohort.py").read_text(encoding="utf-8")
        offer = f["student_offer"]
        self.assertIs(offer["offer_currently_confirmed"], False)
        self.assertEqual(offer["verification_status"], "HOLD_OFFICIAL_PAGE_CONTRADICTS_ITSELF")
        self.assertIn("historical_student_offer_snapshot", f)
        self.assertIn("data-student-offer-status", source)
        self.assertNotIn("Google currently advertises", source)
        self.assertNotIn("student['claim_deadline']", source)

    def test_expired_spotify_promotion_is_explicitly_archived(self):
        f = fact("ENTERTAINMENT-COHORT-FACTS-2026-09-09.json")
        self.assertEqual(f["spotify"]["promo"]["status"], "EXPIRED_ARCHIVAL_OFFER_DO_NOT_PUBLISH")
        self.assertIn("current_intro_offer", f["spotify"])

    def test_chatgpt_legacy_shared_offer_not_marked_authorized(self):
        f = fact("CHATGPT-COHORT-FACTS-2026-09-07.json")
        self.assertIn("Do not advertise or fulfill", f["account_policy"]["site_rule"])
        self.assertEqual(f["saveonsub_offer_snapshot_archive"]["status"], "HISTORICAL_NOT_CURRENT_NOT_APPROVED")

    def test_runway_legacy_unlimited_not_new_plan(self):
        f = fact("RUNWAY-COHORT-FACTS-2026-09-09.json")
        self.assertEqual(f["unlimited"]["new_sales_ended"], "2026-06-01")
        self.assertEqual(f["unlimited"]["legacy_extended_until"], "2026-11-30")
        self.assertIn("separate", f["unlimited"]["mode_note"])


if __name__ == "__main__":
    unittest.main()
