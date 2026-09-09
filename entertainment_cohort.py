#!/usr/bin/env python3
"""Truth-harden Netflix, Spotify and YouTube Premium public pages.

Verified 2026-09-09 against first-party provider sources. This release-time
transformer preserves ranking URLs and seller prices while removing stale FX
conversions, unsupported savings/equivalence language and misleading household-
sharing labels. It also refreshes the entertainment comparison guide.
"""
from pathlib import Path
import json
import re

ROOT = Path("_site")
FACTS = json.loads(Path("ops/ENTERTAINMENT-COHORT-FACTS-2026-09-09.json").read_text(encoding="utf-8"))
VERIFIED = FACTS["verified_on"]

if not ROOT.is_dir():
    raise SystemExit("ENTERTAINMENT COHORT ERROR — _site missing")


def load(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — missing staged page: {rel}")
    return p, p.read_text(encoding="utf-8")


def replace_meta(text, name, value):
    pattern = rf'(<meta\s+name="{re.escape(name)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — meta {name} missing")
    return text


def replace_property(text, prop, value):
    pattern = rf'(<meta\s+property="{re.escape(prop)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — property {prop} missing")
    return text


def replace_product_description(text, value):
    return re.sub(
        r'("@type":\s*"Product".*?"description":\s*")[^"]*(")',
        lambda m: m.group(1) + value + m.group(2),
        text,
        count=1,
        flags=re.S,
    )


def remove_fx_rows(text):
    text = re.sub(r'<tr><td>Official list converted at site anchor rate</td>.*?</tr>', '', text, flags=re.S)
    text = re.sub(r'<tr><td>Official list, site anchor rate[^<]*</td>.*?</tr>', '', text, flags=re.S)
    text = re.sub(r'<tr><td>অফিসিয়াল[^<]*(?:anchor|converted)[^<]*</td>.*?</tr>', '', text, flags=re.S | re.I)
    text = re.sub(r'\s*<span class="savepct">[^<]*</span>', '', text, flags=re.I)
    return text


GLOBAL_REPLACEMENTS = {
    "By default, Netflix shows the BD library which is smaller than US. With a VPN (NordVPN or Surfshark, from ৳249), you can access the US catalog — it's a common combination. We sell both Netflix seats and VPNs; ask on WhatsApp for the setup guide.":
        "Netflix catalog availability varies by region. VPN compatibility and provider policies can change, so SaveOnSub does not guarantee access to any specific foreign catalog.",
    "Netflix private profile ৳349 + Spotify family slot ৳129 = ৳478/month for premium streaming and ad-free music. Or YouTube Premium family slot ৳149 which includes YouTube Music — skip Spotify if you mainly use YouTube. The full entertainment guide is on our blog.":
        "Compare the current Netflix Bangladesh plan range, Spotify Bangladesh plans, YouTube live checkout, and each SaveOnSub access method before combining services. Household eligibility matters for family-based offers.",
    "Premium-tier slots stream 4K where your device supports it — mention 4K on WhatsApp when ordering.":
        "Resolution depends on the underlying Netflix plan, title, device, network and account settings. Confirm the exact underlying tier before payment if 4K matters.",
    "Premium-tier shared slots stream at 4K where your device supports it. Mention '4K' on WhatsApp when ordering and we'll allocate a Premium slot. Most BD viewers watch on mobile/laptop at 1080p which all plans support.":
        "Do not assume a shared Netflix profile includes 4K. Resolution depends on the underlying Netflix plan, title, device, network and account settings; confirm the exact tier before payment.",
    "A family slot is YOUR OWN separate Spotify account with YOUR playlists, library, and algorithm — just paid as part of a family plan. Individual is the official ৳219 plan on your own card. We recommend official for zero risk; family slot saves ৳90/month.":
        "Spotify Family uses separate member accounts, but Spotify requires Family members to reside at the same address. A third-party family-slot offer is therefore provider-policy dependent and is not equivalent to an Individual subscription.",
    "Official BD student price is ৳109 — if you have .edu, take that instead. We'll tell you.":
        "Spotify Student is ৳109/month for eligible verified higher-education students. Spotify controls eligibility verification; a .edu email alone is not the rule.",
    "৳239/month individual (verified), Family ৳359 for 5 members at the same household address, YouTube Music alone ৳199. Our family slot at ৳149 sits between the ৳99 market slots and official — with warranty.":
        "YouTube Premium is officially available in Bangladesh. Exact checkout price and payment methods can vary by billing platform; verify live YouTube checkout. Family members must live at the same residential address.",
    "Google requires same-household; enforcement is light but real. ৳149 slot vs ৳239 official — both honest options, you choose informed.":
        "YouTube requires family members to live at the same residential address, and its help center says an electronic check may confirm this periodically. Do not use a family-slot offer if you do not meet the household requirement.",
    "Yes — Premium includes ad-free YouTube + YouTube Music. If you already pay for both separately, switch to Premium and cancel your music subscription. One ৳149 slot replaces two payments.":
        "YouTube Premium includes YouTube Music Premium benefits. Compare your current memberships and the live YouTube offer before changing or cancelling another service.",
}

# Repeated cross-product FAQ text is normalized globally so stale entertainment
# claims cannot survive on Prime/Hoichoi/VPN pages that inherited the same FAQ.
for path in ROOT.rglob("*.html"):
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    for old, new in GLOBAL_REPLACEMENTS.items():
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")


def product_panel(product, bn=False):
    if product == "netflix":
        f = FACTS["netflix"]
        rows = "".join(
            f"<tr><td>{name}</td><td>US${data['price_month']:.2f}/mo</td><td>{data['quality']}</td><td>{data['devices']}</td></tr>"
            for name, data in f["plans"].items()
        )
        if bn:
            return f'''<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="netflix"><h2 style="font-size:20px;margin:0 0 8px">Netflix বাংলাদেশ — official plan facts</h2><div class="tbl"><table><tr><th>Plan</th><th>Netflix BD price</th><th>Quality</th><th>Devices</th></tr>{rows}</table></div><p style="font-size:13px;color:var(--muted);margin-top:8px">Netflix-এর Bangladesh page থেকে {VERIFIED} তারিখে যাচাই করা। SaveOnSub-এর private-profile/personal labels Netflix-এর official tier name নয়। Underlying tier, household/account control এবং warranty payment-এর আগে confirm করুন। <a href="{f['official_source']}" target="_blank" rel="noopener nofollow">Netflix BD যাচাই ↗</a></p></section>'''
        return f'''<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="netflix"><h2 style="font-size:20px;margin:0 0 8px">Netflix Bangladesh — verified official plans</h2><div class="tbl"><table><tr><th>Plan</th><th>Netflix BD price</th><th>Quality</th><th>Devices</th></tr>{rows}</table></div><p style="font-size:13px;color:var(--muted);margin-top:8px">Verified on Netflix's Bangladesh page on {VERIFIED}. SaveOnSub private-profile/personal labels are seller access labels, not official Netflix tier names. Confirm the underlying tier, household/account control and warranty before payment. <a href="{f['official_source']}" target="_blank" rel="noopener nofollow">Check Netflix BD ↗</a></p></section>'''
    if product == "spotify":
        f = FACTS["spotify"]
        p = f["plans"]
        if bn:
            return f'''<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="spotify"><h2 style="font-size:20px;margin:0 0 8px">Spotify Premium বাংলাদেশ — official price + Family rule</h2><p style="font-size:14px"><b>Official BD prices:</b> Individual ৳{p['Individual']}/মাস · Student ৳{p['Student']}/মাস · Duo ৳{p['Duo']}/মাস · Family ৳{p['Family']}/মাস।</p><p style="font-size:14px;margin-top:8px"><b>Family eligibility:</b> Spotify Family একই address-এ বসবাসকারী family members-এর জন্য। SaveOnSub family-slot offer official Individual-এর equivalent নয়; household eligibility না মিললে official Individual/Student বেছে নিন।</p><p style="font-size:13px;color:var(--muted);margin-top:8px">Spotify Bangladesh থেকে {VERIFIED} তারিখে যাচাই করা। <a href="{f['official_source']}" target="_blank" rel="noopener nofollow">Spotify BD যাচাই ↗</a></p></section>'''
        return f'''<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="spotify"><h2 style="font-size:20px;margin:0 0 8px">Spotify Premium Bangladesh — verified price + Family rule</h2><p style="font-size:14px"><b>Official BD prices:</b> Individual ৳{p['Individual']}/month · Student ৳{p['Student']}/month · Duo ৳{p['Duo']}/month · Family ৳{p['Family']}/month.</p><p style="font-size:14px;margin-top:8px"><b>Family eligibility:</b> Spotify says Family members must reside at the same address. A SaveOnSub family-slot offer is not equivalent to official Individual; use Individual/Student if you do not meet Family eligibility.</p><p style="font-size:13px;color:var(--muted);margin-top:8px">Verified against Spotify Bangladesh on {VERIFIED}. <a href="{f['official_source']}" target="_blank" rel="noopener nofollow">Check Spotify BD ↗</a></p></section>'''
    f = FACTS["youtube"]
    if bn:
        return f'''<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="youtube"><h2 style="font-size:20px;margin:0 0 8px">YouTube Premium বাংলাদেশ — availability + household rule</h2><p style="font-size:14px">YouTube Premium বাংলাদেশে officially available। Exact BDT checkout price/payment method billing platform অনুযায়ী বদলাতে পারে, তাই live YouTube checkout authoritative।</p><p style="font-size:14px;margin-top:8px"><b>Family rule:</b> family member-কে family manager-এর একই residential address-এ থাকতে হবে; YouTube help অনুযায়ী household eligibility electronic check-এর মাধ্যমে periodical verify হতে পারে।</p><p style="font-size:13px;color:var(--muted);margin-top:8px">Official YouTube Help থেকে {VERIFIED} তারিখে যাচাই করা। <a href="{f['availability_source']}" target="_blank" rel="noopener nofollow">Availability ↗</a> · <a href="{f['family_source']}" target="_blank" rel="noopener nofollow">Family rules ↗</a></p></section>'''
    return f'''<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="youtube"><h2 style="font-size:20px;margin:0 0 8px">YouTube Premium Bangladesh — verified availability + household rule</h2><p style="font-size:14px">YouTube Premium is officially available in Bangladesh. Exact BDT checkout price and payment methods can vary by billing platform, so the live YouTube checkout is authoritative.</p><p style="font-size:14px;margin-top:8px"><b>Family rule:</b> family members must live at the same residential address as the family manager; YouTube Help says household eligibility may be confirmed by periodic electronic checks.</p><p style="font-size:13px;color:var(--muted);margin-top:8px">Verified from official YouTube Help on {VERIFIED}. <a href="{f['availability_source']}" target="_blank" rel="noopener nofollow">Availability ↗</a> · <a href="{f['family_source']}" target="_blank" rel="noopener nofollow">Family rules ↗</a></p></section>'''


def patch_product(product, rel, bn=False):
    p, t = load(rel)
    t = remove_fx_rows(t)

    if product == "netflix":
        desc = ("Netflix বাংলাদেশে SaveOnSub-এ ৳349 থেকে। Netflix BD official US$2.99–US$9.99/month plan range, underlying tier, household/account risk ও warranty কেনার আগে তুলনা করুন।" if bn else "Netflix in Bangladesh from ৳349 on SaveOnSub. Compare the current official Netflix BD US$2.99–US$9.99/month plan range, underlying tier, household/account risk and warranty before buying.")
        official = ('<span class="official" data-entertainment-official="2026-09-09">Netflix BD: US$2.99–US$9.99/মাস</span>' if bn else '<span class="official" data-entertainment-official="2026-09-09">Netflix BD: US$2.99–US$9.99/month</span>')
        risk_en = "SHARED · HOUSEHOLD / ACCOUNT RISK"
        risk_bn = "শেয়ার্ড · household/account ঝুঁকি"
    elif product == "spotify":
        desc = ("Spotify Premium বাংলাদেশে SaveOnSub-এ ৳129 থেকে। Official BD ৳219 Individual/৳109 Student সহ plan prices ও same-address Family rule কেনার আগে তুলনা করুন।" if bn else "Spotify Premium in Bangladesh from ৳129 on SaveOnSub. Compare official BD plans (৳219 Individual, ৳109 Student, ৳299 Duo, ৳379 Family) and the same-address Family rule before buying.")
        official = ('<span class="official" data-entertainment-official="2026-09-09">Spotify BD: Individual ৳219/মাস · Student ৳109</span>' if bn else '<span class="official" data-entertainment-official="2026-09-09">Spotify BD: Individual ৳219/mo · Student ৳109/mo</span>')
        risk_en = "SHARED · HOUSEHOLD-POLICY RISK"
        risk_bn = "শেয়ার্ড · household-policy ঝুঁকি"
    else:
        desc = ("YouTube Premium বাংলাদেশে officially available। SaveOnSub ৳149 থেকে; live YouTube checkout, same-residential-address Family rule, access method ও warranty কেনার আগে যাচাই করুন।" if bn else "YouTube Premium is officially available in Bangladesh. SaveOnSub starts at ৳149; verify live YouTube checkout, the same-residential-address Family rule, access method and warranty before buying.")
        official = ('<span class="official" data-entertainment-official="2026-09-09">YouTube Premium: বাংলাদেশে available · live checkout যাচাই করুন</span>' if bn else '<span class="official" data-entertainment-official="2026-09-09">YouTube Premium: available in Bangladesh · verify live checkout</span>')
        risk_en = "SHARED · HOUSEHOLD-POLICY RISK"
        risk_bn = "শেয়ার্ড · household-policy ঝুঁকি"

    t = replace_meta(t, "description", desc)
    t = replace_property(t, "og:description", desc)
    t = replace_product_description(t, desc)

    t, count = re.subn(r'<span class="official"[^>]*>.*?</span>', official, t, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — official anchor missing in {rel}")

    for phrase in ["SHARED · WARRANTY COVERED", "SHARED · CHECK ACCESS RISK", "SHARED · LOW RISK"]:
        t = t.replace(f'<span class="tos shared-med">{phrase}</span>', f'<span class="tos shared-high">{risk_en}</span>')
        t = t.replace(f'<span class="tos shared-low">{phrase}</span>', f'<span class="tos shared-high">{risk_en}</span>')
    for phrase in ["শেয়ার্ড · কম ঝুঁকি", "শেয়ার্ড·কম-ঝুঁকি", "শেয়ার্ড · ওয়ারেন্টিসহ", "শেয়ার্ড·ওয়ারেন্টিসহ"]:
        t = t.replace(f'<span class="tos shared-med">{phrase}</span>', f'<span class="tos shared-high">{risk_bn}</span>')
        t = t.replace(f'<span class="tos shared-low">{phrase}</span>', f'<span class="tos shared-high">{risk_bn}</span>')

    if product in {"spotify", "youtube"}:
        t = t.replace('<span class="tos official">OFFICIAL</span>', '<span class="tos official">ASSISTED OFFICIAL PATH</span>')
        t = t.replace('<span class="tos official">অফিসিয়াল</span>', '<span class="tos official">ASSISTED OFFICIAL PATH</span>')
        t = t.replace("Official BD Individual (guide)", "Assisted official-path setup")

    anchor = '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>' if bn else '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>'
    if f'data-entertainment-facts="{VERIFIED}"' not in t:
        if anchor not in t:
            raise SystemExit(f"ENTERTAINMENT COHORT ERROR — plan anchor missing in {rel}")
        t = t.replace(anchor, product_panel(product, bn) + "\n  " + anchor, 1)

    # Remove old official-FX comparison language that can imply tier equivalence.
    t = re.sub(r'official reference ~?৳[\d,]+', 'current provider reference', t, flags=re.I)
    t = re.sub(r'Official: ~?৳[\d,]+/mo(?: \([^<]+\))?', '', t)
    t = re.sub(r'অফিসিয়াল: ~?৳[\d,]+/মাস', '', t)
    t = t.replace("zero-risk option", "lower provider-policy risk when you meet the provider terms")

    p.write_text(t, encoding="utf-8")


for product in ("netflix", "spotify", "youtube-premium"):
    key = "youtube" if product == "youtube-premium" else product
    patch_product(key, f"p/{product}.html", False)
    patch_product(key, f"bn/p/{product}.html", True)

# Refresh the comparison guide at the public boundary without changing its URL.
p, guide = load("blog/netflix-spotify-youtube-premium-price-bd.html")
guide_desc = "Netflix, Spotify and YouTube Premium in Bangladesh: current official provider facts verified 2026-09-09, plus SaveOnSub access options and household-policy warnings."
guide = replace_meta(guide, "description", guide_desc)
guide = replace_property(guide, "og:description", guide_desc)
guide = re.sub(r'("@type":\s*"Article".*?"description":\s*")[^"]*(")', lambda m: m.group(1) + guide_desc + m.group(2), guide, count=1, flags=re.S)
guide = guide.replace("PRICE SHEET · UPDATED 2026-09-03", "PRICE SHEET · VERIFIED 2026-09-09")
guide = guide.replace("Some have official taka prices (use them!). Some don't. Here's the honest map.", "Provider billing differs by service. Compare current official provider facts with the exact SaveOnSub access method before paying.")
old_table = re.compile(r'<div class="tbl mt3"><table>.*?</table></div>\s*<h2 class="mt3" style="font-size:22px">The rule of thumb</h2>\s*<p class="sub" style="font-size:15px">.*?</p>', re.S)
new_table = f'''<section data-entertainment-guide-facts="{VERIFIED}"><div class="tbl mt3"><table>
<tr><th>Service</th><th>Current official provider fact</th><th>SaveOnSub option</th><th>Key decision point</th></tr>
<tr><td>Spotify</td><td>Individual ৳219 · Student ৳109 · Duo ৳299 · Family ৳379</td><td><a href="../p/spotify.html" style="color:var(--green2)">From ৳129</a></td><td>Family members must reside at the same address; shared/family-slot access is not Individual.</td></tr>
<tr><td>YouTube Premium</td><td>Officially available in Bangladesh; verify live checkout price</td><td><a href="../p/youtube-premium.html" style="color:var(--green2)">From ৳149</a></td><td>Family members must share the same residential address; periodic household checks may apply.</td></tr>
<tr><td>Netflix</td><td>Bangladesh page: US$2.99–US$9.99/month across Mobile, Basic, Standard, Premium</td><td><a href="../p/netflix.html" style="color:var(--green2)">From ৳349</a></td><td>Private-profile/personal are SaveOnSub access labels, not official Netflix tier names; confirm underlying tier.</td></tr>
</table></div>
<h2 class="mt3" style="font-size:22px">The rule of thumb</h2>
<p class="sub" style="font-size:15px">Prefer the provider's own plan when it fits your payment method and eligibility. If considering a SaveOnSub shared/family/profile option, compare household rules, account control, privacy/continuity risk and the exact warranty before payment. Do not treat a seller slot as equivalent to an official individual subscription.</p></section>'''
guide, count = old_table.subn(new_table, guide, count=1)
if count != 1:
    raise SystemExit("ENTERTAINMENT COHORT ERROR — comparison guide table anchor changed")

guide = guide.replace("৳219/month individual, ৳109 student, ৳299 duo, ৳379 family — official BD pricing paid via local methods.", "Spotify Bangladesh lists Individual ৳219/month, Student ৳109/month, Duo ৳299/month and Family ৳379/month. Family eligibility includes a same-address requirement.")
guide = guide.replace("No — Netflix bills in USD requiring an international card. BD users either use cards, or warranted resellers offering private profiles from ~৳349/month.", "Netflix's Bangladesh page lists official plans in USD, currently US$2.99–US$9.99/month. Payment-method availability is determined by Netflix checkout; a SaveOnSub private profile is a separate seller access method.")
guide = guide.replace("Yes, with regional pricing around ৳239/month including YouTube Music — check the app for your exact offer.", "Yes. Official YouTube Help lists Bangladesh as a Premium market. Verify the live checkout price and payment methods; Family members must share the same residential address.")
for old, new in GLOBAL_REPLACEMENTS.items():
    guide = guide.replace(old, new)
p.write_text(guide, encoding="utf-8")

for rel in ["p/netflix.html", "p/spotify.html", "p/youtube-premium.html", "bn/p/netflix.html", "bn/p/spotify.html", "bn/p/youtube-premium.html"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    if f'data-entertainment-facts="{VERIFIED}"' not in text or f'data-entertainment-official="{VERIFIED}"' not in text:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — current markers missing in {rel}")

for phrase in [
    "official reference ~৳879",
    "Official: ~৳879/mo",
    "Official: ~৳220/mo",
    "Official: ~৳242/mo",
    "SHARED · WARRANTY COVERED",
    "SHARED · LOW RISK",
    "enforcement is light but real",
    "No official path without a card",
    "Netflix has no official taka price",
    "regional pricing around ৳239/month",
    "zero risk; family slot saves",
]:
    for path in list(ROOT.rglob("*.html")):
        if phrase.lower() in path.read_text(encoding="utf-8", errors="replace").lower():
            raise SystemExit(f"ENTERTAINMENT COHORT ERROR — stale phrase survived: {phrase} in {path}")

if f'data-entertainment-guide-facts="{VERIFIED}"' not in (ROOT / "blog/netflix-spotify-youtube-premium-price-bd.html").read_text(encoding="utf-8"):
    raise SystemExit("ENTERTAINMENT COHORT ERROR — guide marker missing")

print("Entertainment cohort hardening OK — Netflix/Spotify/YouTube facts, household rules and comparison guide refreshed.")
