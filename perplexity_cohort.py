#!/usr/bin/env python3
"""Harden Perplexity Pro money pages with verified 2026-09-09 official facts."""
from pathlib import Path
import re

ROOT = Path("_site")
VERIFIED = "2026-09-09"


def load(path):
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"PERPLEXITY COHORT ERROR — missing staged page: {path}")
    return p, p.read_text(encoding="utf-8")


def inject_notice(text, block):
    marker = '<div class="notice mt2"'
    if block in text:
        return text
    if marker not in text:
        raise SystemExit("PERPLEXITY COHORT ERROR — notice injection anchor missing")
    return text.replace(marker, block + marker, 1)


def replace_meta(text, name, value):
    pattern = rf'(<meta\s+name="{re.escape(name)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"PERPLEXITY COHORT ERROR — meta {name} missing")
    return text


def replace_property(text, prop, value):
    pattern = rf'(<meta\s+property="{re.escape(prop)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"PERPLEXITY COHORT ERROR — property {prop} missing")
    return text


def harden(path, bn=False):
    p, t = load(path)

    # Remove stale converted-BDT official price and derived savings claims.
    for stale in [
        "official reference ~৳2,200",
        "Official: ~৳2,200/mo ($20)",
        "~৳2,200/mo",
        "অফিসিয়াল: ~৳2,200/মাস ($20)",
        "~৳2,200/মাস",
    ]:
        t = t.replace(stale, "")
    t = re.sub(r'\s*<span class="savepct">SAVE\s*\d+%</span>', '', t, flags=re.I)
    t = re.sub(r'<tr><td>Official list converted at site anchor rate</td>.*?</tr>', '', t, flags=re.S)
    t = re.sub(r'<tr><td>অফিসিয়াল[^<]*</td>.*?</tr>', '', t, flags=re.S)

    desc = (
        "Perplexity Pro in Bangladesh from ৳350. Compare SaveOnSub access types with current official Perplexity Pro/Max pricing, account-sharing rules, delivery timing and warranty before buying."
        if not bn else
        "Perplexity Pro বাংলাদেশে ৳350 থেকে। কেনার আগে SaveOnSub access type-এর সাথে current official Perplexity Pro/Max pricing, account-sharing rules, delivery time ও warranty তুলনা করুন।"
    )
    t = replace_meta(t, "description", desc)
    t = replace_property(t, "og:description", desc)
    t = re.sub(
        r'("@type":\s*"Product".*?"description":\s*")[^"]*(")',
        lambda m: m.group(1) + desc + m.group(2),
        t,
        count=1,
        flags=re.S,
    )

    official = (
        '<span class="official" data-perplexity-facts="2026-09-09">Perplexity official reference: Pro US$20/month or US$200/year; Max US$200/month or US$2,000/year. Education Pro is US$10/month for verified students/educators. Verify your live checkout and eligibility before buying.</span>'
        if not bn else
        '<span class="official" data-perplexity-facts="2026-09-09">Perplexity official reference: Pro US$20/মাস বা US$200/বছর; Max US$200/মাস বা US$2,000/বছর। Verified student/educator-এর জন্য Education Pro US$10/মাস। কেনার আগে live checkout ও eligibility যাচাই করুন।</span>'
    )
    t, count = re.subn(r'<span class="official"[^>]*>.*?</span>', official, t, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"PERPLEXITY COHORT ERROR — official price anchor missing in {path}")

    # Provider policy: account sharing is not low-risk and is against Terms.
    t = t.replace('class="tos shared-low">SHARED · LOW RISK', 'class="tos shared-high">SHARED · PROVIDER-POLICY RISK')
    t = t.replace('class="tos shared-low">শেয়ার্ড · লো রিস্ক', 'class="tos shared-high">শেয়ার্ড · প্রোভাইডার-পলিসি ঝুঁকি')
    t = t.replace('Shared seats work the same as personal on mobile — the seat type doesn\'t affect functionality.', 'Shared-account access is not equivalent to a personal subscription; Perplexity says account sharing violates its Terms and can risk suspension or termination.')

    if not bn:
        block = f'''<section class="notice mt2" data-perplexity-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Perplexity Pro in Bangladesh — verified buying facts</h2>
<p style="font-size:14px"><b>Official consumer pricing:</b> Perplexity currently lists <b>Pro at US$20/month or US$200/year</b> and <b>Max at US$200/month or US$2,000/year</b>. Verified students and educators can qualify for <b>Education Pro at US$10/month</b>. Live checkout and eligibility are authoritative.</p>
<p style="font-size:14px;margin-top:8px"><b>Account-sharing warning:</b> Perplexity's Help Center says sharing an account violates its Terms of Use and can risk suspension or termination. A shared SaveOnSub option is therefore not equivalent to owning your own Perplexity Pro account; avoid sensitive or confidential work on shared access.</p>
<p style="font-size:14px;margin-top:8px"><b>What Pro adds:</b> extended Pro Search access, advanced AI models, image/video generation, higher file-upload limits, Create files and apps access, and priority support. Exact limits and model availability can change.</p>
<p style="font-size:14px;margin-top:8px"><b>API is separate:</b> Perplexity's API Platform is billed separately and does not include complimentary API credits with the consumer Pro plan.</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Perplexity subscription-plan guide, Max billing FAQ, account-security guidance and API-plan guidance.</p>
</section>'''
    else:
        block = f'''<section class="notice mt2" data-perplexity-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Perplexity Pro বাংলাদেশে — যাচাই করা buying facts</h2>
<p style="font-size:14px"><b>Official consumer pricing:</b> Perplexity বর্তমানে <b>Pro US$20/মাস বা US$200/বছর</b> এবং <b>Max US$200/মাস বা US$2,000/বছর</b> দেখায়। Verified student/educator <b>Education Pro US$10/মাস</b>-এর জন্য eligible হতে পারেন। Live checkout ও eligibility authoritative।</p>
<p style="font-size:14px;margin-top:8px"><b>Account-sharing warning:</b> Perplexity Help Center অনুযায়ী account share করা Terms of Use ভঙ্গ করে এবং suspension/termination risk তৈরি করতে পারে। তাই shared SaveOnSub option নিজের personal Perplexity Pro account-এর সমান নয়; sensitive/confidential কাজ shared access-এ ব্যবহার করবেন না।</p>
<p style="font-size:14px;margin-top:8px"><b>Pro-তে কী যোগ হয়:</b> extended Pro Search, advanced AI models, image/video generation, বেশি file-upload limits, Create files and apps access এবং priority support। Exact limits ও model availability পরিবর্তন হতে পারে।</p>
<p style="font-size:14px;margin-top:8px"><b>API আলাদা:</b> Perplexity API Platform আলাদাভাবে bill হয় এবং consumer Pro plan-এর সাথে complimentary API credit included নয়।</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Perplexity subscription-plan guide, Max billing FAQ, account-security guidance এবং API-plan guidance.</p>
</section>'''
    t = inject_notice(t, block)

    low = t.lower()
    for phrase in ["official: ~৳2,200", "official reference ~৳2,200", "save 84%", "shared · low risk"]:
        if phrase in low:
            raise SystemExit(f"PERPLEXITY COHORT ERROR — stale/risky phrase survived in {path}: {phrase}")
    if f'data-perplexity-cohort="{VERIFIED}"' not in t or f'data-perplexity-facts="{VERIFIED}"' not in t:
        raise SystemExit(f"PERPLEXITY COHORT ERROR — verified fact markers missing in {path}")
    if desc not in t:
        raise SystemExit(f"PERPLEXITY COHORT ERROR — normalized metadata missing in {path}")

    p.write_text(t, encoding="utf-8")


def main():
    harden("p/perplexity-pro.html", bn=False)
    harden("bn/p/perplexity-pro.html", bn=True)
    print("Perplexity cohort hardening OK — pricing, account-sharing risk, plan/API distinctions enforced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
