#!/usr/bin/env python3
"""Buyer-intent answers on every priced product page (build step, after category_copy_polish.py).

Competitor research (SEO-COMPETITIVE-AUDIT, AIPS competitor intel, Semrush BD
buyer-phrase tab, 10 Nov 2026) shows BD rivals win on exact buyer phrases:
"<product> subscription bd", "<product> price in bd", "buy <product> with
bkash", "cheap/shared <product>", and Banglish "<product> dam koto". Our pages
answered "how much" and "how to pay" but not "which plan" or "is there a cheap
option", and the BN pages never used the Banglish phrase people type.

This step adds one short section per EN and BN product page with three
answers built only from the governed catalog (the page's own plans and
prices, access labels) and the standing order process. It also appends the
same three questions to the page's FAQPage JSON-LD so search engines and AI
assistants read the same answers as people do. No delivery time, rating,
order count, provider claim or competitor price is added. ``--check``
re-verifies without writing.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import product_rich_results as rr

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
KEYMAP = ROOT / "ops" / "seo" / "KEYWORD-MAP-2026-11-06.json"
MARK = "buyer-intent-2026-11-10"
ANCHORS = {False: ('<h2 class="mt3" style="font-size:22px">Related tools', "Price and ordering FAQ"),
           True: ('<h2 class="mt3" style="font-size:22px">সম্পর্কিত টুল', "দাম ও অর্ডার")}


def banglish(pid: str, name: str) -> str:
    try:
        for p in json.loads(KEYMAP.read_text(encoding="utf-8"))["products"]:
            if p["id"] == pid:
                hit = next((t for t in p.get("transliteration", []) if "dam koto" in t), "")
                if hit:
                    return hit
    except (OSError, ValueError, KeyError):
        pass
    return f"{name.lower()} dam koto"


def qa(pid: str, p: dict, bn: bool) -> list[tuple[str, str]]:
    name = rr.clean_name(p["name"])
    plans = sorted(p["plans"], key=lambda x: x["bdt"])
    low = plans[0]
    shared = [pl for pl in plans if pl.get("type") == "shared"]
    own = [pl for pl in plans if pl.get("type") != "shared"]
    def line(pl: dict) -> str:
        return f'{pl.get("label", "Plan")}: {rr.price_text(pl, bn)} ({rr.access_text(pl, bn)})'
    if bn:
        if shared and own:
            pick = (f"শুধু চেষ্টা করতে বা হালকা ব্যবহারে শেয়ার্ড প্ল্যান ({rr.price_text(shared[0], True)}) চলে, তবে এতে একাধিক জন "
                    f"একই অ্যাকাউন্ট ব্যবহার করেন। কাজ, ব্যক্তিগত চ্যাট বা ফাইলের জন্য কাস্টমার-নির্দিষ্ট প্ল্যান "
                    f"({rr.price_text(own[0], True)}) নিন।")
        elif shared:
            pick = "এখানে যে প্ল্যান আছে তা শেয়ার্ড: একাধিক জন একই অ্যাকাউন্ট ব্যবহার করেন। ব্যক্তিগত বা কাজের তথ্যের জন্য এটি উপযুক্ত নয়।"
        else:
            pick = "এখানে প্রতিটি প্ল্যান কাস্টমার-নির্দিষ্ট, অন্য কারো সাথে শেয়ার করা হয় না। আপনার কাজের পরিমাণ অনুযায়ী প্ল্যান বেছে নিন।"
        return [
            (f"{name} কোন প্ল্যান নেব?", pick),
            (f"{banglish(pid, name)}? {name}-এর সবচেয়ে কম দামের প্ল্যান কোনটা?",
             f"SaveOnSub-এ সবচেয়ে কম দাম {line(low)}। সব প্ল্যান: " + "; ".join(line(pl) for pl in plans)
             + "। বিকাশ, নগদ বা রকেটে টাকায় পেমেন্ট।"),
            ("নিশ্চিত হওয়ার আগে কি টাকা দিতে হয়?",
             "না। প্ল্যান, অ্যাক্সেস পদ্ধতি ও সময় আগে হোয়াটসঅ্যাপে লিখিতভাবে নিশ্চিত করা হয়, তারপর পেমেন্ট করবেন।"),
        ]
    if shared and own:
        pick = (f"The shared plan ({rr.price_text(shared[0], False)}) suits trying {name} or light use, but several people "
                f"use one account. For work, private chats or files, choose the customer-specific plan "
                f"({rr.price_text(own[0], False)}).")
    elif shared:
        pick = "The plan listed here is shared: several people use one account, so it is not suitable for private or work data."
    else:
        pick = "Every plan listed here is customer-specific and not shared with anyone else. Pick the one that matches how much you use it."
    return [
        (f"Which {name} plan should I choose in Bangladesh?", pick),
        (f"What is the cheapest {name} subscription in BD?",
         f"At SaveOnSub the lowest price is {line(low)}. All plans: " + "; ".join(line(pl) for pl in plans)
         + ". Pay in taka by bKash, Nagad or Rocket."),
        ("Do I pay before the order is confirmed?",
         "No. The plan, access method and timing are confirmed in writing on WhatsApp first, and you pay after that."),
    ]


def section(pairs: list[tuple[str, str]], name: str, bn: bool) -> str:
    head = f"{name}: কেনার আগে তিনটি প্রশ্ন" if bn else f"{name} in Bangladesh: three quick answers"
    body = "".join(f'<h3 style="font-size:17px;margin:14px 0 4px">{html.escape(q)}</h3><p>{html.escape(a)}</p>'
                   for q, a in pairs)
    return f'<section data-sos="{MARK}" class="buyer-qa"><h2 class="mt3" style="font-size:22px">{html.escape(head)}</h2>{body}</section>'


def add_ld(text: str, pairs: list[tuple[str, str]]) -> str:
    def fix(m: re.Match) -> str:
        try:
            data = json.loads(m.group(2))
        except ValueError:
            return m.group(0)
        nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
        for node in nodes if isinstance(nodes, list) else []:
            if isinstance(node, dict) and node.get("@type") == "FAQPage":
                have = {q.get("name") for q in node.get("mainEntity", [])}
                node.setdefault("mainEntity", []).extend(
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in pairs if q not in have)
                return m.group(1) + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + m.group(3)
        return m.group(0)
    return re.sub(r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', fix, text, flags=re.S)


def process(text: str, pid: str, p: dict, bn: bool) -> tuple[str, bool]:
    if f'data-sos="{MARK}"' in text:
        return text, False
    pairs = qa(pid, p, bn)
    block = section(pairs, rr.clean_name(p["name"]), bn)
    first, faq = ANCHORS[bn]
    if first in text:
        text = text.replace(first, block + first, 1)
    else:
        m = re.search(r'<h2[^>]*>[^<]*' + re.escape(faq), text)
        if not m:
            return text, False
        text = text[:m.start()] + block + text[m.start():]
    return add_ld(text, pairs), True


def main(argv: list[str]) -> int:
    check = "--check" in argv
    products = rr.priced(rr.load_catalog(SITE))
    errors, done = [], 0
    for pid, p in products.items():
        for path, bn in ((SITE / "p" / f"{pid}.html", False), (SITE / "bn" / "p" / f"{pid}.html", True)):
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            if not check:
                text, changed = process(text, pid, p, bn)
                if changed:
                    path.write_text(text, encoding="utf-8")
                    done += 1
            rel = path.relative_to(SITE).as_posix()
            sec = re.search(rf'<section data-sos="{MARK}".*?</section>', text, re.S)
            if not sec:
                errors.append(f"{rel}: section missing")
                continue
            allowed = {int(pl["bdt"]) for pl in p["plans"]}
            shown = {int(x.replace(",", "")) for x in re.findall(r"৳([\d,]+)", sec.group(0))}
            if not shown <= allowed:
                errors.append(f"{rel}: prices {sorted(shown - allowed)} not in pricebook")
            q = qa(pid, p, bn)[0][0]
            if json.dumps(q, ensure_ascii=False) not in text:
                errors.append(f"{rel}: FAQPage JSON-LD lacks buyer questions")
    if errors:
        print(f"[buyer-intent] FAIL — {len(errors)}: " + "; ".join(errors[:8]))
        return 1
    print(f"[buyer-intent] {'PASS' if check else str(done) + ' page(s) updated'} — {len(products)} products x EN/BN carry buyer answers, prices == pricebook")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
