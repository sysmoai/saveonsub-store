// Synthetic, no-network test for the Meta Pixel ViewContent value on product pages.
// Runs the real assets/meta-pixel.js inside a Node VM. No credentials, customers or external requests.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const pixelSrc = fs.readFileSync(path.resolve(__dirname, '..', 'assets/meta-pixel.js'), 'utf8');

function viewContents(pathname, ldBlocks) {
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
  vm.runInContext(pixelSrc, ctx, { filename: 'meta-pixel.js' });
  // fbq() queues its arguments object until Meta's script loads (it never does here);
  // copy the parameters out of the VM realm for deepEqual.
  return ctx.fbq.queue
    .filter(a => a[0] === 'track' && a[1] === 'ViewContent')
    .map(a => JSON.parse(JSON.stringify(a[2])));
}

const product = offers => ({ '@type': 'Product', name: 'Example', category: 'cat', offers });
const offer = price => ({ '@type': 'Offer', price, priceCurrency: 'BDT' });

function expectValue(label, pathname, blocks, value) {
  const sent = viewContents(pathname, blocks);
  assert.equal(sent.length, 1, label + ': exactly one ViewContent');
  assert.equal(sent[0].value, value, label + ': value');
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
expectValue('unusable prices skipped', '/p/example', [product([null, offer('on request'), offer('0'), offer('800')])], 800);

// The rest of the payload is unchanged by the value fix.
const [payload] = viewContents('/p/canva-pro', [product([offer('299')])]);
assert.deepEqual(payload.content_ids, ['canva-pro']);
assert.equal(payload.content_type, 'product');
assert.equal(payload.content_name, 'Example');
assert.equal(payload.content_category, 'cat');
assert.equal(viewContents('/about', [product([offer('1')])]).length, 0, 'non-product page sends no ViewContent');

process.stdout.write('PASS: synthetic Meta Pixel ViewContent value\n');
