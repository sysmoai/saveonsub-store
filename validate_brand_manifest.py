#!/usr/bin/env python3
"""Fail-closed validation for SaveOnSub brand/manifest.json.

No external package is required. This validator protects the machine-readable
brand routing layer and the two locked master wrappers before any site build.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "brand" / "manifest.json"
SCHEMA_PATH = ROOT / "brand" / "manifest.schema.json"
REQUIRED_TOP = {
    "manifestVersion", "brand", "authority", "palette", "assets",
    "platformRouting", "socialMetadata", "blocked", "agentRules", "figma", "verification",
}
REQUIRED_BLOCKED = {
    "stacked-logo-production-master",
    "transparent-full-logo-original",
    "editable-vector-path-master",
}


def fail(message: str) -> None:
    print(f"BRAND MANIFEST ERROR — {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def git_blob_sha(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    load_json(SCHEMA_PATH)  # schema must itself remain valid JSON

    missing = sorted(REQUIRED_TOP - set(manifest))
    if missing:
        fail(f"missing top-level keys: {', '.join(missing)}")

    brand = manifest["brand"]
    if brand.get("name") != "SaveOnSub":
        fail("brand.name must be SaveOnSub")
    if brand.get("domain") != "https://saveonsub.com":
        fail("brand.domain drift")
    if brand.get("lockDate") != "2026-08-19" or brand.get("status") != "approved-locked":
        fail("brand lock date/status drift")

    verification = manifest["verification"]
    marker = verification.get("brandLockMarker")
    if marker != 'data-brand-lock="2026-08-19-approved"':
        fail("brand lock marker drift")

    assets = manifest["assets"]
    for key in ("horizontalLockup", "primaryIcon"):
        item = assets.get(key)
        if not isinstance(item, dict):
            fail(f"missing master asset entry: {key}")
        rel = item.get("path")
        if not rel:
            fail(f"{key} has no path")
        path = ROOT / rel
        if not path.is_file():
            fail(f"master asset missing: {rel}")
        text = path.read_text(encoding="utf-8", errors="strict")
        if marker not in text:
            fail(f"brand lock marker missing from {rel}")
        expected_sha = item.get("gitBlobSha")
        actual_sha = git_blob_sha(path)
        if expected_sha != actual_sha:
            fail(f"locked master byte drift: {rel} expected={expected_sha} actual={actual_sha}")
        if item.get("immutableArtwork") is not True:
            fail(f"{key} must declare immutableArtwork=true")

    known_paths = {
        item.get("path")
        for item in assets.values()
        if isinstance(item, dict) and item.get("path")
    }
    for surface, rel in manifest["platformRouting"].items():
        if rel not in known_paths:
            fail(f"platformRouting.{surface} points to an undeclared asset: {rel}")

    for key, item in assets.items():
        if not isinstance(item, dict):
            continue
        rel = item.get("path")
        if not rel:
            continue
        if item.get("generatedAtBuild"):
            if item.get("generatedBy") != "stage_deploy.py":
                fail(f"{key} generatedAtBuild but generatedBy is not stage_deploy.py")
        elif not (ROOT / rel).exists():
            fail(f"non-generated asset path missing: {rel}")

    social = manifest["socialMetadata"]
    image = social.get("image", {})
    if social.get("status") != "canonical-deterministic":
        fail("socialMetadata.status drift")
    if social.get("normalizer") != "stage_deploy.py::normalize_social_head":
        fail("socialMetadata.normalizer drift")
    if social.get("validator") != "validate_social_metadata.py":
        fail("socialMetadata.validator drift")
    if social.get("siteName") != "SaveOnSub":
        fail("socialMetadata.siteName drift")
    if image.get("path") != "assets/og-image.png":
        fail("socialMetadata.image.path drift")
    if image.get("url") != "https://saveonsub.com/assets/og-image.png":
        fail("socialMetadata.image.url drift")
    if (image.get("width"), image.get("height")) != (1200, 630):
        fail("socialMetadata image dimensions drift")
    if not image.get("alt"):
        fail("socialMetadata.image.alt missing")
    if social.get("twitterCard") != "summary_large_image":
        fail("socialMetadata.twitterCard drift")
    for surface in (
        "openGraphImage", "twitterLargeCardImage", "facebookShareImage",
        "linkedinShareImage", "messagingShareImage",
    ):
        if manifest["platformRouting"].get(surface) != "assets/og-image.png":
            fail(f"platformRouting.{surface} must use assets/og-image.png")
    if len(social.get("requiredOpenGraph", [])) < 10:
        fail("socialMetadata.requiredOpenGraph incomplete")
    if len(social.get("requiredTwitter", [])) < 5:
        fail("socialMetadata.requiredTwitter incomplete")

    blocked_ids = {
        item.get("id")
        for item in manifest["blocked"]
        if isinstance(item, dict)
    }
    if not REQUIRED_BLOCKED.issubset(blocked_ids):
        fail("required blocked-source entries are missing")
    for item in manifest["blocked"]:
        if item.get("status") != "blocked-source-required":
            fail(f"blocked asset {item.get('id')} must remain blocked-source-required")
        if not item.get("agentAction"):
            fail(f"blocked asset {item.get('id')} has no agentAction")

    for rel in (
        "BRAND-SYSTEM.md",
        "AGENTS.md",
        "brand/AI-BRAND-INSTRUCTIONS.md",
        "brand/README.md",
        "stage_deploy.py",
        "validate_social_metadata.py",
    ):
        if not (ROOT / rel).is_file():
            fail(f"authority file missing: {rel}")

    deploy = (ROOT / "stage_deploy.py").read_text(encoding="utf-8")
    for token in (
        "icon-maskable-512.png",
        "safe_icon = icon.resize((288, 288)",
        "((512 - 288) // 2, (512 - 288) // 2)",
        "def normalize_social_head():",
        "SOCIAL_IMAGE_URL = 'https://saveonsub.com/assets/og-image.png'",
        "twitter:card",
        "twitter:image:alt",
    ):
        if token not in deploy:
            fail(f"maskable derivative rule missing from stage_deploy.py: {token}")

    must = manifest["agentRules"].get("must", [])
    must_not = manifest["agentRules"].get("mustNot", [])
    if not must or not must_not:
        fail("agentRules.must and agentRules.mustNot must both be populated")

    print(
        "Brand manifest validation OK — locked master bytes, routing, "
        "blocked sources and derivative governance are consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
