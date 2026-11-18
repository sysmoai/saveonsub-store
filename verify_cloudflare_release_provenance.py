#!/usr/bin/env python3
"""Read-only Cloudflare Pages canonical-production provenance gate.

Consumes the authenticated GET Pages project JSON response written by the
GitHub release workflow. Never receives or prints any API token. A successful
public HTTP response alone cannot prove which Git SHA Cloudflare deployed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def validate_project(payload: object, expected_sha: str, previous_id: str) -> list[str]:
    problems: list[str] = []
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        return ["Expected release SHA must be exactly 40 lowercase hex characters"]
    if not previous_id or not previous_id.strip():
        return ["Rollback baseline deployment ID is missing"]
    if not isinstance(payload, dict) or payload.get("success") is not True:
        return ["Cloudflare project API response not successful"]
    project = payload.get("result")
    if not isinstance(project, dict) or project.get("name") != "saveonsub":
        return ["Cloudflare API did not return the exact SaveOnSub Pages project"]
    canonical = project.get("canonical_deployment")
    if not isinstance(canonical, dict):
        return ["Cloudflare project has no canonical production deployment"]
    current_id = canonical.get("id")
    if not isinstance(current_id, str) or not current_id:
        problems.append("Canonical production deployment ID is absent")
    elif current_id == previous_id.strip():
        problems.append("Canonical production still points at the previous rollback target")
    if canonical.get("environment") != "production":
        problems.append("Canonical deployment is not tagged production")
    if canonical.get("is_skipped") is True:
        problems.append("Canonical deployment is marked skipped")
    stage = canonical.get("latest_stage")
    if not isinstance(stage, dict) or stage.get("status") != "success":
        problems.append("Canonical deployment latest_stage is not successful")
    trigger = canonical.get("deployment_trigger")
    metadata = trigger.get("metadata") if isinstance(trigger, dict) else None
    if not isinstance(metadata, dict):
        problems.append("Canonical deployment commit metadata is missing")
    else:
        if metadata.get("branch") != "main":
            problems.append("Canonical deployment branch is not main")
        if metadata.get("commit_hash") != expected_sha:
            problems.append("Canonical deployment commit hash does not equal approved SHA")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-json", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--previous-deployment-id", required=True)
    args = parser.parse_args()
    try:
        obj = json.loads(args.project_json.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"[cf-provenance] FAIL: cannot read API project response: {type(exc).__name__}")
        return 1
    errors = validate_project(obj, args.expected_sha, args.previous_deployment_id)
    if errors:
        print(f"[cf-provenance] FAIL: {len(errors)} verification error(s)")
        for error in errors:
            print("  " + error)
        return 1
    dep = obj["result"]["canonical_deployment"]
    print(f"[cf-provenance] PASS: canonical project=saveonsub deployment={dep['id']} "
          f"branch=main sha={args.expected_sha}; previous={args.previous_deployment_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
