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

bp = Path('build_pages.py')
text = bp.read_text(encoding='utf-8')
old = '''  <div class="notice mt2">🧭 <b>Price-match guarantee:</b> Find a lower official price? We match it + 5% off. Every subscription is official, activated on YOUR own account, and 100% customer-owned.</div>
  <div class="notice mt2" style="font-size:12.5px;color:var(--muted);line-height:1.6"><b>Important Notice:</b> SAVEONSUB is not an official distributor, reseller, or partner of any subscription platform. We provide setup and activation support to help Bangladesh-based users access plans using local payment methods (bKash, Nagad, bank transfer). Your account is 100% customer-owned; we do not retain access to your credentials. If we cannot complete activation within the agreed window, you receive a full refund per our refund policy.</div>'''
new = '''  <div class="notice mt2">🧭 <b>Compare before buying:</b> Provider pricing, regional availability and plan features can change. Verify the linked official provider page, then compare the SaveOnSub access method, current BDT price and written warranty before ordering.</div>
  <div class="notice mt2" style="font-size:12.5px;color:var(--muted);line-height:1.6"><b>Independent service notice:</b> SAVEONSUB is an independent subscription access/setup service and does not claim official distributor or partner status unless a product page explicitly documents it. Access may be personal/customer-specific or shared depending on the selected plan; the access method and applicable warranty/refund terms are disclosed before payment. Do not use shared-access products for sensitive information.</div>'''
if old not in text:
    raise SystemExit('expected legacy product notice block not found')
bp.write_text(text.replace(old, new), encoding='utf-8')

tg = Path('truth_guard.py')
t = tg.read_text(encoding='utf-8')
marker = "    'thousands of times daily': 'unsupported scam-frequency claim',\n}"
replacement = """    'thousands of times daily': 'unsupported scam-frequency claim',
    'Price-match guarantee:': 'price-match promise is not an evidenced global policy',
    'Every subscription is official': 'blanket official claim conflicts with shared/access-method disclosures',
    '100% customer-owned': 'blanket ownership claim conflicts with shared/access-method disclosures',
    'our ৳500 is market leader': 'unsupported competitor leadership claim',
    '83% off special': 'hard-coded discount percentage can become stale when reference pricing changes',
}"""
if marker not in t:
    raise SystemExit('truth guard insertion marker not found')
tg.write_text(t.replace(marker, replacement), encoding='utf-8')

print('residual claim hardening applied; BDT prices preserved')
