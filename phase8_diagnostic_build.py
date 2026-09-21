#!/usr/bin/env python3
"""Temporary Phase 8 preview diagnostic wrapper.

This file is intentionally short-lived. It captures the canonical build output
into the protected Vercel preview artifact so a connector outage in Vercel build
logs cannot hide the exact failing step. Remove after diagnosis.
"""
from __future__ import annotations

import html
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "_site"
LOG = DEST / "phase8-diagnostic.txt"

proc = subprocess.run(
    [sys.executable, "build_site.py"],
    cwd=ROOT,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

if proc.returncode == 0:
    print(proc.stdout, end="")
    raise SystemExit(0)

DEST.mkdir(parents=True, exist_ok=True)
tail = proc.stdout[-30000:]
LOG.write_text(tail, encoding="utf-8")

# Ensure the preview can expose the diagnostic even if failure happened before
# stage_deploy created a complete artifact.
index = DEST / "index.html"
if not index.exists():
    index.write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"robots\" content=\"noindex,nofollow\">"
        "<title>Phase 8 diagnostic preview</title></head><body>"
        "<h1>Phase 8 diagnostic preview</h1>"
        "<p>Build intentionally captured for debugging; not production.</p>"
        "<pre>" + html.escape(tail[-12000:]) + "</pre></body></html>",
        encoding="utf-8",
    )

print(tail, end="")
print("\nPHASE8_DIAGNOSTIC_CAPTURED")
raise SystemExit(0)
