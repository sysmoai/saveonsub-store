"""Fail-closed release-freeze regression tests for the R13 review branch.

These tests only inspect in-repository workflow source. They do not prove
Cloudflare Pages Git integration, Workers routes, or deployed SHA are safe.
The deployment job remains intentionally unavailable until separately
authorized, reviewed, and verified by the production owner.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / ".github" / "workflows" / "canonical-deploy-manual.yml"
QUALITY = ROOT / ".github" / "workflows" / "quality-gates.yml"


class CanonicalReleaseFreezeR13(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deploy = DEPLOY.read_text(encoding="utf-8")
        cls.quality = QUALITY.read_text(encoding="utf-8")
        cls.events = cls.deploy.split("\nconcurrency:", 1)[0]

    def test_canonical_workflow_cannot_autotrigger_from_main_push(self):
        self.assertIn("\non:\n  workflow_dispatch:\n", self.events)
        for event in ("push", "pull_request", "schedule", "repository_dispatch", "workflow_run"):
            with self.subTest(event=event):
                self.assertNotRegex(self.events, rf"(?m)^  {event}:")

    def test_manual_job_is_explicitly_disabled(self):
        self.assertIn("\n  validate-and-deploy:\n", self.deploy)
        self.assertRegex(self.deploy, r"(?m)^    if: \$\{\{ false \}\}$")
        self.assertIn("\n    environment: production\n", self.deploy)

    def test_original_scoped_pages_target_remains_reviewable(self):
        self.assertIn("wrangler pages deploy", self.deploy)
        self.assertIn("--project-name=saveonsub", self.deploy)
        self.assertIn("CLOUDFLARE_API_TOKEN", self.deploy)

    def test_quality_gates_are_source_validation_not_a_publisher(self):
        self.assertIn("python build_site.py", self.quality)
        self.assertIn("unittest discover", self.quality)
        self.assertNotIn("wrangler pages deploy", self.quality)
        self.assertNotIn("CLOUDFLARE_API_TOKEN", self.quality)


if __name__ == "__main__":
    unittest.main()
