#!/usr/bin/env python3
"""Normalize EN/BN homepage truth claims and catalog counts in staged artifact."""
from pathlib import Path
import json, re, sys

SITE = Path('_site')
cat = json.loads(Path('catalog.json').read_text(encoding='utf-8'))
products = cat['products']
nonb = [p for p in products if p.get('category') != 'Bundles']
count = len(nonb)
more = max(count - 5, 0)
verified = '2026-09-09'

if not SITE.is_dir():
    raise SystemExit('HOMEPAGE TRUTH ERROR — _site missing')


def load(rel):
    p = SITE / rel
    if not p.exists():
        raise SystemExit(f'HOMEPAGE TRUTH ERROR — missing {rel}')
    return p, p.read_text(encoding='utf-8')


def save(p, t):
    marker = f'<meta name="saveonsub-home-truth-verified" content="{verified}">'
    if marker not in t:
        t = t.replace('</head>', marker + '\n</head>', 1)
    p.write_text(t, encoding='utf-8')


def en():
    p, t = load('index.html')
    t = re.sub(r'(property="og:description" content=")\d+\+ subscription options', rf'\g<1>{count} subscription options', t, count=1)
    t = re.sub(r'ChatGPT, Claude, Netflix, Canva, Midjourney and \d+\+ more', f'ChatGPT, Claude, Netflix, Canva, Midjourney and {more} more', t, count=1)
    save(p, t)


def bn():
    p, t = load('bn.html')
    t = re.sub(r'(<meta property="og:description" content=")[^"]*(">)',
               rf'\g<1>{count}টি subscription option — access type, payment method, delivery SLA এবং applicable warranty terms অর্ডারের আগে দেখুন।\g<2>', t, count=1)
    t = t.replace('"description":"সৎ দামে আসল প্রিমিয়াম সাবস্ক্রিপশন — বিকাশ/নগদ/রকেটে।"',
                  '"description":"বাংলাদেশে clearly labeled subscription options with local BDT payment support."')
    t = re.sub(r'ChatGPT, Netflix, Canva, Midjourney সহ ৫০\+ টুল —.*?প্রতিটা সিটে ওয়ারেন্টি।',
               f'ChatGPT, Netflix, Canva, Midjourney সহ {count}টি subscription option — access type, current price, delivery SLA এবং applicable warranty/payment terms অর্ডারের আগে দেখুন।', t, count=1)
    t = re.sub(r'<span class="official">অফিসিয়াল ChatGPT Plus: ৳[\d,]+/মাস</span><span class="ours">আমাদের: ৳([\d,]+)</span><span class="savepct">\d+% সাশ্রয়</span>',
               r'<span class="official">ChatGPT Plus web list: $20/mo</span><span class="ours">SAVEONSUB: ৳\1</span><span class="savepct">ACCESS TYPE দেখুন</span>', t, count=1)
    t = re.sub(r'<div class="ticker mt2"><span class="dotp"></span><span>211\+ অর্ডার — Google AI Pro \(আমাদের #১\)</span></div>',
               '<div class="ticker mt2"><span class="dotp"></span><span>প্রতিটি প্ল্যানের access type, price ও terms অর্ডারের আগে দেখুন</span></div>', t, count=1)
    t = re.sub(r'<span class="cat">#\d+ বেস্টসেলার</span>', '<span class="cat">ফিচার্ড</span>', t)
    t = t.replace('শেয়ার্ড·কম-ঝুঁকি', 'শেয়ার্ড')
    t = t.replace('শেয়ার্ড·ওয়ারেন্টিসহ', 'শেয়ার্ড')
    t = t.replace('<h2>২ মিনিটে অর্ডার। <span class="grad-text">১৫ মিনিটে ডেলিভারি।</span></h2>',
                  '<h2>অর্ডার সহজ। <span class="grad-text">ডেলিভারি selected plan SLA অনুযায়ী।</span></h2>')
    t = t.replace('এক ট্যাপে অর্ডার + পেমেন্ট তথ্য যায়। মিনিটেই মানুষ উত্তর দেয় — বাংলায় বা ইংরেজিতে।',
                  'এক ট্যাপে অর্ডার + পেমেন্ট তথ্য WhatsApp-এ প্রস্তুত হয়। Support বাংলায় বা ইংরেজিতে পাওয়া যায়; response time পরিস্থিতি অনুযায়ী ভিন্ন হতে পারে।')
    t = t.replace('ইনস্ট্যান্ট প্রোডাক্ট ৫–১৫ মিনিটে আসে। প্রথম মিনিট থেকেই ওয়ারেন্টি।',
                  'Instant plan-এর delivery SLA ৫–১৫ মিনিট হতে পারে। Applicable warranty/replacement terms selected product অনুযায়ী প্রযোজ্য।')
    t = re.sub(rf'{count}টি প্রোডাক্ট · বিকাশ/নগদ · ৫–১৫ মিনিটে ডেলিভারি · সবকিছুতে ওয়ারেন্টি।',
               f'{count}টি subscription option · available local payment methods · plan-specific delivery SLA · written warranty terms।', t, count=1)
    save(p, t)


def verify():
    checks = {
        'index.html': ['58+ more', f'{count}+ subscription options'],
        'bn.html': ['৫০+ টুল', '211+ অর্ডার', 'আমাদের #১', 'বেস্টসেলার', 'শেয়ার্ড·কম-ঝুঁকি', 'শেয়ার্ড·ওয়ারেন্টিসহ', 'প্রথম মিনিট থেকেই ওয়ারেন্টি', 'সবকিছুতে ওয়ারেন্টি'],
    }
    errors=[]
    for rel, banned in checks.items():
        text=(SITE/rel).read_text(encoding='utf-8')
        if f'name="saveonsub-home-truth-verified" content="{verified}"' not in text:
            errors.append(f'{rel}: marker missing')
        for phrase in banned:
            if phrase in text:
                errors.append(f'{rel}: stale claim survived: {phrase}')
    en_text=(SITE/'index.html').read_text(encoding='utf-8')
    bn_text=(SITE/'bn.html').read_text(encoding='utf-8')
    if f'{count} subscription options' not in en_text:
        errors.append('index.html: exact catalog count missing')
    if f'{count}টি subscription option' not in bn_text:
        errors.append('bn.html: exact catalog count missing')
    if errors:
        print('HOMEPAGE TRUTH FAILED:', file=sys.stderr)
        for e in errors: print(' - '+e, file=sys.stderr)
        return 1
    print(f'Homepage truth/count cohort OK — {count} non-bundle subscription options, EN/BN parity normalized.')
    return 0


en(); bn(); raise SystemExit(verify())
