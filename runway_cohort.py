#!/usr/bin/env python3
"""Harden Runway money pages with verified 2026-09-09 plan facts."""
from pathlib import Path
import json
import re

ROOT = Path("_site")
FACTS = json.loads(Path("ops/RUNWAY-COHORT-FACTS-2026-09-09.json").read_text(encoding="utf-8"))
VERIFIED = FACTS["verified_on"]
SOURCES = FACTS["official_sources"]
PLANS = FACTS["plans"]

if not ROOT.is_dir():
    raise SystemExit("RUNWAY COHORT ERROR — _site missing")


def load(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f"RUNWAY COHORT ERROR — missing staged page: {rel}")
    return p, p.read_text(encoding="utf-8")


def meta(text, key, value, prop=False):
    attr = "property" if prop else "name"
    pattern = rf'(<meta\s+{attr}="{re.escape(key)}"\s+content=")[^"]*(">)'
    text, count = re.subn(pattern, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if count != 1:
        raise SystemExit(f"RUNWAY COHORT ERROR — meta missing: {key}")
    return text


def product_desc(text, value):
    return re.sub(
        r'("@type":\s*"Product".*?"description":\s*")[^"]*(")',
        lambda m: m.group(1) + value + m.group(2),
        text,
        count=1,
        flags=re.S,
    )


def panel(bn=False):
    s, p, m = PLANS["Standard"], PLANS["Pro"], PLANS["Max"]
    if bn:
        return f'''<section class="notice mt2" data-runway-facts="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Runway — current official plans ও Unlimited transition</h2>
<div class="tbl"><table><tr><th>Plan</th><th>Monthly</th><th>Annual effective</th><th>Credits</th></tr>
<tr><td>Standard</td><td>US${s['monthly_usd']}/মাস</td><td>US${s['annual_effective_usd_month']}/মাস</td><td>{s['credits_month']} credits/মাস</td></tr>
<tr><td>Pro</td><td>US${p['monthly_usd']}/মাস</td><td>US${p['annual_effective_usd_month']}/মাস</td><td>{p['credits_month']} credits/মাস</td></tr>
<tr><td>Max</td><td>US${m['monthly_usd']}/মাস</td><td>US${m['annual_effective_usd_month']}/মাস</td><td>{m['credits_month']} credits/মাস</td></tr></table></div>
<p style="font-size:14px;margin-top:8px"><b>Unlimited নতুন order নয়:</b> Runway 1 June 2026 থেকে নতুন Unlimited subscription বন্ধ করেছে। Existing legacy Unlimited users-এর transition 30 November 2026 পর্যন্ত extend করা হয়েছে, এরপর Max replacement path প্রযোজ্য। তাই SaveOnSub-এ legacy Unlimited inventory নতুন order হিসেবে checkout করা যাবে না।</p>
<p style="font-size:14px;margin-top:8px"><b>Credit behavior:</b> Standard/Pro monthly credits roll over করে না; Max unused credits সর্বোচ্চ এক মাসের entitlement পর্যন্ত carry করতে পারে। Exact model credit costs পরিবর্তন হতে পারে।</p>
<p style="font-size:14px;margin-top:8px"><b>Account policy:</b> individual account credentials share করা Runway-এর Terms-এর বিরুদ্ধে হতে পারে; selected SaveOnSub access method payment-এর আগে confirm করুন।</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official Runway sources verified {VERIFIED}: <a href="{SOURCES['pricing']}" target="_blank" rel="noopener nofollow">pricing ↗</a> · <a href="{SOURCES['credits']}" target="_blank" rel="noopener nofollow">credits ↗</a> · <a href="{SOURCES['unlimited_transition']}" target="_blank" rel="noopener nofollow">Unlimited→Max ↗</a></p>
</section>'''
    return f'''<section class="notice mt2" data-runway-facts="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Runway — current official plans and Unlimited transition</h2>
<div class="tbl"><table><tr><th>Plan</th><th>Monthly</th><th>Annual effective</th><th>Credits</th></tr>
<tr><td>Standard</td><td>US${s['monthly_usd']}/mo</td><td>US${s['annual_effective_usd_month']}/mo</td><td>{s['credits_month']} credits/mo</td></tr>
<tr><td>Pro</td><td>US${p['monthly_usd']}/mo</td><td>US${p['annual_effective_usd_month']}/mo</td><td>{p['credits_month']} credits/mo</td></tr>
<tr><td>Max</td><td>US${m['monthly_usd']}/mo</td><td>US${m['annual_effective_usd_month']}/mo</td><td>{m['credits_month']} credits/mo</td></tr></table></div>
<p style="font-size:14px;margin-top:8px"><b>Unlimited is not a new-order tier:</b> Runway stopped offering new Unlimited subscriptions on June 1, 2026. Existing legacy Unlimited users received a transition extension through November 30, 2026, after which Max is the replacement path. SaveOnSub therefore does not present legacy Unlimited inventory as a new checkout option.</p>
<p style="font-size:14px;margin-top:8px"><b>Credit behavior:</b> Standard and Pro monthly credits do not roll over. Max unused credits can roll over only up to one month's entitlement. Exact model credit costs can change.</p>
<p style="font-size:14px;margin-top:8px"><b>Account policy:</b> sharing individual account credentials can violate Runway's Terms; confirm the exact SaveOnSub access method before payment.</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Official Runway sources verified {VERIFIED}: <a href="{SOURCES['pricing']}" target="_blank" rel="noopener nofollow">pricing ↗</a> · <a href="{SOURCES['credits']}" target="_blank" rel="noopener nofollow">credits ↗</a> · <a href="{SOURCES['unlimited_transition']}" target="_blank" rel="noopener nofollow">Unlimited→Max ↗</a></p>
</section>'''


def disable_legacy_unlimited(text, bn=False):
    text = re.sub(r',?\s*\{"@type":\s*"Offer",\s*"name":\s*"Unlimited Personal".*?\}', '', text, count=1, flags=re.S)
    text = text.replace('"offerCount": 3', '"offerCount": 2')
    text = text.replace('"highPrice": 11362', '"highPrice": 4186')
    pattern = re.compile(
        r'<div class="pcard" style="flex-direction:row;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">\s*'
        r'<div><b>Unlimited Personal</b><br>.*?'</n        r'</div></div>',
        re.S,
    )
    replacement = (
        '<div class="notice mt2" data-runway-legacy-unlimited="retired-new-sales"><b>Legacy Unlimited — নতুন order বন্ধ</b><p style="margin-top:6px;font-size:13.5px">Runway 1 June 2026 থেকে নতুন Unlimited subscription বন্ধ করেছে। Existing legacy subscribers transition period-এর জন্য আলাদা support পেতে পারেন; নতুন order-এর জন্য current Runway tiers compare করুন।</p></div>'
        if bn else
        '<div class="notice mt2" data-runway-legacy-unlimited="retired-new-sales"><b>Legacy Unlimited — not available for new orders</b><p style="margin-top:6px;font-size:13.5px">Runway stopped new Unlimited subscriptions on June 1, 2026. Existing legacy subscribers may remain in the transition window; for a new order, compare current Runway tiers instead.</p></div>'
    )
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit("RUNWAY COHORT ERROR — legacy Unlimited card structure changed")
    return text


def patch(rel, bn=False):
    p, t = load(rel)
    desc = (
        "Runway বাংলাদেশে SaveOnSub-এ ৳499 থেকে। Official Standard/Pro/Max pricing, credits, legacy Unlimited→Max transition এবং access method কেনার আগে যাচাই করুন।"
        if bn else
        "Runway in Bangladesh from ৳499 on SaveOnSub. Compare current official Standard/Pro/Max pricing, credits, the legacy Unlimited→Max transition and access method before buying."
    )
    t = meta(t, "description", desc)
    t = meta(t, "og:description", desc, prop=True)
    t = product_desc(t, desc)
    t = re.sub(r'\s*<span class="savepct">[^<]*</span>', '', t, count=1)
    official = (
        '<span class="official" data-runway-official="2026-09-09">Runway: Standard US$15 · Pro US$35 · Max US$95/মাস</span>'
        if bn else
        '<span class="official" data-runway-official="2026-09-09">Runway: Standard US$15 · Pro US$35 · Max US$95/month</span>'
    )
    t, count = re.subn(r'<span class="official"[^>]*>.*?</span>', official, t, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"RUNWAY COHORT ERROR — official anchor missing: {rel}")
    t = re.sub(r'<tr><td>Official list converted at site anchor rate</td>.*?</tr>', '', t, flags=re.S)
    t = re.sub(r'<tr><td>Official list, site anchor rate[^<]*</td>.*?</tr>', '', t, flags=re.S)
    t = re.sub(r'<tr><td>অফিসিয়াল[^<]*(?:anchor|converted)[^<]*</td>.*?</tr>', '', t, flags=re.S | re.I)
    t = disable_legacy_unlimited(t, bn)
    anchor = '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>' if bn else '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>'
    if f'data-runway-facts="{VERIFIED}"' not in t:
        if anchor not in t:
            raise SystemExit(f"RUNWAY COHORT ERROR — plan anchor missing: {rel}")
        t = t.replace(anchor, panel(bn) + "\n  " + anchor, 1)
    t = t.replace("Official $12 Basic · $28 Standard · $76 Pro", "Runway annual-effective references: Standard $12 · Pro $28 · Max $76")
    t = t.replace("Runway = pro editing suite + Gen-4 video; Kling = pure generation value. Filmmakers pick Runway.", "Runway combines generative video and creative tools; Kling has a different model/credit structure. Compare the current models, credits and workflow you need rather than assuming one is best for every creator.")
    p.write_text(t, encoding="utf-8")


patch("p/runway.html", False)
patch("bn/p/runway.html", True)

gp, g = load("blog/ai-video-tools-price-comparison-bd-2026.html")
gdesc = "AI video tools in Bangladesh: current SaveOnSub prices plus provider-plan caveats. Runway facts verified 2026-09-09; compare access type, credits and current provider pricing before buying."
g = meta(g, "description", gdesc)
g = meta(g, "og:description", gdesc, prop=True)
g = re.sub(r'("@type":\s*"Article".*?"description":\s*")[^"]*(")', lambda m: m.group(1) + gdesc + m.group(2), g, count=1, flags=re.S)
g = g.replace("PRICE SHEET · UPDATED 2026-09-03", "PRICE SHEET · RUNWAY VERIFIED 2026-09-09")
g = g.replace("Every AI video tool we carry, cheapest plan, versus the wider BD market where we surveyed it. Receipts on each product page.", "Compare current SaveOnSub offers with each provider's live plan structure, credits and access method. Historical BD market ranges are secondary and should not be treated as live quotes.")
g = re.sub(r'<tr><td><a href="\.\./p/runway\.html".*?</tr>', '<tr data-runway-guide-facts="2026-09-09"><td><a href="../p/runway.html" style="color:var(--green2)">Runway</a></td><td>From ৳499</td><td>Official: Standard US$15 · Pro US$35 · Max US$95 monthly</td><td>Generative video + creative workflow; check credits and tier</td></tr>', g, count=1, flags=re.S)
g = g.replace("Kling at ৳270 vs a ৳1,299+ market is not a typo.", "Historical market ranges can become stale quickly. Use the current SaveOnSub product price plus the provider's live plan page for the decision.")
g = g.replace("Kling AI at ৳270/month via SAVEONSUB — dramatically below the ৳1,299–13,000 BD market range, with warranty.", "The lowest listed SaveOnSub AI-video offer can change. Compare current product pages, access type, credits and applicable warranty instead of relying on a historical market-range claim.")
gp.write_text(g, encoding="utf-8")

for rel in ["p/runway.html", "bn/p/runway.html"]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    for marker in [f'data-runway-facts="{VERIFIED}"', f'data-runway-official="{VERIFIED}"', 'data-runway-legacy-unlimited="retired-new-sales"']:
        if marker not in text:
            raise SystemExit(f"RUNWAY COHORT ERROR — marker missing in {rel}: {marker}")
    for stale in ["Official: ~৳1,320", "SAVE 62%", "cartAdd(&quot;runway&quot;,&quot;Unlimited Personal&quot;", '"name": "Unlimited Personal"']:
        if stale in text:
            raise SystemExit(f"RUNWAY COHORT ERROR — stale/new-sale Unlimited signal survived in {rel}: {stale}")

if 'data-runway-guide-facts="2026-09-09"' not in (ROOT / "blog/ai-video-tools-price-comparison-bd-2026.html").read_text(encoding="utf-8"):
    raise SystemExit("RUNWAY COHORT ERROR — guide marker missing")

print("Runway cohort hardening OK — current tiers/credits enforced; legacy Unlimited removed from new-sale flow.")
