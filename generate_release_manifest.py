#!/usr/bin/env python3
"""Generate a non-public cryptographic manifest for a staged SAVEONSUB release."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

from catalog_model import load_catalog

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
OUT_DIR = ROOT / "_release_meta"
OUT = OUT_DIR / "release-manifest.json"

CONTROL_FILES = [
    ROOT / "docs/control/launch_state.json",
    ROOT / "docs/control/contact_authority.json",
    ROOT / "docs/control/payment_authority.json",
    ROOT / "docs/control/pricing_authority.json",
    ROOT / "docs/control/provider_eligibility.json",
    ROOT / "docs/control/legal_authority.json",
]


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(root: pathlib.Path) -> tuple[str, int, int]:
    h = hashlib.sha256()
    count = 0
    size = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        stat = path.stat()
        count += 1
        size += stat.st_size
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest(), count, size


def main() -> int:
    if not SITE.is_dir():
        raise SystemExit("_site missing; stage the strict release first")
    build_manifest = SITE / "BUILD-MANIFEST.txt"
    if not build_manifest.is_file():
        raise SystemExit("_site/BUILD-MANIFEST.txt missing")

    git_sha = (os.getenv("GITHUB_SHA") or os.getenv("SAVEONSUB_RELEASE_SHA") or "").strip().lower()
    if len(git_sha) != 40:
        raise SystemExit("release SHA missing or invalid")

    catalog = load_catalog()
    products = catalog.get("products", [])
    plans = [plan for product in products for plan in product.get("plans", [])]
    media = [item for product in products for item in product.get("media_v3", [])]
    site_hash, file_count, byte_count = tree_hash(SITE)

    control_hashes = {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in CONTROL_FILES}
    payload = {
        "schema": "saveonsub-release-manifest-v1",
        "git_sha": git_sha,
        "release_mode": "L1_PUBLIC_INFO_ONLY",
        "site_tree_sha256": site_hash,
        "site_file_count": file_count,
        "site_bytes": byte_count,
        "catalog_source_sha256": sha256_file(ROOT / "catalog.json"),
        "control_sha256": control_hashes,
        "product_count": len(products),
        "plan_count": len(plans),
        "media_reference_count": len(media),
        "build_manifest_sha256": sha256_file(build_manifest),
    }
    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
