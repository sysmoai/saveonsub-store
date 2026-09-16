#!/usr/bin/env python3
"""Remove stale legacy commercial residues after all historical cohorts have run.

This sanitizer is deliberately narrow: it operates only on final staged AI money
pages governed by pricing-v2. The raw historical catalog remains untouched for
auditability, while crawler/browser HTML cannot leak superseded shared-plan prices
or merchandising claims after the governed main content has been projected.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"

TARGETS = {
    "p/chatgpt-plus.html": (
        "৳499",
        "৳999",
        "৳2,990",
        "Starter Shared (6–8 users)",
        "Premium Shared (2–3 users)",
        "SHARED · POLICY RISK",
        "SHARED · WARRANTY COVERED",
        "SAVE 77%",
        "5–15 min",
        "5-15 min",
    ),
}


def main() -> int:
    changed = 0
    for rel, blocked in TARGETS.items():
        path = SITE / rel
        if not path.exists():
            raise SystemExit(f"[pricing-v2-legacy-sanitizer] missing governed artifact: {rel}")
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        for phrase in blocked:
            text = text.replace(phrase, "")
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed += 1
        lower = text.lower()
        for phrase in blocked:
            if phrase.lower() in lower:
                raise SystemExit(f"[pricing-v2-legacy-sanitizer] {rel} still contains {phrase!r}")
    print(f"[pricing-v2-legacy-sanitizer] sanitized {changed} governed artifact(s); raw catalog retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
