#!/usr/bin/env python3
"""Apply verified Google AI Bangladesh facts to staged money pages.

This is a deterministic release-time cohort transformer. It preserves existing
ranking URLs while replacing stale official references, unsupported savings/social
proof, and injecting current decision-helping information verified on 2026-09-04.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
FACTS_PATH = ROOT / "ops" / "GOOGLE-AI-COHORT-FACTS-2026-09-04.json"

if not SITE.is_dir():
    print("ERROR: _site/ missing; run stage_deploy.py first.", file=sys.stderr)
    raise SystemExit(1)

facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
verified_on = facts["verified_on"]
source = facts["official_source"]
student = facts["student_offer"]
plans = facts["official_plans"]


def cohort_panel(lang="en"):
    plus = plans["google-ai-plus"]
    pro = plans["google-ai-pro"]
    if lang == "bn":
        return f'''\n  <section class="notice mt2" data-google-ai-facts="{verified_on}">
    <h2 style="font-size:22px;margin:0 0 10px">Google AI Plus বনাম Pro — বাংলাদেশ</h2>
    <div class="tbl"><table>
      <tr><th>প্ল্যান</th><th>Google-এর BD দাম</th><th>স্টোরেজ</th><th>Free-এর তুলনায় usage</th><th>Flow credits/মাস</th></tr>
      <tr><td>Google AI Plus</td><td>৳{plus['official_bdt_month']:,}/মাস</td><td>{plus['storage']}</td><td>{plus['usage_vs_free']}</td><td>{plus['flow_credits_month']}</td></tr>
      <tr><td>Google AI Pro</td><td>৳{pro['official_bdt_month']:,}/মাস</td><td>{pro['storage']}</td><td>{pro['usage_vs_free']}</td><td>{pro['flow_credits_month']:,}</td></tr>
    </table></div>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Google Bangladesh subscription page থেকে {verified_on} তারিখে যাচাই করা। Provider feature/limit বদলাতে পারে। <a href="{source}" target="_blank" rel="noopener nofollow">Google-এ বর্তমান তথ্য দেখুন ↗</a></p>
  </section>
  <section class="notice green mt2" data-student-offer="{student['claim_deadline']}">
    🎓 <b>Eligible college student হলে আগে Google-এর free offer check করুন:</b> Google বর্তমানে eligible 18+ college students-এর জন্য {student['plan']} ১ বছর ৳0 অফার দেখাচ্ছে; claim deadline {student['claim_deadline']}. Offer শেষে current regular price অনুযায়ী auto-renew হতে পারে। <a href="{student['official_source']}" target="_blank" rel="noopener nofollow">Eligibility/terms যাচাই ↗</a>
  </section>'''
    return f'''\n  <section class="notice mt2" data-google-ai-facts="{verified_on}">
    <h2 style="font-size:22px;margin:0 0 10px">Google AI Plus vs Pro — Bangladesh</h2>
    <div class="tbl"><table>
      <tr><th>Plan</th><th>Google BD price</th><th>Storage</th><th>Usage vs free</th><th>Flow credits/mo</th></tr>
      <tr><td>Google AI Plus</td><td>৳{plus['official_bdt_month']:,}/mo</td><td>{plus['storage']}</td><td>{plus['usage_vs_free']}</td><td>{plus['flow_credits_month']}</td></tr>
      <tr><td>Google AI Pro</td><td>৳{pro['official_bdt_month']:,}/mo</td><td>{pro['storage']}</td><td>{pro['usage_vs_free']}</td><td>{pro['flow_credits_month']:,}</td></tr>
    </table></div>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Verified against Google’s Bangladesh subscription page on {verified_on}. Provider features and limits can change. <a href="{source}" target="_blank" rel="noopener nofollow">Check current Google details ↗</a></p>
  </section>
  <section class="notice green mt2" data-student-offer="{student['claim_deadline']}">
    🎓 <b>Eligible college student? Check Google’s free offer before buying:</b> Google currently advertises {student['plan']} for 1 year at ৳0 for eligible 18+ college students, with a claim deadline of {student['claim_deadline']}. After the offer, auto-renewal may apply at the then-current regular price. <a href="{student['official_source']}" target="_blank" rel="noopener nofollow">Verify eligibility and terms ↗</a>
  </section>'''


def patch_page(path: Path, product_id: str, lang="en"):
    text = path.read_text(encoding="utf-8", errors="strict")
    official = plans[product_id]["official_bdt_month"]
    storage = "5 TB" if product_id == "google-ai-pro" else "400 GB"

    if lang == "en":
        text = re.sub(r'<span class="official">Official: ~?৳[\d,]+/mo(?: \([^<]+\))?</span>',
                      f'<span class="official">Google Bangladesh: ৳{official:,}/mo</span>', text, count=1)
        text = re.sub(r'<span class="savepct">[^<]*</span>\s*', '', text, count=1)
        text = re.sub(r'Official list converted at site anchor rate</td><td>~?৳[\d,]+/mo',
                      f'Google Bangladesh official page</td><td>৳{official:,}/mo', text, count=1)
        insert_marker = '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>'
    else:
        text = re.sub(r'<span class="official">অফিসিয়াল: ~?৳[\d,]+/মাস</span>',
                      f'<span class="official">Google Bangladesh: ৳{official:,}/মাস</span>', text, count=1)
        text = re.sub(r'<span class="savepct">[^<]*</span>\s*', '', text, count=1)
        text = re.sub(r'Official list, site anchor rate-এ converted</td><td>~?৳[\d,]+/মাস',
                      f'Google Bangladesh official page</td><td>৳{official:,}/মাস', text, count=1)
        insert_marker = '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>'

    text = text.replace('https://one.google.com/about/google-ai-plans/', source)
    text = text.replace('2TB Google One storage', f'{storage} storage')
    text = text.replace('2TB storage', f'{storage} storage')
    text = text.replace('Personal (your Gmail) — 83% off special', 'Personal (your Gmail)')

    # Remove/neutralize unsupported portfolio proof and absolute value claims.
    text = re.sub(r'<details><summary>Why our #1 seller\?</summary><p>.*?</p></details>', '', text, flags=re.S)
    text = re.sub(r'<details><summary>Why is Google AI Pro our #1 seller at ৳500\?</summary><p>.*?</p></details>', '', text, flags=re.S)
    text = re.sub(r'211\+ orders[^<\"]*', 'Current SaveOnSub plan details are shown on this page. ', text)
    text = text.replace('our #1 seller at ৳500', 'a current SaveOnSub option')
    text = text.replace('our #1 seller', 'a current SaveOnSub option')
    text = text.replace('This is the best single-AI value in BD — lower risk than shared, better value than official.',
                        'Compare the access method, Google’s current Bangladesh price, and the exact SaveOnSub terms before choosing.')
    text = text.replace('our ৳500 is market leader', 'SaveOnSub listed ৳500 in that historical snapshot')

    if 'data-google-ai-facts=' not in text:
        if insert_marker not in text:
            raise RuntimeError(f"insert marker missing in {path}")
        text = text.replace(insert_marker, cohort_panel(lang) + '\n  ' + insert_marker, 1)

    text = re.sub(r'official reference ~?৳[\d,]+', f'Google Bangladesh reference ৳{official:,}', text)
    text = re.sub(r'official ~?৳[\d,]+', f'Google Bangladesh ৳{official:,}', text)
    path.write_text(text, encoding="utf-8")


for pid in ("google-ai-pro", "google-ai-plus"):
    for lang, rel in (("en", Path("p") / f"{pid}.html"), ("bn", Path("bn") / "p" / f"{pid}.html")):
        path = SITE / rel
        if not path.exists():
            raise SystemExit(f"ERROR: missing staged Google AI page: {rel}")
        patch_page(path, pid, lang)

checks = {
    "p/google-ai-pro.html": ["2TB", "83% off special", "our #1 seller", "211+ orders", "market leader", "official reference ~৳2,199"],
    "bn/p/google-ai-pro.html": ["2TB", "83% off special", "211+ orders", "official reference ~৳2,199"],
}
for rel, forbidden in checks.items():
    text = (SITE / rel).read_text(encoding="utf-8", errors="replace")
    for phrase in forbidden:
        if phrase.lower() in text.lower():
            raise SystemExit(f"ERROR: stale Google AI cohort phrase survived in {rel}: {phrase}")

required = {
    "p/google-ai-pro.html": "Google Bangladesh: ৳2,500/mo",
    "p/google-ai-plus.html": "Google Bangladesh: ৳600/mo",
    "bn/p/google-ai-pro.html": "Google Bangladesh: ৳2,500/মাস",
    "bn/p/google-ai-plus.html": "Google Bangladesh: ৳600/মাস",
}
for rel, marker in required.items():
    text = (SITE / rel).read_text(encoding="utf-8", errors="replace")
    if f'data-google-ai-facts="{verified_on}"' not in text or marker not in text:
        raise SystemExit(f"ERROR: verified Google AI cohort marker missing in {rel}")

print("Google AI cohort hardening OK — official BD facts, comparison, student path, and proof cleanup applied.")
