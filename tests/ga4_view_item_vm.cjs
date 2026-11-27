// Synthetic, no-network test for the GA4 view_item value on product pages.
// Runs the real assets/ga4.js inside a Node VM. No credentials, customers or external requests.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const gaSrc = fs.readFileSync(path.resolve(__dirname, '..', 'assets/ga4.js'), 'utf8');

function viewItems(pathname, ldBlocks) {
  const ctx = {
    document: {
      readyState: 'complete',
      addEventListener: () => {},
      createElement: () => ({}),
      head: { appendChild: () => {} },
      querySelectorAll: () => ldBlocks.map(d => ({ textContent: JSON.stringify(d) }))
    },
    navigator: {}, location: { pathname },
    localStorage: { getItem: () => null },
    addEventListener: () => {}
  };
  ctx.window = ctx;
  vm.createContext(ctx);
  vm.runInContext(gaSrc, ctx, { filename: 'ga4.js' });
  // gtag() pushes its arguments object; copy it out of the VM realm for deepEqual.
  return ctx.dataLayer
    .filter(a => a[0] === 'event' && a[1] === 'view_item')
    .map(a => JSON.parse(JSON.stringify(a[2])));
}

const product = offers => ({ '@type': 'Product', name: 'Example', category: 'cat', offers });
const offer = price => ({ '@type': 'Offer', price, priceCurrency: 'BDT' });

function expectValue(label, pathname, blocks, value) {
  const sent = viewItems(pathname, blocks);
  assert.equal(sent.length, 1, label + ': exactly one view_item');
  assert.equal(sent[0].value, value, label + ': value');
  assert.equal(sent[0].items[0].price, value, label + ': item price');
  assert.equal(sent[0].currency, 'BDT', label + ': currency');
}

// The shape product_rich_results.py publishes: an array of Offers.
expectValue('one offer in an array', '/p/chatgpt-go', [product([offer('1290')])], 1290);
expectValue('lowest of several offers', '/bn/p/canva-pro', [product([offer('1499'), offer('299')])], 299);
// Older single-object shapes keep working.
expectValue('single Offer object', '/p/example', [product(offer('500'))], 500);
expectValue('AggregateOffer', '/p/example.html', [product({ '@type': 'AggregateOffer', lowPrice: 700 })], 700);
// Held / price-on-request pages must never invent a value.
expectValue('no Product block', '/p/capcut-pro', [{ '@type': 'WebPage' }], 0);
expectValue('no offers', '/p/example', [product(undefined)], 0);
expectValue('empty offers', '/p/example', [product([])], 0);
expectValue('unusable prices skipped', '/p/example', [product([offer('on request'), offer('0'), offer('800')])], 800);
assert.equal(viewItems('/about', [product([offer('1')])]).length, 0, 'non-product page sends no view_item');

process.stdout.write('PASS: synthetic GA4 view_item value\n');
