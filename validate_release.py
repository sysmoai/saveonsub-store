#!/usr/bin/env python3
"""Fail-closed SAVEONSUB release integrity gate.

This gate intentionally blocks production while known P0 commercial/authority
conflicts remain. It is not a substitute for per-provider eligibility records;
it prevents the current unsafe state from being deployed as commerce.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CATALOG = ROOT / 'catalog.json'
LAUNCH = ROOT / 'docs/control/launch_state.json'
TERMS = ROOT / 'terms.html'

errors = []
warnings = []


def fail(code, message):
    errors.append((code, message))


def warn(code, message):
    warnings.append((code, message))


if not CATALOG.exists():
    fail('P0-CATALOG-MISSING', 'catalog.json is missing')
    catalog = {}
else:
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))

if not LAUNCH.exists():
    fail('P0-LAUNCH-STATE-MISSING', 'launch control record is missing')
    launch = {}
else:
    launch = json.loads(LAUNCH.read_text(encoding='utf-8'))

state = launch.get('state')
commerce_authorized = launch.get('commerce_authorized') is True
public_price_authorized = launch.get('public_price_authorized') is True
indexing_authorized = launch.get('indexing_authorized') is True

if state not in {'L0_BOOTSTRAP_PRIVATE', 'L1_PUBLIC_INFO_ONLY', 'L2_LIMITED_COMMERCE', 'L3_FULL_APPROVED_COMMERCE'}:
    fail('P0-LAUNCH-STATE-INVALID', f'unrecognized launch state: {state!r}')

products = catalog.get('products', [])
meta = catalog.get('meta', {})

# Cross-brand pricing provenance is not valid SAVEONSUB commercial authority.
for source in meta.get('price_precedence', []):
    if re.search(r'(^|[-_])aips($|[-_])', str(source), re.I):
        fail('P0-CROSS-BRAND-PRICE-SOURCE', f'active price precedence references AIPS: {source}')

# OpenAI consumer account-sharing commerce is prohibited by current provider policy.
# Fail on shared plans for ChatGPT/OpenAI-branded catalog records.
for product in products:
    pid = str(product.get('id', ''))
    name = str(product.get('name', ''))
    is_openai = pid.startswith('chatgpt') or 'chatgpt' in name.lower() or 'openai' in name.lower()
    for plan in product.get('plans', []):
        tos = str(plan.get('tos', '')).lower()
        label = str(plan.get('label', ''))
        plan_type = str(plan.get('type', '')).lower()
        if is_openai and (tos.startswith('shared') or plan_type == 'shared' or 'shared' in label.lower()):
            fail('P0-OPENAI-SHARED-COMMERCE', f'{name} / {label} is modeled as shared commerce')

    # Seeded/unproven social proof must not silently become production truth.
    if product.get('orders') not in (None, 0) and not product.get('orders_evidence'):
        fail('P1-UNVERIFIED-ORDER-COUNT', f'{name} has orders={product.get("orders")} without orders_evidence')
    if product.get('bestseller_rank') not in (None, 0) and not product.get('bestseller_evidence'):
        fail('P1-UNVERIFIED-BESTSELLER', f'{name} has bestseller_rank={product.get("bestseller_rank")} without bestseller_evidence')

# Terms cannot use disclosure/warranty as the mechanism that normalizes known ToS violations.
if TERMS.exists():
    terms_text = TERMS.read_text(encoding='utf-8', errors='replace')
    if re.search(r'shared seats violate most providers.? terms of service', terms_text, re.I):
        fail('P0-TERMS-NORMALIZE-PROHIBITED-SHARING', 'terms explicitly sell shared seats while acknowledging provider ToS violations')

# At L0/L1, generated commerce and public prices are blocked regardless of UI intent.
commerce_markers = []
price_markers = []
for path in list((ROOT / 'p').glob('*.html')) + list((ROOT / 'bn' / 'p').glob('*.html')):
    text = path.read_text(encoding='utf-8', errors='replace')
    if 'cartAdd(' in text or '"@type": "Offer"' in text or '"@type": "AggregateOffer"' in text:
        commerce_markers.append(path.relative_to(ROOT).as_posix())
    if re.search(r'৳\s*[0-9]', text):
        price_markers.append(path.relative_to(ROOT).as_posix())

if state in {'L0_BOOTSTRAP_PRIVATE', 'L1_PUBLIC_INFO_ONLY'} and commerce_markers:
    fail('P0-LAUNCH-COMMERCE-BLOCK', f'{len(commerce_markers)} generated product page(s) contain commerce while state={state}')
if not commerce_authorized and commerce_markers:
    fail('P0-COMMERCE-AUTHORITY-MISSING', 'commerce exists in generated output but commerce_authorized is false')
if not public_price_authorized and price_markers:
    fail('P0-PUBLIC-PRICE-AUTHORITY-MISSING', f'{len(price_markers)} generated product page(s) expose BDT prices without public price authority')

robots = ROOT / 'robots.txt'
if not indexing_authorized and robots.exists():
    robots_text = robots.read_text(encoding='utf-8', errors='replace')
    if re.search(r'(?mi)^Allow:\s*/\s*$', robots_text):
        fail('P1-INDEXING-STATE-MISMATCH', 'robots.txt allows global crawling while indexing_authorized is false')

for code, message in warnings:
    print(f'WARN {code}: {message}')

if errors:
    print(f'RELEASE BLOCKED: {len(errors)} integrity failure(s)')
    for code, message in errors:
        print(f'FAIL {code}: {message}')
    sys.exit(1)

print('release integrity gate passed')
