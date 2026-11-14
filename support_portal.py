#!/usr/bin/env python3
"""Generate the customer support-ticket pages (/bn/support first, /support).

NON-PRODUCTION. The pages are noindex, are not linked from navigation or the
sitemap, and are inert until assets/order-config.js sets `apiBase` (the Pages
project that serves /api/support/*). With apiBase empty every control is disabled
and the page only points customers to WhatsApp.

What it gives a customer:
  * create a ticket for an order they can prove with its tracking token;
  * "no tracking code?" - the manual / WhatsApp path: staff verify ownership and
    hand over a one-time ticket code (see ops/order-os/ACCESS-SETUP.md);
  * look a ticket up by ID + access code, read the conversation, reply.

Basic subscription support is the default category and is never gated. Paid
personalised AI training or implementation is a SEPARATE optional service: it is
a different category, carries no price here and is not a support entitlement.
No prices, SLAs, refund promises or ranking claims appear on the page.

Usage: python3 support_portal.py [SITE_DIR] [--check]
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WA = "https://wa.me/8801305869242"
from urllib.parse import quote

CSS = """<style>
.sp{max-width:760px;margin:0 auto}.sp h2{font-size:clamp(18px,3.4vw,22px);margin:0 0 8px}
.sp .box{margin-top:16px}.sp label{display:block;font-weight:600;margin:12px 0 4px}
.sp input,.sp select,.sp textarea{width:100%;box-sizing:border-box;font:inherit;padding:12px;border-radius:10px;border:1px solid rgba(127,127,127,.5);background:transparent;color:inherit;min-height:44px}
.sp textarea{min-height:110px}.sp button{min-height:44px;margin-top:14px}
.sp .sp-warn{border-left:4px solid #e0a800;padding:10px 12px;margin-top:12px}
.sp .sp-msg{margin:10px 0 0;min-height:1.2em}.sp .sp-bad{color:#ff6b6b}
.sp .sp-off{border:1px dashed rgba(127,127,127,.6);padding:12px;border-radius:10px}
.sp .sp-code{font-family:ui-monospace,monospace;word-break:break-all;padding:10px;border:1px solid rgba(127,127,127,.5);border-radius:8px;margin:6px 0}
.sp .sp-bubble{padding:10px 12px;border-radius:12px;margin:8px 0;max-width:92%}
.sp .sp-you{background:rgba(80,160,255,.14);margin-left:auto}.sp .sp-sup{background:rgba(127,127,127,.16)}
.sp .sp-bubble p{margin:4px 0;white-space:pre-wrap;overflow-wrap:anywhere}.sp .sp-bubble time{font-size:12px;opacity:.7}
.sp-inert .box{opacity:.65}.sp [hidden]{display:none!important}
</style>"""

T = {
    "bn": {
        "file": "bn/support.html", "other": "/support", "self": "/bn/support", "lang": "bn", "locale": "bn_BD", "asset": "../assets/",
        "title": "সাপোর্ট টিকেট — আপনার অর্ডারের সমস্যা জানান | SaveOnSub",
        "desc": "অর্ডার নিয়ে সমস্যা বা প্রশ্ন? টিকেট খুলুন, অগ্রগতি দেখুন, উত্তর দিন। পাসওয়ার্ড বা OTP কখনো লিখবেন না।",
        "crumb_home": "../bn", "crumb": "সাপোর্ট টিকেট",
        "pill": "🎫 সাপোর্ট", "h1": 'সাপোর্ট টিকেট — <span class="grad-text">সমস্যা জানান, অগ্রগতি দেখুন।</span>',
        "off": "", "scope_h": "এই ফর্ম কীসের জন্য",
        "scope": "আপনার অর্ডার করা সাবস্ক্রিপশনের সাধারণ সাপোর্ট: লগইন/অ্যাক্সেস সমস্যা, অর্ডার স্ট্যাটাস, রিনিউয়াল প্রশ্ন। কোন সমস্যায় কী প্রযোজ্য তা আমাদের সাপোর্ট শর্তে লেখা আছে।",
        "ai": "ব্যক্তিগত AI ট্রেনিং বা ইমপ্লিমেন্টেশন সাহায্য একটি আলাদা, ঐচ্ছিক সার্ভিস। সাবস্ক্রিপশন সাপোর্টের সাথে এর সম্পর্ক নেই; জানতে চাইলে নিচে “AI ট্রেনিং সম্পর্কে জানতে চাই” বেছে নিন।",
        "safe": "এখানে পাসওয়ার্ড, OTP, PIN, কার্ড নম্বর বা পেমেন্টের স্ক্রিনশট লিখবেন না। আমরা কখনো এগুলো চাই না। লিখলেও স্বয়ংক্রিয়ভাবে মুছে ফেলার চেষ্টা হয়, কিন্তু সেটির ওপর নির্ভর করবেন না।",
        "new_h": "১. নতুন টিকেট খুলুন",
        "track": "অর্ডার ট্র্যাকিং কোড", "track_help": "অর্ডার নিশ্চিত হওয়ার পর পাওয়া লম্বা গোপন কোড। এটি অর্ডারের মালিকানার প্রমাণ।",
        "cat": "বিষয়", "cats": [("subscription_support", "সাবস্ক্রিপশন সাপোর্ট (লগইন/অ্যাক্সেস/সমস্যা)"), ("order_status", "অর্ডার স্ট্যাটাস"), ("renewal", "রিনিউয়াল"), ("ai_training_inquiry", "AI ট্রেনিং সম্পর্কে জানতে চাই (আলাদা, ঐচ্ছিক সার্ভিস)"), ("other", "অন্য কিছু")],
        "subj": "সংক্ষিপ্ত শিরোনাম (ঐচ্ছিক)", "msg": "আপনার সমস্যা বা প্রশ্ন", "go": "টিকেট খুলুন",
        "created_h": "টিকেট তৈরি হয়েছে", "created_id": "টিকেট আইডি", "created_code": "অ্যাক্সেস কোড (একবারই দেখানো হয়)",
        "created_note": "টিকেট দেখতে এই আইডি ও কোড দুটোই লাগবে। কোড হারালে সাপোর্টকে জানান; যাচাইয়ের পর নতুন কোড দেওয়া হবে।",
        "no_h": "ট্র্যাকিং কোড নেই?", 
        "no": "WhatsApp-এ নেওয়া বা আগের অর্ডার হলে ট্র্যাকিং কোড নাও থাকতে পারে। তখন WhatsApp-এ জানান। আমাদের স্টাফ অর্ডারের মালিকানা যাচাই করে আপনাকে একটি টিকেট আইডি ও অ্যাক্সেস কোড দেবেন। আমরা কোনো অর্ডার অনুমান বা তৈরি করি না।",
        "wa": "WhatsApp-এ টিকেটের জন্য জানান", "wa_text": "হ্যালো, আমার অর্ডারের জন্য একটি সাপোর্ট টিকেট দরকার। আমার কাছে ট্র্যাকিং কোড নেই।",
        "find_h": "২. টিকেট দেখুন ও উত্তর দিন", "id": "টিকেট আইডি", "code": "অ্যাক্সেস কোড", "find": "টিকেট খুলুন",
        "st": "অবস্থা", "reply": "উত্তর লিখুন", "send": "উত্তর পাঠান",
        "priv": "আপনার টিকেট শুধু আইডি ও কোড দিয়ে দেখা যায়। ভুল আইডি বা ভুল কোডে একই উত্তর আসে, তাই অন্য কারও টিকেট অনুমান করা যায় না।",
    },
    "en": {
        "file": "support.html", "other": "/bn/support", "self": "/support", "lang": "en", "locale": "en_BD", "asset": "assets/",
        "title": "Support Ticket — Report an Order Problem | SaveOnSub",
        "desc": "Problem or question about your order? Open a ticket, follow progress and reply. Never share passwords or OTPs.",
        "crumb_home": "./", "crumb": "Support ticket",
        "pill": "🎫 Support", "h1": 'Support ticket — <span class="grad-text">report a problem, follow progress.</span>',
        "scope_h": "What this form is for",
        "scope": "General support for the subscription you ordered: login/access problems, order status and renewal questions. What applies to each case is written in our support terms.",
        "ai": "Personalised AI training or implementation help is a separate, optional service. It is not part of subscription support; choose “I want to know about AI training” below if you are interested.",
        "safe": "Never write passwords, OTPs, PINs, card numbers or payment screenshots here. We never ask for them. We try to strip them automatically, but do not rely on that.",
        "new_h": "1. Open a new ticket",
        "track": "Order tracking code", "track_help": "The long secret code you received when your order was confirmed. It proves you own the order.",
        "cat": "Topic", "cats": [("subscription_support", "Subscription support (login/access/problem)"), ("order_status", "Order status"), ("renewal", "Renewal"), ("ai_training_inquiry", "I want to know about AI training (separate, optional service)"), ("other", "Something else")],
        "subj": "Short title (optional)", "msg": "Your problem or question", "go": "Open ticket",
        "created_h": "Ticket created", "created_id": "Ticket ID", "created_code": "Access code (shown only once)",
        "created_note": "You need both the ID and the code to view the ticket. If you lose the code, tell support; after verification we issue a new one.",
        "no_h": "No tracking code?",
        "no": "Orders taken over WhatsApp or placed earlier may not have a tracking code. Message us on WhatsApp. Our staff verify you own the order, then give you a ticket ID and access code. We never guess or create an order.",
        "wa": "Ask for a ticket on WhatsApp", "wa_text": "Hello, I need a support ticket for my order. I do not have a tracking code.",
        "find_h": "2. View a ticket and reply", "id": "Ticket ID", "code": "Access code", "find": "Open ticket",
        "st": "Status", "reply": "Write a reply", "send": "Send reply",
        "priv": "A ticket opens only with its ID and code. A wrong ID or wrong code returns the same answer, so nobody can guess another customer's ticket.",
    },
}
T["en"]["crumb_home"] = "./"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main_html(t: dict) -> str:
    opts = "".join(f'<option value="{v}">{esc(l)}</option>' for v, l in t["cats"])
    wa = f'{WA}?text={quote(t["wa_text"])}'
    return f'''<main id="main"><div class="wrap sp"><div id="sp-app" data-lang="{t["lang"]}" data-support-portal>
  <div class="crumbs"><a href="{t["crumb_home"]}">{"হোম" if t["lang"]=="bn" else "Home"}</a> › {t["crumb"]}</div>
  <span class="pill">{t["pill"]}</span><h1 style="font-size:clamp(26px,4vw,38px)">{t["h1"]}</h1>
  <p id="sp-off" class="sp-off" hidden></p>
  <div class="box"><h2>{t["scope_h"]}</h2><p>{t["scope"]}</p><p>{t["ai"]}</p><p class="sp-warn">{t["safe"]}</p></div>

  <form id="sp-new" class="box" autocomplete="off"><h2>{t["new_h"]}</h2>
    <label for="sp-track">{t["track"]}</label><input id="sp-track" name="track" required minlength="40" maxlength="200" autocomplete="off" autocapitalize="off" spellcheck="false">
    <small>{t["track_help"]}</small>
    <label for="sp-cat">{t["cat"]}</label><select id="sp-cat" name="cat">{opts}</select>
    <label for="sp-subj">{t["subj"]}</label><input id="sp-subj" name="subj" maxlength="120">
    <label for="sp-text">{t["msg"]}</label><textarea id="sp-text" name="text" required maxlength="2000"></textarea>
    <div id="sp-ts"></div>
    <button class="btn" id="sp-new-go" type="submit">{t["go"]}</button>
    <p id="sp-new-msg" class="sp-msg" role="status" aria-live="polite"></p>
    <div id="sp-created" hidden><h2>{t["created_h"]}</h2>
      <b>{t["created_id"]}</b><div class="sp-code" id="sp-created-id"></div>
      <b>{t["created_code"]}</b><div class="sp-code" id="sp-created-code"></div>
      <p>{t["created_note"]}</p></div>
  </form>

  <div class="box"><h2>{t["no_h"]}</h2><p>{t["no"]}</p>
    <a class="btn" href="{wa}" target="_blank" rel="noopener">{t["wa"]}</a></div>

  <form id="sp-find" class="box" autocomplete="off"><h2>{t["find_h"]}</h2>
    <label for="sp-id">{t["id"]}</label><input id="sp-id" name="id" required maxlength="40" autocomplete="off" autocapitalize="characters" spellcheck="false">
    <label for="sp-code">{t["code"]}</label><input id="sp-code" name="code" required minlength="40" maxlength="200" autocomplete="off" autocapitalize="off" spellcheck="false">
    <button class="btn" type="submit">{t["find"]}</button>
    <p id="sp-find-msg" class="sp-msg" role="status" aria-live="polite"></p>
    <small>{t["priv"]}</small>
  </form>

  <section id="sp-ticket" class="box" hidden aria-live="polite"><h2>{t["st"]}: <span id="sp-status"></span></h2>
    <div id="sp-thread"></div>
    <form id="sp-reply"><label for="sp-reply-text">{t["reply"]}</label><textarea id="sp-reply-text" required maxlength="2000"></textarea>
      <button class="btn" type="submit">{t["send"]}</button><p id="sp-reply-msg" class="sp-msg" role="status" aria-live="polite"></p></form>
  </section>
</div></div></main>'''


def build(site: Path) -> None:
    src_js = ROOT / "assets" / "support-portal.js"
    (site / "assets").mkdir(exist_ok=True)
    shutil.copyfile(src_js, site / "assets" / "support-portal.js")
    for key, t in T.items():
        base = site / ("bn/refund.html" if key == "bn" else "refund.html")
        html = base.read_text(encoding="utf-8")
        head, rest = html.split("<main", 1)
        tail = rest.split("</main>", 1)[1]
        bn = key == "bn"
        url = f'https://saveonsub.com{t["self"]}'
        other = f'https://saveonsub.com{t["other"]}'
        head = re.sub(r"<title>.*?</title>", f'<title>{esc(t["title"])}</title>', head, flags=re.S)
        head = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{esc(t["desc"])}">', head)
        head = re.sub(r'<link rel="canonical" href=".*?">', f'<link rel="canonical" href="{url}">', head)
        bn_url, en_url = ("https://saveonsub.com/bn/support", "https://saveonsub.com/support")
        head = re.sub(r'<link rel="alternate" hreflang="bn-bd" href=".*?">', f'<link rel="alternate" hreflang="bn-bd" href="{bn_url}">', head)
        head = re.sub(r'<link rel="alternate" hreflang="en-bd" href=".*?">', f'<link rel="alternate" hreflang="en-bd" href="{en_url}">', head)
        head = re.sub(r'<link rel="alternate" hreflang="x-default" href=".*?">', f'<link rel="alternate" hreflang="x-default" href="{en_url}">', head)
        head = re.sub(r'(<meta property="og:title" content=").*?(">)', lambda m: m.group(1) + esc(t["title"]) + m.group(2), head)
        head = re.sub(r'(<meta property="og:description" content=").*?(">)', lambda m: m.group(1) + esc(t["desc"]) + m.group(2), head)
        head = re.sub(r'(<meta property="og:url" content=").*?(">)', lambda m: m.group(1) + url + m.group(2), head)
        head = re.sub(r'<meta name="robots" content=".*?">', '<meta name="robots" content="noindex,nofollow,noarchive">', head)
        if "noindex" not in head:
            head = head.replace("</head>", '<meta name="robots" content="noindex,nofollow,noarchive">\n</head>')
        head = head.replace("</head>", CSS + "\n</head>")
        a = t["asset"]
        tail = tail.replace("</body>", f'<script src="{a}order-config.js"></script>\n<script src="{a}support-portal.js" defer></script>\n</body>')
        out = site / t["file"]
        out.write_text(head + main_html(t) + tail, encoding="utf-8")
        print(f"support_portal: wrote {t['file']}")


def check(site: Path) -> int:
    errs = []
    for t in T.values():
        p = site / t["file"]
        if not p.exists():
            errs.append(f"missing {t['file']}")
            continue
        h = p.read_text(encoding="utf-8")
        if "noindex" not in h:
            errs.append(f"{t['file']}: must be noindex")
        if "sitemap" in h and "support" in h and re.search(r"<loc>[^<]*/support", h):
            errs.append("support page listed in sitemap")
        m = re.search(r"<main.*?</main>", h, flags=re.S)
        vis = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", m.group(0) if m else h, flags=re.S)
        for bad in ("মার্চেন্ট", "merchant account", "automatic settlement", "৳", "BDT", "Tk ", "guarantee", "গ্যারান্টি"):
            if bad.lower() in vis.lower():
                errs.append(f"{t['file']}: forbidden term {bad!r}")
        if h.count("order-config.js") != 1 or "support-portal.js" not in h:
            errs.append(f"{t['file']}: scripts not wired once")
    sm = site / "sitemap.xml"
    if sm.exists() and re.search(r"/(bn/)?support<", sm.read_text(encoding="utf-8")):
        errs.append("sitemap.xml lists a support page")
    for e in errs:
        print("support_portal: FAIL -", e)
    if not errs:
        print("support_portal: PASS")
    return 1 if errs else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    site = Path(args[0]) if args else ROOT / "_site"
    if "--check" not in sys.argv:
        build(site)
    sys.exit(check(site))
