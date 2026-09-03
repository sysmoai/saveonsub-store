#!/usr/bin/env python3
import json
from pathlib import Path

# 1) Global catalog warranty copy must not imply a universal one-hour SLA or
# fixed coverage period for every access method/product.
cpath = Path('catalog.json')
data = json.loads(cpath.read_text(encoding='utf-8'))
before = {p['id']: [pl.get('bdt') for pl in p.get('plans', [])] for p in data['products']}
data.setdefault('meta', {})['warranty'] = (
    'SaveOnSub support follows the written warranty/refund terms for the selected '
    'plan or order. Coverage, replacement eligibility and resolution timing vary '
    'by product, access method and issue.'
)
after = {p['id']: [pl.get('bdt') for pl in p.get('plans', [])] for p in data['products']}
assert before == after, 'SaveOnSub BDT selling prices changed unexpectedly'
cpath.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# 2) Trust-page generator: preserve a warranty page, but make its terms
# explicitly product/order-specific rather than inventing universal durations.
bt = Path('build_trust.py')
s = bt.read_text(encoding='utf-8')
repls = {
    'Under the current SaveOnSub policy, applicable shared-plan warranty coverage is 7 days with a replacement target within 1 hour during support hours unless the product states otherwise; see the written warranty/refund pages for scope and exclusions.':
        'If a shared plan has a stated SaveOnSub warranty, the selected product/order terms control its coverage and remedy. Contact support with the order ID; replacement or refund eligibility depends on those written terms.',
    '<tr><td><span class="tos shared-med">Shared</span></td><td>7 days from delivery</td><td>Within 1 hour (support hours 9am–12am)</td><td>Refund for unused days</td></tr>':
        '<tr><td><span class="tos shared-med">Shared</span></td><td>Check selected plan/order terms</td><td>Depends on issue and coverage</td><td>Replacement/refund per written terms</td></tr>',
    '<tr><td><span class="tos personal">Personal</span></td><td>30 days from delivery</td><td>Within 1 hour</td><td>Full refund</td></tr>':
        '<tr><td><span class="tos personal">Personal</span></td><td>Check selected plan/order terms</td><td>Depends on issue and coverage</td><td>Replacement/refund per written terms</td></tr>',
    "Seat stops working, password reset by provider, account banned, plan downgraded by provider, activation failed. Basically: if what you paid for stops existing, we fix it or refund it.":
        'Covered events depend on the selected plan/order terms. If access stops working, contact support with your order ID and evidence; support will assess replacement or refund eligibility under those written terms.',
    "You broke the seat rules we told you at delivery (changing the password on a shared account, adding extra devices beyond the limit, reselling your seat), or provider-side feature changes that affect ALL users including official ones (e.g. a model being retired).":
        'Coverage can exclude customer-caused access changes, misuse, provider-wide feature changes, or circumstances listed in the selected plan/order terms. Review those terms before payment and before making account changes.',
    "WhatsApp <b>+880 1305-869242</b> with your order ID and a screenshot. That's the whole process — resolved within the 1-hour promise during support hours.":
        'WhatsApp <b>+880 1305-869242</b> with your order ID and a screenshot. Support will review the issue under the written terms for the selected plan/order and confirm the applicable remedy and timing.',
    '⏱️ Claims outside support hours (12am–9am) are handled first thing next morning — the warranty clock pauses, you lose nothing.':
        '⏱️ Messages outside support hours are reviewed when support resumes. The selected plan/order terms determine coverage and any applicable response or resolution timing.',
    'Warranty — 1-Hour Replacement | SAVEONSUB': 'Warranty & Support | SAVEONSUB',
    '7-day guarantee on shared seats, 30-day on personal plans, replacement within 1 hour. What\'s covered, what\'s not, and how to claim in one WhatsApp message.':
        'How SaveOnSub warranty and support claims work. Coverage, remedies and timing follow the written terms for the selected product or order.',
}
for a, b in repls.items():
    if a in s:
        s = s.replace(a, b)
bt.write_text(s, encoding='utf-8')

