#!/usr/bin/env python3
"""Price-consistency guard. Run before every deploy:  python check_prices.py

Why this exists
---------------
Prices were hardcoded into SEO copy, blog posts, checkout CTAs and the homepage
ticker. When ChatGPT Plus moved 350 -> 499 (and personal 2499 -> 2990) those
literals were not updated, so the organic-traffic surface advertised a price the
store no longer honoured — a 43% gap at the last step of the funnel, on a store
whose entire pitch is honest labelling.

This script fails the build if a price that a product NO LONGER charges appears
next to that product's name in shipped HTML.

Deliberately narrow: it only flags a stale number when it sits next to the
product name, because several products legitimately share prices (Perplexity Pro
and Truecaller Premium really are 350).
"""
import json, re, sys, glob, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
cat = json.load(open('catalog.json', encoding='utf-8'))

# Products whose price has changed and whose OLD values must never resurface.
# Extend this when you change a price: {product-name-as-written: [retired, ...]}
RETIRED = {
    'ChatGPT': [350, 2499],
}

SKIP_DIRS = {'.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
             '__pycache__', 'node_modules', 'marketing'}

# Intentional exceptions: text that cites a price COMPETITORS charge, not ours.
# Kept deliberately — the sentence exists to contrast our offer against the
# market's ৳350 anchor. Matched as a substring of the surrounding line.
ALLOWED_CONTEXT = [
    "Every BD seller offers 'ChatGPT ৳350'",
]


def current_prices(name_fragment):
    for p in cat['products']:
        if name_fragment.lower() in p['name'].lower():
            return sorted(pl['bdt'] for pl in p.get('plans', []))
    return []


def main():
    problems = []
    files = [f for f in glob.glob('**/*.html', recursive=True)
             if not any(part in SKIP_DIRS for part in f.replace('\\', '/').split('/'))]

    for name, retired in RETIRED.items():
        live = current_prices(name)
        for old in retired:
            if old in live:
                continue  # price came back; not stale
            # match "ChatGPT ... ৳350" within a short window
            pat = re.compile(re.escape(name) + r'[^৳<]{0,40}৳' + f'{old:,}'.replace(',', '[,]?'))
            for f in files:
                try:
                    s = open(f, encoding='utf-8', errors='replace').read()
                except OSError:
                    continue
                for m in pat.finditer(s):
                    line_start = s.rfind('\n', 0, m.start()) + 1
                    line_end = s.find('\n', m.end())
                    context = s[line_start:line_end if line_end != -1 else len(s)]
                    if any(a in context for a in ALLOWED_CONTEXT):
                        continue
                    line = s[:m.start()].count('\n') + 1
                    problems.append((f, line, name, old, live, m.group(0)[:60]))

    if problems:
        print(f"STALE PRICES: {len(problems)} occurrence(s)\n")
        for f, line, name, old, live, snippet in problems[:40]:
            print(f"  {f}:{line}  {name} shows ৳{old}, catalog has {live}")
            print(f"      {snippet}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1

    print("Price check OK — no retired price appears next to its product name.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
