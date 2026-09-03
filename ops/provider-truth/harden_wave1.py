#!/usr/bin/env python3
import json
from pathlib import Path

cpath = Path('catalog.json')
data = json.loads(cpath.read_text(encoding='utf-8'))
before = {p['id']: [pl.get('bdt') for pl in p.get('plans', [])] for p in data['products']}
byid = {p['id']: p for p in data['products']}

g = byid['google-ai-pro']
for plan in g.get('plans', []):
    if plan.get('label') == 'Personal (your Gmail) — 83% off special':
        plan['label'] = 'Personal (your Gmail)'
market = g.get('market', {})
if market.get('who') == 'AISubscriptionBD ৳1,500 · TechHaat ৳899 · our ৳500 is market leader':
    market['who'] = 'AISubscriptionBD ৳1,500 · TechHaat ৳899 · SaveOnSub ৳500 at survey date'

after = {p['id']: [pl.get('bdt') for pl in p.get('plans', [])] for p in data['products']}
assert before == after, 'SaveOnSub BDT selling price changed unexpectedly'
cpath.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Product-page generator: remove blanket ownership/official/price-match promises.
bp = Path('build_pages.py')
text = bp.read_text(encoding='utf-8')
old = '''  <div class="notice mt2">🧭 <b>Price-match guarantee:</b> Find a lower official price? We match it + 5% off. Every subscription is official, activated on YOUR own account, and 100% customer-owned.</div>
  <div class="notice mt2" style="font-size:12.5px;color:var(--muted);line-height:1.6"><b>Important Notice:</b> SAVEONSUB is not an official distributor, reseller, or partner of any subscription platform. We provide setup and activation support to help Bangladesh-based users access plans using local payment methods (bKash, Nagad, bank transfer). Your account is 100% customer-owned; we do not retain access to your credentials. If we cannot complete activation within the agreed window, you receive a full refund per our refund policy.</div>'''
new = '''  <div class="notice mt2">🧭 <b>Compare before buying:</b> Provider pricing, regional availability and plan features can change. Verify the linked official provider page, then compare the SaveOnSub access method, current BDT price and written warranty before ordering.</div>
  <div class="notice mt2" style="font-size:12.5px;color:var(--muted);line-height:1.6"><b>Independent service notice:</b> SAVEONSUB is an independent subscription access/setup service and does not claim official distributor or partner status unless a product page explicitly documents it. Access may be personal/customer-specific or shared depending on the selected plan; the access method and applicable warranty/refund terms are disclosed before payment. Do not use shared-access products for sensitive information.</div>'''
if old not in text:
    raise SystemExit('expected legacy product notice block not found')
bp.write_text(text.replace(old, new), encoding='utf-8')

# Historical Mode pages: keep the role/package concept but remove universal
# official/customer-owned/price-match assertions that conflict with shared plans.
mode_old_notice = '''<div class="notice green mt3">
    <b>🧭 Find a lower official price? We match it + 5% off.</b> All subscriptions in this Mode are 100% official, activated on YOUR own account.
  </div>'''
mode_new_notice = '''<div class="notice green mt3">
    <b>🧭 Compare before buying.</b> Provider pricing and availability can change. Verify the included products, exact access methods, current BDT price and written warranty before ordering.
  </div>'''
mode_old_important = '''<div class="notice mt3">
    <b>Important Notice:</b> SAVEONSUB is not an official distributor, reseller, or partner of any platform. We provide setup assistance and activation support to help Bangladesh-based users access subscription plans using local payment methods. Your account is 100% customer-owned; we do not retain access to your credentials. If we cannot complete activation within the agreed window, you receive a full refund.
  </div>'''
mode_new_important = '''<div class="notice mt3">
    <b>Independent service notice:</b> SAVEONSUB does not claim official distributor or partner status unless explicitly documented. Included products can use different access methods, including personal/customer-specific or shared access; verify each included product and the applicable warranty/refund terms before payment.
  </div>'''
for mp in sorted(Path('modes').glob('*.html')):
    s = mp.read_text(encoding='utf-8')
    s = s.replace('Official, customer-owned, activated on your account, paid in BDT via bKash.', 'Access type, BDT price and plan terms shown before payment.')
    s = s.replace('Official, customer-owned, Bangladesh-first.', 'Access-type transparent, Bangladesh-first.')
    s = s.replace('Role-based subscription pack — official, customer-owned, activated on your account', 'Role-based subscription pack — access method, price and warranty disclosed before payment')
    s = s.replace(mode_old_notice, mode_new_notice)
    s = s.replace(mode_old_important, mode_new_important)
    s = s.replace('100% customer-owned', 'access method disclosed before payment')
    s = s.replace('100% official', 'access-method specific')
    s = s.replace('activated on YOUR own account', 'delivered according to the selected access method')
    mp.write_text(s, encoding='utf-8')

