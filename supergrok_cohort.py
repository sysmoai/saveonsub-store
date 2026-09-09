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
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"SUPERGROK COHORT ERROR — meta {name} missing")
    return text


def replace_property(text, prop, value):
    pattern = rf'(<meta\s+property="{re.escape(prop)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"SUPERGROK COHORT ERROR — property {prop} missing")
    return text


def harden(path, bn=False):
    p, t = load(path)

    for stale in [
        "official reference ~৳3,300",
        "Official: ~৳3,300/mo ($30)",
        "অফিসিয়াল: ~৳3,300/মাস",
        "~৳3,300/mo",
        "~৳3,300/মাস",
    ]:
        t = t.replace(stale, "")
    t = re.sub(r'\s*<span class="savepct">SAVE\s*\d+%</span>', '', t, flags=re.I)

    desc = (
        "SuperGrok in Bangladesh from ৳1,495. Compare SaveOnSub seller options with current official SpaceXAI tiers, account rules, delivery timing and warranty before buying."
        if not bn else
        "SuperGrok বাংলাদেশে ৳1,495 থেকে। কেনার আগে SaveOnSub seller option-এর সাথে current official SpaceXAI tiers, account rules, delivery time ও warranty তুলনা করুন।"
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
        '<span class="official" data-supergrok-facts="2026-09-09">SpaceXAI currently lists Free, SuperGrok Lite, SuperGrok, SuperGrok Plus and SuperGrok Heavy. Public pricing shows SuperGrok at US$30/month and SuperGrok Plus at US$100/month. Verify the exact delivered tier before payment.</span>'
        if not bn else
        '<span class="official" data-supergrok-facts="2026-09-09">SpaceXAI বর্তমানে Free, SuperGrok Lite, SuperGrok, SuperGrok Plus এবং SuperGrok Heavy দেখায়। Public pricing-এ SuperGrok US$30/মাস এবং SuperGrok Plus US$100/মাস। Payment-এর আগে exact delivered tier যাচাই করুন।</span>'
    )
    t, count = re.subn(r'<span class="official"[^>]*>.*?</span>', official, t, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"SUPERGROK COHORT ERROR — official price anchor missing in {path}")

    # SaveOnSub labels are seller labels, not verified provider tier names.
    t = t.replace("Lite — Personal", "SaveOnSub Lite — Personal")
    t = t.replace("Standard — Personal", "SaveOnSub Standard — Personal")

    if not bn:
        block = f'''<section class="notice mt2" data-supergrok-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">SuperGrok in Bangladesh — verified buying facts</h2>
<p style="font-size:14px"><b>Current official tiers:</b> SpaceXAI lists Free, SuperGrok Lite, SuperGrok, SuperGrok Plus and SuperGrok Heavy. Its public pricing currently shows <b>SuperGrok at US$30/month</b> and <b>SuperGrok Plus at US$100/month</b>.</p>
<p style="font-size:14px;margin-top:8px"><b>Seller-label distinction:</b> “SaveOnSub Lite” and “SaveOnSub Standard” are SaveOnSub option labels. They are not claims that the delivered provider tier has the same official SpaceXAI name. Confirm the exact tier and entitlements visible in the delivered account before payment.</p>
<p style="font-size:14px;margin-top:8px"><b>Account rule:</b> SpaceXAI consumer terms prohibit sharing account credentials or making an account available to another person. Shared credentials can create privacy, continuity and suspension risk.</p>
<p style="font-size:14px;margin-top:8px"><b>Billing distinction:</b> Grok consumer subscriptions and xAI API billing are separate; a Grok subscription does not imply included API credits.</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: SpaceXAI pricing and consumer terms.</p>
</section>'''
    else:
        block = f'''<section class="notice mt2" data-supergrok-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">SuperGrok বাংলাদেশে — যাচাই করা buying facts</h2>
<p style="font-size:14px"><b>Current official tiers:</b> SpaceXAI Free, SuperGrok Lite, SuperGrok, SuperGrok Plus এবং SuperGrok Heavy দেখায়। Public pricing-এ বর্তমানে <b>SuperGrok US$30/মাস</b> এবং <b>SuperGrok Plus US$100/মাস</b> দেখানো আছে।</p>
<p style="font-size:14px;margin-top:8px"><b>Seller-label distinction:</b> “SaveOnSub Lite” এবং “SaveOnSub Standard” SaveOnSub option label। এগুলো delivered provider tier-এর official SpaceXAI name হওয়ার দাবি নয়। Payment-এর আগে delivered account-এ exact tier ও entitlement যাচাই করুন।</p>
<p style="font-size:14px;margin-top:8px"><b>Account rule:</b> SpaceXAI consumer terms account credential share করা বা account অন্য কাউকে ব্যবহার করতে দেওয়া নিষিদ্ধ করে। Shared credential-এ privacy, continuity ও suspension risk থাকতে পারে।</p>
<p style="font-size:14px;margin-top:8px"><b>Billing distinction:</b> Grok consumer subscription এবং xAI API billing আলাদা; Grok subscription কিনলেই API credit included হয় না।</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: SpaceXAI pricing এবং consumer terms.</p>
</section>'''
    t = inject_notice(t, block)

    low = t.lower()
    for phrase in ["official: ~৳3,300", "official reference ~৳3,300", "save 55%"]:
        if phrase in low:
            raise SystemExit(f"SUPERGROK COHORT ERROR — stale phrase survived in {path}: {phrase}")
    if f'data-supergrok-cohort="{VERIFIED}"' not in t or f'data-supergrok-facts="{VERIFIED}"' not in t:
        raise SystemExit(f"SUPERGROK COHORT ERROR — verified fact markers missing in {path}")
    if desc not in t:
        raise SystemExit(f"SUPERGROK COHORT ERROR — normalized metadata missing in {path}")

    p.write_text(t, encoding="utf-8")


def main():
    harden("p/supergrok.html", bn=False)
    harden("bn/p/supergrok.html", bn=True)
    print("SuperGrok cohort hardening OK — tiers, seller-label distinction and account rules enforced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
