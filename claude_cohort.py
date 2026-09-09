#!/usr/bin/env python3
"""Harden Claude Pro money pages with verified 2026-09-09 official facts."""
from pathlib import Path
import re

ROOT = Path("_site")
VERIFIED = "2026-09-09"


def load(path):
    p = ROOT / path
    if not p.exists():
        raise SystemExit(f"CLAUDE COHORT ERROR — missing staged page: {path}")
    return p, p.read_text(encoding="utf-8")


def inject_notice(text, block):
    marker = '<div class="notice mt2"'
    if block in text:
        return text
    if marker not in text:
        raise SystemExit("CLAUDE COHORT ERROR — notice injection anchor missing")
    return text.replace(marker, block + marker, 1)


def replace_meta(text, name, value):
    pattern = rf'(<meta\s+name="{re.escape(name)}"\s+content=")[^"]*(">)'
    new, count = re.subn(pattern, rf'\1{value}\2', text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"CLAUDE COHORT ERROR — meta {name} missing")
    return new


def replace_property(text, prop, value):
    pattern = rf'(<meta\s+property="{re.escape(prop)}"\s+content=")[^"]*(">)'
    new, count = re.subn(pattern, rf'\1{value}\2', text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"CLAUDE COHORT ERROR — property {prop} missing")
    return new


