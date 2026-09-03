#!/usr/bin/env python3
"""Deployment preflight: truth/brand guard + price-consistency guard.

Run before every deploy:  python check_prices.py

Why this exists
---------------
Prices were hardcoded into SEO copy, blog posts, checkout CTAs and the homepage
ticker. When ChatGPT Plus moved 350 -> 499 (and personal 2499 -> 2990) those
literals were not updated, so the organic-traffic surface advertised a price the
store no longer honoured — a 43% gap at the last step of the funnel, on a store
whose entire pitch is honest labelling.

The permanent truth_guard is also executed here so every current deployment
path (Cloudflare and Vercel) blocks known P0 contact, claim, privacy, legal and
brand regressions without each host needing a separate configuration change.

The price portion deliberately flags a retired number only when it sits next to
the relevant product name, because several products may legitimately share the
same price.
"""
import json, re, sys, glob, os
from truth_guard import main as truth_guard_main

os.chdir(os.path.dirname(os.path.abspath(__file__)))
cat = json.load(open('catalog.json', encoding='utf-8'))

# Products whose price has changed and whose OLD values must never resurface.
# Extend this when you change a price: {product-name-as-written: [retired, ...]}
RETIRED = {
    'ChatGPT': [350, 2499],
}

SKIP_DIRS = {'.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
             '__pycache__', 'node_modules', 'marketing'}

# Intentional exceptions: text that cites a competitor/market price rather than
# a current SaveOnSub selling price. Keep this list small and evidence-backed.
ALLOWED_CONTEXT = [
    "Every BD seller offers 'ChatGPT ৳350'",
]


def current_prices(name_fragment):
    for p in cat['products']:
        if name_fragment.lower() in p['name'].lower():
            return sorted(pl['bdt'] for pl in p.get('plans', []))
    return []


def main():
    truth_rc = truth_guard_main()
    if truth_rc:
        return truth_rc

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
