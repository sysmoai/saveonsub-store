#!/usr/bin/env python3
"""Generate a private deterministic quality manifest for the staged SAVEONSUB artifact."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
META = ROOT / "_release_meta"
OUT = META / "quality-manifest.json"

SOURCE_FILES = (
    "catalog.json",
    "_headers",
    "_redirects",
    "sw.js",
    "manifest.webmanifest",
    "site_config.py",
    "authority_model.py",
    "catalog_model.py",
    "routes_v3.py",
    "media_registry.py",
    "build_public_info_v3.py",
    "extend_public_info_v3.py",
    "enhance_social_metadata_v3.py",
    "harden_public_info_v3.py",
    "stamp_release.py",
    "stage_deploy.py",
    "generate_release_manifest.py",
    "generate_quality_manifest.py",
    "validate_public_info_v3.py",
    "validate_l1_release.py",
    "validate_release.py",
    "validate_quality_gates.py",
    "validate_schema_quality.py",
    "validate_localization_quality.py",
    "validate_navigation_accessibility.py",
    "validate_social_metadata.py",
    "validate_pwa_release.py",
    "validate_security_policy.py",
    "verify_build_determinism.py",
    "assets/style.css",
    "assets/favicon.svg",
    "assets/logo.svg",
    "assets/icon-192.png",
    "assets/icon-512.png",
    "assets/apple-touch-icon.png",
)
SOURCE_DIRS = (
    "docs/control",
    "data/media",
    "assets/social",
)
GENERATOR_FILES = {
    "_headers",
    "_redirects",
    "sw.js",
    "manifest.webmanifest",
    "build_public_info_v3.py",
    "extend_public_info_v3.py",
    "enhance_social_metadata_v3.py",
    "harden_public_info_v3.py",
    "stamp_release.py",
    "stage_deploy.py",
    "catalog_model.py",
    "routes_v3.py",
    "site_config.py",
    "authority_model.py",
    "media_registry.py",
}


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path: pathlib.Path, base: pathlib.Path) -> dict[str, object]:
    return {
        "path": path.relative_to(base).as_posix(),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def aggregate(entries: list[dict[str, object]]) -> str:
    h = hashlib.sha256()
    for item in sorted(entries, key=lambda x: str(x["path"])):
        h.update(str(item["path"]).encode("utf-8"))
        h.update(b"\0")
        h.update(str(item["size"]).encode("ascii"))
        h.update(b"\0")
        h.update(str(item["sha256"]).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def source_paths() -> list[pathlib.Path]:
    found: set[pathlib.Path] = set()
    for rel in SOURCE_FILES:
        p = ROOT / rel
        if p.is_file():
            found.add(p)
    for rel in SOURCE_DIRS:
        base = ROOT / rel
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                found.add(p)
    return sorted(found)


def build_manifest_sha() -> str | None:
    p = SITE / "BUILD-MANIFEST.txt"
    return sha256_file(p) if p.is_file() else None


def git_sha() -> str:
    env_sha = (os.getenv("GITHUB_SHA") or os.getenv("VERCEL_GIT_COMMIT_SHA") or "").strip()
    if env_sha:
        return env_sha
    p = SITE / "BUILD-MANIFEST.txt"
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("git_sha="):
                return line.split("=", 1)[1].strip()
    return "unknown"


def sitemap_urls() -> list[str]:
    p = SITE / "sitemap.xml"
    if not p.is_file():
        return []
    root = ET.parse(p).getroot()
    urls: list[str] = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text:
            urls.append(node.text.strip())
    return urls


def main() -> int:
    if not SITE.is_dir():
        raise SystemExit("_site missing; stage the strict artifact first")

    source_entries = [entry(p, ROOT) for p in source_paths()]
    output_paths = sorted(p for p in SITE.rglob("*") if p.is_file())
    output_entries = [entry(p, SITE) for p in output_paths]
    authority_entries = [e for e in source_entries if str(e["path"]).startswith("docs/control/")]
    generator_entries = [e for e in source_entries if str(e["path"]) in GENERATOR_FILES]
    html_routes = sorted(p.relative_to(SITE).as_posix() for p in output_paths if p.suffix.lower() == ".html")
    urls = sitemap_urls()

    manifest = {
        "manifest_version": 1,
        "git_sha": git_sha(),
        "source": {
            "file_count": len(source_entries),
            "tree_sha256": aggregate(source_entries),
            "files": source_entries,
        },
        "authority": {
            "file_count": len(authority_entries),
            "tree_sha256": aggregate(authority_entries),
        },
        "generators": {
            "file_count": len(generator_entries),
            "tree_sha256": aggregate(generator_entries),
        },
        "output": {
            "file_count": len(output_entries),
            "tree_sha256": aggregate(output_entries),
            "build_manifest_sha256": build_manifest_sha(),
            "html_route_count": len(html_routes),
            "html_route_sha256": hashlib.sha256("\n".join(html_routes).encode("utf-8")).hexdigest(),
            "sitemap_url_count": len(urls),
            "sitemap_sha256": hashlib.sha256("\n".join(urls).encode("utf-8")).hexdigest(),
            "files": output_entries,
        },
    }

    META.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "quality_manifest": "generated",
        "git_sha": manifest["git_sha"],
        "source_files": len(source_entries),
        "generator_files": len(generator_entries),
        "output_files": len(output_entries),
        "html_routes": len(html_routes),
        "sitemap_urls": len(urls),
        "source_tree_sha256": manifest["source"]["tree_sha256"],
        "generator_tree_sha256": manifest["generators"]["tree_sha256"],
        "output_tree_sha256": manifest["output"]["tree_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
