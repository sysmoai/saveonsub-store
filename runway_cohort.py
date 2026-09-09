#!/usr/bin/env python3
from pathlib import Path
import json
import re

SITE = Path("_site")
FACTS = json.loads(Path("ops/RUNWAY-COHORT-FACTS-2026-09-09.json").read_text(encoding="utf-8"))
VERIFIED = FACTS["verified_on"]
SOURCES = FACTS["official_sources"]
PLANS = FACTS["plans"]

if not SITE.is_dir():
    raise SystemExit("RUNWAY COHORT ERROR — _site missing")


def load(rel):
    p = SITE / rel
    if not p.exists():
        raise SystemExit(f"RUNWAY COHORT ERROR — missing {rel}")
    return p, p.read_text(encoding="utf-8")


def replace_meta(text, attr, key, value):
    pat = rf'(<meta\s+{attr}="{re.escape(key)}"\s+content=")[^"]*(">)'
    text, n = re.subn(pat, lambda m: m.group(1) + value + m.group(2), text, count=1, flags=re.I)
    if n != 1:
        raise SystemExit(f"RUNWAY COHORT ERROR — missing meta {key}")
    return text


def facts_panel(bn=False):
    s, p, m = PLANS["Standard"], PLANS["Pro"], PLANS["Max"]
    if bn:
        return f'''<section class="notice mt2" data-runway-facts="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Runway — current plans ও Unlimited transition</h2>
<div class="tbl"><table><tr><th>Plan</th><th>Monthly</th><th>Annual effective</th><th>Credits</th></tr>
<tr><td>Standard</td><td>US${s['monthly_usd']}/মাস</td><td>US${s['annual_effective_usd_month']}/মাস</td><td>{s['credits_month']}/মাস</td></tr>
<tr><td>Pro</td><td>US${p['monthly_usd']}/মাস</td><td>US${p['annual_effective_usd_month']}/মাস</td><td>{p['credits_month']}/মাস</td></tr>
<tr><td>Max</td><td>US${m['monthly_usd']}/মাস</td><td>US${m['annual_effective_usd_month']}/মাস</td><td>{m['credits_month']}/মাস</td></tr></table></div>
<p style="font-size:14px;margin-top:8px"><b>Unlimited:</b> Runway 1 June 2026 থেকে নতুন Unlimited subscription বন্ধ করেছে। Existing legacy users-এর transition 30 November 2026 পর্যন্ত extend করা হয়েছে; এরপর Max replacement path প্রযোজ্য। তাই SaveOnSub legacy Unlimited-কে new-order checkout হিসেবে দেখায় না।</p>
<p style="font-size:14px;margin-top:8px"><b>Credits:</b> Standard/Pro monthly credits roll over করে না; Max unused credits সর্বোচ্চ এক মাসের entitlement পর্যন্ত carry করতে পারে।</p>
<p style="font-size:14px;margin-top:8px"><b>Policy:</b> individual account credentials share করা Runway Terms-এর বিরুদ্ধে হতে পারে। Selected SaveOnSub access method payment-এর আগে confirm করুন।</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Verified {VERIFIED}: <a href="{SOURCES['pricing']}" target="_blank" rel="noopener nofollow">pricing ↗</a> · <a href="{SOURCES['credits']}" target="_blank" rel="noopener nofollow">credits ↗</a> · <a href="{SOURCES['unlimited_transition']}" target="_blank" rel="noopener nofollow">Unlimited→Max ↗</a></p>
</section>'''
    return f'''<section class="notice mt2" data-runway-facts="{VERIFIED}">
<h2 style="font-size:20px;margin:0 0 8px">Runway — current plans and Unlimited transition</h2>
<div class="tbl"><table><tr><th>Plan</th><th>Monthly</th><th>Annual effective</th><th>Credits</th></tr>
<tr><td>Standard</td><td>US${s['monthly_usd']}/mo</td><td>US${s['annual_effective_usd_month']}/mo</td><td>{s['credits_month']}/mo</td></tr>
<tr><td>Pro</td><td>US${p['monthly_usd']}/mo</td><td>US${p['annual_effective_usd_month']}/mo</td><td>{p['credits_month']}/mo</td></tr>
<tr><td>Max</td><td>US${m['monthly_usd']}/mo</td><td>US${m['annual_effective_usd_month']}/mo</td><td>{m['credits_month']}/mo</td></tr></table></div>
<p style="font-size:14px;margin-top:8px"><b>Unlimited:</b> Runway stopped new Unlimited subscriptions on June 1, 2026. Existing legacy users received a transition extension through November 30, 2026; Max is the replacement path. SaveOnSub therefore does not expose legacy Unlimited as a new-order checkout option.</p>
<p style="font-size:14px;margin-top:8px"><b>Credits:</b> Standard and Pro monthly credits do not roll over. Max unused credits can roll over only up to one month's entitlement.</p>
<p style="font-size:14px;margin-top:8px"><b>Policy:</b> sharing individual account credentials can violate Runway Terms. Confirm the exact SaveOnSub access method before payment.</p>
<p style="font-size:13px;color:var(--muted);margin-top:8px">Verified {VERIFIED}: <a href="{SOURCES['pricing']}" target="_blank" rel="noopener nofollow">pricing ↗</a> · <a href="{SOURCES['credits']}" target="_blank" rel="noopener nofollow">credits ↗</a> · <a href="{SOURCES['unlimited_transition']}" target="_blank" rel="noopener nofollow">Unlimited→Max ↗</a></p>
</section>'''


