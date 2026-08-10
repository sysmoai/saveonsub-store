#!/usr/bin/env python3
"""Stamp an already-built strict public artifact with immutable release identity.

The stamp is intentionally public because post-deploy verification needs to prove
which Git SHA is serving. It contains no secret, price, contact, payment, or
provider-authority data.
"""
from __future__ import annotations

import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "_public_v3"
MANIFEST = PUBLIC / "BUILD-MANIFEST.txt"


def main() -> int:
    if not MANIFEST.is_file():
        raise SystemExit("_public_v3/BUILD-MANIFEST.txt missing; build strict artifact first")

    sha = (
        os.getenv("GITHUB_SHA")
        or os.getenv("SAVEONSUB_RELEASE_SHA")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or ""
    ).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise SystemExit("release SHA missing or invalid; set GITHUB_SHA, SAVEONSUB_RELEASE_SHA, or VERCEL_GIT_COMMIT_SHA")

    lines = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.startswith("git_sha="):
            lines.append(line)
    lines.append(f"git_sha={sha}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"stamped strict artifact git_sha={sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
