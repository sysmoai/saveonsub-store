"""Fail-closed regression tests for the temporary canonical production freeze.

This test file inspects source workflows only. It does not call GitHub, Cloudflare,
payment systems, or any production endpoint. A future CEO-approved deployment
workflow must deliberately replace/update these tests during release review.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / ".github" / "workflows" / "canonical-deploy-manual.yml"
QUALITY = ROOT / ".github" / "workflows" / "quality-gates.yml"


class MainPublishFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deploy = DEPLOY.read_text(encoding="utf-8")
        cls.quality = QUALITY.read_text(encoding="utf-8")
        cls.events = cls.deploy.split("\nconcurrency:", 1)[0]

    def test_no_publish_on_any_automatic_event(self):
        self.assertIn("\n  workflow_dispatch:", self.events)
        for unsafe in ("\n  push:", "\n  pull_request:", "\n  schedule:", "\n  repository_dispatch:", "\n  workflow_run:"):
            with self.subTest(event=unsafe.strip()):
                self.assertNotIn(unsafe, self.events)

    def test_all_canonical_publish_steps_are_unreachable(self):
        self.assertIn("  validate-and-deploy:", self.deploy)
        self.assertIn("    if: ${{ false }}", self.deploy)
        self.assertIn("    environment: production", self.deploy)
        self.assertIn("wrangler pages deploy", self.deploy)

    def test_quality_workflow_is_not_a_publisher(self):
        self.assertNotIn("wrangler pages deploy", self.quality)
        self.assertNotIn("CLOUDFLARE_API_TOKEN", self.quality)
        self.assertIn("python build_site.py", self.quality)

    def test_existing_provider_fact_unit_tests_are_executed(self):
        self.assertIn("unittest discover -s tests -p 'test_provider_fact_claim_boundaries.py'", self.quality)
        self.assertIn("unittest discover -s tests -p 'test_main_publish_freeze.py'", self.quality)


if __name__ == "__main__":
    unittest.main()
