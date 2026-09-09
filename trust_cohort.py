#!/usr/bin/env python3
"""Harden trust/legal/warranty pages in the staged public artifact.

This pass removes blanket legal conclusions, zero-risk claims, unsupported
competitive absolutes, and universal replacement/refund promises. It keeps the
useful disclosure intent while making product/order-specific written terms the
controlling source of truth.
"""
from pathlib import Path
import re
import sys

SITE = Path("_site")
VERIFIED = "2026-09-09"

if not SITE.is_dir():
    raise SystemExit("TRUST COHORT ERROR — _site missing")


def load(rel):
    p = SITE / rel
    if not p.exists():
        raise SystemExit(f"TRUST COHORT ERROR — missing {rel}")
    return p, p.read_text(encoding="utf-8", errors="strict")


def replace_meta(text, attr, key, value):
    pat = rf'(<meta\s+{attr}="{re.escape(key)}"\s+content=")[^"]*(">)'
    text, n = re.subn(pat, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if n != 1:
        raise SystemExit(f"TRUST COHORT ERROR — missing meta {key}")
    return text


def mark(text, marker):
    if marker in text:
        return text
    if "</head>" not in text:
        raise SystemExit("TRUST COHORT ERROR — missing </head>")
    return text.replace("</head>", f'<meta name="{marker}" content="{VERIFIED}">\n</head>', 1)


def harden_transparency():
    p, t = load("blog/how-we-source-subscriptions-transparency.html")

    desc = (
        "How SaveOnSub labels official, personal and shared subscription access, what provider-policy and privacy risks can differ, and what to verify before buying."
    )
    t = replace_meta(t, "name", "description", desc)
    t = replace_meta(t, "property", "og:description", desc)

    # JSON-LD FAQ answers: remove categorical legal advice and blanket warranty promises.
    t = re.sub(
        r'"name": "Is it legal to buy shared subscriptions in Bangladesh\?", "acceptedAnswer": \{"@type": "Answer", "text": "[^"]*"\}',
        '"name": "What should I know before buying shared subscription access?", "acceptedAnswer": {"@type": "Answer", "text": "Provider terms, account rules and applicable law are separate questions. SaveOnSub does not provide legal advice. Shared access can create provider-policy, privacy, continuity and account-enforcement risk; check the exact access method and written terms before payment."}',
        t,
        count=1,
    )
    t = re.sub(
        r'"name": "What is the risk of a shared subscription\?", "acceptedAnswer": \{"@type": "Answer", "text": "[^"]*"\}',
        '"name": "What is the risk of a shared subscription?", "acceptedAnswer": {"@type": "Answer", "text": "Risk depends on the provider and access method. Shared credentials or seats can create privacy, continuity, sign-in and provider-policy risk. Any SaveOnSub warranty, replacement or refund terms are product-specific and the written terms shown before payment control."}',
        t,
        count=1,
    )

    replacements = {
        "No BD reseller publishes this. We do, because it is the only durable advantage.":
            "We publish our access-method disclosures so buyers can compare risk, privacy, continuity and support terms before paying.",
        "You pay the provider; we guide/activate (e.g. Spotify BD, Hoichoi)":
            "Provider-billed or provider-account activation path where that option is explicitly offered",
        "<td>None</td>":
            "<td>Lower access-method risk; provider billing, account security, service availability and provider terms still apply.</td>",
        "None — your account, your data":
            "Lower sharing risk; provider rules, account security and the exact delivery method still apply.",
        "A seat on a multi-user plan the provider tolerates (e.g. Canva teams, family plans)":
            "Shared or multi-user access; compatibility with provider rules depends on the service and exact plan.",
        "Low — rare interruption, warranty-covered":
            "Privacy, continuity and provider-policy risk vary; check the selected offer's written terms.",
        "A seat on a plan whose ToS prohibits sharing — that is why it is cheapest":
            "Shared access where provider rules may restrict credential or seat sharing; confirm the exact method before buying.",
        "Seat can reset; 1-hour replacement warranty":
            "Account/seat interruption is possible; replacement or refund terms vary by the selected offer.",
        "Buying a shared seat is <b>not illegal for you under BD law</b> — seat-sharing is a violation of the <i>provider's</i> terms of service (their contract with the account holder), not a crime you commit. The practical worst case for you is a seat reset, which our warranty fixes. We label every plan so you decide with full information — something no Facebook seller does.":
            "Provider terms, account rules and applicable law are separate questions. <b>SaveOnSub does not provide legal advice.</b> Shared access can create provider-policy, privacy, continuity and account-enforcement risk. Check the exact access method and written product/order terms before payment; obtain qualified local advice if legal status matters for your situation.",
        "It is not illegal for you under BD law — seat-sharing violates the provider's terms of service (a contract issue), not a crime. The practical risk is a seat reset, which SAVEONSUB's warranty replaces.":
            "Provider terms, account rules and applicable law are separate questions. SaveOnSub does not provide legal advice. Shared access can create provider-policy, privacy, continuity and account-enforcement risk; check the exact access method and written terms before payment.",
        "Three ways: official (you pay the provider, we activate), personal (a real plan on your own account via regional pricing), and shared seats on multi-user plans — each honestly risk-labeled.":
            "SaveOnSub distinguishes provider-billed/official access paths where available, personal/customer-specific access, and shared/multi-user access. The exact credential, invite, billing and support method must be confirmed for the selected offer before payment.",
        "A seat can occasionally be reset because sharing violates provider ToS. That is why it is cheapest, and why SAVEONSUB covers it with a 1-hour replacement warranty.":
            "Shared access can carry privacy, continuity, sign-in and provider-policy risk. Replacement, warranty and refund terms vary by product and the written terms shown before payment control.",
    }
    for old, new in replacements.items():
        t = t.replace(old, new)

    t = t.replace("Is this legal in Bangladesh?", "Legal and provider-policy considerations")
    t = t.replace("Is it legal to buy shared subscriptions in Bangladesh?", "What should I know before buying shared subscription access?")
    t = mark(t, "saveonsub-trust-verified")
    p.write_text(t, encoding="utf-8")


def harden_warranty(rel, bn=False):
    p, t = load(rel)
    if not bn:
        title = "Warranty & Support Terms | SAVEONSUB"
        desc = "SaveOnSub warranty and support terms vary by product and access type. Check the written coverage, replacement and refund terms shown before payment."
        t = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', t, count=1, flags=re.S)
        t = replace_meta(t, "name", "description", desc)
        t = replace_meta(t, "property", "og:title", title)
        t = replace_meta(t, "property", "og:description", desc)
        t = re.sub(
            r'<div class="tbl mt3"><table>.*?</table></div>',
            '<div class="notice mt3"><b>Coverage is offer-specific.</b> Warranty duration, replacement timing, refund eligibility and exclusions can differ by product and access method. The written terms shown on the selected product/order before payment control.</div>',
            t,
            count=1,
            flags=re.S,
        )
        t = re.sub(
            r'<h2 class="mt3" style="font-size:21px">What\'s covered</h2>.*?<h2 class="mt3" style="font-size:21px">What\'s not covered</h2>',
            '<h2 class="mt3" style="font-size:21px">What may be covered</h2><p class="sub" style="font-size:15px">Depending on the selected offer, written coverage may include activation failure or loss of the purchased access during the stated coverage window. Provider feature changes, policy enforcement and account-security events may be excluded or handled differently.</p><h2 class="mt3" style="font-size:21px">Common exclusions</h2>',
            t,
            count=1,
            flags=re.S,
        )
        t = re.sub(
            r'<p class="sub" style="font-size:15px">You broke the seat rules.*?</p>',
            '<p class="sub" style="font-size:15px">Misuse, credential changes not permitted by the selected access method, reselling, unsupported device/account changes, provider-wide feature changes, or other exclusions stated for the selected offer may not be covered.</p>',
            t,
            count=1,
            flags=re.S,
        )
        t = re.sub(
            r'<p class="sub" style="font-size:15px">WhatsApp <b>\+880 1305-869242</b>.*?</p>',
            '<p class="sub" style="font-size:15px">WhatsApp <b>+880 1305-869242</b> with your order ID and a screenshot. Support will assess the claim against the written terms for your selected offer and confirm the applicable resolution.</p>',
            t,
            count=1,
            flags=re.S,
        )
        t = re.sub(
            r'<div class="notice mt3">⏱️ Claims outside support hours.*?</div>',
            '<div class="notice mt3">⏱️ Response and resolution timing can vary by issue, provider dependency and support hours. Any specific SLA stated in your written order terms controls.</div>',
            t,
            count=1,
            flags=re.S,
        )
    else:
        title = "ওয়ারেন্টি ও সাপোর্ট শর্ত | SAVEONSUB"
        desc = "SaveOnSub ওয়ারেন্টি ও সাপোর্ট শর্ত product ও access type অনুযায়ী ভিন্ন হতে পারে। Payment-এর আগে written coverage, replacement ও refund terms যাচাই করুন।"
        t = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', t, count=1, flags=re.S)
        t = replace_meta(t, "name", "description", desc)
        t = replace_meta(t, "property", "og:title", title)
        t = replace_meta(t, "property", "og:description", desc)
        # Use a broad deterministic replacement on the central warranty table and hard SLA phrases.
        t = re.sub(
            r'<div class="tbl mt3"><table>.*?</table></div>',
            '<div class="notice mt3"><b>Coverage offer-specific।</b> Warranty duration, replacement timing, refund eligibility ও exclusions product এবং access method অনুযায়ী ভিন্ন হতে পারে। Payment-এর আগে selected product/order-এ দেখানো written terms-ই প্রযোজ্য।</div>',
            t,
            count=1,
            flags=re.S,
        )
        t = re.sub(r'১ ঘণ্টার[^<]*', 'নির্দিষ্ট resolution timing selected offer-এর written terms অনুযায়ী', t)
        t = re.sub(r'1-hour[^<]*', 'offer-specific support timing', t, flags=re.I)
        t = re.sub(r'১ ঘন্টার[^<]*', 'নির্দিষ্ট resolution timing selected offer-এর written terms অনুযায়ী', t)
    t = mark(t, "saveonsub-trust-verified")
    p.write_text(t, encoding="utf-8")


def main():
    harden_transparency()
    harden_warranty("warranty.html", bn=False)
    harden_warranty("bn/warranty.html", bn=True)

    forbidden = {
        "blog/how-we-source-subscriptions-transparency.html": [
            "not illegal for you under BD law",
            "not a crime",
            "provider tolerates",
            "Low — rare interruption, warranty-covered",
            "1-hour replacement warranty",
            "no Facebook seller does",
            "No BD reseller publishes this",
        ],
        "warranty.html": [
            "Warranty — 1-Hour Replacement",
            "replacement within 1 hour",
            "Within 1 hour",
            "resolved within the 1-hour promise",
            "7-day guarantee on shared seats",
            "30-day on personal plans",
        ],
        "bn/warranty.html": [
            "১ ঘণ্টার রিপ্লেসমেন্ট",
            "১ ঘন্টার রিপ্লেসমেন্ট",
        ],
    }
    errors = []
    for rel, phrases in forbidden.items():
        text = (SITE / rel).read_text(encoding="utf-8", errors="replace")
        if f'name="saveonsub-trust-verified" content="{VERIFIED}"' not in text:
            errors.append(f"{rel}: trust verification marker missing")
        low = text.lower()
        for phrase in phrases:
            if phrase.lower() in low:
                errors.append(f"{rel}: stale trust claim survived: {phrase}")

    if errors:
        print(f"TRUST COHORT FAILED — {len(errors)} issue(s):", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1

    print("Trust cohort hardening OK — legal/risk/warranty blanket claims normalized in EN/BN trust surfaces.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
