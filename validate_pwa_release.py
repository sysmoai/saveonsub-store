#!/usr/bin/env python3
"""Validate release-bound PWA caching for the staged SAVEONSUB strict artifact."""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def manifest_values() -> dict[str, str]:
    path = SITE / "BUILD-MANIFEST.txt"
    if not path.is_file():
        fail("BUILD-MANIFEST.txt missing")
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def main() -> int:
    if not SITE.is_dir():
        print("PWA release quality blocked: _site missing")
        return 1

    manifest = manifest_values()
    sha = manifest.get("git_sha", "")
    cache = manifest.get("service_worker_cache", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        fail("BUILD-MANIFEST git_sha is missing or invalid")
    expected_cache = f"sos-info-v3-{sha[:12]}" if len(sha) == 40 else ""
    if cache != expected_cache:
        fail(f"service_worker_cache mismatch: {cache!r} != {expected_cache!r}")

    sw_path = SITE / "sw.js"
    if not sw_path.is_file():
        fail("sw.js missing")
        sw = ""
    else:
        sw = sw_path.read_text(encoding="utf-8", errors="replace")

    match = re.search(r"const\s+CACHE\s*=\s*'([^']+)';", sw)
    if not match:
        fail("sw.js CACHE declaration missing")
    elif match.group(1) != expected_cache:
        fail("sw.js CACHE namespace is not bound to release SHA")

    required_core = (
        "'/'",
        "'/index.html'",
        "'/all.html'",
        "'/bn/all.html'",
        "'/assets/site.webmanifest'",
        "'/assets/app.js'",
        "'/assets/a11y.js'",
        "'/assets/discovery.js'",
        "'/assets/discovery.css'",
        "'/assets/style.css'",
        "'/assets/favicon.svg'",
        "'/assets/icon-192.png'",
        "'/assets/icon-512.png'",
    )
    for token in required_core:
        if token not in sw:
            fail(f"sw.js core cache missing {token}")

    forbidden = ("checkout.html", "track.html", "catalog.json", "aips-live.json", "/assets/catalog.js")
    for token in forbidden:
        if token in sw:
            fail(f"sw.js must not cache forbidden legacy path {token}")

    if "k!==CACHE" not in sw or "caches.delete(k)" not in sw:
        fail("sw.js activation must delete prior cache namespaces")
    if "mode==='navigate'" not in sw and 'mode === \'navigate\'' not in sw:
        fail("sw.js must treat navigation requests separately")
    if len(re.findall(r"\.ok\b", sw)) < 2:
        fail("sw.js must gate both navigation and asset persistence on successful HTTP status")
    if "c.addAll(CORE)" not in sw:
        fail("sw.js install must pre-cache the strict core")
    if "caches.match('/all.html')" not in sw:
        fail("sw.js navigation fallback must resolve to the safe information catalog")

    if errors:
        print(f"PWA RELEASE QUALITY BLOCKED: {len(errors)} failure(s)")
        for message in errors:
            print(f"FAIL: {message}")
        return 1
    print(json.dumps({
        "pwa_release_quality": "PASS",
        "git_sha": sha,
        "cache_namespace": cache,
        "release_bound_cache": True,
        "core_manifest": "/assets/site.webmanifest",
        "core_discovery_assets": 2,
        "legacy_cache_paths": 0,
        "failed_response_cache_risk": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
