#!/usr/bin/env python3
"""Rebuild SAVEONSUB strict L1 twice and prove staged bytes are deterministic."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
COMMANDS = (
    (sys.executable, "build_public_info_v3.py"),
    (sys.executable, "harden_public_info_v3.py"),
    (sys.executable, "stamp_release.py"),
    (sys.executable, "validate_public_info_v3.py"),
    (sys.executable, "validate_l1_release.py"),
    (sys.executable, "stage_deploy.py", "--public-v3"),
)


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def site_digest() -> tuple[str, int, int]:
    if not SITE.is_dir():
        raise RuntimeError("_site missing after strict build")
    h = hashlib.sha256()
    files = sorted(p for p in SITE.rglob("*") if p.is_file())
    total = 0
    for p in files:
        rel = p.relative_to(SITE).as_posix()
        size = p.stat().st_size
        total += size
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(str(size).encode("ascii"))
        h.update(b"\0")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest(), len(files), total


def run_build() -> tuple[str, int, int]:
    env = os.environ.copy()
    for command in COMMANDS:
        print("+", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, env=env, check=True)
    return site_digest()


def main() -> int:
    first = run_build()
    second = run_build()
    if first != second:
        print(json.dumps({
            "deterministic": False,
            "first": {"tree_sha256": first[0], "file_count": first[1], "bytes": first[2]},
            "second": {"tree_sha256": second[0], "file_count": second[1], "bytes": second[2]},
        }, indent=2))
        return 1
    print(json.dumps({
        "deterministic": True,
        "tree_sha256": first[0],
        "file_count": first[1],
        "bytes": first[2],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
