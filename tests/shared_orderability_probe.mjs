// SOS-21 probe (read-only): for every plan in the BUILT public catalog, report whether it is
// orderable through (a) browser cartAdd, (b) the legacy checkout/waOrder WhatsApp handoff,
// (c) the server order API resolver. Prints one JSON document. Changes nothing.
// Usage: node --import ./tests/order-os/register.mjs tests/shared_orderability_probe.mjs [SITE_DIR]
import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const site = path.resolve(process.argv[2] || path.join(root, "_site"));
const store = {};
const ctx = {
  localStorage: { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = v; }, removeItem: k => { delete store[k]; } },
  document: { querySelectorAll: () => [], getElementById: () => null, createElement: () => ({ style: {} }), body: { appendChild() {} }, addEventListener() {}, documentElement: { lang: "en" } },
  navigator: {}, location: {}, setTimeout, clearTimeout, setInterval: () => 0, console,
};
ctx.window = ctx; ctx.addEventListener = () => {};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(site, "assets/catalog.js"), "utf8"), ctx);
try { vm.runInContext(fs.readFileSync(path.join(site, "assets/app.js"), "utf8"), ctx); } catch (e) { /* DOM-only tail */ }
const catalog = vm.runInContext("CATALOG", ctx);
const { resolveGovernedPlan } = await import(path.join(root, "functions/lib/order-os/catalog-policy.ts"));

const page = (loc, id) => { try { return fs.readFileSync(path.join(site, loc, `${id}.html`), "utf8"); } catch { return ""; } };
const rows = [];
for (const p of catalog.products) {
  for (const pl of p.plans || []) {
    store.sos_cart = "[]";
    ctx.__p = p; ctx.__pl = pl;
    vm.runInContext("cartAdd(__p.id, __pl.label, __pl.bdt, __p.name, __pl.plan_id)", ctx);
    const inCart = JSON.parse(store.sos_cart).length;
    const wa = inCart ? vm.runInContext("waOrder({oid:'SOS-PROBE'})", ctx) : "";
    const text = wa ? decodeURIComponent(wa.split("?text=")[1] || "") : "";
    const needle = `onclick="cartAdd(&quot;${p.id}&quot;,&quot;${pl.label}&quot;`;
    const esc = s => s.replace(/&/g, "&amp;");
    rows.push({
      product: p.id, plan_id: pl.plan_id, label: pl.label, bdt: pl.bdt,
      access_type: pl.access_type || pl.type || "",
      request_price: !!p.request_price,
      cart_add: inCart === 1,
      wa_handoff: inCart === 1 && wa.startsWith("https://wa.me/8801305869242?text=") && text.includes(pl.label) && text.includes(`৳${pl.bdt}`),
      server_api: !!resolveGovernedPlan(p.id, pl.plan_id),
      en_page_button: page("p", p.id).includes(needle) || page("p", p.id).includes(esc(needle)),
      bn_page_button: page("bn/p", p.id).includes(needle) || page("bn/p", p.id).includes(esc(needle)),
    });
  }
}
process.stdout.write(JSON.stringify({ site, plans: rows }, null, 1));
