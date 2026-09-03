#!/usr/bin/env python3
"""Harden the staged SaveOnSub public artifact before any deployment.

This pass operates only on `_site/` after `stage_deploy.py`. It removes known
SEO/truth regressions from the public release without rewriting established
URLs or source catalog data. It is intentionally deterministic and fail-closed.
"""
from pathlib import Path
import re
import sys

SITE = Path('_site')

if not SITE.is_dir():
    print('ERROR: _site/ missing; run stage_deploy.py first.', file=sys.stderr)
    raise SystemExit(1)

REPLACEMENTS = {
    '🧭 <b>Price-match guarantee:</b> Find a lower official price? We match it + 5% off. Every subscription is official, activated on YOUR own account, and 100% customer-owned.':
        '🧭 <b>Access disclosure:</b> Access method varies by plan. Check the visible plan label and confirm the exact credential/invite method before payment.',
    '<b>Important Notice:</b> SAVEONSUB is not an official distributor, reseller, or partner of any subscription platform. We provide setup and activation support to help Bangladesh-based users access plans using local payment methods (bKash, Nagad, bank transfer). Your account is 100% customer-owned; we do not retain access to your credentials. If we cannot complete activation within the agreed window, you receive a full refund per our refund policy.':
        '<b>Important Notice:</b> SAVEONSUB is not an official distributor, reseller, or partner of the listed subscription platforms unless a specific page explicitly says otherwise. Access method, delivery terms and applicable refund/warranty terms vary by plan and must be confirmed before payment.',
    'SaveOnSub policy: replacement within 1 hour during support hours where the stated warranty applies; shared plans carry 7-day coverage and personal plans 30-day coverage unless a product page states otherwise.':
        'Warranty scope and replacement timing vary by product and plan. The applicable terms shown before payment control.',
    "SaveOnSub's written warranty policy currently targets replacement within 1 hour during support hours where the stated warranty applies; shared coverage is 7 days and personal coverage 30 days unless a product page states otherwise.":
        'Warranty scope and replacement timing vary by product and plan; use the terms shown before payment for the selected offer.',
    'Your chats stay private — other users can\'t see them. But seat-sharing violates OpenAI\'s terms, so seats occasionally get reset. That\'s WHY it\'s 84% cheaper. We label this on the product page and replace dead seats within 1 hour (7-day guarantee).':
        'Privacy and continuity depend on the exact access method. Shared credentials can expose activity or data to other people with access, and provider policies can change. Check the current plan disclosure before ordering.',
    'Your conversations remain private per-user. The risk is seat interruption because sharing violates OpenAI ToS — SAVEONSUB discloses this and covers it with a 1-hour replacement warranty.':
        'Privacy and continuity depend on the exact access method. Shared access can carry additional privacy, continuity and provider-policy risk; check the current plan disclosure before ordering.',
}

GENERIC_REPLACEMENTS = {
    '100% customer-owned': 'customer-specific where the selected plan explicitly says so',
    'we do not retain access to your credentials': 'credential handling depends on the selected access method and is disclosed before payment',
    'Every subscription is official': 'Every plan is labeled by access type',
}

FORBIDDEN_PUBLIC = {
    'Every subscription is official': 'blanket official claim',
    '100% customer-owned': 'blanket ownership claim',
    'we do not retain access to your credentials': 'blanket credential-access claim',
    'Price-match guarantee': 'unsupported blanket price-match promise',
    'replace dead seats within 1 hour': 'unsupported blanket replacement SLA',
    'Your chats stay private — other users can\'t see them': 'absolute shared privacy claim',
    'Your conversations remain private per-user': 'absolute shared privacy claim',
}

changed = 0
for path in SITE.rglob('*.html'):
    text = path.read_text(encoding='utf-8', errors='replace')
    original = text

    text = re.sub(r'\n?<meta name="keywords" content="[^"]*">', '', text)
    text = re.sub(
        r'\n\s*<h2 class="mt3" style="font-size:20px">Commonly searched as</h2>\s*'
        r'<p[^>]*>.*?</p>\s*(?:<p[^>]*>.*?</p>\s*)?'
        r'<p[^>]*>However you search it,.*?</p>',
        '', text, flags=re.S,
    )

    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    for old, new in GENERIC_REPLACEMENTS.items():
        text = text.replace(old, new)

    # First-party attribution only: no external network request is introduced.
    # Absolute path works on every nested EN/BN/category/product page.
    if '/assets/measurement.js' not in text and '</body>' in text:
        text = text.replace('</body>', '<script src="/assets/measurement.js" defer></script>\n</body>')

    if text != original:
        path.write_text(text, encoding='utf-8')
        changed += 1

robots = SITE / 'robots.txt'
if robots.exists():
    r = robots.read_text(encoding='utf-8', errors='replace')
    if 'User-agent: OAI-SearchBot' not in r:
        marker = '# AI crawlers welcome — see llms.txt for structured store facts\n'
        addition = 'User-agent: OAI-SearchBot\nAllow: /\n\n'
        r = r.replace(marker, marker + addition) if marker in r else r + '\n' + addition
        robots.write_text(r, encoding='utf-8')

llms = SITE / 'llms.txt'
if llms.exists():
    text = llms.read_text(encoding='utf-8', errors='replace')
    text = re.sub(r'^\s*searched:.*$', '', text, flags=re.M)
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    for old, new in GENERIC_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r'\n{3,}', '\n\n', text)
    llms.write_text(text, encoding='utf-8')

measurement = SITE / 'assets' / 'measurement.js'
if not measurement.exists():
    print('RELEASE HARDENING FAILED — staged measurement.js missing.', file=sys.stderr)
    raise SystemExit(1)

hits = []
html_pages = list(SITE.rglob('*.html'))
for path in html_pages + [p for p in (SITE / 'llms.txt',) if p.exists()]:
    text = path.read_text(encoding='utf-8', errors='replace')
    for phrase, reason in FORBIDDEN_PUBLIC.items():
        if phrase in text:
            hits.append((path.as_posix(), phrase, reason))
    if 'Commonly searched as' in text:
        hits.append((path.as_posix(), 'Commonly searched as', 'visible keyword-dump block'))
    if '<meta name="keywords"' in text:
        hits.append((path.as_posix(), '<meta name="keywords"', 'obsolete generated keyword meta tag'))
    if path.suffix == '.html' and '/assets/measurement.js' not in text:
        hits.append((path.as_posix(), '/assets/measurement.js', 'first-party attribution script missing'))

if hits:
    print(f'RELEASE HARDENING FAILED — {len(hits)} unsafe staged item(s):', file=sys.stderr)
    for path, phrase, reason in hits[:50]:
        print(f'  {path}: {reason}: {phrase!r}', file=sys.stderr)
    raise SystemExit(1)

print(f'Release hardening OK — {changed} HTML files normalized; robots/llms/measurement policy checked.')
