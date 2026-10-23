// Node VM harness for assets/app.js cartAdd/cartGet (T018-02). Prints JSON.
const fs = require('fs'); const vm = require('vm'); const path = require('path');
const root = path.resolve(__dirname, '..');
const catalog = JSON.parse(process.argv[2] || 'null');
const store = {};
const ctx = { localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; } },
  document: { querySelectorAll: () => [], getElementById: () => null, createElement: () => ({ style: {} }), body: { appendChild() {} }, addEventListener() {} },
  navigator: {}, location: {}, setTimeout, clearTimeout, console };
ctx.window = ctx; ctx.addEventListener = () => {};
vm.createContext(ctx);
if (catalog) vm.runInContext('var CATALOG = ' + JSON.stringify(catalog) + ';', ctx);
try { vm.runInContext(fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8'), ctx); } catch (e) { /* DOM-only tail */ }
const out = {};
vm.runInContext("cartAdd('chatgpt-plus','x',3390,'ChatGPT Plus')", ctx); out.wrongPlan = JSON.parse(store.sos_cart || '[]').length;
vm.runInContext("cartAdd('chatgpt-plus','Plus — 1 Month',3390,'ChatGPT Plus')", ctx); out.holdPlan = JSON.parse(store.sos_cart || '[]').length;
vm.runInContext("cartAdd('demo','Demo — 1 Month',100,'Demo')", ctx); out.validPlan = JSON.parse(store.sos_cart || '[]').length;
vm.runInContext("cartAdd('demo','Demo — 1 Month',1,'Demo')", ctx); out.editedPrice = JSON.parse(store.sos_cart || '[]').length;
store.sos_cart = JSON.stringify([{ id: 'chatgpt-plus', plan: 'Plus — 1 Month', bdt: 3390, qty: 1 }]);
out.staleRead = vm.runInContext('cartGet().length', ctx);
process.stdout.write(JSON.stringify(out));
