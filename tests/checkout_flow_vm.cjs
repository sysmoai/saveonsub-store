// Node VM regression for both checkout pages: synthetic cart, fake browser, no network.
const assert = require('assert'); const fs = require('fs'); const vm = require('vm'); const path = require('path');
const root = path.resolve(__dirname, '..');
const app = fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8');
const plan = (id, bdt) => ({ id, name: id, icon: '*', request_price: false,
  plans: [{ plan_id: id + '-1', label: id + ' plan', bdt }] });
const CATALOG = { products: [plan('demo', 100), plan('canva-pro', 200)] };

function page(file, { cart, session = {}, storage = {} } = {}) {
  const store = Object.assign({}, storage);
  if (cart) store.sos_cart = JSON.stringify(cart);
  const els = {}; const opened = [];
  const el = () => ({ style: {}, classList: { toggle() {} }, value: '', textContent: '', innerHTML: '',
    appendChild() {}, setAttribute() {}, prepend(n) { this.note = n; }, remove() {} });
  const box = s => ({ getItem: k => (k in s ? s[k] : null), setItem: (k, v) => { s[k] = String(v); } });
  const ctx = { CATALOG, localStorage: box(store), sessionStorage: box(session), navigator: {}, console,
    location: { pathname: '/' + file.replace('.html', ''), href: '' },
    document: { documentElement: { lang: file.startsWith('bn/') ? 'bn' : 'en' }, querySelectorAll: () => [],
      querySelector: () => null, addEventListener() {}, createElement: el, body: { appendChild() {} },
      getElementById: id => (id === 'emptynote' ? null : (els[id] = els[id] || el())) },
    setTimeout: () => 0, clearTimeout() {}, setInterval: () => 0, clearInterval() {} };
  ctx.window = ctx; ctx.addEventListener = () => {}; ctx.open = url => { opened.push(url); return {}; };
  vm.createContext(ctx); vm.runInContext(app, ctx);
  const html = fs.readFileSync(path.join(root, file), 'utf8');
  vm.runInContext(html.match(/<script>\s*(let PAY='bKash';[\s\S]*?)<\/script>/)[1], ctx);
  return { run: code => vm.runInContext(code, ctx), store, session, els, opened,
    cart: () => JSON.parse(store.sos_cart || '[]') };
}

const LINE = [{ id: 'demo', plan: 'demo plan', plan_id: 'demo-1', bdt: 100, name: 'demo', qty: 2 }];
for (const file of ['checkout.html', 'bn/checkout.html']) {
  // The WhatsApp order carries the item lines and total, then the cart is cleared.
  const send = page(file, { cart: LINE });
  send.run('renderCart(); confirmWA()');
  const message = new URL(send.opened[0]).searchParams.get('text');
  assert.match(message, /demo — demo plan ×2 = ৳200/, file + ': order lines missing');
  assert.match(message, /TOTAL: ৳200/, file + ': total wrong');
  assert.deepStrictEqual(send.cart(), []);

  // The add-on button really adds the plan.
  const addon = page(file, { cart: LINE });
  addon.run('renderCart()');
  const onclick = addon.els.upsell.innerHTML.match(/onclick="([^"]+)"/)[1];
  addon.run(onclick);
  assert.deepStrictEqual(addon.cart().map(i => i.id), ['demo', 'canva-pro'], file + ': add-on refused');

  // Quantity steps stay between 1 and 20.
  const qty = page(file, { cart: LINE });
  qty.run('cartStep(0,-1); cartStep(0,-1)');
  assert.strictEqual(qty.cart()[0].qty, 1);
  qty.run('for(let i=0;i<40;i++) cartStep(0,1)');
  assert.strictEqual(qty.cart()[0].qty, 20);

  // A reload keeps the order ID; a saved order gets a new one next time.
  const session = {};
  const first = page(file, { cart: LINE, session }); first.run('renderCart()');
  const again = page(file, { cart: LINE, session }); again.run('renderCart()');
  assert.strictEqual(again.els.oid.textContent, first.els.oid.textContent);
  again.run('confirmWA()');
  const after = page(file, { session, storage: again.store });
  after.run('renderCart()');
  assert.match(after.els.empty.note.textContent, new RegExp(first.els.oid.textContent));

  // A changed price is explained instead of showing a silently empty cart.
  const stale = page(file, { cart: [Object.assign({}, LINE[0], { bdt: 90 })] });
  stale.run('renderCart()');
  assert.ok(stale.els.empty.note.textContent.length > 20, file + ': no explanation');
}
console.log('checkout flow EN and BN: PASS');
