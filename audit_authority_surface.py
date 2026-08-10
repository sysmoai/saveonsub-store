#!/usr/bin/env python3
"""Inventory authority-sensitive strings across SAVEONSUB source and public files.

Read-only. This is an evidence report, not a release gate by itself. The hard
release gate remains validate_release.py. It intentionally excludes audit/docs
history so historical evidence can retain old values without becoming public
operational authority.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
EXCLUDE_PARTS = {".git", "_site", "_preview_v3", "node_modules", "__pycache__", "docs", "reports"}
TEXT_SUFFIXES = {".py", ".html", ".js", ".css", ".xml", ".txt", ".md", ".json", ".toml", ".yml", ".yaml", ".sh"}

PATTERNS = {
    "stale_whatsapp_number": re.compile(r"(?:\+?880[ -]?1305[ -]?869242|8801305869242|01305869242)"),
    "whatsapp_url": re.compile(r"(?:wa\.me/|api\.whatsapp\.com|whatsapp)", re.I),
    "payment_destination_claim": re.compile(r"(?:merchant number|send money to|payment number|bank account|account number)", re.I),
    "shared_commerce": re.compile(r"(?:shared (?:plan|seat|account|subscription)|shared-low|shared-med|type[\"']?\s*:\s*[\"']shared)", re.I),
    "unsupported_proof": re.compile(r"(?:\b[0-9]{2,}[+]\s*(?:orders|customers|users)|bestseller_rank|lifetime orders|trusted in bangladesh)", re.I),
    "legal_operator_claim": re.compile(r"(?:operated by|legal operator|private limited|registered company)", re.I),
    "aips_operational_reference": re.compile(r"(?:aips-live|aipremiumshop\.com|AI Premium Shop)", re.I),
}


def files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in EXCLUDE_PARTS for part in path.relative_to(ROOT).parts):
            continue
        yield path


def main() -> int:
    report = {key: [] for key in PATTERNS}
    for path in files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(ROOT).as_posix()
        for key, pattern in PATTERNS.items():
            count = len(pattern.findall(text))
            if count:
                report[key].append({"path": rel, "matches": count})

    summary = {key: sum(item["matches"] for item in value) for key, value in report.items()}
    print(json.dumps({"summary": summary, "files": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