def disable_unlimited_card(text, bn=False):
    start = text.find('<div class="pcard"', text.find('<b>Unlimited Personal</b>') - 250)
    if start < 0:
        raise SystemExit("RUNWAY COHORT ERROR — Unlimited card start missing")
    marker = 'cartAdd(&quot;runway&quot;,&quot;Unlimited Personal&quot;'
    button_pos = text.find(marker, start)
    if button_pos < 0:
        raise SystemExit("RUNWAY COHORT ERROR — Unlimited purchase action missing")
    end = text.find('</div></div>', button_pos)
    if end < 0:
        raise SystemExit("RUNWAY COHORT ERROR — Unlimited card end missing")
    end += len('</div></div>')
    repl = (
        '<div class="notice mt2" data-runway-legacy-unlimited="retired-new-sales"><b>Legacy Unlimited — নতুন order বন্ধ</b><p style="margin-top:6px;font-size:13.5px">Runway নতুন Unlimited subscription আর offer করে না। Existing legacy transition আলাদা; নতুন order-এর জন্য current Standard, Pro বা Max compare করুন।</p></div>'
        if bn else
        '<div class="notice mt2" data-runway-legacy-unlimited="retired-new-sales"><b>Legacy Unlimited — not available for new orders</b><p style="margin-top:6px;font-size:13.5px">Runway no longer offers new Unlimited subscriptions. Existing legacy transition is separate; for a new order compare current Standard, Pro or Max instead.</p></div>'
    )
    return text[:start] + repl + text[end:]


