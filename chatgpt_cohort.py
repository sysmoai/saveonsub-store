#!/usr/bin/env python3
"""Apply verified ChatGPT/OpenAI Bangladesh facts to staged money pages.

This release-time transformer preserves URL equity while fixing volatile provider
pricing/billing language and OpenAI account-sharing risk disclosures. It also
hardens the existing ChatGPT price guide until the legacy generators are refactored.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
FACTS = json.loads((ROOT / "ops" / "CHATGPT-COHORT-FACTS-2026-09-07.json").read_text(encoding="utf-8"))
VERIFIED = FACTS["verified_on"]
SOURCES = FACTS["official_sources"]

if not SITE.is_dir():
    raise SystemExit("ERROR: _site/ missing; run stage_deploy.py first")


def save(path, text):
    path.write_text(text, encoding="utf-8")


def replace_all(text):
    # Fixed FX conversions are not an official Bangladesh checkout price.
    text = re.sub(r'official reference ~?৳2,200', 'OpenAI reference $20/month; BDT web billing supported', text, flags=re.I)
    text = re.sub(r'official reference ~?৳880', 'OpenAI Go reference $8/month; localized pricing may apply', text, flags=re.I)
    text = re.sub(r'Official: ~?৳2,200/mo \(\$20\)', 'OpenAI reference: $20/month · BDT web billing supported', text)
    text = re.sub(r'Official: ~?৳880/mo \(\$8\)', 'OpenAI Go reference: $8/month · localized pricing may apply', text)
    text = re.sub(r'Official list converted at site anchor rate</td><td>~?৳2,200/mo', 'OpenAI published reference</td><td>$20/month; exact BDT shown at checkout', text)
    text = re.sub(r'Official list converted at site anchor rate</td><td>~?৳880/mo', 'OpenAI Go published reference</td><td>$8/month; localized checkout may differ', text)
    text = re.sub(r'<span class="savepct">[^<]*</span>\s*', '', text)

    # Remove unsafe reassurance / obsolete payment assertions wherever they occur.
    replacements = {
        'Your chats stay private — other users can\'t see them.': 'Do not assume shared-account chats or account data are private from other people who can access the same credentials.',
        'Your conversations remain private per-user.': 'Do not treat shared credentials as private: other people with account access may be able to see account activity or data.',
        'accepts only international cards': 'supports web card payments and localized billing in supported currencies, including BDT',
        'requiring an international card': 'with localized BDT web billing supported; exact checkout amount depends on the account/market',
        'card required': 'BDT web billing supported; verify your own checkout',
        'None — your own email': 'Lower sharing risk; verify exact activation method before payment',
        'Risk</th><th>Best for': 'Policy / privacy risk</th><th>Best for',
        'ToS violation → seat can reset (warranty covers)': 'Conflicts with OpenAI individual-account policy; privacy, continuity and suspension risk',
        'High — no warranty, no recourse': 'Seller/access risk varies; verify method and recourse',
        'seat-sharing violates OpenAI\'s terms, so seats occasionally get reset.': 'credential sharing conflicts with OpenAI\'s individual-account policy and can create privacy, misuse, continuity or account-restriction risk.',
        'The risk is seat interruption because sharing violates OpenAI ToS': 'Shared credentials conflict with OpenAI individual-account policy and can create privacy, misuse, continuity or suspension risk',
        'replace dead seats within 1 hour (7-day guarantee)': 'review the exact SaveOnSub warranty terms shown for the selected access method before payment',
        'replaces dead seats within 1 hour (7-day guarantee)': 'shows the applicable warranty terms before payment',
        'SHARED · LOW RISK': 'SHARED · POLICY RISK',
        'SHARED · WARRANTY COVERED': 'SHARED · POLICY RISK',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def plus_panel(lang='en'):
    if lang == 'bn':
        return f'''\n  <section class="notice mt2" data-chatgpt-facts="{VERIFIED}">
    <h2 style="font-size:22px;margin:0 0 10px">OpenAI reference — Bangladesh buyers যা জানবেন</h2>
    <ul style="margin:0;padding-left:20px;line-height:1.7">
      <li>ChatGPT Plus-এর published reference price <b>$20/month</b>; API usage আলাদা billing.</li>
      <li>OpenAI web billing-এ <b>BDT supported currency</b>. তাই fixed USD→BDT conversion-কে official Bangladesh price বলা ঠিক নয়; নিজের checkout amount verify করুন.</li>
      <li>OpenAI বলে individual account সেই ব্যক্তির জন্য যিনি account তৈরি করেছেন; credentials share করা উচিত নয়.</li>
      <li>Shared credentials নিলে privacy, misuse, continuity ও account restriction/suspension risk থাকতে পারে. Sensitive/work data-এর জন্য shared access ব্যবহার করবেন না.</li>
    </ul>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Verified {VERIFIED}. <a href="{SOURCES['plus_help']}" target="_blank" rel="noopener nofollow">Plus details ↗</a> · <a href="{SOURCES['multi_currency']}" target="_blank" rel="noopener nofollow">BDT billing ↗</a> · <a href="{SOURCES['account_sharing']}" target="_blank" rel="noopener nofollow">Account-sharing policy ↗</a></p>
  </section>'''
    return f'''\n  <section class="notice mt2" data-chatgpt-facts="{VERIFIED}">
    <h2 style="font-size:22px;margin:0 0 10px">OpenAI reference — what Bangladesh buyers should know</h2>
    <ul style="margin:0;padding-left:20px;line-height:1.7">
      <li>ChatGPT Plus has a published reference price of <b>$20/month</b>; API usage is billed separately.</li>
      <li><b>BDT is a supported currency</b> for ChatGPT web billing. A fixed USD→BDT conversion is therefore not the official Bangladesh checkout price; verify the amount shown in your own checkout.</li>
      <li>OpenAI states that an individual account is for the person who created it and that account credentials should not be shared.</li>
      <li>Shared credentials can create privacy, misuse, continuity and account-restriction/suspension risk. Do not use shared access for sensitive or work data.</li>
    </ul>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Verified {VERIFIED}. <a href="{SOURCES['plus_help']}" target="_blank" rel="noopener nofollow">Plus details ↗</a> · <a href="{SOURCES['multi_currency']}" target="_blank" rel="noopener nofollow">BDT billing ↗</a> · <a href="{SOURCES['account_sharing']}" target="_blank" rel="noopener nofollow">Account-sharing policy ↗</a></p>
  </section>'''


def go_panel(lang='en'):
    if lang == 'bn':
        return f'''\n  <section class="notice mt2" data-chatgpt-go-facts="{VERIFIED}">
    <h2 style="font-size:22px;margin:0 0 10px">ChatGPT Go বনাম Plus</h2>
    <p style="margin:0">OpenAI Go-এর published reference <b>$8/month</b> এবং Plus-এর <b>$20/month</b>. Localized pricing/limits বদলাতে পারে, তাই feature matrix ও নিজের checkout verify করুন. Go lower-cost personal tier; Plus broader model/tool access দেয়.</p>
  </section>'''
    return f'''\n  <section class="notice mt2" data-chatgpt-go-facts="{VERIFIED}">
    <h2 style="font-size:22px;margin:0 0 10px">ChatGPT Go vs Plus</h2>
    <p style="margin:0">OpenAI publishes Go at <b>$8/month</b> and Plus at <b>$20/month</b>. Localized pricing and limits can change, so verify the current feature matrix and your own checkout. Go is the lower-cost personal tier; Plus offers broader model/tool access.</p>
  </section>'''


def patch_product(path: Path, kind: str, lang='en'):
    text = replace_all(path.read_text(encoding="utf-8", errors="strict"))
    if kind == 'plus':
        marker = '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>' if lang == 'en' else '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>'
        panel = plus_panel(lang)
        # Ensure plan labels themselves do not imply provider authorization or low risk.
        text = text.replace('SHARED · LOW RISK', 'SHARED · POLICY RISK').replace('SHARED · WARRANTY COVERED', 'SHARED · POLICY RISK')
    else:
        marker = '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>' if lang == 'en' else '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>'
        panel = go_panel(lang)
    if ('data-chatgpt-facts=' not in text and kind == 'plus') or ('data-chatgpt-go-facts=' not in text and kind == 'go'):
        if marker not in text:
            raise SystemExit(f"ERROR: plan marker missing in {path}")
        text = text.replace(marker, panel + '\n  ' + marker, 1)
    save(path, text)


def patch_guide(path: Path):
    text = replace_all(path.read_text(encoding="utf-8", errors="strict"))
    # Replace stale title/description comparisons against a fake fixed official BDT amount.
    text = text.replace('ChatGPT Plus Price in Bangladesh (2026) — ৳499 vs ৳2,200', 'ChatGPT Plus Price in Bangladesh (2026) — Plans, BDT Billing & Risks')
    text = text.replace('ChatGPT Plus costs $20/mo officially (~৳2,200, card required). Real BD options compared: shared ৳499, personal ৳2,990, bKash payment — honest guide with risks.', 'ChatGPT Plus is $20/month as OpenAI’s published reference and BDT web billing is supported. Compare SaveOnSub options, payment paths, and shared-access policy/privacy risks.')
    text = re.sub(r'<h2 class="mt3" style="font-size:22px">The official price</h2>.*?</p>',
                  '<h2 class="mt3" style="font-size:22px">The official reference</h2><p class="sub" style="font-size:15px">OpenAI publishes ChatGPT Plus at <b>$20/month</b>. BDT is supported for ChatGPT web billing, so the exact Bangladesh checkout amount should be read from your own OpenAI checkout rather than calculated with a fixed exchange rate. API usage is separate.</p>', text, count=1, flags=re.S)
    if 'data-chatgpt-facts=' not in text:
        marker = '<h2 class="mt3" style="font-size:22px">Your real options in BD</h2>'
        if marker not in text:
            raise SystemExit('ERROR: ChatGPT guide insert marker missing')
        text = text.replace(marker, plus_panel('en') + '\n' + marker, 1)
    save(path, text)


for rel, kind, lang in [
    ('p/chatgpt-plus.html', 'plus', 'en'),
    ('bn/p/chatgpt-plus.html', 'plus', 'bn'),
    ('p/chatgpt-go.html', 'go', 'en'),
    ('bn/p/chatgpt-go.html', 'go', 'bn'),
]:
    path = SITE / rel
    if not path.exists():
        raise SystemExit(f"ERROR: missing staged page {rel}")
    patch_product(path, kind, lang)

blog = SITE / 'blog/chatgpt-plus-price-in-bangladesh.html'
if not blog.exists():
    raise SystemExit('ERROR: missing staged ChatGPT price guide')
patch_guide(blog)

# Fail closed on known stale/high-risk claims in the governed cohort.
for rel in [
    'p/chatgpt-plus.html', 'bn/p/chatgpt-plus.html',
    'p/chatgpt-go.html', 'bn/p/chatgpt-go.html',
    'blog/chatgpt-plus-price-in-bangladesh.html'
]:
    text = (SITE / rel).read_text(encoding='utf-8', errors='replace').lower()
    forbidden = [
        'official: ~৳2,200/mo', 'official: ~৳880/mo', 'official reference ~৳2,200',
        'your chats stay private', 'your conversations remain private per-user',
        'shared · low risk', 'shared · warranty covered', 'accepts only international cards'
    ]
    for phrase in forbidden:
        if phrase in text:
            raise SystemExit(f"ERROR: stale ChatGPT cohort phrase survived in {rel}: {phrase}")

plus = (SITE / 'p/chatgpt-plus.html').read_text(encoding='utf-8')
if f'data-chatgpt-facts="{VERIFIED}"' not in plus or 'BDT is a supported currency' not in plus:
    raise SystemExit('ERROR: verified ChatGPT Plus fact panel missing')
if 'SHARED · POLICY RISK' not in plus:
    raise SystemExit('ERROR: shared ChatGPT plans are not policy-risk labeled')

go = (SITE / 'p/chatgpt-go.html').read_text(encoding='utf-8')
if f'data-chatgpt-go-facts="{VERIFIED}"' not in go:
    raise SystemExit('ERROR: verified ChatGPT Go comparison panel missing')

print('ChatGPT cohort hardening OK — BDT billing, Plus/Go references and account-sharing risk enforced.')
