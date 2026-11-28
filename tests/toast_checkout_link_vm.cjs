// Node VM harness: after a successful add-to-cart the toast offers a checkout link.
const assert = require('assert'); const fs = require('fs'); const vm = require('vm'); const path = require('path');
const src = fs.readFileSync(path.resolve(__dirname, '..', 'assets/app.js'), 'utf8');
const CATALOG = { products: [{ id: 'demo', request_price: false,
  plans: [{ plan_id: 'demo-1-month', label: 'Demo — 1 Month', bdt: 100 }] }] };

function el(tag) {
  let text = '';
  const node = { tag, style: {}, children: [], appendChild(c) { this.children.push(c); } };
  // Same as the DOM: assigning textContent drops every child node.
  Object.defineProperty(node, 'textContent', { get: () => text, set(v) { text = String(v); node.children = []; } });
  return node;
}

function page(pathname, lang) {
  const store = {}; const timers = []; let toastEl = null;
  const ctx = { localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } },
    document: { documentElement: { lang }, querySelectorAll: () => [], getElementById: id => (id === 'toast' ? toastEl : null),
      createElement: el, body: { appendChild(n) { if (n.id === 'toast') toastEl = n; } }, addEventListener() {} },
    navigator: {}, location: { pathname }, setTimeout: (fn, ms) => { timers.push(ms); return timers.length; },
    clearTimeout() {}, console, CATALOG };
  ctx.window = ctx; ctx.addEventListener = () => {};
  vm.createContext(ctx);
  try { vm.runInContext(src, ctx); } catch (e) { /* DOM-only tail */ }
  return { run: code => vm.runInContext(code, ctx), toast: () => toastEl, lastTimer: () => timers[timers.length - 1] };
}

const ADD = "cartAdd('demo','Demo — 1 Month',100,'Demo','demo-1-month')";
const links = p => p.toast().children.filter(c => c.tag === 'a');

for (const [pathname, lang, href, label] of [
  ['/p/demo', 'en', '/checkout', 'Checkout →'],
  ['/bn/p/demo', 'bn', '/bn/checkout', 'চেকআউটে যান →'],
]) {
  const p = page(pathname, lang);
  p.run(ADD);
  assert.strictEqual(p.toast().textContent, '✅ Demo added — ৳100');
  assert.strictEqual(links(p).length, 1, pathname + ': checkout link missing');
  assert.strictEqual(links(p)[0].href, href);
  assert.strictEqual(links(p)[0].textContent, label);
  assert.strictEqual(p.lastTimer(), 6000, 'a toast with a link must stay long enough to tap');
  // A later plain message must not keep the old link or the longer timeout.
  p.run("toast('plain')");
  assert.strictEqual(links(p).length, 0);
  assert.strictEqual(p.lastTimer(), 2400);
}

// Rejected plan: nothing was added, so no checkout link.
const rejected = page('/p/demo', 'en');
rejected.run("cartAdd('demo','Demo — 1 Month',1,'Demo','demo-1-month')");
assert.strictEqual(links(rejected).length, 0);

// Already on checkout (add-on deals): no link to the current page.
for (const pathname of ['/checkout', '/checkout.html', '/bn/checkout', '/bn/checkout.html']) {
  const p = page(pathname, pathname.startsWith('/bn/') ? 'bn' : 'en');
  p.run(ADD);
  assert.strictEqual(links(p).length, 0, pathname + ': must not link to itself');
}
console.log('toast checkout link: PASS');
