#!/usr/bin/env python3
"""Harden SuperGrok money pages with verified 2026-09-09 SpaceXAI facts."""
from pathlib import Path
import re

ROOT = Path("_site")
VERIFIED = "2026-09-09"


def load(path):
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"SUPERGROK COHORT ERROR — missing staged page: {path}")
    return p, p.read_text(encoding="utf-8")


def inject_notice(text, block):
    marker = '<div class="notice mt2"'
    if block in text:
        return text
    if marker not in text:
        raise SystemExit("SUPERGROK COHORT ERROR — notice injection anchor missing")
    return text.replace(marker, block + marker, 1)


def replace_meta(text, name, value):
    pattern = rf'(<meta\s+name="{re.escape(name)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, rf'\1{value}\2', text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"SUPERGROK COHORT ERROR — meta {name} missing")
    return text


def replace_property(text, prop, value):
    pattern = rf'(<meta\s+property="{re.escape(prop)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, rf'\1{value}\2', text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"SUPERGROK COHORT ERROR — property {prop} missing")
    return text


def harden(path, bn=False):
    p, t = load(path)

    stale = [
        "official reference ~৳3,300", "Official: ~৳3,300/mo ($30)",
        "অফিসিয়াল: ~৳3,300/মাস", "~৳3,300/mo", "~৳3,300/মাস",
        "SAVE 55%",
    ]
    for s in stale:
        t = t.replace(s, "")
    t = re.sub(r'\s*<span class="savepct">SAVE\s*\d+%</span>', '', t, flags=re.I)

    desc = (
        "SuperGrok in Bangladesh from ৳1,495. Compare SaveOnSub seller options with SpaceXAI's current official SuperGrok tiers, account rules, delivery timing and warranty before buying."
        if not bn else
        "SuperGrok বাংলাদেশে ৳1,495 থেকে। কেনার আগে SaveOnSub seller option-এর সাথে SpaceXAI-এর current official SuperGrok tiers, account rules, delivery time ও warranty তুলনা করুন।"
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
        '<span class="official" data-supergrok-facts="2026-09-09">SpaceXAI official pricing: SuperGrok US$30/month and SuperGrok Plus US$100/month. The official comparison also lists Free, SuperGrok Lite and SuperGrok Heavy. Verify the exact tier shown in your delivered account before payment.</span>'
        if not bn else
        '<span class="official" data-supergrok-facts="2026-09-09">SpaceXAI official pricing: SuperGrok US$30/মাস এবং SuperGrok Plus US$100/মাস। Official comparison-এ Free, SuperGrok Lite ও SuperGrok Heavy-ও আছে। Payment-এর আগে delivered account-এ exact tier যাচাই করুন।</span>'
    )
    t = re.sub(r'<span class="official"[^>]*>.*?</span>', official, t, count=1, flags=re.S)

    # Seller labels are not verified provider tier names.
    t = t.replace("Lite — Personal", "SaveOnSub Lite — Personal")
    t = t.replace("Standard — Personal", "SaveOnSub Standard — Personal")

    # Remove stale exact-tier FAQ wording where source pages asserted unverified amounts/mapping.
    t = re.sub(r'"Are there other Grok tiers\?".*?"text":\s*"[^"]*"',
               '"Are there other Grok tiers?", "acceptedAnswer": {"@type": "Answer", "text": "Yes. SpaceXAI currently lists Free, SuperGrok Lite, SuperGrok, SuperGrok Plus and SuperGrok Heavy. Verify the live official pricing page for the exact tier and current price before buying."', t, count=1, flags=re.S)

    if not bn:
        block = f'''<section class="notice mt2" data-supergrok-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">SuperGrok in Bangladesh — verified buying facts</h2>
<p style="font-size:14px"><b>Current official tiers:</b> SpaceXAI lists Free, SuperGrok Lite, SuperGrok, SuperGrok Plus and SuperGrok Heavy. The public pricing page currently shows <b>SuperGrok at US$30/month</b> and <b>SuperGrok Plus at US$100/month</b>.</p>
<p style="font-size:14px;margin-top:8px"><b>Important label distinction:</b> “SaveOnSub Lite” and “SaveOnSub Standard” are seller option labels. Do not assume they are the same as SpaceXAI's official tier names. Confirm the exact provider tier and entitlements visible in the delivered account before payment.</p>
<p style="font-size:14px;margin-top:8px"><b>Account-sharing rule:</b> SpaceXAI's current consumer terms say you may not share account credentials or make your account available to anyone else. Shared credentials can create privacy, continuity and suspension risk.</p>
<p style="font-size:14px;margin-top:8px"><b>Billing distinction:</b> Grok consumer subscriptions and xAI API billing are separate. Buying a Grok subscription does not imply included API credits.</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: SpaceXAI pricing, consumer terms and account/billing documentation.</p>
</section>'''
    else:
        block = f'''<section class="notice mt2" data-supergrok-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">SuperGrok বাংলাদেশে — যাচাই করা buying facts</h2>
<p style="font-size:14px"><b>Current official tiers:</b> SpaceXAI Free, SuperGrok Lite, SuperGrok, SuperGrok Plus এবং SuperGrok Heavy দেখায়। Public pricing page-এ বর্তমানে <b>SuperGrok US$30/মাস</b> এবং <b>SuperGrok Plus US$100/মাস</b> দেখানো আছে।</p>
<p style="font-size:14px;margin-top:8px"><b>Label distinction:</b> “SaveOnSub Lite” এবং “SaveOnSub Standard” seller option label; এগুলো SpaceXAI-এর official tier name ধরে নেবেন না। Payment-এর আগে delivered account-এ exact provider tier ও entitlement যাচাই করুন।</p>
<p style="font-size:14px;margin-top:8px"><b>Account-sharing rule:</b> SpaceXAI consumer terms অনুযায়ী account credential share করা বা account অন্যকে ব্যবহার করতে দেওয়া যাবে না। Shared credential-এ privacy, continuity ও suspension risk থাকতে পারে।</p>
<p style="font-size:14px;margin-top:8px"><b>Billing distinction:</b> Grok consumer subscription এবং xAI API billing আলাদা। Grok subscription কিনলেই API credit included হয় না।</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: SpaceXAI pricing, consumer terms এবং account/billing documentation.</p>
</section>'''
    t = inject_notice(t, block)

    low = t.lower()
    forbidden = ["official: ~৳3,300", "official reference ~৳3,300", "save 55%"]
    for phrase in forbidden:
        if phrase in low:
            raise SystemExit(f"SUPERGROK COHORT ERROR — stale phrase survived in {path}: {phrase}")
    if f'data-supergrok-cohort="{VERIFIED}"' not in t or f'data-supergrok-facts="{VERIFIED}"' not in t:
        raise SystemExit(f"SUPERGROK COHORT ERROR — verified fact markers missing in {path}")
    p.write_text(t, encoding="utf-8")


def main():
    harden("p/supergrok.html", bn=False)
    harden("bn/p/supergrok.html", bn=True)
    print("SuperGrok cohort hardening OK — current tiers, seller-label distinction and account rules enforced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
