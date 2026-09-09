#!/usr/bin/env python3
"""Canonical staged-site build orchestrator.

Keep vercel.json's buildCommand short enough for Vercel schema limits while
preserving the exact ordered, fail-closed build pipeline used to validate the
same hardened artifact intended for canonical Cloudflare Pages production.
"""
import subprocess
import sys

STEPS = [
    "check_prices.py",
    "catalog_source_hardening.py",
    "stage_deploy.py",
    "release_hardening.py",
    "google_ai_cohort.py",
    "chatgpt_cohort.py",
    "design_cohort.py",
    "claude_cohort.py",
    "supergrok_cohort.py",
    "perplexity_cohort.py",
    "entertainment_cohort.py",
    "runway_cohort.py",
    "trust_cohort.py",
    "homepage_truth_cohort.py",
    "cache_safe_brand.py",
    "technical_seo_hardening.py",
]


def main():
    for script in STEPS:
        print(f"BUILD STEP — {script}", flush=True)
        subprocess.run([sys.executable, script], check=True)
    print("Canonical site build OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
