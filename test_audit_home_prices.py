import copy
import json
import unittest
from pathlib import Path
from audit_home_prices import homepage_price_issues


class HomepagePricesTest(unittest.TestCase):
    def setUp(self):
        self.product = {'id': 'example', 'bestseller_rank': 1, 'plans': [{'bdt': 100}]}
        self.policy = {'approved_products': {'example': {'mode': 'inquiry'}}}

    def card(self, text, pid='example', cart=''):
        return f'<div class="pcard"><div class="price">{text}</div>{cart}<div><a href="p/{pid}.html">View</a></div></div>'

    def check(self, product, html, policy=None):
        return homepage_price_issues([product], html, policy or {})

    def held(self):
        return dict(self.product, plans=[], request_price=True, pricing_status='price-review-required')

    def test_fixed_price_and_minimum(self):
        self.product['plans'].append({'bdt': 200})
        self.assertEqual([], self.check(self.product, self.card('৳100')))
        self.assertTrue(self.check(self.product, self.card('৳200')))

    def test_other_product_price_cannot_mask_drift(self):
        self.assertTrue(self.check(self.product, self.card('৳200') + self.card('৳100', 'other')))

    def test_explicit_inquiry_has_no_price(self):
        self.assertEqual([], self.check(self.held(), self.card('Confirm current price'), self.policy))

    def test_hold_cannot_leak_price_or_cart(self):
        for text, cart in [('৳500 Confirm current price', ''), ('BDT 500 Confirm current price', ''),
                           ('Confirm current price', '<button onclick="cartAdd(1)">Buy</button>'), ('View', '')]:
            with self.subTest(text=text, cart=cart):
                self.assertTrue(self.check(self.held(), self.card(text, cart=cart), self.policy))

    def test_hold_missing_or_incomplete_card(self):
        for html in ['', self.card('Confirm current price')[:-6]]:
            self.assertTrue(self.check(self.held(), html, self.policy))

    def test_empty_plans_need_all_hold_markers_and_policy(self):
        for field in ['request_price', 'pricing_status']:
            product = self.held()
            del product[field]
            self.assertTrue(self.check(product, self.card('Confirm current price'), self.policy))
        self.assertTrue(self.check(self.held(), self.card('Confirm current price')))
        self.assertTrue(self.check(dict(self.product, plans=[]), self.card('৳100')))

    def test_malformed_plans_fail_without_exception(self):
        for plans in [None, {}, 'bad', [None], [{}], [{'bdt': '100'}], [{'bdt': True}],
                      [{'bdt': 0}], [{'bdt': -1}], [{'bdt': float('nan')}], [{'bdt': float('inf')}]]:
            with self.subTest(plans=plans):
                self.assertTrue(self.check(dict(self.product, plans=plans), self.card('৳100')))
        product = copy.deepcopy(self.product)
        del product['plans']
        self.assertTrue(self.check(product, self.card('৳100')))

    def test_conflicting_hold_with_plans(self):
        self.assertTrue(self.check(dict(self.held(), plans=[{'bdt': 100}]), self.card('৳100'), self.policy))

    def test_actual_google_hold_reports_stale_homepage(self):
        root = Path(__file__).parent
        products = json.loads((root / 'catalog.json').read_text())['products']
        google = next(p for p in products if p['id'] == 'google-ai-pro')
        policy = json.loads((root / 'ops/PRICING-V2-2026-09-17.json').read_text())
        self.assertEqual([], google['plans'])
        self.assertEqual('inquiry', policy['approved_products'][google['id']]['mode'])
        errors = self.check(google, self.card('৳500', 'google-ai-pro'), policy)
        self.assertTrue(any('google-ai-pro' in error and 'HOLD card' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
