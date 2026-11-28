// Node VM check: everyday Bangla/Banglish wording still finds the product. Synthetic catalog.
const assert = require('assert'); const fs = require('fs'); const vm = require('vm'); const path = require('path');
const ctx = { console }; ctx.window = ctx; ctx.module = { exports: {} };
vm.createContext(ctx);
const src = fs.readFileSync(path.resolve(__dirname, '..', 'assets/search.js'), 'utf8');
vm.runInContext(src, ctx);
const api = ctx.SOSSearch || ctx.window.SOSSearch || ctx.module.exports;
assert.ok(api && api.search, 'search API is exposed');
const product = (id, name, category) => ({ id, name, category, sellability: 'approved', request_price: false,
  plans: [{ plan_id: id + '-1', type: 'personal', bdt: 100 }] });
const index = api.buildIndex({ products: [product('canva-pro', 'Canva Pro', 'AI Image & Design'),
  product('chatgpt-plus', 'ChatGPT Plus', 'AI Assistants'), product('bundle-x', 'Starter Combo', 'Bundles')] });
for (const q of ['canva lagbe', 'ami canva kinte chai', 'আমার ক্যানভা লাগবে', 'canva er dam koto']) {
  assert.deepStrictEqual(Array.from(api.search(index, q), d => d.id), ['canva-pro'], q);
}
assert.strictEqual(api.search(index, 'চ্যাটজিপিটি লাগবে')[0].id, 'chatgpt-plus');
assert.ok(api.search(index, 'combo').some(d => d.bundle), 'combo finds the pack');
console.log('search wording: PASS');
