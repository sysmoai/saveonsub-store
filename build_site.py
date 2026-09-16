#!/usr/bin/env python3
"""Canonical staged-site build orchestrator.

Pricing v2 is projected only inside the build workspace. The committed raw catalog
remains an audit/history source; every public renderer consumes the governed
projection and the final commercial-truth pass runs after legacy cohort scripts.
"""
import subprocess
import sys

STEPS = [
    "check_prices.py",
    "provider_fact_freshness.py",
    "apply_pricing_v2.py",
    "build_catalog_public.py",
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
    "commercial_truth_v2.py",
    "audit_commercial_truth_v2.py",
]


def main():
    for script in STEPS:
        print(f"BUILD STEP — {script}", flush=True)
        subprocess.run([sys.executable, script], check=True)
    print("Canonical site build OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
