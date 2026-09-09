#!/usr/bin/env python3
"""Normalize known stale/high-risk generic claims in catalog.json before generation.

This operates on the CI/deployment working copy only. It moves truth protection
upstream so generated pages do not depend solely on post-generation cleanup.
The repository source remains reviewable, while every canonical candidate is
built from a normalized catalog and fails closed if forbidden phrases survive.
"""
from pathlib import Path
import json
import sys

CATALOG = Path("catalog.json")
if not CATALOG.is_file():
    raise SystemExit("CATALOG SOURCE HARDENING ERROR — catalog.json missing")

REPLACEMENTS = {
    "Shared seats work the same as personal on mobile — the seat type doesn't affect functionality.": "Mobile availability depends on the provider and exact access method. Shared access can differ from personal access in privacy, continuity, sign-in method and provider-policy risk.",
    "Shared seats work the same as personal on mobile — the seat type doesn’t affect functionality.": "Mobile availability depends on the provider and exact access method. Shared access can differ from personal access in privacy, continuity, sign-in method and provider-policy risk.",
    "You get whatever the provider ships — same as an official subscriber.": "Provider features and models can change. What you receive depends on the exact plan and access method disclosed for your order.",
    "Model upgrades (like GPT-4 to GPT-5) are automatically included.": "Provider model availability and upgrade eligibility depend on the exact provider plan and can change over time.",
    "If a provider retires a model or changes pricing, we update the product page and notify active subscribers within 24 hours.": "If a provider retires a model or changes pricing, SaveOnSub updates product information after the change is verified; timing can vary.",
    "Gemini (Google AI Pro) gives you 2TB storage on top of AI — our #1 seller at ৳500.": "Google AI Pro combines Google AI features with Google One storage. Check Google's current Bangladesh plan page and the current SaveOnSub offer before choosing."
}

FORBIDDEN = [
    "Shared seats work the same as personal on mobile",
    "seat type doesn't affect functionality",
    "seat type doesn’t affect functionality",
    "You get whatever the provider ships — same as an official subscriber.",
    "Model upgrades (like GPT-4 to GPT-5) are automatically included.",
    "notify active subscribers within 24 hours",
    "2TB storage on top of AI — our #1 seller at ৳500"
]

def walk(value):
    if isinstance(value, dict): return {k: walk(v) for k, v in value.items()}
    if isinstance(value, list): return [walk(v) for v in value]
    if isinstance(value, str):
        for old, new in REPLACEMENTS.items(): value = value.replace(old, new)
    return value

def strings(value):
    if isinstance(value, dict):
        for v in value.values(): yield from strings(v)
    elif isinstance(value, list):
        for v in value: yield from strings(v)
    elif isinstance(value, str): yield value

def main():
    try: data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except Exception as exc: raise SystemExit(f"CATALOG SOURCE HARDENING ERROR — invalid JSON: {exc}")
    data = walk(data)
    corpus = list(strings(data))
    hits = [p for p in FORBIDDEN if any(p.lower() in s.lower() for s in corpus)]
    if hits:
        print("CATALOG SOURCE HARDENING FAILED — forbidden source claims survived:", file=sys.stderr)
        for p in hits: print(f"  {p}", file=sys.stderr)
        raise SystemExit(1)
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Catalog source hardening OK — stale generic shared-access/model/Google-AI claims normalized before generation.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
