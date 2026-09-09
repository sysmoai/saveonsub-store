#!/usr/bin/env python3
"""Truth-harden Netflix, Spotify and YouTube Premium staged pages."""
from pathlib import Path
import json
import re

SITE = Path("_site")
FACTS = json.loads(Path("ops/ENTERTAINMENT-COHORT-FACTS-2026-09-09.json").read_text(encoding="utf-8"))
VERIFIED = FACTS["verified_on"]

if not SITE.is_dir():
    raise SystemExit("ENTERTAINMENT COHORT ERROR — _site missing")


def read(rel):
    p = SITE / rel
    if not p.exists():
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — missing {rel}")
    return p, p.read_text(encoding="utf-8")


def meta(t, key, value, prop=False):
    attr = "property" if prop else "name"
    pat = rf'(<meta\s+{attr}="{re.escape(key)}"\s+content=")[^"]*(">)'
    t, n = re.subn(pat, lambda m: m.group(1) + value + m.group(2), t, count=1, flags=re.I)
    if n != 1:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — missing {attr}={key}")
    return t


def product_desc(t, value):
    return re.sub(
        r'("@type":\s*"Product".*?"description":\s*")[^"]*(")',
        lambda m: m.group(1) + value + m.group(2), t, count=1, flags=re.S,
    )


GLOBAL = {
    "By default, Netflix shows the BD library which is smaller than US. With a VPN (NordVPN or Surfshark, from ৳249), you can access the US catalog — it's a common combination. We sell both Netflix seats and VPNs; ask on WhatsApp for the setup guide.":
        "Netflix catalog availability varies by region. VPN compatibility and provider policies can change, so SaveOnSub does not guarantee access to any specific foreign catalog.",
    "Netflix private profile ৳349 + Spotify family slot ৳129 = ৳478/month for premium streaming and ad-free music. Or YouTube Premium family slot ৳149 which includes YouTube Music — skip Spotify if you mainly use YouTube. The full entertainment guide is on our blog.":
        "Compare current Netflix Bangladesh plans, Spotify Bangladesh plans, YouTube live checkout and each SaveOnSub access method before combining services. Household eligibility matters for family-based offers.",
    "Premium-tier slots stream 4K where your device supports it — mention 4K on WhatsApp when ordering.":
        "Resolution depends on the underlying Netflix plan, title, device, network and account settings. Confirm the exact underlying tier before payment if 4K matters.",
    "Premium-tier shared slots stream at 4K where your device supports it. Mention '4K' on WhatsApp when ordering and we'll allocate a Premium slot. Most BD viewers watch on mobile/laptop at 1080p which all plans support.":
        "Do not assume a shared Netflix profile includes 4K. Confirm the underlying Netflix tier before payment; resolution also depends on title, device, network and account settings.",
    "A family slot is YOUR OWN separate Spotify account with YOUR playlists, library, and algorithm — just paid as part of a family plan. Individual is the official ৳219 plan on your own card. We recommend official for zero risk; family slot saves ৳90/month.":
        "Spotify Family uses separate member accounts, but Spotify requires Family members to reside at the same address. A third-party family-slot offer is provider-policy dependent and is not equivalent to Individual.",
    "Official BD student price is ৳109 — if you have .edu, take that instead. We'll tell you.":
        "Spotify Student is ৳109/month for eligible verified higher-education students. Spotify controls eligibility verification; a .edu email alone is not the rule.",
    "৳239/month individual (verified), Family ৳359 for 5 members at the same household address, YouTube Music alone ৳199. Our family slot at ৳149 sits between the ৳99 market slots and official — with warranty.":
        "YouTube Premium is officially available in Bangladesh. Verify live YouTube checkout for the current price and payment method; Family members must live at the same residential address.",
    "Google requires same-household; enforcement is light but real. ৳149 slot vs ৳239 official — both honest options, you choose informed.":
        "YouTube requires family members to live at the same residential address, and its Help Center says household eligibility may be confirmed periodically by electronic check.",
    "Yes — Premium includes ad-free YouTube + YouTube Music. If you already pay for both separately, switch to Premium and cancel your music subscription. One ৳149 slot replaces two payments.":
        "YouTube Premium includes YouTube Music Premium benefits. Compare your current memberships and live YouTube offer before changing another subscription.",
}