def patch_product(rel, bn=False):
    path, text = load(rel)
    desc = (
        "Runway বাংলাদেশে SaveOnSub-এ ৳499 থেকে। Current Standard/Pro/Max pricing, credits, Unlimited→Max transition এবং access method কেনার আগে যাচাই করুন।"
        if bn else
        "Runway in Bangladesh from ৳499 on SaveOnSub. Compare current Standard/Pro/Max pricing, credits, the Unlimited→Max transition and access method before buying."
    )
    text = replace_meta(text, "name", "description", desc)
    text = replace_meta(text, "property", "og:description", desc)
    text = re.sub(r'("@type":\s*"Product".*?"description":\s*")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), text, count=1, flags=re.S)
    text = re.sub(r'\s*<span class="savepct">[^<]*</span>', '', text, count=1)
    official = (
        '<span class="official" data-runway-official="2026-09-09">Runway: Standard US$15 · Pro US$35 · Max US$95/মাস</span>'
        if bn else
        '<span class="official" data-runway-official="2026-09-09">Runway: Standard US$15 · Pro US$35 · Max US$95/month</span>'
    )
    text, n = re.subn(r'<span class="official"[^>]*>.*?</span>', official, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"RUNWAY COHORT ERROR — official anchor missing in {rel}")
    text = re.sub(r'<tr><td>Official list converted at site anchor rate</td>.*?</tr>', '', text, flags=re.S)
    text = re.sub(r'<tr><td>অফিসিয়াল[^<]*(?:anchor|converted)[^<]*</td>.*?</tr>', '', text, flags=re.S | re.I)
    text = re.sub(r',?\s*\{"@type":\s*"Offer",\s*"name":\s*"Unlimited Personal".*?\}', '', text, count=1, flags=re.S)
    text = text.replace('"offerCount": 3', '"offerCount": 2').replace('"highPrice": 11362', '"highPrice": 4186')
    text = disable_unlimited_card(text, bn)
    anchor = '<h2 class="mt3" style="font-size:22px">আপনার প্ল্যান বেছে নিন</h2>' if bn else '<h2 class="mt3" style="font-size:22px">Choose your plan</h2>'
    if anchor not in text:
        raise SystemExit(f"RUNWAY COHORT ERROR — plan anchor missing in {rel}")
    text = text.replace(anchor, facts_panel(bn) + "\n  " + anchor, 1)
    text = text.replace("Official $12 Basic · $28 Standard · $76 Pro", "Runway annual-effective references: Standard $12 · Pro $28 · Max $76")
    path.write_text(text, encoding="utf-8")


patch_product("p/runway.html")
patch_product("bn/p/runway.html", True)

path, guide = load("blog/ai-video-tools-price-comparison-bd-2026.html")
guide_desc = "AI video tools in Bangladesh: current SaveOnSub prices plus provider-plan caveats. Runway facts verified 2026-09-09; compare access type, credits and current provider pricing before buying."
guide = replace_meta(guide, "name", "description", guide_desc)
guide = replace_meta(guide, "property", "og:description", guide_desc)
guide = re.sub(r'("@type":\s*"Article".*?"description":\s*")[^"]*(")', lambda m: m.group(1) + guide_desc + m.group(2), guide, count=1, flags=re.S)
guide = guide.replace("PRICE SHEET · UPDATED 2026-09-03", "PRICE SHEET · RUNWAY VERIFIED 2026-09-09")
guide = guide.replace("Every AI video tool we carry, cheapest plan, versus the wider BD market where we surveyed it. Receipts on each product page.", "Compare current SaveOnSub offers with each provider's live plan structure, credits and access method. Historical BD market ranges are secondary and should not be treated as live quotes.")
guide = re.sub(r'<tr><td><a href="\.\./p/runway\.html".*?</tr>', '<tr data-runway-guide-facts="2026-09-09"><td><a href="../p/runway.html" style="color:var(--green2)">Runway</a></td><td>From ৳499</td><td>Official: Standard US$15 · Pro US$35 · Max US$95 monthly</td><td>Generative video + creative workflow; check credits and tier</td></tr>', guide, count=1, flags=re.S)
guide = guide.replace("Kling at ৳270 vs a ৳1,299+ market is not a typo.", "Historical market ranges can become stale quickly. Use the current SaveOnSub product price plus the provider's live plan page for the decision.")
guide = guide.replace("Kling AI at ৳270/month via SAVEONSUB — dramatically below the ৳1,299–13,000 BD market range, with warranty.", "The lowest listed SaveOnSub AI-video offer can change. Compare current product pages, access type, credits and applicable warranty instead of relying on a historical market-range claim.")
path.write_text(guide, encoding="utf-8")

for rel in ["p/runway.html", "bn/p/runway.html"]:
    text = (SITE / rel).read_text(encoding="utf-8")
    for marker in [f'data-runway-facts="{VERIFIED}"', f'data-runway-official="{VERIFIED}"', 'data-runway-legacy-unlimited="retired-new-sales"']:
        if marker not in text:
            raise SystemExit(f"RUNWAY COHORT ERROR — missing marker {marker} in {rel}")
    for stale in ["Official: ~৳1,320", "SAVE 62%", "cartAdd(&quot;runway&quot;,&quot;Unlimited Personal&quot;", '"name": "Unlimited Personal"']:
        if stale in text:
            raise SystemExit(f"RUNWAY COHORT ERROR — stale signal survived in {rel}: {stale}")

if 'data-runway-guide-facts="2026-09-09"' not in (SITE / "blog/ai-video-tools-price-comparison-bd-2026.html").read_text(encoding="utf-8"):
    raise SystemExit("RUNWAY COHORT ERROR — guide marker missing")

print("Runway cohort hardening OK — current tiers/credits enforced; legacy Unlimited removed from new-sale flow.")
