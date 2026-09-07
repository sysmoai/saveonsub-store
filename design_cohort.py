#!/usr/bin/env python3
"""Apply verified Canva + Midjourney facts to the staged public artifact.

This is a fail-closed release overlay. It preserves existing ranking URLs while
neutralizing stale/unsafe claims generated from catalog-level USD anchors.
"""
from pathlib import Path
import re

ROOT = Path("_site")
VERIFIED = "2026-09-08"

CANVA_EN = ROOT / "p/canva-pro.html"
CANVA_BN = ROOT / "bn/p/canva-pro.html"
MJ_EN = ROOT / "p/midjourney.html"
MJ_BN = ROOT / "bn/p/midjourney.html"


def load(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"missing staged cohort page: {path}")
    return path.read_text(encoding="utf-8")


def save(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def remove_savings_badge(text: str) -> str:
    return re.sub(r'\s*<span class="savepct">.*?</span>', '', text, flags=re.I | re.S)


def neutralize_fixed_refs(text: str, refs: list[str]) -> str:
    for s in refs:
        text = text.replace(s, "")
    text = re.sub(r'\s*\(official reference ~?৳[0-9,]+\)', '', text, flags=re.I)
    text = re.sub(r'\s*\(official reference ~?৳[0-9,]+[^)]*\)', '', text, flags=re.I)
    return text


def inject_before(text: str, needle: str, block: str) -> str:
    if block in text:
        return text
    if needle not in text:
        raise SystemExit(f"injection anchor missing: {needle[:80]}")
    return text.replace(needle, block + needle, 1)


def harden_canva(path: Path, bn: bool) -> None:
    t = load(path)
    t = neutralize_fixed_refs(t, [
        "Official: ~৳1,650/mo ($15)",
        "Official: ~৳1,650/মাস ($15)",
        "Official list converted at site anchor rate",
        "~৳1,650/mo",
        "~৳1,650/মাস",
        "official reference ~৳1,650",
    ])
    t = remove_savings_badge(t)

    # Team/invite access is not equivalent to individual Canva Pro.
    t = t.replace("SHARED · LOW RISK", "TEAM WORKSPACE · ADMIN-CONTROLLED")
    t = t.replace("শেয়ার্ড · কম ঝুঁকি", "টিম ওয়ার্কস্পেস · অ্যাডমিন নিয়ন্ত্রিত")
    t = t.replace("Shared · Low Risk", "Team workspace · admin-controlled")

    risky = [
        "your designs stay yours",
        "lowest-risk shared product we sell",
        "Team seats are officially supported by Canva — lowest-risk shared product we sell.",
        "Team seats are officially supported by Canva",
    ]
    for phrase in risky:
        t = t.replace(phrase, "workspace access and design ownership depend on the exact team/workspace setup")

    official_anchor = (
        '<span class="official" data-design-facts="2026-09-08">Canva official reference: Pro is for one person; '
        'Canva lists Pro at US$180/year. New team sign-ups use Canva Business. Verify local checkout before buying.</span>'
    ) if not bn else (
        '<span class="official" data-design-facts="2026-09-08">Canva অফিসিয়াল রেফারেন্স: Pro এক ব্যক্তির জন্য; '
        'Canva Pro-এর প্রকাশিত বার্ষিক মূল্য US$180। নতুন team signup Canva Business-এ যায়। কিনার আগে local checkout যাচাই করুন।</span>'
    )
    t = re.sub(r'<span class="official">.*?</span>', official_anchor, t, count=1, flags=re.S)

    if not bn:
        block = f'''\n  <section class="notice mt2" data-canva-facts="{VERIFIED}">
    <h2 style="font-size:20px;margin:0 0 8px">Canva Pro vs team access — what you are actually buying</h2>
    <p style="font-size:14px"><b>Canva Pro is an individual plan.</b> Canva currently lists Pro at <b>US$180/year for one person</b>. For new team sign-ups, Canva directs users to <b>Canva Business</b>; existing legacy Teams subscribers can continue on their current plan.</p>
    <p style="font-size:14px;margin-top:8px"><b>Team-seat warning:</b> if this SaveOnSub option is delivered through a Canva team/workspace, the team owner/admin controls membership. Designs created inside that team workspace stay with the team workspace, and you can lose access if the admin removes you. Before payment, confirm the exact source plan, workspace owner, expected duration, and whether you should keep sensitive/client work outside that workspace.</p>
    <p style="font-size:14px;margin-top:8px"><b>Do not share Canva login credentials.</b> Canva's terms require each person to have a unique account. A team invitation is different from sharing one login.</p>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Canva pricing, Canva Business announcement, Canva Terms, and Canva team/workspace help.</p>
  </section>\n'''
    else:
        block = f'''\n  <section class="notice mt2" data-canva-facts="{VERIFIED}">
    <h2 style="font-size:20px;margin:0 0 8px">Canva Pro বনাম team access — আসলে কী কিনছেন</h2>
    <p style="font-size:14px"><b>Canva Pro ব্যক্তিগত প্ল্যান।</b> Canva বর্তমানে এক ব্যক্তির Pro প্ল্যানের প্রকাশিত মূল্য <b>US$180/বছর</b> দেখায়। নতুন team signup-এর জন্য Canva Business ব্যবহৃত হয়; পুরনো Teams subscriber তাদের existing plan চালিয়ে যেতে পারে।</p>
    <p style="font-size:14px;margin-top:8px"><b>Team-seat সতর্কতা:</b> SaveOnSub option যদি Canva team/workspace invite দিয়ে দেওয়া হয়, membership team owner/admin নিয়ন্ত্রণ করে। Team workspace-এর ভিতরে তৈরি design team workspace-এই থাকে; admin আপনাকে remove করলে access হারাতে পারেন। Payment-এর আগে source plan, owner/admin control, duration, এবং sensitive/client work কোথায় রাখবেন—সব পরিষ্কার করে নিন।</p>
    <p style="font-size:14px;margin-top:8px"><b>Canva login credential share করবেন না।</b> Canva terms অনুযায়ী প্রত্যেক ব্যক্তির আলাদা account থাকা উচিত; team invitation এক login share করার সমান নয়।</p>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Canva pricing, Canva Business announcement, Canva Terms, এবং team/workspace help.</p>
  </section>\n'''

    t = inject_before(t, '<h2 class="mt3" style="font-size:22px">BD Market Snapshot', block)

    # Remove unsupported/overbroad commercial-rights simplifications if present.
    t = t.replace("Your Fiverr thumbnails, client logos, and social media posts are fully yours.",
                  "Commercial use depends on the specific Canva content/license terms and the assets used in each design.")
    t = t.replace("Canva Pro includes commercial use rights for designs you create.",
                  "Canva permits many commercial uses, but the applicable content/license terms and asset-specific restrictions still apply.")

    banned = [
        "Official: ~৳1,650",
        "SAVE 82%",
        "SHARED · LOW RISK",
        "your designs stay yours",
        "lowest-risk shared product we sell",
    ]
    lower = t.lower()
    for phrase in banned:
        if phrase.lower() in lower:
            raise SystemExit(f"stale/high-risk Canva phrase survived in {path}: {phrase}")
    if f'data-canva-facts="{VERIFIED}"' not in t:
        raise SystemExit(f"Canva fact block missing in {path}")
    save(path, t)


def harden_midjourney(path: Path, bn: bool) -> None:
    t = load(path)
    t = neutralize_fixed_refs(t, [
        "Official: ~৳3,300/mo ($30)",
        "Official: ~৳3,300/মাস ($30)",
        "Official list converted at site anchor rate",
        "~৳3,300/mo",
        "~৳3,300/মাস",
        "official reference ~৳3,300",
    ])
    t = remove_savings_badge(t)

    t = t.replace("SHARED · WARRANTY COVERED", "SHARED · PROVIDER-POLICY RISK")
    t = t.replace("SHARED · LOW RISK", "SHARED · PROVIDER-POLICY RISK")
    t = t.replace("শেয়ার্ড · ওয়ারেন্টি কভারড", "শেয়ার্ড · প্রোভাইডার-পলিসি ঝুঁকি")
    t = t.replace("শেয়ার্ড · কম ঝুঁকি", "শেয়ার্ড · প্রোভাইডার-পলিসি ঝুঁকি")

    official_anchor = (
        '<span class="official" data-design-facts="2026-09-08">Midjourney official plans: Basic US$10, Standard US$30, Pro US$60, Mega US$120 per month. Annual billing is 20% lower.</span>'
    ) if not bn else (
        '<span class="official" data-design-facts="2026-09-08">Midjourney অফিসিয়াল মাসিক প্ল্যান: Basic US$10, Standard US$30, Pro US$60, Mega US$120। Annual billing 20% কম।</span>'
    )
    t = re.sub(r'<span class="official">.*?</span>', official_anchor, t, count=1, flags=re.S)

    if not bn:
        block = f'''\n  <section class="notice mt2" data-midjourney-facts="{VERIFIED}">
    <h2 style="font-size:20px;margin:0 0 8px">Midjourney official plan matrix</h2>
    <div class="tbl"><table>
      <tr><th>Plan</th><th>Monthly</th><th>Fast GPU</th><th>Relax</th><th>Stealth</th></tr>
      <tr><td>Basic</td><td>US$10</td><td>3.3 hr</td><td>No</td><td>No</td></tr>
      <tr><td>Standard</td><td>US$30</td><td>15 hr</td><td>Unlimited images</td><td>No</td></tr>
      <tr><td>Pro</td><td>US$60</td><td>30 hr</td><td>Unlimited images + SD video</td><td>Yes</td></tr>
      <tr><td>Mega</td><td>US$120</td><td>60 hr</td><td>Unlimited images + SD video</td><td>Yes</td></tr>
    </table></div>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Annual billing is 20% lower than month-to-month on the official plan comparison.</p>
  </section>
  <section class="notice mt2">
    <h2 style="font-size:20px;margin:0 0 8px">Important shared-account policy warning</h2>
    <p style="font-size:14px"><b>Midjourney says only one user may use each registered account.</b> Its terms also prohibit reselling or redistributing the service or access to it, including sharing an account. A SaveOnSub listing labelled “Shared” therefore conflicts with Midjourney's current account/service-access policy and can carry suspension, ban, privacy, misuse and continuity risk.</p>
    <p style="font-size:14px;margin-top:8px">For client, confidential or business-critical work, choose a personal account under your own control. Companies above US$1M annual gross revenue need Pro or Mega for company commercial use under Midjourney's current terms.</p>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Midjourney plan comparison, Terms of Service, Community Guidelines and commercial-use guidance.</p>
  </section>\n'''
    else:
        block = f'''\n  <section class="notice mt2" data-midjourney-facts="{VERIFIED}">
    <h2 style="font-size:20px;margin:0 0 8px">Midjourney অফিসিয়াল প্ল্যান তুলনা</h2>
    <div class="tbl"><table>
      <tr><th>Plan</th><th>Monthly</th><th>Fast GPU</th><th>Relax</th><th>Stealth</th></tr>
      <tr><td>Basic</td><td>US$10</td><td>3.3 hr</td><td>না</td><td>না</td></tr>
      <tr><td>Standard</td><td>US$30</td><td>15 hr</td><td>Unlimited images</td><td>না</td></tr>
      <tr><td>Pro</td><td>US$60</td><td>30 hr</td><td>Unlimited images + SD video</td><td>হ্যাঁ</td></tr>
      <tr><td>Mega</td><td>US$120</td><td>60 hr</td><td>Unlimited images + SD video</td><td>হ্যাঁ</td></tr>
    </table></div>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Official annual billing month-to-month-এর তুলনায় 20% কম।</p>
  </section>
  <section class="notice mt2">
    <h2 style="font-size:20px;margin:0 0 8px">Shared account নিয়ে গুরুত্বপূর্ণ policy warning</h2>
    <p style="font-size:14px"><b>Midjourney অনুযায়ী প্রতিটি registered account শুধু একজন user ব্যবহার করতে পারে।</b> তাদের terms service/access resale বা redistribution, account sharing-সহ, নিষিদ্ধ করে। তাই SaveOnSub-এর “Shared” option Midjourney-এর current policy-এর সাথে conflict করে এবং suspension/ban, privacy, misuse ও continuity risk তৈরি করতে পারে।</p>
    <p style="font-size:14px;margin-top:8px">Client, confidential বা business-critical কাজের জন্য নিজের control-এর personal account ব্যবহার করুন। বছরে US$1M-এর বেশি gross revenue থাকা company-র commercial use-এর জন্য Midjourney current terms অনুযায়ী Pro বা Mega দরকার।</p>
    <p style="font-size:13px;color:var(--muted);margin-top:8px">Official references verified {VERIFIED}: Midjourney plan comparison, Terms of Service, Community Guidelines, এবং commercial-use guidance.</p>
  </section>\n'''

    t = inject_before(t, '<h2 class="mt3" style="font-size:22px">BD Market Snapshot', block)

    # Remove stale cross-product/legal simplifications and unsupported proof.
    t = re.sub(r'\([^)]*156\+ orders[^)]*\)', '', t, flags=re.I)
    t = t.replace("15h fast GPU + relax mode unlimited", "15 hours of Fast GPU time plus unlimited Relax Mode for images")
    t = t.replace("15 hours of fast GPU + unlimited relax mode", "15 hours of Fast GPU time plus unlimited Relax Mode for images")
    t = t.replace("paid plans include commercial rights for your business/freelance work.",
                  "subscribed users receive commercial-use rights subject to Midjourney's current terms; company revenue thresholds and other restrictions can apply.")
    t = t.replace("Your Fiverr thumbnails, client logos, and social media posts are fully yours.",
                  "Commercial use is subject to the provider's current terms and applicable law; do not treat subscription access as a blanket copyright guarantee.")

    banned = [
        "Official: ~৳3,300",
        "SAVE 64%",
        "SHARED · LOW RISK",
        "SHARED · WARRANTY COVERED",
        "156+ orders",
    ]
    lower = t.lower()
    for phrase in banned:
        if phrase.lower() in lower:
            raise SystemExit(f"stale/high-risk Midjourney phrase survived in {path}: {phrase}")
    if f'data-midjourney-facts="{VERIFIED}"' not in t:
        raise SystemExit(f"Midjourney fact block missing in {path}")
    save(path, t)


for p, bn in [(CANVA_EN, False), (CANVA_BN, True)]:
    harden_canva(p, bn)
for p, bn in [(MJ_EN, False), (MJ_BN, True)]:
    harden_midjourney(p, bn)

print("Applied verified Canva + Midjourney cohort hardening.")
