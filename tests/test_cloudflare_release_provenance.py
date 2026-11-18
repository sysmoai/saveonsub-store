"""Offline synthetic tests for exact Cloudflare canonical production provenance."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import verify_cloudflare_release_provenance as gate


SHA = "a" * 40
PREVIOUS = "previous-successful-production-id"


def fixture() -> dict:
    return {
        "success": True,
        "result": {
            "name": "saveonsub",
            "canonical_deployment": {
                "id": "new-production-id",
                "environment": "production",
                "is_skipped": False,
                "latest_stage": {"name": "deploy", "status": "success"},
                "deployment_trigger": {
                    "type": "ad_hoc",
                    "metadata": {"branch": "main", "commit_hash": SHA},
                },
            },
        },
    }


class CloudflareProvenanceGateTest(unittest.TestCase):
    def test_exact_canonical_sha_passes(self):
        self.assertEqual([], gate.validate_project(fixture(), SHA, PREVIOUS))

    def test_wrong_sha_or_abridged_sha_fails(self):
        self.assertTrue(gate.validate_project(fixture(), "f" * 40, PREVIOUS))
        self.assertTrue(gate.validate_project(fixture(), SHA[:7], PREVIOUS))

    def test_previous_deployment_must_not_still_be_canonical(self):
        r = fixture()
        r["result"]["canonical_deployment"]["id"] = PREVIOUS
        self.assertTrue(any("previous rollback target" in e
                            for e in gate.validate_project(r, SHA, PREVIOUS)))

    def test_failed_skipped_preview_or_wrong_branch_never_pass(self):
        for key, value in (
            ("environment", "preview"),
            ("is_skipped", True),
        ):
            r = fixture()
            r["result"]["canonical_deployment"][key] = value
            with self.subTest(key=key):
                self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))
        r = fixture()
        r["result"]["canonical_deployment"]["latest_stage"]["status"] = "failure"
        self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))
        r = fixture()
        r["result"]["canonical_deployment"]["deployment_trigger"]["metadata"]["branch"] = "review/test"
        self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))

    def test_wrong_account_project_and_missing_deployment_fail(self):
        r = fixture()
        r["result"]["name"] = "another-project"
        self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))
        r = fixture()
        r["result"]["canonical_deployment"] = None
        self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))
        r = fixture()
        r["success"] = False
        self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))

    def test_missing_metadata_or_previous_baseline_fails(self):
        r = fixture()
        r["result"]["canonical_deployment"]["deployment_trigger"] = {}
        self.assertTrue(gate.validate_project(r, SHA, PREVIOUS))
        self.assertTrue(gate.validate_project(fixture(), SHA, ""))

    def test_live_workflow_requires_canonical_sha_after_public_sku_checks(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/canonical-deploy-manual.yml").read_text("utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("python verify_production_shared_skus.py --site-dir _site", workflow)
        self.assertLess(workflow.index("python verify_production_shared_skus.py --base-url"),
                        workflow.index("python verify_cloudflare_release_provenance.py"))
        self.assertIn('--expected-sha "${DEPLOY_SHA}"', workflow)
        self.assertIn("--previous-deployment-id", workflow)
        self.assertIn("result", json.dumps(fixture()))


if __name__ == "__main__":
    unittest.main()