def harden(path, bn=False):
    p, t = load(path)

    stale = [
        "official reference ~৳2,200", "Official: ~৳2,200/mo ($20)",
        "Official list converted at site anchor rate", "~৳2,200/mo",
        "অফিসিয়াল রেফারেন্স ~৳2,200", "অফিসিয়াল: ~৳2,200/মাস ($20)",
    ]
    for s in stale:
        t = t.replace(s, "")
    t = re.sub(r'\s*<span class="savepct">SAVE\s*\d+%</span>', '', t, flags=re.I)

    if not bn:
        desc = "Claude Pro in Bangladesh from ৳1,495. Compare SaveOnSub access types, delivery timing and warranty, plus current official Claude Pro pricing and Bangladesh availability before buying."
    else:
        desc = "Claude Pro বাংলাদেশে ৳1,495 থেকে। কেনার আগে SaveOnSub access type, delivery time, warranty, current official Claude Pro pricing এবং Bangladesh availability দেখুন।"
    t = replace_meta(t, "description", desc)
    t = replace_property(t, "og:description", desc)

    # Normalize Product JSON-LD description independently from stale source copy.
    t = re.sub(
        r'("@type":\s*"Product".*?"description":\s*")[^"]*(")',
        lambda m: m.group(1) + desc + m.group(2),
        t,
        count=1,
        flags=re.S,
    )

    official = (
        '<span class="official" data-claude-facts="2026-09-09">Claude Pro official reference: US$20/month in the U.S.; Anthropic says local-currency pricing is available where supported. Bangladesh is a supported Claude location. Verify your current checkout and tax before buying.</span>'
        if not bn else
        '<span class="official" data-claude-facts="2026-09-09">Claude Pro অফিসিয়াল রেফারেন্স: যুক্তরাষ্ট্রে US$20/মাস; Anthropic supported market-এ local-currency pricing দেয়। Bangladesh Claude-supported location। কেনার আগে current checkout ও tax যাচাই করুন।</span>'
    )
    t = re.sub(r'<span class="official"[^>]*>.*?</span>', official, t, count=1, flags=re.S)

    t = t.replace("SHARED · WARRANTY COVERED", "SHARED · PROVIDER-POLICY RISK")
    t = t.replace("শেয়ার্ড · ওয়ারেন্টি কভারড", "শেয়ার্ড · প্রোভাইডার-পলিসি ঝুঁকি")
    t = t.replace("Anthropic actively bans shared seats.", "Shared consumer-account access can conflict with Anthropic account rules and carries privacy, continuity and suspension risk.")

    if not bn:
        block = f'''<section class="notice mt2" data-claude-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Claude Pro in Bangladesh — verified buying facts</h2>
<p style="font-size:14px"><b>Official price:</b> Anthropic lists Claude Pro at <b>US$20/month in the U.S.</b> and says local-currency pricing is available where supported. <b>Bangladesh is officially supported for Claude.</b> Your live checkout is the authoritative source for currency, tax and final charge.</p>
<p style="font-size:14px;margin-top:8px"><b>What Pro includes:</b> higher usage than Free, priority access during busy periods, early access to features, Claude Code access and Cowork access. API usage is billed separately and is not included with Pro.</p>
<p style="font-size:14px;margin-top:8px"><b>Shared-access warning:</b> do not treat shared credentials as equivalent to your own individual Claude Pro account. Shared access can create privacy, misuse, continuity and suspension risk. Avoid confidential or sensitive data on any shared-access option.</p>
<p style="font-size:14px;margin-top:8px"><b>Team seat is different from Pro:</b> an organization-managed Claude for Work seat can be controlled by an owner/admin and should not be described as the same product as an individual Pro subscription.</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Claude Pro Help Center, Anthropic supported countries/regions and current Claude access guidance.</p>
</section>'''
    else:
        block = f'''<section class="notice mt2" data-claude-cohort="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Claude Pro বাংলাদেশে — যাচাই করা buying facts</h2>
<p style="font-size:14px"><b>Official price:</b> Anthropic যুক্তরাষ্ট্রে Claude Pro-এর মূল্য <b>US$20/মাস</b> দেখায় এবং supported market-এ local-currency pricing দেয়। <b>Bangladesh Claude-supported location।</b> Currency, tax ও final charge-এর জন্য live checkout-ই authoritative।</p>
<p style="font-size:14px;margin-top:8px"><b>Pro-তে কী আছে:</b> Free-এর তুলনায় বেশি usage, busy period-এ priority access, নতুন feature-এ early access, Claude Code এবং Cowork access। API usage আলাদা bill হয়; Pro-এর মধ্যে API অন্তর্ভুক্ত নয়।</p>
<p style="font-size:14px;margin-top:8px"><b>Shared-access warning:</b> shared credentials-কে নিজের individual Claude Pro account-এর সমান ধরে নেবেন না। Privacy, misuse, continuity ও suspension risk থাকতে পারে। Sensitive বা confidential data shared access-এ ব্যবহার করবেন না।</p>
<p style="font-size:14px;margin-top:8px"><b>Team seat Pro-এর সমান নয়:</b> organization-managed Claude for Work seat owner/admin control করতে পারে; এটিকে individual Pro subscription হিসেবে বর্ণনা করা উচিত নয়।</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Claude Pro Help Center, Anthropic supported countries/regions এবং Claude access guidance.</p>
</section>'''
    t = inject_notice(t, block)

    t = re.sub(r'<tr><td>Official list converted at site anchor rate</td>.*?</tr>', '', t, flags=re.S)
    t = re.sub(r'<tr><td>অফিসিয়াল[^<]*</td>.*?</tr>', '', t, flags=re.S)

    low = t.lower()
    forbidden = ["official: ~৳2,200", "official reference ~৳2,200", "save 32%", "official list converted at site anchor rate"]
    for phrase in forbidden:
        if phrase in low:
            raise SystemExit(f"CLAUDE COHORT ERROR — stale phrase survived in {path}: {phrase}")
    if f'data-claude-cohort="{VERIFIED}"' not in t or f'data-claude-facts="{VERIFIED}"' not in t:
        raise SystemExit(f"CLAUDE COHORT ERROR — verified fact markers missing in {path}")
    if desc not in t:
        raise SystemExit(f"CLAUDE COHORT ERROR — normalized metadata description missing in {path}")
    p.write_text(t, encoding="utf-8")


def main():
    harden("p/claude-pro.html", bn=False)
    harden("bn/p/claude-pro.html", bn=True)
    print("Claude cohort hardening OK — metadata, official price/support facts and shared-access risk enforced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