# 3) Transparency guide: remove legal conclusions, universal provider-ToS claims,
# zero-risk claims, ownership absolutes and one-hour warranty assertions.
blog = Path('blog/how-we-source-subscriptions-transparency.html')
b = blog.read_text(encoding='utf-8')
repls = {
    'No BD reseller publishes this. We do, because it is the only durable advantage.':
        'This guide explains the access labels SaveOnSub uses so buyers can compare trade-offs before payment.',
    'A real plan activated on YOUR own account via legitimate regional pricing/bulk channels':
        'Customer-specific access delivered according to the selected plan and provider conditions',
    '<td>None — your account, your data</td>': '<td>Lower sharing risk; provider/account conditions still apply</td>',
    'A seat on a multi-user plan the provider tolerates (e.g. Canva teams, family plans)':
        'Multi-user/shared access where the selected product explicitly discloses that access method',
    '<td>Low — rare interruption, warranty-covered</td>': '<td>Higher continuity/privacy risk than personal access; check written coverage</td>',
    'A seat on a plan whose ToS prohibits sharing — that is why it is cheapest':
        'Shared access with higher policy, continuity or privacy risk; provider rules vary by service',
    '<td>Seat can reset; 1-hour replacement warranty</td>': '<td>Access can change or stop; check the selected plan/order warranty terms</td>',
    'Buying a shared seat is <b>not illegal for you under BD law</b> — seat-sharing is a violation of the <i>provider\'s</i> terms of service (their contract with the account holder), not a crime you commit. The practical worst case for you is a seat reset, which our warranty fixes. We label every plan so you decide with full information — something no Facebook seller does.':
        'SAVEONSUB does not provide legal advice. Applicable law and provider terms vary by service, account type and access method. Shared credentials or seats can carry provider-policy, privacy and continuity risk. Check the selected plan label, official provider terms where available, and the written SaveOnSub warranty/refund terms before payment.',
    'It is not illegal for you under BD law — seat-sharing violates the provider\'s terms of service (a contract issue), not a crime. The practical risk is a seat reset, which SAVEONSUB\'s warranty replaces.':
        'SAVEONSUB does not provide legal advice. Applicable law and provider terms vary by service and access method; shared access can carry provider-policy, privacy and continuity risk. Review the selected plan terms before payment.',
    'Three ways: official (you pay the provider, we activate), personal (a real plan on your own account via regional pricing), and shared seats on multi-user plans — each honestly risk-labeled.':
        'SaveOnSub uses access labels such as official/provider-direct, personal/customer-specific and shared where applicable. The exact sourcing/activation method and provider conditions can differ by product, so verify the selected plan before payment.',
    'A seat can occasionally be reset because sharing violates provider ToS. That is why it is cheapest, and why SAVEONSUB covers it with a 1-hour replacement warranty.':
        'Shared access can stop working or change because of account, provider, seat or policy changes. Check the selected plan/order terms for the applicable SaveOnSub support, replacement or refund coverage.',
    'Exactly how we source official, personal and shared plans, what the ToS risk really is, and why we label it.':
        'How SaveOnSub labels official/provider-direct, personal/customer-specific and shared access, the trade-offs to review, and what to verify before payment.',
}
for a, c in repls.items():
    b = b.replace(a, c)
blog.write_text(b, encoding='utf-8')

# 4) Extend permanent source/public truth guard so these classes cannot return.
tg = Path('truth_guard.py')
t = tg.read_text(encoding='utf-8')
marker = "    '83% off special': 'hard-coded discount percentage can become stale when reference pricing changes',\n}"
addition = """    '83% off special': 'hard-coded discount percentage can become stale when reference pricing changes',
    'not illegal for you under BD law': 'unsupported legal conclusion',
    'It is not illegal for you': 'unsupported legal conclusion',
    'the provider tolerates': 'blanket provider-policy claim requires product-specific evidence',
    '1-hour replacement warranty': 'blanket replacement SLA requires plan-specific evidence',
    'the warranty clock pauses': 'blanket warranty timing promise requires written plan/order terms',
    'No BD reseller publishes this': 'unsupported competitor exclusivity claim',
}"""
if marker not in t:
    raise SystemExit('truth guard policy insertion marker not found')
tg.write_text(t.replace(marker, addition), encoding='utf-8')

print('global warranty and transparency policy hardening applied; BDT selling prices preserved')
