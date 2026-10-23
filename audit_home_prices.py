"""Fail-closed price checks for homepage bestseller cards."""
import math
import re
from html.parser import HTMLParser


class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.depth = 0
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if self.depth:
                self.depth += 1
            elif 'pcard' in attrs.get('class', '').split():
                self.depth = 1
                self.current = {'text': '', 'links': [], 'cart': False}
        if self.current is not None:
            if tag == 'a':
                self.current['links'].append(attrs.get('href', ''))
            if 'cartAdd' in attrs.get('onclick', ''):
                self.current['cart'] = True

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data + ' '

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1
            if not self.depth:
                self.cards.append(self.current)
                self.current = None


def homepage_price_issues(products, html, policy):
    """Never infer a price or treat missing/malformed plans as an approved HOLD."""
    parser = Cards()
    parser.feed(html)
    issues = []
    for product in products:
        if product.get('bestseller_rank', 0) <= 0:
            continue
        pid = product['id']
        prefix = f'HOMEPAGE DRIFT: {pid}'
        plans = product.get('plans')
        if not isinstance(plans, list):
            issues.append(f'{prefix}: malformed plans; expected a list')
            continue
        rule = policy.get('approved_products', {}).get(pid, {})
        inquiry = (product.get('request_price') is True
                   and product.get('pricing_status') == 'price-review-required'
                   and ((rule.get('mode') == 'inquiry' and not rule.get('plans'))
                        or (policy.get('commercial_hold') or {}).get('status') == 'HOLD'))
        cards = [card for card in parser.cards if any(
            link in (f'p/{pid}.html', f'/p/{pid}.html', f'p/{pid}', f'/p/{pid}')
            for link in card['links'])]
        if not plans:
            if not inquiry:
                issues.append(f'{prefix}: empty plans without an explicit matching inquiry policy')
                continue
            if not cards or parser.depth:
                issues.append(f'{prefix}: HOLD requires a complete inquiry-only product card')
            for card in cards:
                if (re.search(r'৳|\bBDT\b|\bTk\b|\$', card['text'], re.I)
                        or card['cart'] or 'Confirm current price' not in card['text']):
                    issues.append(f'{prefix}: HOLD card must confirm current price without a fixed price/cart action')
            continue
        if (product.get('request_price') or rule.get('mode') == 'inquiry'
                or product.get('pricing_status') == 'price-review-required'):
            issues.append(f'{prefix}: inquiry/HOLD conflicts with fixed plans')
            continue
        prices = [plan.get('bdt') if isinstance(plan, dict) else None for plan in plans]
        if any(type(price) not in (int, float) or not math.isfinite(price) or price <= 0
               for price in prices):
            issues.append(f'{prefix}: every plan requires a finite positive numeric bdt')
            continue
        price = min(prices)
        if not cards or not all(any(re.search(re.escape(value) + r'(?![\d,.])', card['text']) for value in
                                   (f'৳{price:,}', f'৳{price}')) for card in cards):
            issues.append(f'{prefix}: from-price ৳{price} not on its product card')
    return issues