# OS page: remove features/automation/competitor promises that are not implemented
# or cannot apply to every shared/personal product.
os_path = Path('os.html')
os = os_path.read_text(encoding='utf-8')
repls = {
    'Official, BD-first.': 'Access-type transparent, BD-first.',
    'Official, customer-owned, Bangladesh-first.': 'Access-type transparent, Bangladesh-first.',
    'activate it officially on your own account': 'activate the selected access method with plan details disclosed before payment',
    'Every other option in Bangladesh sells you a subscription and disappears. SAVEONSUB covers the full lifecycle — before, during, and after activation.': 'Many sellers focus mainly on activation. SAVEONSUB is designed to make plan type, ordering, support and renewal information easier to review before and after purchase.',
    'Choose a Mode or subscription, message us on WhatsApp, pay in BDT via bKash/Nagad, and we activate everything on YOUR own account — usually within 24 hours. 100% official. 100% customer-owned. No sharing, no gray market.': 'Choose a Mode or subscription, message us on WhatsApp, and pay using the options shown at checkout. Access may be personal/customer-specific or shared depending on the selected plan; the exact access method, delivery SLA and written warranty are disclosed before payment. Do not use shared access for sensitive information.',
    'Track all your active subscriptions in one place. WhatsApp reminders before expiry. One-tap renewal. Upgrade or downgrade anytime. Replacement support if anything stops working — warranty on every plan, in writing.': 'Use order tracking and the public WhatsApp support channel to review an order or renewal. Renewal is not automatic. Replacement or refund support follows the written terms shown for the selected plan.',
    'Subscription needs change. Our system watches for overpayments, suggests Mode upgrades when they genuinely save, and flags unused subscriptions. Eid discounts, seasonal optimization, and honest recommendations — never spam.': 'Subscription needs change. Use current guides, offers and product pages to compare whether your stack still makes sense. SAVEONSUB does not promise automated overpayment monitoring or proactive optimization alerts unless a specific service explicitly includes them.',
    '<tr><td>Account ownership</td><td>Often shared or unknown</td><td>100% customer-owned</td></tr>': '<tr><td>Access method</td><td>Varies by seller</td><td>Disclosed before payment</td></tr>',
    '<tr><td>Renewal</td><td>You track it yourself</td><td>WhatsApp reminders 3 days before</td></tr>': '<tr><td>Renewal</td><td>Varies by seller</td><td>Manual renewal support; no automatic charge</td></tr>',
    '<tr><td>Support</td><td>Disappears after sale</td><td>WhatsApp, Bangla + English, 7 days</td></tr>': '<tr><td>Support</td><td>Varies by seller</td><td>Public WhatsApp support in Bangla/English</td></tr>',
    '<tr><td>Optimization</td><td>No concept of it</td><td>Overpay alerts + Mode suggestions</td></tr>': '<tr><td>Optimization</td><td>Varies by seller</td><td>Guides, product comparisons and current offers</td></tr>',
    '<tr><td>Warranty</td><td>Usually none</td><td>In writing, replacement within 1 hour</td></tr>': '<tr><td>Warranty</td><td>Varies by seller</td><td>Written plan-specific terms</td></tr>',
    "Bangladesh's Subscription Operating System — official, customer-owned subscriptions paid in BDT.": "Bangladesh's subscription-access platform — access type and plan terms disclosed before payment, with BDT checkout options.",
}
for a, b in repls.items():
    os = os.replace(a, b)
os_path.write_text(os, encoding='utf-8')

# Make the truth guard enforce the newly cleaned boundaries permanently.
tg = Path('truth_guard.py')
t = tg.read_text(encoding='utf-8')
marker = "    'thousands of times daily': 'unsupported scam-frequency claim',\n}"
replacement = """    'thousands of times daily': 'unsupported scam-frequency claim',
    'Price-match guarantee:': 'price-match promise is not an evidenced global policy',
    'We match it + 5% off': 'price-match promise is not an evidenced global policy',
    'Every subscription is official': 'blanket official claim conflicts with shared/access-method disclosures',
    '100% customer-owned': 'blanket ownership claim conflicts with shared/access-method disclosures',
    '100% official': 'blanket official claim conflicts with shared/access-method disclosures',
    'activated on YOUR own account': 'blanket ownership/activation claim conflicts with shared access',
    'No sharing, no gray market': 'blanket no-sharing claim conflicts with shared plans',
    'WhatsApp reminders before expiry': 'proactive reminder automation is not implemented',
    'WhatsApp reminders 3 days before': 'proactive reminder automation is not implemented',
    'replacement within 1 hour': 'blanket replacement SLA requires plan-specific evidence',
    'our ৳500 is market leader': 'unsupported competitor leadership claim',
    '83% off special': 'hard-coded discount percentage can become stale when reference pricing changes',
}"""
if marker not in t:
    raise SystemExit('truth guard insertion marker not found')
tg.write_text(t.replace(marker, replacement), encoding='utf-8')

print('residual claim hardening applied across product generator, modes and OS; BDT prices preserved')
