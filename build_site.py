#!/usr/bin/env python3
"""Canonical Vercel build orchestrator.

Keep vercel.json's buildCommand short enough for Vercel schema limits while
preserving the exact ordered, fail-closed build pipeline.
"""
import subprocess
import sys

STEPS = [
    "check_prices.py",
    "stage_deploy.py",
    "release_hardening.py",
    "google_ai_cohort.py",
    "chatgpt_cohort.py",
    "design_cohort.py",
    "claude_cohort.py",
    "supergrok_cohort.py",
    "cache_safe_brand.py",
]


def main():
    for script in STEPS:
        print(f"BUILD STEP — {script}", flush=True)
        subprocess.run([sys.executable, script], check=True)
    print("Canonical site build OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
