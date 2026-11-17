"""Regression checks for SaveOnSub's review-only canonical publishing freeze.

Does not test or assert anything about authenticated Cloudflare publisher topology.
A future controlled release redesign must explicitly update these tests and receive
separate CEO approval. No production action occurs by running this test file.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / ".github" / "workflows" / "canonical-deploy-manual.yml"
QUALITY = ROOT / ".github" / "workflows" / "quality-gates.yml"


class CanonicalReleaseFreezeC002(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deploy = DEPLOY.read_text(encoding="utf-8")
        cls.quality = QUALITY.read_text(encoding="utf-8")
        cls.trigger = cls.deploy.split("\nconcurrency:", 1)[0]

    def test_no_automatic_canonical_deploy_trigger(self):
        self.assertIn("\non:\n", self.trigger)
        self.assertRegex(self.trigger, r"(?m)^  workflow_dispatch:$")
        for event in ("push", "pull_request", "schedule", "workflow_run", "repository_dispatch"):
            with self.subTest(event=event):
                self.assertNotRegex(self.trigger, rf"(?m)^  {event}:")

    def test_manual_deploy_requires_main_and_pinned_source_sha(self):
        self.assertIn("\n  validate-and-deploy:\n", self.deploy)
        self.assertIn("if: ${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' }}", self.deploy)
        self.assertIn("\n    environment: production\n", self.deploy)
        self.assertIn("ref: 6d8c8898985896e7857dfbb35ea4d277d0873170", self.deploy)
        self.assertIn('test "$DEPLOY_SHA" = "6d8c8898985896e7857dfbb35ea4d277d0873170"', self.deploy)
        self.assertIn("Cannot verify previous Cloudflare production deployment for rollback", self.deploy)

    def test_current_price_and_hold_smoke_guards(self):
        self.assertIn("grep -q '৳1,290' /tmp/chatgpt-go.html", self.deploy)
        self.assertIn("! grep -q '৳450' /tmp/chatgpt-go.html", self.deploy)
        self.assertIn("! grep -q '৳1,499' /tmp/chatgpt-business.html", self.deploy)
        self.assertIn('data-held-plans="1"', self.deploy)
        self.assertIn("python -m unittest -v tests.test_held_plans", self.deploy)

    def test_scoped_target_retained_for_separate_owner_review(self):
        self.assertIn("wrangler pages deploy", self.deploy)
        self.assertIn("--project-name=saveonsub", self.deploy)
        self.assertIn("CLOUDFLARE_API_TOKEN", self.deploy)

    def test_versioned_favicon_assertion_matches_quality_gate(self):
        needle = r"""grep -Eq 'favicon-32\.png\?v=[0-9a-f]{10}" type="image/png"'"""
        self.assertIn(needle, self.deploy)
        self.assertIn(needle, self.quality)
        self.assertNotIn("grep -q 'favicon-32.png", self.deploy)

    def test_quality_gates_do_not_publish(self):
        self.assertIn("python build_site.py", self.quality)
        self.assertIn("unittest discover", self.quality)
        self.assertNotIn("wrangler pages deploy", self.quality)


if __name__ == "__main__":
    unittest.main()
