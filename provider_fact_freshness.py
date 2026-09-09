#!/usr/bin/env python3
"""Fail-closed freshness guard for volatile provider fact files.

Policy:
- governed files are ops/*COHORT-FACTS*.json
- every governed file must contain a valid ISO YYYY-MM-DD `verified_on`
- warn when facts are older than 7 days
- fail when facts are older than 14 days
- never changes pricing or facts; it only blocks stale releases
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

WARN_AFTER_DAYS = int(os.environ.get("PROVIDER_FACT_WARN_DAYS", "7"))
FAIL_AFTER_DAYS = int(os.environ.get("PROVIDER_FACT_FAIL_DAYS", "14"))
FACT_GLOB = "*COHORT-FACTS*.json"


def parse_iso_day(value: object, path: Path) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{path}: missing string verified_on")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{path}: verified_on must be YYYY-MM-DD, got {value!r}") from exc


def main() -> int:
    if WARN_AFTER_DAYS < 0 or FAIL_AFTER_DAYS <= 0 or WARN_AFTER_DAYS >= FAIL_AFTER_DAYS:
        print("::error::Invalid provider freshness policy thresholds.", file=sys.stderr)
        return 2

    today = date.today()
    paths = sorted(Path("ops").glob(FACT_GLOB))
    if not paths:
        print("::error::No governed provider fact files found.", file=sys.stderr)
        return 1

    stale: list[str] = []
    warnings: list[str] = []

    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            verified = parse_iso_day(data.get("verified_on"), path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"::error::{exc}", file=sys.stderr)
            return 1

        age = (today - verified).days
        if age < 0:
            print(f"::error::{path}: verified_on {verified} is in the future relative to {today}.", file=sys.stderr)
            return 1
        if age > FAIL_AFTER_DAYS:
            stale.append(f"{path} ({age} days old; verified {verified})")
        elif age > WARN_AFTER_DAYS:
            warnings.append(f"{path} ({age} days old; verified {verified})")

    for item in warnings:
        print(f"::warning::Provider facts approaching staleness: {item}")

    if stale:
        for item in stale:
            print(f"::error::Provider facts are stale: {item}", file=sys.stderr)
        print(
            f"Provider fact freshness FAILED: refresh verified source facts before release "
            f"(warn>{WARN_AFTER_DAYS}d, fail>{FAIL_AFTER_DAYS}d).",
            file=sys.stderr,
        )
        return 1

    print(
        f"Provider fact freshness OK — {len(paths)} governed file(s); "
        f"warn>{WARN_AFTER_DAYS}d, fail>{FAIL_AFTER_DAYS}d."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
