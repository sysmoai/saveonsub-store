#!/usr/bin/env python3
"""Run the deterministic social metadata normalizer on the final staged site.

This deliberately runs after all cohort/content/SEO mutators so Open Graph and
Twitter metadata reflect the final page truth rather than an earlier staged copy.
"""
from stage_deploy import normalize_social_head


def main() -> int:
    normalize_social_head()
    print("Final social metadata normalization OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