for path in SITE.rglob("*.html"):
    t = path.read_text(encoding="utf-8", errors="replace")
    old = t
    for a, b in GLOBAL.items():
        t = t.replace(a, b)
    if t != old:
        path.write_text(t, encoding="utf-8")


def panel(kind, bn):
    if kind == "netflix":
        f = FACTS["netflix"]
        rows = "".join(f"<tr><td>{n}</td><td>US${v['price_month']:.2f}/mo</td><td>{v['quality']}</td><td>{v['devices']}</td></tr>" for n, v in f["plans"].items())
        title = "Netflix বাংলাদেশ — official plan facts" if bn else "Netflix Bangladesh — verified official plans"
        note = "SaveOnSub private-profile/personal labels Netflix-এর official tier name নয়; underlying tier, household/account control ও warranty payment-এর আগে confirm করুন।" if bn else "SaveOnSub private-profile/personal labels are seller access labels, not official Netflix tier names. Confirm underlying tier, household/account control and warranty before payment."
        return f'<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="netflix"><h2 style="font-size:20px;margin:0 0 8px">{title}</h2><div class="tbl"><table><tr><th>Plan</th><th>Netflix BD price</th><th>Quality</th><th>Devices</th></tr>{rows}</table></div><p style="font-size:13px;color:var(--muted);margin-top:8px">{note} <a href="{f["official_source"]}" target="_blank" rel="noopener nofollow">Netflix BD ↗</a></p></section>'
    if kind == "spotify":
        f, p = FACTS["spotify"], FACTS["spotify"]["plans"]
        title = "Spotify Premium বাংলাদেশ — official price + Family rule" if bn else "Spotify Premium Bangladesh — verified price + Family rule"
        prices = f"Individual ৳{p['Individual']} · Student ৳{p['Student']} · Duo ৳{p['Duo']} · Family ৳{p['Family']}"
        rule = "Family members-কে একই address-এ থাকতে হয়; SaveOnSub family slot official Individual-এর equivalent নয়।" if bn else "Spotify requires Family members to reside at the same address; a SaveOnSub family slot is not equivalent to official Individual."
        return f'<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="spotify"><h2 style="font-size:20px;margin:0 0 8px">{title}</h2><p style="font-size:14px"><b>Official BD prices:</b> {prices}</p><p style="font-size:14px;margin-top:8px"><b>Family eligibility:</b> {rule}</p><p style="font-size:13px;color:var(--muted);margin-top:8px"><a href="{f["official_source"]}" target="_blank" rel="noopener nofollow">Spotify BD ↗</a></p></section>'
    f = FACTS["youtube"]
    title = "YouTube Premium বাংলাদেশ — availability + household rule" if bn else "YouTube Premium Bangladesh — verified availability + household rule"
    body = "YouTube Premium বাংলাদেশে officially available। Exact checkout price/payment method-এর জন্য live YouTube checkout authoritative। Family member-কে family manager-এর একই residential address-এ থাকতে হবে; periodic electronic checks হতে পারে।" if bn else "YouTube Premium is officially available in Bangladesh. Live YouTube checkout is authoritative for current price/payment method. Family members must live at the same residential address as the family manager; periodic electronic checks may apply."
    return f'<section class="notice mt2" data-entertainment-facts="{VERIFIED}" data-provider="youtube"><h2 style="font-size:20px;margin:0 0 8px">{title}</h2><p style="font-size:14px">{body}</p><p style="font-size:13px;color:var(--muted);margin-top:8px"><a href="{f["availability_source"]}" target="_blank" rel="noopener nofollow">Availability ↗</a> · <a href="{f["family_source"]}" target="_blank" rel="noopener nofollow">Family rules ↗</a></p></section>'


