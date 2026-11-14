#!/usr/bin/env python3
"""Show the support/refund terms on every product page (EN + BN), before payment.

Why: /refund and /warranty say the covered period is "shown on your product", but
product pages never showed one. This step adds one short, truthful block per
product page. It invents NO period, number of days or guarantee.

* The block lists EVERY plan of the product with its own access type and covered
  period. The period reads "confirmed in writing for your order before you pay"
  unless the CEO supplies a real value per plan in
  ops/seo/control/coverage-periods.json: {product_id: {plan_id: {"en": "...", "bn": "..."}}}.
  Empty file = no period promised for any plan.
* Each SHARED plan row carries its own plain disclosure: arranged by SaveOnSub, not
  provided or endorsed by the provider, the provider's own account rules may apply.
  Personal/official rows carry none. It never claims provider permission.

Usage: python3 coverage_disclosure.py [SITE_DIR] [--check]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
WA = "https://wa.me/8801305869242"
MARK = 'data-coverage-block="1"'
PERIODS = ROOT / "ops" / "seo" / "control" / "coverage-periods.json"

L = {
    "en": {
        "dir": "p", "up": "../",
        "h2": "Support and refund terms for this plan",
        "period": "Covered support period",
        "default": "confirmed in writing for your order before you pay",
        "fix": "If access stops working through no fault of yours inside that period, we fix it first. If we cannot restore working access, you get a refund for the unused days.",
        "full": "Full table:", "refund": "Refund policy", "support": "Support terms",
        "plans": "Plan by plan",
        "kind": {"shared": "Shared access", "personal": "Personal access", "official": "Official provider plan"},
        "shared": "arranged by SaveOnSub, not provided or endorsed by {name}; {name}'s own account rules may apply. Choose a personal plan if you need access that is yours alone.",
        "cta": "Ask for my covered period before paying",
        "wa": "Hi! Before I pay for {name}, please confirm my covered support period and refund terms in writing.",
        "faq": re.compile(r'<h2[^>]*>\s*Questions about[^<]*</h2>'),
    },
    "bn": {
        "dir": "bn/p", "up": "../../",
        "h2": "এই প্ল্যানের সাপোর্ট ও রিফান্ড শর্ত",
        "period": "কভারের সাপোর্ট সময়",
        "default": "পেমেন্টের আগে আপনার অর্ডারের জন্য লিখিতভাবে নিশ্চিত করা হয়",
        "fix": "আপনার দোষ ছাড়া ওই সময়ের মধ্যে অ্যাক্সেস বন্ধ হলে আগে আমরা ঠিক করি। কাজ করা অ্যাক্সেস ফিরিয়ে দিতে না পারলে অব্যবহৃত দিনের টাকা ফেরত পাবেন।",
        "full": "পূর্ণ তালিকা:", "refund": "রিফান্ড নীতি", "support": "সাপোর্ট শর্ত",
        "plans": "প্ল্যান ধরে ধরে",
        "kind": {"shared": "শেয়ার্ড অ্যাক্সেস", "personal": "পার্সোনাল অ্যাক্সেস", "official": "প্রোভাইডারের অফিশিয়াল প্ল্যান"},
        "shared": "অ্যাক্সেস SaveOnSub ব্যবস্থা করে, {name} দেয় না বা অনুমোদন করে না; {name}-এর নিজস্ব অ্যাকাউন্ট নিয়ম প্রযোজ্য হতে পারে। শুধু আপনার নিজের অ্যাক্সেস দরকার হলে পার্সোনাল প্ল্যান বেছে নিন।",
        "cta": "পেমেন্টের আগে আমার কভারের সময় জানতে চাই",
        "wa": "হাই! {name} কেনার আগে আমার কভারের সাপোর্ট সময় ও রিফান্ড শর্ত লিখিতভাবে নিশ্চিত করুন।",
        "faq": re.compile(r'<h2[^>]*>\s*[^<]*নিয়ে সাধারণ প্রশ্ন</h2>'),
    },
}
FALLBACK = re.compile(r"</div></main>")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_catalog(site: Path) -> dict:
    t = (site / "assets" / "catalog.js").read_text(encoding="utf-8")
    start = t.index("const CATALOG = ") + len("const CATALOG = ")
    obj, _ = json.JSONDecoder().raw_decode(t[start:])
    return {p["id"]: p for p in obj["products"]}


def load_periods() -> dict:
    if not PERIODS.exists():
        return {}
    return json.loads(PERIODS.read_text(encoding="utf-8"))


def block(lang: str, prod: dict, periods: dict) -> str:
    s = L[lang]
    name = prod["name"]
    per_plan = periods.get(prod["id"]) or {}
    rows = []
    for pl in prod.get("plans", []):
        custom = (per_plan.get(pl.get("plan_id")) or {}).get(lang)
        period = esc(custom) if custom else s["default"]
        kind = s["kind"].get(pl.get("type"), esc(str(pl.get("type", ""))))
        note = f' {esc(s["shared"].format(name=name))}' if pl.get("type") == "shared" else ""
        rows.append(
            f'<li data-plan-id="{esc(pl.get("plan_id", ""))}"><b>{esc(pl["label"])}</b> ({kind}): '
            f'{s["period"]}: {period}.{note}</li>'
        )
    href = f'{WA}?text={quote(s["wa"].format(name=name))}'
    return (
        f'<section class="mt3" id="support-terms" {MARK} '
        'style="border:1px solid var(--line,rgba(255,255,255,.12));border-radius:14px;padding:14px 16px">'
        f'<h2 style="font-size:20px;margin:0 0 8px">{s["h2"]}</h2>'
        f'<p style="margin:0 0 8px;font-size:15px;line-height:1.7">{s["fix"]} {s["full"]} '
        f'<a href="{s["up"]}refund">{s["refund"]}</a> · <a href="{s["up"]}warranty">{s["support"]}</a>.</p>'
        f'<h3 style="font-size:16px;margin:0 0 6px">{s["plans"]}</h3>'
        '<ul style="margin:0 0 12px 18px;padding:0;font-size:15px;line-height:1.7">'
        f'{"".join(rows)}</ul>'
        f'<a class="btn btn-wa btn-sm" href="{href}" target="_blank" rel="noopener">{s["cta"]}</a>'
        "</section>\n  "
    )


def apply(site: Path) -> int:
    cat, periods = load_catalog(site), load_periods()
    done = 0
    for lang, s in L.items():
        for f in sorted((site / s["dir"]).glob("*.html")):
            prod = cat.get(f.stem)
            if not prod or not prod.get("plans"):
                continue  # inquiry-only or non-product page
            t = f.read_text(encoding="utf-8")
            if MARK in t:
                continue
            blk = block(lang, prod, periods)
            m = s["faq"].search(t) or FALLBACK.search(t)
            if not m:
                print(f"[coverage] FAIL — no anchor in {f.relative_to(site)}")
                return 1
            t = t[: m.start()] + blk + t[m.start():]
            f.write_text(t, encoding="utf-8")
            done += 1
    print(f"[coverage] PASS — support/refund block added to {done} product pages (no period or guarantee invented)")
    return 0


def check(site: Path) -> int:
    cat = load_catalog(site)
    bad = []
    for lang, s in L.items():
        for f in sorted((site / s["dir"]).glob("*.html")):
            prod = cat.get(f.stem)
            if prod and prod.get("plans") and MARK not in f.read_text(encoding="utf-8"):
                bad.append(str(f.relative_to(site)))
    if bad:
        print("[coverage] FAIL — missing block on:", ", ".join(bad[:10]))
        return 1
    print("[coverage] CHECK PASS")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    site = Path(args[0]) if args else ROOT / "_site"
    return check(site) if "--check" in sys.argv else apply(site)


if __name__ == "__main__":
    sys.exit(main())
