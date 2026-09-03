#!/usr/bin/env python3
"""SaveOnSub locked-brand asset validator.

The pre-2026-08-19 asset generator used a tilted price-tag + ৳ concept and is
permanently retired. This filename is intentionally kept so an old runbook or
human command such as `python build_assets.py` cannot silently regenerate the
deprecated identity.

This script is validation-only. Production derivatives are created from the
approved locked master assets during the safe staging process; this file must
never draw or approximate the logo.
"""
from pathlib import Path
import sys

LOCK = 'data-brand-lock="2026-08-19-approved"'
REQUIRED = ('assets/logo.svg', 'assets/favicon.svg')


def main() -> int:
    failures = []
    for rel in REQUIRED:
        p = Path(rel)
        if not p.exists():
            failures.append(f'missing {rel}')
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        if LOCK not in text:
            failures.append(f'{rel} is not the approved locked asset')
        if '>৳<' in text or 'rotate(-12' in text:
            failures.append(f'{rel} contains deprecated tilted-৳ artwork')

    if failures:
        print('BRAND ASSET VALIDATION FAILED:')
        for item in failures:
            print(f'  - {item}')
        return 1

    print('Brand asset validation OK — approved 2026-08-19 logo and icon are locked.')
    print('No artwork was generated. The legacy tilted-৳ generator is retired.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
