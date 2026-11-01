// No-network checkout regression: synthetic products and fake browser state.
// Never calls a real WhatsApp, payment rail, or customer account.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const root = process.argv[2] || process.cwd();
const app = fs.readFileSync(path.join(root, 'assets', 'app.js'), 'utf8');
const checkout = fs.readFileSync(path.join(root, 'checkout.html'), 'utf8');
const inline = checkout.match(/<script>\s*(let PAY='bKash';[\s\S]*?)<\/script>/);
assert.ok(inline, 'Checkout script is available for a browser-like test');

const store = new Map();
const price = 1234, qty = 2;
store.set('sos_cart', JSON.stringify([{
  id: 'synthetic-plan', plan: 'Synthetic Authorized', bdt: price,
  name: 'Synthetic Tool', qty,
}]));
const localStorage = {
  getItem: k => store.has(k) ? store.get(k) : null,
  setItem: (k, v) => { store.set(k, String(v)); },
};
let outboundUrl = null;
const context = vm.createContext({
  localStorage,
  CATALOG: { products: [{
    id: 'synthetic-plan', request_price: false,
    plans: [{ label: 'Synthetic Authorized', bdt: price }],
  }] },
  document: {
    querySelectorAll: () => [],
    addEventListener: () => {},
    getElementById: id => id === 'txn' ? { value: 'SYNTHETIC-REF-001' } : null,
  },
  navigator: {},
  window: { addEventListener: () => {}, open: url => { outboundUrl = url; return {}; } },
  location: { href: '' },
  console,
  setTimeout, clearTimeout, setInterval, clearInterval,
});
vm.runInContext(app, context, { filename: 'assets/app.js', timeout: 5000 });
vm.runInContext(inline[1], context, { filename: 'checkout.inline.js', timeout: 5000 });
vm.runInContext('confirmWA()', context, { timeout: 5000 });

assert.ok(outboundUrl, 'A WhatsApp navigation was prepared');
const url = new URL(outboundUrl);
assert.equal(url.hostname, 'wa.me');
const message = url.searchParams.get('text') || '';
assert.match(message, /Synthetic Tool — Synthetic Authorized ×2 = ৳2468/);
assert.match(message, /TOTAL: ৳2468/);
assert.match(message, /Payment: bKash/);
assert.match(message, /SYNTHETIC-REF-001/);
const saved = JSON.parse(store.get('sos_last_order'));
assert.equal(saved.total, price * qty);
assert.equal(saved.items.length, 1);
assert.equal(saved.items[0].bdt, price);
assert.equal(saved.items[0].qty, qty);
assert.deepEqual(JSON.parse(store.get('sos_cart')), []);
assert.equal(context.location.href, 'order.html');
console.log('PASS: synthetic order snapshot preserved in WhatsApp handoff and local receipt; cart cleared');
