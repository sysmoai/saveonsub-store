#!/usr/bin/env python3
"""Make /checkout and /bn/checkout follow the confirm-before-pay sequence.

Problem (CEO audit 14 Nov 2026): the checkout payment box told buyers to open
bKash, send money to the number, put the order ID in the reference and only then
"Confirm order on WhatsApp", while the same page, the homepage and every product
page say price, access method, timing, covered period and payment destination are
confirmed in writing BEFORE payment.

Sequence now: choose plan (cart) -> order ID + written confirmation on WhatsApp
-> pay -> receiving-side verification of the actual incoming credit -> fulfilment.

The order ID already exists when the box is shown. The confirm button is first.
The payment steps stay available but collapsed under a "pay only after written
confirmation" heading, still showing the SAME number that was shown before: this
step adds no new receiving instruction and removes none. Which number is the
CEO-verified receiving account, and whether each rail is eligible, is a CEO
decision. No automatic settlement is claimed: a payment counts only after the
actual incoming credit is verified in the authorized receiving account.

All element ids used by the inline checkout script are preserved (oid, oid2,
paymethod, payamount, txn, pb-bKash/Nagad/Rocket, confirmWA, setPay, copyText),
so cart, order record and WhatsApp hand-off behave exactly as before.

Usage: python3 checkout_sequence_truth.py [SITE_DIR] [--check]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = "data-checkout-sequence"
NUM_EN = "+880 1305-869242"
NUM_BN = "+880 1305-869242"  # the BN checkout already showed the Latin-digit form; unchanged

PAYBOX = re.compile(r'<div class="box mt2" id="paybox".*?(?=\n    </div>\n\n    <!-- RIGHT)', re.S)

TXT = {
    "checkout.html": {
        "h1": 'Checkout — <span class="grad-text">confirm first, then pay.</span>',
        "h2": '💳 Your order ID <span class="oid" id="oid">SOS-…</span>',
        "s1_h": "1. Send your order on WhatsApp first",
        "s1": "Your order ID is already created. Send it to us on WhatsApp. We reply in writing with the plan, access method, total, delivery timing, covered period and the payment destination for your order. Do not pay before you have that reply.",
        "btn": "💬 Send order on WhatsApp →",
        "s2_h": "2. Pay only after our written confirmation",
        "s2_note": "Open this only after you have our written reply. The number below is the one currently shown here; pay only if it matches the number in our written reply. A payment counts only after we see the actual incoming credit in the authorized receiving account.",
        "step_open": "Open",
        "send_money": "Send Money",
        "amount": "Send the confirmed total",
        "number_label": "Currently shown payment number:",
        "copy": "📋 Copy",
        "copied": "Number copied",
        "ref": "In <b>Reference</b>, put your existing order ID",
        "oidcopy": "copy",
        "oidcopied": "Order ID copied",
        "txn_step": "After paying, add the TxnID if you have it (optional). A TxnID or screenshot alone is not payment.",
        "txn_label": "bKash/Nagad TxnID (optional)",
        "txn_ph": "e.g. 9H7X2K1LMN",
        "s3_h": "3. We verify, then deliver",
        "s3": "We check the incoming credit in the authorized receiving account, then update the payment status and delivery status of your order ID.",
        "resend": "💬 Send order and TxnID on WhatsApp →",
    },
    "bn/checkout.html": {
        "h1": 'চেকআউট — <span class="grad-text">আগে নিশ্চিত করুন, তারপর পেমেন্ট।</span>',
        "h2": '💳 আপনার অর্ডার আইডি <span class="oid" id="oid">SOS-…</span>',
        "s1_h": "১. আগে WhatsApp-এ অর্ডার পাঠান",
        "s1": "আপনার অর্ডার আইডি তৈরি হয়ে আছে। সেটি WhatsApp-এ আমাদের পাঠান। আমরা লিখিতভাবে জানাব প্ল্যান, অ্যাক্সেস পদ্ধতি, মোট দাম, ডেলিভারির সময়, কভারের সময় ও পেমেন্ট গ্রহণের গন্তব্য। সেই উত্তর পাওয়ার আগে পেমেন্ট করবেন না।",
        "btn": "💬 WhatsApp-এ অর্ডার পাঠান →",
        "s2_h": "২. আমাদের লিখিত নিশ্চিতকরণের পরই পেমেন্ট",
        "s2_note": "আমাদের লিখিত উত্তর পাওয়ার পরই এটি খুলুন। নিচের নম্বরটি এখানে বর্তমানে দেখানো নম্বর। আমাদের লিখিত উত্তরের নম্বরের সাথে মিললে তবেই পেমেন্ট করুন। অনুমোদিত রিসিভিং অ্যাকাউন্টে আসল ইনকামিং টাকা দেখার পরই পেমেন্ট গণ্য হয়।",
        "step_open": "খুলুন",
        "send_money": "সেন্ড মানি",
        "amount": "নিশ্চিত করা মোট পাঠান",
        "number_label": "বর্তমানে দেখানো পেমেন্ট নম্বর:",
        "copy": "📋 কপি",
        "copied": "নম্বর কপি হয়েছে",
        "ref": "<b>রেফারেন্সে</b> আপনার বিদ্যমান অর্ডার আইডি লিখুন",
        "oidcopy": "কপি",
        "oidcopied": "অর্ডার আইডি কপি হয়েছে",
        "txn_step": "পেমেন্টের পর TxnID থাকলে দিন (ঐচ্ছিক)। শুধু TxnID বা স্ক্রিনশট পেমেন্ট নয়।",
        "txn_label": "বিকাশ/নগদ TxnID (ঐচ্ছিক)",
        "txn_ph": "যেমন 9H7X2K1LMN",
        "s3_h": "৩. আমরা যাচাই করি, তারপর ডেলিভারি",
        "s3": "অনুমোদিত রিসিভিং অ্যাকাউন্টে আসল ইনকামিং টাকা দেখে আপনার অর্ডার আইডির পেমেন্ট স্ট্যাটাস ও ডেলিভারি স্ট্যাটাস আপডেট করি।",
        "resend": "💬 WhatsApp-এ অর্ডার ও TxnID পাঠান →",
    },
}


def paybox(c: dict, bn: bool) -> str:
    num = NUM_BN if bn else NUM_EN
    open_w = c["step_open"]
    pay_app = ('<b id="paymethod">bKash</b> অ্যাপ খুলুন → ' if bn else f'{open_w} <b id="paymethod">bKash</b> → ') + f'<b>{c["send_money"]}</b>'
    return (
        f'<div class="box mt2" id="paybox" style="display:none" {MARK}="1">\n'
        f'        <h2 style="font-size:19px">{c["h2"]}</h2>\n'
        f'        <h3 style="font-size:16px;margin:12px 0 4px">{c["s1_h"]}</h3>\n'
        f'        <p class="sub" style="font-size:14.5px;margin:0 0 6px">{c["s1"]}</p>\n'
        f'        <button class="btn btn-wa mt2" style="width:100%;font-size:16px" onclick="confirmWA()">{c["btn"]}</button>\n'
        f'        <details class="mt2" style="margin-top:14px"><summary>{c["s2_h"]}</summary>\n'
        f'        <p class="sub" style="font-size:13.5px">{c["s2_note"]}</p>\n'
        '        <div class="paybtns">\n'
        '          <button class="paybtn on" id="pb-bKash" onclick="setPay(\'bKash\')">bKash</button>\n'
        '          <button class="paybtn" id="pb-Nagad" onclick="setPay(\'Nagad\')">Nagad</button>\n'
        '          <button class="paybtn" id="pb-Rocket" onclick="setPay(\'Rocket\')">Rocket</button>\n'
        '        </div>\n'
        f'        <div class="steps-mini">\n'
        f'          a. {pay_app}<br>\n'
        f'          b. {c["amount"]}: <b id="payamount" style="color:var(--green2)">৳0</b><br>\n'
        f'          c. {c["number_label"]}\n'
        '        </div>\n'
        f'        <div class="merchant"><span>{num}</span><button class="btn btn-primary btn-sm" onclick="copyText(\'+8801305869242\',\'{c["copied"]}\')">{c["copy"]}</button></div>\n'
        f'        <div class="steps-mini">d. {c["ref"]} <span class="oid" id="oid2">…</span> <button class="btn btn-ghost btn-sm" onclick="copyText(OID,\'{c["oidcopied"]}\')" style="padding:4px 10px;font-size:12px">{c["oidcopy"]}</button><br>e. {c["txn_step"]}</div>\n'
        f'        <label for="txn">{c["txn_label"]}</label>\n'
        f'        <input id="txn" placeholder="{c["txn_ph"]}" autocomplete="off">\n'
        f'        <h3 style="font-size:16px;margin:12px 0 4px">{c["s3_h"]}</h3>\n'
        f'        <p class="sub" style="font-size:14px;margin:0">{c["s3"]}</p>\n'
        f'        <button class="btn btn-wa mt2" style="width:100%;font-size:15px" onclick="confirmWA()">{c["resend"]}</button>\n'
        '        </details>\n'
        '      </div>'
    )


def apply_page(site: Path, rel: str, c: dict) -> str | None:
    f = site / rel
    if not f.exists():
        return f"missing {rel}"
    t = f.read_text(encoding="utf-8")
    if MARK in t:
        return None
    if not PAYBOX.search(t):
        return f"paybox anchor not found in {rel}"
    t = PAYBOX.sub(lambda m: paybox(c, rel.startswith("bn/")), t, count=1)
    t = re.sub(r'(<h1 style="font-size:clamp\(26px,4vw,38px\)">).*?(</h1>)', lambda m: m.group(1) + c["h1"] + m.group(2), t, count=1, flags=re.S)
    f.write_text(t, encoding="utf-8")
    return None


def verify(site: Path) -> list[str]:
    errs = []
    for rel in TXT:
        bn = rel.startswith("bn/")
        f = site / rel
        t = f.read_text(encoding="utf-8") if f.exists() else ""
        if MARK not in t:
            errs.append(f"{rel}: sequence block missing")
            continue
        box = t[t.find('id="paybox"'): t.find("<!-- RIGHT")]
        first_btn = box.find("confirmWA()")
        number = box.find(NUM_BN if bn else NUM_EN)
        if not (0 <= first_btn < number):
            errs.append(f"{rel}: the WhatsApp confirmation must come before the payment number")
        if box.count(NUM_BN if bn else NUM_EN) != 1:
            errs.append(f"{rel}: payment number must appear exactly once")
        if "<details" not in box[:number]:
            errs.append(f"{rel}: payment steps must be gated behind the written-confirmation heading")
        for need in ("oid", "oid2", "paymethod", "payamount", "txn", "pb-bKash", "pb-Nagad", "pb-Rocket"):
            if f'id="{need}"' not in box:
                errs.append(f"{rel}: lost element id {need}")
        for bad in ("60 seconds", "৬০ সেকেন্ড", "instantly", "automatic", "অটো"):
            if bad in t[t.find("<main"): t.find("</main>")]:
                errs.append(f"{rel}: forbidden phrase {bad!r}")
    return errs


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    site = Path(args[0]) if args else ROOT / "_site"
    if "--check" not in sys.argv:
        for rel, c in TXT.items():
            e = apply_page(site, rel, c)
            if e:
                print(f"[checkout-sequence] FAIL — {e}")
                return 1
    errs = verify(site)
    if errs:
        print("[checkout-sequence] FAIL")
        for e in errs:
            print("  " + e)
        return 1
    print("[checkout-sequence] PASS — /checkout (EN+BN): order ID + written confirmation first, payment gated, payment number unchanged, no automatic-settlement claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
