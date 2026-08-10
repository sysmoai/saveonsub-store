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


def ensure_core_path(text: str, path: str) -> str:
    quoted = f"'{path}'"
    if quoted in text:
        return text
    anchor = "'/assets/favicon.svg'"
    if anchor not in text:
        raise SystemExit(f"strict service worker core anchor missing while adding {path}")
    return text.replace(anchor, f"{anchor},{quoted}", 1)


def stamp_service_worker(cache_name: str) -> None:
    if not SERVICE_WORKER.is_file():
        raise SystemExit("_public_v3/sw.js missing; strict PWA release cannot be stamped")
    text = SERVICE_WORKER.read_text(encoding="utf-8", errors="replace")

    # Defensive cleanup if a legacy commerce path ever leaks into the generated
    # worker. The strict builder currently emits no catalog.js, but the release
    # boundary must keep that invariant explicit.
    text = re.sub(r",?\s*['\"]/assets/catalog\.js['\"]", "", text)

    # The strict builder generates site.webmanifest in /assets. Cache the actual
    # generated PWA identity and icons so addAll(CORE) contains only real files.
    for required in ("/assets/site.webmanifest", "/assets/icon-192.png", "/assets/icon-512.png"):
        text = ensure_core_path(text, required)

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
    for required in ("/assets/site.webmanifest", "/assets/icon-192.png", "/assets/icon-512.png"):
        if required not in new:
            raise SystemExit(f"strict service worker core missing generated asset: {required}")
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
