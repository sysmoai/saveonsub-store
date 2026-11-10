#!/usr/bin/env python3
"""Category intro copy (build step, after motion_polish.py).

The 13 EN and 13 BN category pages opened with hand-written intros from
September that carried unverified or stale numbers ("~৳2,200/mo", "official
৳219", "6,000 servers", "7,000+ courses", "from ৳199"), broken fragments
("Save up to vs buying separately", "... via bKash.") and a legend of labels
("official / shared·low / shared·covered") that no card on the page uses.

This step replaces the first intro paragraph under the h1 with plain copy that
makes no price, count or provider claim, and replaces the legend with one line
about how plans are labelled. Prices stay only in the product cards, which come
from the governed catalog. ``--check`` re-verifies without writing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
MARK = 'data-sos="category-copy-2026-11-10"'

EN = {
    "ai-assistants": "ChatGPT, Claude, Gemini, Grok, Perplexity and more, side by side. Compare plans, see whether each one is shared or personal, and pay in taka with bKash, Nagad or Rocket.",
    "ai-image-design": "Image and design tools for freelancers, sellers and brands: thumbnails, ad creatives, product shots and brand kits. Every plan shows its access type before you pay.",
    "ai-video": "AI video and editing tools for Reels, Shorts and TikTok creators. Price, access method and timing are confirmed in writing on WhatsApp before you pay.",
    "ai-voice-music": "Voiceover, music and transcription tools for creators and teams. Check the plan type on each card, then confirm the details on WhatsApp before paying.",
    "ai-code-dev": "Coding assistants and developer tools. Students: GitHub Copilot can be free through the GitHub Student Developer Pack, and we will help you claim it instead of selling it.",
    "ai-writing": "Writing, grammar and paraphrasing tools for students, freelancers and marketers. If a free tier is enough for you, we will tell you.",
    "workspace-productivity": "Notes, documents, presentations and research tools for teams and students. Many have useful free tiers; pick a paid plan only when you need more.",
    "entertainment": "Streaming and music subscriptions. Where a provider sells directly in Bangladesh we tell you, and every plan here shows whether it is shared or personal.",
    "vpn-security": "VPN and security subscriptions for privacy on public Wi-Fi and safer browsing. Renewal prices can differ from the first term, so confirm the term before paying.",
    "education-career": "Learning and career subscriptions for certificates and job search. If free courses or financial aid fit you better, we will say so.",
    "bundles": "Tools packaged together for a goal: study, research, freelancing or a business stack with setup help. Contents and price are confirmed with you before payment.",
    "bd-lifestyle": "Everyday Bangladesh subscriptions, paid in taka. Plan type and terms are confirmed on WhatsApp before you pay.",
    "gaming": "Gaming subscriptions paid in taka. Plan type and terms are confirmed on WhatsApp before you pay.",
}
BN = {
    "ai-assistants": "ChatGPT, Claude, Gemini, Grok, Perplexity সহ AI অ্যাসিস্ট্যান্ট এক জায়গায়। প্ল্যান তুলনা করুন, কোনটা শেয়ার্ড আর কোনটা পার্সোনাল দেখে নিন, তারপর বিকাশ, নগদ বা রকেটে টাকায় পেমেন্ট করুন।",
    "ai-image-design": "ফ্রিল্যান্সার, সেলার ও ব্র্যান্ডের জন্য ইমেজ ও ডিজাইন টুল: থাম্বনেইল, অ্যাড ক্রিয়েটিভ, প্রোডাক্ট ছবি ও ব্র্যান্ড কিট। পেমেন্টের আগে প্রতিটি প্ল্যানের অ্যাক্সেস টাইপ দেখানো হয়।",
    "ai-video": "Reels, Shorts ও TikTok ক্রিয়েটরদের জন্য AI ভিডিও ও এডিটিং টুল। দাম, অ্যাক্সেস পদ্ধতি ও সময় পেমেন্টের আগে হোয়াটসঅ্যাপে লিখিতভাবে নিশ্চিত করা হয়।",
    "ai-voice-music": "ক্রিয়েটর ও টিমের জন্য ভয়েসওভার, মিউজিক ও ট্রান্সক্রিপশন টুল। প্রতিটি কার্ডে প্ল্যানের ধরন দেখুন, তারপর পেমেন্টের আগে হোয়াটসঅ্যাপে বিস্তারিত নিশ্চিত করুন।",
    "ai-code-dev": "ডেভেলপারদের জন্য কোডিং অ্যাসিস্ট্যান্ট ও টুল। স্টুডেন্ট হলে GitHub Student Developer Pack দিয়ে GitHub Copilot ফ্রি পেতে পারেন, আমরা বিক্রি না করে সেটা পেতে সাহায্য করব।",
    "ai-writing": "স্টুডেন্ট, ফ্রিল্যান্সার ও মার্কেটারদের জন্য লেখা, গ্রামার ও প্যারাফ্রেজিং টুল। ফ্রি প্ল্যানেই কাজ হলে আমরা সেটাই বলব।",
    "workspace-productivity": "টিম ও স্টুডেন্টদের জন্য নোট, ডকুমেন্ট, প্রেজেন্টেশন ও রিসার্চ টুল। অনেকগুলোর ফ্রি প্ল্যান কাজের; বেশি দরকার হলে তবেই পেইড প্ল্যান নিন।",
    "entertainment": "স্ট্রিমিং ও মিউজিক সাবস্ক্রিপশন। কোনো প্রোভাইডার বাংলাদেশে সরাসরি বিক্রি করলে আমরা জানিয়ে দিই, আর প্রতিটি প্ল্যান শেয়ার্ড না পার্সোনাল তা দেখানো থাকে।",
    "vpn-security": "পাবলিক Wi-Fi-তে প্রাইভেসি ও নিরাপদ ব্রাউজিংয়ের জন্য VPN ও সিকিউরিটি সাবস্ক্রিপশন। রিনিউয়ালের দাম প্রথম মেয়াদের থেকে আলাদা হতে পারে, তাই পেমেন্টের আগে মেয়াদ নিশ্চিত করুন।",
    "education-career": "সার্টিফিকেট ও চাকরি খোঁজার জন্য লার্নিং ও ক্যারিয়ার সাবস্ক্রিপশন। ফ্রি কোর্স বা financial aid আপনার জন্য ভালো হলে আমরা সেটাই বলব।",
    "bundles": "একটা লক্ষ্যের জন্য কয়েকটি টুল একসাথে: পড়াশোনা, রিসার্চ, ফ্রিল্যান্সিং বা সেটআপসহ বিজনেস স্ট্যাক। কী থাকবে আর দাম কত, পেমেন্টের আগে আপনার সাথে নিশ্চিত করা হয়।",
    "bd-lifestyle": "বাংলাদেশের দৈনন্দিন সাবস্ক্রিপশন, টাকায় পেমেন্ট। প্ল্যানের ধরন ও শর্ত পেমেন্টের আগে হোয়াটসঅ্যাপে নিশ্চিত করা হয়।",
    "gaming": "টাকায় পেমেন্টে গেমিং সাবস্ক্রিপশন। প্ল্যানের ধরন ও শর্ত পেমেন্টের আগে হোয়াটসঅ্যাপে নিশ্চিত করা হয়।",
}
LEGEND = {False: "🏷️ Every plan is labelled shared, personal, team or bundle · 💳 bKash, Nagad, Rocket · 🛡️ support terms on every plan",
          True: "🏷️ প্রতিটি প্ল্যানে শেয়ার্ড, পার্সোনাল, টিম বা বান্ডেল লেবেল · 💳 বিকাশ, নগদ, রকেট · 🛡️ প্রতিটি প্ল্যানে সাপোর্ট শর্ত"}
INTRO = re.compile(r'(</h1>\s*)<p class="(sub[^"]*)"(?![^>]*data-sos)([^>]*)>.*?</p>', re.S)
BN_FROM = re.compile(r'<div class="price">থেকে (৳[\d,]+)</div>')
LEG = re.compile(r'<p class="sub"([^>]*)>\s*🏷️(?:(?!</p>).)*?(?:Honest labels|সৎ লেবেল)(?:(?!</p>).)*</p>', re.S)


def process(text: str, slug: str, bn: bool) -> tuple[str, int]:
    copy = (BN if bn else EN).get(slug)
    if not copy or MARK in text:
        return text, 0
    text, n = INTRO.subn(lambda m: f'{m.group(1)}<p class="{m.group(2)}" {MARK}{m.group(3)}>{copy}</p>', text, count=1)
    text, k = LEG.subn(lambda m: f'<p class="sub"{m.group(1)}>{LEGEND[bn]}</p>', text, count=1)
    j = 0
    if bn:
        text, j = BN_FROM.subn(r'<div class="price">\1 থেকে</div>', text)
    return text, n + k + j


def main(argv: list[str]) -> int:
    check = "--check" in argv
    pages = [(p, False) for p in sorted((SITE / "c").glob("*.html"))] + \
            [(p, True) for p in sorted((SITE / "bn" / "c").glob("*.html"))]
    missing, done = [], 0
    for page, bn in pages:
        text = page.read_text(encoding="utf-8")
        new, n = process(text, page.stem, bn)
        if not check and n:
            page.write_text(new, encoding="utf-8")
            done += 1
            text = new
        if page.stem in EN and MARK not in text:
            missing.append(page.relative_to(SITE).as_posix())
        if re.search(r"shared·(?:low|covered)|Honest labels", text):
            missing.append(page.relative_to(SITE).as_posix() + " (old legend)")
    if missing:
        print(f"[category-copy] FAIL — {len(missing)} page(s): {', '.join(missing[:8])}")
        return 1
    print(f"[category-copy] {'PASS' if check else str(done) + ' page(s) rewritten'} — {len(pages)} category pages carry the verified intro and plan legend")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
