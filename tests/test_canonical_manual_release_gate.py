"""Static fail-closed regression checks for the canonical production workflow.

These checks never deploy, purchase, modify a customer account, or call Cloudflare.
They protect the EXEC-010 commercial HOLD on the staged SOS review branch.
"""

from pathlib import Path
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "canonical-deploy-manual.yml"


class CanonicalManualReleaseGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.trigger = cls.workflow.split("\nconcurrency:", 1)[0]

    def test_only_explicit_manual_dispatch(self):
        self.assertIn("\n  workflow_dispatch:", self.trigger)
        self.assertNotIn("\n  push:", self.trigger)
        self.assertNotIn("\n  schedule:", self.trigger)

    def test_exact_sha_and_acknowledgement_are_required(self):
        self.assertIn("approved_sha:", self.trigger)
        self.assertIn("release_ack:", self.trigger)
        self.assertIn("DEPLOY_SOS_EXEC010_HOLD", self.workflow)
        self.assertIn("refs/heads/main", self.workflow)
        self.assertIn("TRIGGER_SHA: ${{ github.sha }}", self.workflow)
        self.assertIn("APPROVED_SHA: ${{ inputs.approved_sha }}", self.workflow)

    def test_exact_commit_is_checked_out_and_rechecked(self):
        self.assertIn("ref: ${{ github.sha }}", self.workflow)
        self.assertIn('[[ "$DEPLOY_SHA" != "$APPROVED_SHA" ]]', self.workflow)
        self.assertNotIn("github.event_name == 'push'", self.workflow)

    def test_preflight_runs_before_build_or_publish(self):
        gate = self.workflow.index("- name: Fail closed unless manual CEO release acknowledgement")
        checkout = self.workflow.index("- name: Checkout exact release source")
        build = self.workflow.index("- name: Build exact hardened public artifact")
        publish = self.workflow.index("- name: Preflight scoped Cloudflare token and publish")
        self.assertLess(gate, checkout)
        self.assertLess(checkout, build)
        self.assertLess(build, publish)
        self.assertIn("environment: production", self.workflow)

    def test_commercial_hold_applies_to_full_staged_artifact(self):
        self.assertIn("python catalog_hold_gate.py", self.workflow)
        self.assertIn("python hold_content_price_guard.py --check", self.workflow)
        self.assertIn("python audit_commercial_truth_v2.py", self.workflow)
        self.assertIn("! grep -q '৳3,390' _site/p/chatgpt-plus.html", self.workflow)
        self.assertIn("! grep -q 'cartAdd' _site/p/chatgpt-plus.html", self.workflow)

    def test_live_checks_do_not_accept_legacy_catalog_or_traction(self):
        self.assertIn("price_precedence", self.workflow)
        self.assertIn("! grep -q '211+ orders' /tmp/sos-google-guide.html", self.workflow)
        self.assertIn("wrangler pages deploy", self.workflow)
        self.assertIn('--commit-hash="$DEPLOY_SHA"', self.workflow)


if __name__ == "__main__":
    unittest.main()
