#!/usr/bin/env python3
"""Enforce the SAVEONSUB editorial freshness SLA without relying on network calls."""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
POLICY = ROOT / "content" / "editorial_policy_v1.json"
RESOURCES = ROOT / "content" / "resources_v1.json"
errors: list[str] = []
warnings: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def load_json(path: pathlib.Path) -> dict:
    if not path.is_file():
        fail(f"missing editorial control file: {path.relative_to(ROOT)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
        return {}


def current_date() -> dt.date:
    override = os.getenv("SAVEONSUB_AUDIT_DATE", "").strip()
    if override:
        try:
            return dt.date.fromisoformat(override)
        except ValueError:
            fail("SAVEONSUB_AUDIT_DATE must be YYYY-MM-DD")
    return dt.datetime.now(dt.timezone.utc).date()


def main() -> int:
    policy = load_json(POLICY)
    resources = load_json(RESOURCES)
    today = current_date()

    if policy.get("schema") != "saveonsub-editorial-policy-v1":
        fail("editorial policy schema mismatch")
    if resources.get("schema") != "saveonsub-resources-v1":
        fail("resource schema mismatch")

    expected_owner = policy.get("editorial_owner")
    if expected_owner != "SAVEONSUB Admin":
        fail("editorial policy owner must be SAVEONSUB Admin")
    if resources.get("editorial_owner") != expected_owner:
        fail("resource editorial owner differs from policy")

    freshness = policy.get("freshness") or {}
    try:
        review_due = int(freshness.get("review_due_days"))
        hard_fail = int(freshness.get("hard_fail_days"))
    except (TypeError, ValueError):
        fail("freshness day limits must be integers")
        review_due, hard_fail = 0, 0
    if review_due <= 0 or hard_fail <= review_due:
        fail("freshness policy must satisfy 0 < review_due_days < hard_fail_days")

    raw_checked = str(resources.get("checked_on") or "")
    try:
        checked_on = dt.date.fromisoformat(raw_checked)
    except ValueError:
        fail("resources checked_on must be ISO YYYY-MM-DD")
        checked_on = today

    age_days = (today - checked_on).days
    if age_days < 0:
        fail(f"resource checked_on is in the future: {checked_on}")
    elif age_days > hard_fail:
        fail(f"resource source review is stale: {age_days} days old > hard fail {hard_fail}")
    elif age_days > review_due:
        warn(f"resource source review is due: {age_days} days old > review target {review_due}")

    publishing = policy.get("publishing") or {}
    required_true = (
        "people_first",
        "bangladesh_relevance_required",
        "bilingual_for_resource_cluster",
        "primary_or_authoritative_sources_required",
        "paid_ranking_without_disclosure_forbidden",
        "unverified_commercial_claims_forbidden",
        "automated_mass_publishing_for_search_rankings_forbidden",
    )
    for key in required_true:
        if publishing.get(key) is not True:
            fail(f"editorial publishing policy must keep {key}=true")
    try:
        min_sources = int(publishing.get("minimum_sources_per_article"))
    except (TypeError, ValueError):
        fail("minimum_sources_per_article must be an integer")
        min_sources = 0
    if min_sources < 2:
        fail("minimum_sources_per_article cannot be below 2")

    for article in resources.get("articles") or []:
        slug = article.get("slug") or "<missing>"
        sources = article.get("sources") or []
        if len(sources) < min_sources:
            fail(f"{slug}: only {len(sources)} sources, requires {min_sources}")
        if not article.get("en") or not article.get("bn"):
            fail(f"{slug}: EN/BN pair required")

    release = policy.get("release") or {}
    for key in (
        "production_requires_authenticated_canonical_path",
        "production_requires_green_release_gates",
        "production_gate_bypass_forbidden",
    ):
        if release.get(key) is not True:
            fail(f"editorial release policy must keep {key}=true")

    for message in warnings:
        print(f"WARN: {message}")
    if errors:
        print(f"EDITORIAL FRESHNESS BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1

    print(json.dumps({
        "editorial_freshness": "PASS",
        "editorial_owner": expected_owner,
        "audit_date": today.isoformat(),
        "checked_on": checked_on.isoformat(),
        "age_days": age_days,
        "review_due_days": review_due,
        "hard_fail_days": hard_fail,
        "review_due": age_days > review_due,
        "articles": len(resources.get("articles") or []),
        "minimum_sources_per_article": min_sources,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