def patch(kind, rel, bn=False):
    p, t = read(rel)
    t = re.sub(r'\s*<span class="savepct">[^<]*</span>', '', t, flags=re.I)
    t = re.sub(r'<tr><td>Official list converted at site anchor rate</td>.*?</tr>', '', t, flags=re.S)
    t = re.sub(r'<tr><td>Official list, site anchor rate[^<]*</td>.*?</tr>', '', t, flags=re.S)

    if kind == "netflix":
        desc = "Netflix বাংলাদেশে SaveOnSub-এ ৳349 থেকে। Netflix BD official US$2.99–US$9.99/month range, underlying tier ও household/account risk কেনার আগে তুলনা করুন।" if bn else "Netflix in Bangladesh from ৳349 on SaveOnSub. Compare Netflix BD's current US$2.99–US$9.99/month range, underlying tier and household/account risk before buying."
        official = "Netflix BD: US$2.99–US$9.99/মাস" if bn else "Netflix BD: US$2.99–US$9.99/month"
        risk = "শেয়ার্ড · household/account ঝুঁকি" if bn else "SHARED · HOUSEHOLD / ACCOUNT RISK"
    elif kind == "spotify":
        desc = "Spotify Premium বাংলাদেশে SaveOnSub-এ ৳129 থেকে। Official BD prices ও same-address Family rule কেনার আগে তুলনা করুন।" if bn else "Spotify Premium in Bangladesh from ৳129 on SaveOnSub. Compare official BD prices and Spotify's same-address Family rule before buying."
        official = "Spotify BD: Individual ৳219/মাস · Student ৳109" if bn else "Spotify BD: Individual ৳219/mo · Student ৳109/mo"
        risk = "শেয়ার্ড · household-policy ঝুঁকি" if bn else "SHARED · HOUSEHOLD-POLICY RISK"
    else:
        desc = "YouTube Premium বাংলাদেশে officially available। SaveOnSub ৳149 থেকে; live checkout ও same-residential-address Family rule যাচাই করুন।" if bn else "YouTube Premium is officially available in Bangladesh. SaveOnSub starts at ৳149; verify live checkout and the same-residential-address Family rule."
        official = "YouTube Premium: বাংলাদেশে available · live checkout যাচাই করুন" if bn else "YouTube Premium: available in Bangladesh · verify live checkout"
        risk = "শেয়ার্ড · household-policy ঝুঁকি" if bn else "SHARED · HOUSEHOLD-POLICY RISK"

    t = meta(t, "description", desc)
    t = meta(t, "og:description", desc, prop=True)
    t = product_desc(t, desc)
    t, n = re.subn(r'<span class="official"[^>]*>.*?</span>', f'<span class="official" data-entertainment-official="{VERIFIED}">{official}</span>', t, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — official anchor missing in {rel}")

    t = re.sub(r'<span class="tos shared-(?:low|med)">(?:SHARED · LOW RISK|SHARED · CHECK ACCESS RISK|SHARED · WARRANTY COVERED)</span>', f'<span class="tos shared-high">{risk}</span>', t)
    t = re.sub(r'<span class="tos shared-(?:low|med)">(?:শেয়ার্ড ?· ?কম ঝুঁকি|শেয়ার্ড ?· ?ওয়ারেন্টিসহ)</span>', f'<span class="tos shared-high">{risk}</span>', t)
    if kind in {"spotify", "youtube"}:
        t = t.replace('<span class="tos official">OFFICIAL</span>', '<span class="tos official">ASSISTED OFFICIAL PATH</span>')
        t = t.replace("Official BD Individual (guide)", "Assisted official-path setup")

    anchor = '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>' if bn else '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>'
    if f'data-entertainment-facts="{VERIFIED}"' not in t:
        if anchor not in t:
            raise SystemExit(f"ENTERTAINMENT COHORT ERROR — plan anchor missing in {rel}")
        t = t.replace(anchor, panel(kind, bn) + "\n" + anchor, 1)
    p.write_text(t, encoding="utf-8")


for slug in ("netflix", "spotify", "youtube-premium"):
    kind = "youtube" if slug == "youtube-premium" else slug
    patch(kind, f"p/{slug}.html")
    patch(kind, f"bn/p/{slug}.html", True)

p, g = read("blog/netflix-spotify-youtube-premium-price-bd.html")
desc = "Netflix, Spotify and YouTube Premium in Bangladesh: official provider facts verified 2026-09-09, plus SaveOnSub access options and household-policy warnings."
g = meta(g, "description", desc)
g = meta(g, "og:description", desc, prop=True)
g = re.sub(r'("@type":\s*"Article".*?"description":\s*")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), g, count=1, flags=re.S)
g = g.replace("PRICE SHEET · UPDATED 2026-09-03", "PRICE SHEET · VERIFIED 2026-09-09")
g = g.replace("Some have official taka prices (use them!). Some don't. Here's the honest map.", "Compare current official provider facts with the exact SaveOnSub access method before paying.")
pat = re.compile(r'<div class="tbl mt3"><table>.*?</table></div>\s*<h2 class="mt3" style="font-size:22px">The rule of thumb</h2>\s*<p class="sub" style="font-size:15px">.*?</p>', re.S)
replacement = f'''<section data-entertainment-guide-facts="{VERIFIED}"><div class="tbl mt3"><table><tr><th>Service</th><th>Official provider fact</th><th>SaveOnSub</th><th>Decision point</th></tr><tr><td>Spotify</td><td>Individual ৳219 · Student ৳109 · Duo ৳299 · Family ৳379</td><td><a href="../p/spotify.html">From ৳129</a></td><td>Family requires same address; seller slot ≠ Individual.</td></tr><tr><td>YouTube Premium</td><td>Available in Bangladesh; verify live checkout</td><td><a href="../p/youtube-premium.html">From ৳149</a></td><td>Family requires same residential address; periodic checks may apply.</td></tr><tr><td>Netflix</td><td>US$2.99–US$9.99/month on Netflix BD</td><td><a href="../p/netflix.html">From ৳349</a></td><td>Confirm underlying Netflix tier; seller access label ≠ official tier.</td></tr></table></div><h2 class="mt3" style="font-size:22px">The rule of thumb</h2><p class="sub" style="font-size:15px">Prefer the provider's own plan when it fits your payment method and eligibility. For a SaveOnSub shared/family/profile option, compare household rules, account control, privacy/continuity risk and exact warranty before payment.</p></section>'''
g, n = pat.subn(replacement, g, count=1)
if n != 1:
    raise SystemExit("ENTERTAINMENT COHORT ERROR — guide table anchor changed")
g = g.replace("No — Netflix bills in USD requiring an international card. BD users either use cards, or warranted resellers offering private profiles from ~৳349/month.", "Netflix's Bangladesh page currently lists official plans at US$2.99–US$9.99/month. A SaveOnSub private profile is a separate seller access method; confirm the underlying tier.")
g = g.replace("Yes, with regional pricing around ৳239/month including YouTube Music — check the app for your exact offer.", "Yes. YouTube Help lists Bangladesh as a Premium market. Verify live checkout; Family members must share the same residential address.")
for a, b in GLOBAL.items():
    g = g.replace(a, b)
p.write_text(g, encoding="utf-8")

SCOPED = [SITE / x for x in [
    "p/netflix.html", "p/spotify.html", "p/youtube-premium.html",
    "bn/p/netflix.html", "bn/p/spotify.html", "bn/p/youtube-premium.html",
    "blog/netflix-spotify-youtube-premium-price-bd.html",
]]
for path in SCOPED[:6]:
    t = path.read_text(encoding="utf-8")
    if f'data-entertainment-facts="{VERIFIED}"' not in t or f'data-entertainment-official="{VERIFIED}"' not in t:
        raise SystemExit(f"ENTERTAINMENT COHORT ERROR — current markers missing in {path}")

for phrase in [
    "official reference ~৳879", "Official: ~৳879/mo", "Official: ~৳220/mo", "Official: ~৳242/mo",
    "SHARED · WARRANTY COVERED", "SHARED · LOW RISK", "enforcement is light but real",
    "No official path without a card", "Netflix has no official taka price", "regional pricing around ৳239/month",
]:
    for path in SCOPED:
        if phrase.lower() in path.read_text(encoding="utf-8", errors="replace").lower():
            raise SystemExit(f"ENTERTAINMENT COHORT ERROR — stale phrase survived: {phrase} in {path}")

if f'data-entertainment-guide-facts="{VERIFIED}"' not in SCOPED[-1].read_text(encoding="utf-8"):
    raise SystemExit("ENTERTAINMENT COHORT ERROR — guide marker missing")

print("Entertainment cohort hardening OK — Netflix/Spotify/YouTube facts and household rules refreshed.")
