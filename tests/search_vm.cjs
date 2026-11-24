// VM harness for assets/search.js (used by tests/test_search_discovery.py).
// Usage: node tests/search_vm.cjs <request.json>
// request = { catalog_js, search_js, extra_products?, queries: [{ q, opts }], perf_runs? }
'use strict';
const fs = require('fs');
const vm = require('vm');

const req = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const ctx = { console };
ctx.globalThis = ctx;
vm.createContext(ctx);
// catalog.js declares `const CATALOG`: a script-scope binding shared by later scripts in the
// same realm but NOT a property of globalThis, exactly as in a browser. Do not copy it onto ctx.
vm.runInContext(fs.readFileSync(req.catalog_js, 'utf8'), ctx);
if (vm.runInContext('typeof globalThis.CATALOG', ctx) !== 'undefined') throw new Error('harness must not expose CATALOG on globalThis');
if (Array.isArray(req.extra_products)) {
  vm.runInContext('CATALOG.products = CATALOG.products.concat(' + JSON.stringify(req.extra_products) + ');', ctx);
}
vm.runInContext(fs.readFileSync(req.search_js, 'utf8'), ctx);
const S = ctx.SOSSearch;
const catalog = S.pageCatalog(); // same lookup mount() uses in the browser
if (!catalog || !Array.isArray(catalog.products)) throw new Error('pageCatalog() did not find the page CATALOG');
const index = S.buildIndex(catalog);

const out = { index: index.map(d => ({ id: d.id, category: d.category, orderable: d.orderable, minBdt: d.minBdt,
  types: d.types, planIds: d.plans.map(p => p.plan_id) })), results: [] };
for (const item of req.queries || []) {
  const res = S.search(index, item.q, item.opts || {});
  out.results.push({
    q: item.q, opts: item.opts || {}, ids: res.map(d => d.id), minBdt: res.map(d => d.minBdt),
    html: res.map(d => S.cardHtml(d, (item.opts && item.opts.lang) || 'en')).join(''),
    dym: S.didYouMean(index, item.q, 3).map(d => d.id)
  });
}
if (req.perf_runs) {
  const qs = ['chatgpt', 'chobi', 'midjorney', 'ভিডিও', 'chat gpt', 'gaan', 'vpn', 'zzzz'];
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < req.perf_runs; i++) S.search(index, qs[i % qs.length], {});
  out.perf_ms = Number(process.hrtime.bigint() - t0) / 1e6;
}
process.stdout.write(JSON.stringify(out));
