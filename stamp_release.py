#!/usr/bin/env python3
"""Stamp an already-built strict public artifact with immutable release identity.

The stamp is intentionally public because post-deploy verification needs to prove
which Git SHA is serving. It contains no secret, price, contact, payment, or
provider-authority data. The same identity is embedded in the service-worker
cache namespace so a new release cannot silently reuse stale static-asset caches.
"""
from __future__ import annotations

import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "_public_v3"
MANIFEST = PUBLIC / "BUILD-MANIFEST.txt"
SERVICE_WORKER = PUBLIC / "sw.js"
CACHE_PREFIX = "sos-info-v3"


def release_sha() -> str:
    sha = (
        os.getenv("GITHUB_SHA")
        or os.getenv("SAVEONSUB_RELEASE_SHA")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or ""
    ).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise SystemExit("release SHA missing or invalid; set GITHUB_SHA, SAVEONSUB_RELEASE_SHA, or VERCEL_GIT_COMMIT_SHA")
    return sha


def stamp_manifest(sha: str, cache_name: str) -> None:
    lines = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.startswith(("git_sha=", "service_worker_cache=")):
            continue
        lines.append(line)
    lines.append(f"git_sha={sha}")
    lines.append(f"service_worker_cache={cache_name}")
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def stamp_service_worker(cache_name: str) -> None:
    if not SERVICE_WORKER.is_file():
        raise SystemExit("_public_v3/sw.js missing; strict PWA release cannot be stamped")
    text = SERVICE_WORKER.read_text(encoding="utf-8", errors="replace")

    # Remove legacy commerce data from the install list. Strict L1 does not
    # publish assets/catalog.js, and leaving it in cache.addAll() would reject
    # the whole pre-cache transaction and silently defeat offline resilience.
    text = re.sub(r",?\s*['\"]/assets/catalog\.js['\"]", "", text)
    text = text.replace("'/assets/site.webmanifest'", "'/manifest.webmanifest'")
    text = text.replace('"/assets/site.webmanifest"', '"/manifest.webmanifest"')

    new, count = re.subn(
        r"const\s+CACHE\s*=\s*'[^']+';",
        f"const CACHE = '{cache_name}';",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("service-worker CACHE declaration missing or ambiguous")
    if "/assets/catalog.js" in new:
        raise SystemExit("strict service worker still references forbidden legacy catalog.js")
    if "/manifest.webmanifest" not in new:
        raise SystemExit("strict service worker does not cache the public web manifest")
    SERVICE_WORKER.write_text(new, encoding="utf-8")


def main() -> int:
    if not MANIFEST.is_file():
        raise SystemExit("_public_v3/BUILD-MANIFEST.txt missing; build strict artifact first")
    sha = release_sha()
    cache_name = f"{CACHE_PREFIX}-{sha[:12]}"
    stamp_service_worker(cache_name)
    stamp_manifest(sha, cache_name)
    print(f"stamped strict artifact git_sha={sha} service_worker_cache={cache_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
