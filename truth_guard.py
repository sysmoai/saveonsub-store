#!/usr/bin/env python3
"""Fail builds when known P0 SaveOnSub truth/brand regressions return.

This guard blocks customer-facing claims/contact data that were verified as
wrong, stale, unsafe or incompatible with the approved operating rules. It also
ensures every SaveOnSub WhatsApp link uses the canonical public number from
site_config.py. It is not a substitute for human fact-checking of new claims.
"""
from pathlib import Path
import re
import sys

from site_config import BRAND_LOCK_MARKER, SUPPORT_PHONE_DIGITS

ROOT = Path(__file__).resolve().parent
EXCLUDE_DIRS = {'.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
                '__pycache__', 'node_modules', '_site', 'ops', 'reports'}
SOURCE_ALLOW = {
    'build_home.py', 'build_trust.py', 'build_pages.py', 'templates.py',
}

FORBIDDEN = {
    '1714-672094': 'retired/incorrect payment or support number',
    '১৭১৪-৬৭২০৯৪': 'retired/incorrect Bangla payment or support number',
    '8801714672094': 'retired/incorrect WhatsApp/payment number',
    '100% official, customer-owned': 'blanket official/customer-owned claim conflicts with shared plans',
    'No other BD store offers this': 'unsupported exclusivity claim',
    'বাংলাদেশে আর কেউ এটা দেয় না': 'unsupported Bangla exclusivity claim',
    "It's not illegal for you": 'unsupported legal conclusion',
    'Legally in Bangladesh: yes': 'unsupported legal conclusion',
    'আপনার জন্য এটা অবৈধ নয়': 'unsupported Bangla legal conclusion',
    'OpenAI only accepts international Visa/Mastercard': 'stale OpenAI Bangladesh payment claim',
    'Resellers are the only path': 'unsupported exclusivity/payment claim',
    'other seat-holders cannot see your chats': 'overbroad shared-access privacy guarantee',
    'শুধু খরচটা শেয়ার হয়, ডেটা কখনো নয়': 'overbroad Bangla shared-access privacy guarantee',
    'shared at ৳350': 'retired ChatGPT shared price wording',
    'shared from ৳350': 'retired ChatGPT shared price wording',
    'we sell at ৳350': 'retired ChatGPT shared price wording',
    'No shortcuts.': 'blanket official-only positioning conflicts with disclosed shared plans',
    'merchant number': 'account type is not independently verified; use neutral checkout payment wording',
    'মার্চেন্ট নম্বর': 'account type is not independently verified; use neutral checkout payment wording',
    "Bangladesh's trusted subscription OS": 'unsupported trust-superlative claim; use verifiable facts instead',
}

WA_RE = re.compile(r'https://wa\.me/(\d+)')


def should_scan(p: Path) -> bool:
    rel = p.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if p.suffix.lower() in {'.html', '.htm'}:
        return True
    return p.name in SOURCE_ALLOW


def main() -> int:
    hits = []
    for p in ROOT.rglob('*'):
        if not p.is_file() or not should_scan(p):
            continue
        try:
            text = p.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        rel = p.relative_to(ROOT).as_posix()
        for pattern, reason in FORBIDDEN.items():
            if pattern in text:
                hits.append((rel, pattern, reason))
        for number in WA_RE.findall(text):
            if number != SUPPORT_PHONE_DIGITS:
                hits.append((rel, f'wa.me/{number}', 'non-canonical SaveOnSub WhatsApp number'))

    # Public-repository data boundary: internal market-research metadata
    # must not be committed into the customer catalog or browser catalog.
    catalog = ROOT / 'catalog.json'
    if catalog.exists():
        ctext = catalog.read_text(encoding='utf-8', errors='replace')
        for key in ('\"market_survey\"', '\"competitor_watchlist\"'):
            if key in ctext:
                hits.append(('catalog.json', key, 'internal market-research metadata must stay outside the public catalog'))
    public_catalog = ROOT / 'assets/catalog.js'
    if public_catalog.exists():
        ptext = public_catalog.read_text(encoding='utf-8', errors='replace')
        for key in ('market_survey', 'competitor_watchlist'):
            if key in ptext:
                hits.append(('assets/catalog.js', key, 'internal market-research metadata leaked into browser catalog'))

    # Approved identity must remain the build source of truth.
    for rel in ('assets/logo.svg', 'assets/favicon.svg'):
        p = ROOT / rel
        if not p.exists():
            hits.append((rel, '<missing>', 'approved locked brand asset missing'))
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        if BRAND_LOCK_MARKER not in text:
            hits.append((rel, '<brand-lock>', 'approved brand-lock marker missing'))
        if '>৳<' in text or 'rotate(-12' in text:
            hits.append((rel, '<deprecated-art>', 'deprecated tilted ৳ logo artwork detected'))

    if hits:
        print(f'TRUTH GUARD FAILED — {len(hits)} regression(s) found:')
        for path, pattern, reason in hits:
            print(f'  {path}: {reason} :: {pattern!r}')
        return 1

    print('Truth guard OK — no known P0 claim/contact/brand regressions found.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
