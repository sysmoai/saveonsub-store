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


def replace_once(text, pattern, replacement, flags=0, label="pattern"):
    new, n = re.subn(pattern, replacement, text, count=1, flags=flags)
    if n != 1:
        raise RuntimeError(f"expected exactly one {label}, found {n}")
    return new


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
    plan = plans[product_id]
    official = plan["official_bdt_month"]

    # Replace stale official reference in visible anchor and market table.
    if lang == "en":
        text = re.sub(r'<span class="official">Official: ~?৳[\d,]+/mo(?: \([^<]+\))?</span>',
                      f'<span class="official">Google Bangladesh: ৳{official:,}/mo</span>', text, count=1)
        text = re.sub(r'<span class="savepct">[^<]*</span>\s*', '', text, count=1)
        text = re.sub(r'Official list converted at site anchor rate</td><td>~?৳[\d,]+/mo',
                      f'Google Bangladesh official page</td><td>৳{official:,}/mo', text, count=1)
        text = text.replace('https://one.google.com/about/google-ai-plans/', source)
        text = text.replace('2TB Google One storage', '5 TB storage' if product_id == 'google-ai-pro' else '400 GB storage')
        text = text.replace('2TB storage', '5 TB storage' if product_id == 'google-ai-pro' else '400 GB storage')
        # Remove cross-brand proof and absolute superiority claims.
        text = re.sub(r'<details><summary>Why our #1 seller\?</summary><p>.*?</p></details>', '', text, flags=re.S)
        text = re.sub(r'<details><summary>Why is Google AI Pro our #1 seller at ৳500\?</summary><p>.*?</p></details>', '', text, flags=re.S)
        text = text.replace('Personal (your Gmail) — 83% off special', 'Personal (your Gmail)')
        insert_marker = '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>'
    else:
        text = re.sub(r'<span class="official">অফিসিয়াল: ~?৳[\d,]+/মাস</span>',
                      f'<span class="official">Google Bangladesh: ৳{official:,}/মাস</span>', text, count=1)
        text = re.sub(r'<span class="savepct">[^<]*</span>\s*', '', text, count=1)
        text = re.sub(r'Official list, site anchor rate-এ converted</td><td>~?৳[\d,]+/মাস',
                      f'Google Bangladesh official page</td><td>৳{official:,}/মাস', text, count=1)
        text = text.replace('https://one.google.com/about/google-ai-plans/', source)
        text = text.replace('2TB Google One storage', '5 TB storage' if product_id == 'google-ai-pro' else '400 GB storage')
        text = text.replace('2TB storage', '5 TB storage' if product_id == 'google-ai-pro' else '400 GB storage')
        text = text.replace('Personal (your Gmail) — 83% off special', 'Personal (your Gmail)')
        insert_marker = '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>'

    if 'data-google-ai-facts=' not in text:
        if insert_marker not in text:
            raise RuntimeError(f"insert marker missing in {path}")
        text = text.replace(insert_marker, cohort_panel(lang) + '\n  ' + insert_marker, 1)

    # Update stale meta/JSON-LD official-reference snippets that are public-visible to search engines.
    text = re.sub(r'official reference ~?৳[\d,]+', f'Google Bangladesh reference ৳{official:,}', text)
    text = re.sub(r'official ~?৳[\d,]+', f'Google Bangladesh ৳{official:,}', text)

    path.write_text(text, encoding="utf-8")


for pid in ("google-ai-pro", "google-ai-plus"):
    en = SITE / "p" / f"{pid}.html"
    bn = SITE / "bn" / "p" / f"{pid}.html"
    if not en.exists() or not bn.exists():
        raise SystemExit(f"ERROR: missing staged Google AI page(s) for {pid}")
    patch_page(en, pid, "en")
    patch_page(bn, pid, "bn")

# Fail closed if known stale cohort claims survive.
checks = {
    "p/google-ai-pro.html": ["2TB", "83% off special", "our #1 seller", "official reference ~৳2,199"],
    "bn/p/google-ai-pro.html": ["2TB", "83% off special", "official reference ~৳2,199"],
}
for rel, forbidden in checks.items():
    text = (SITE / rel).read_text(encoding="utf-8", errors="replace")
    for phrase in forbidden:
        if phrase.lower() in text.lower():
            raise SystemExit(f"ERROR: stale Google AI cohort phrase survived in {rel}: {phrase}")

for rel in ("p/google-ai-pro.html", "p/google-ai-plus.html", "bn/p/google-ai-pro.html", "bn/p/google-ai-plus.html"):
    text = (SITE / rel).read_text(encoding="utf-8", errors="replace")
    if f'data-google-ai-facts="{verified_on}"' not in text:
        raise SystemExit(f"ERROR: verified Google AI fact panel missing in {rel}")

print("Google AI cohort hardening OK — official BD facts, comparison, and student path applied.")
