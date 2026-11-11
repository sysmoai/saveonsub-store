// Acceptance against the BUILT governed catalog (run after `python build_site.py`,
// which writes approved plans + stable plan_id into catalog.json). On the source
// catalog (HOLD shape, zero priced plans) every test here is skipped.
// Synthetic data only: FakeD1, stubbed Turnstile, fake phone number.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { FakeD1, handler, restoreFetch } from "./harness.mjs";

const catalog = JSON.parse(readFileSync(new URL("../../catalog.json", import.meta.url), "utf8"));
const priced = catalog.products.filter(p => p.request_price === false && Array.isArray(p.plans) && p.plans.length);
const plans = priced.flatMap(p => p.plans.map(pl => ({ product: p, plan: pl, type: pl.access_type || pl.type })));
const skip = plans.length === 0 ? "source catalog has no priced plans (run build_site.py first)" : false;
const SERVER_ORDERABLE = new Set(["personal", "team"]);

async function post(items, db = new FakeD1(), key = `idem-${Math.random().toString(36).slice(2)}-xxxxxxxxxxxx`) {
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ success: true }) }); // Turnstile stub
  try {
    const fn = await handler("api/orders/index.ts", "onRequestPost");
    const request = new Request("https://staging.test/api/orders", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        idempotency_key: key,
        turnstile_token: "synthetic",
        payment_method: "bkash",
        customer: { name: "Synthetic Customer", phone: "+8801000000000" },
        items,
      }),
    });
    const response = await fn({ request, env: { DB: db, TURNSTILE_SECRET_KEY: "synthetic" } });
    return { status: response.status, body: await response.json(), db };
  } finally {
    restoreFetch();
  }
}

test("every priced plan has a unique stable plan_id", { skip }, () => {
  const seen = new Set();
  for (const { product, plan } of plans) {
    assert.ok(plan.plan_id, `${product.id}: ${plan.label} has no plan_id`);
    const k = `${product.id}:${plan.plan_id}`;
    assert.ok(!seen.has(k), `duplicate ${k}`);
    seen.add(k);
  }
});

test("server resolves only personal/team plans; shared and official-guide stay WhatsApp-only", { skip }, async () => {
  const { resolveGovernedPlan } = await import("../../functions/lib/order-os/catalog-policy.ts");
  for (const { product, plan, type } of plans) {
    const r = resolveGovernedPlan(product.id, plan.plan_id);
    if (SERVER_ORDERABLE.has(type)) {
      assert.ok(r, `${product.id}:${plan.plan_id} (${type}) should resolve`);
      assert.equal(r.price_bdt, plan.bdt, "server price must equal the governed catalog price");
    } else {
      assert.equal(r, null, `${product.id}:${plan.plan_id} (${type}) must not be server-orderable`);
    }
  }
});

test("a personal plan creates one order at the server price; a replayed key is not duplicated", { skip }, async () => {
  const pick = plans.find(p => SERVER_ORDERABLE.has(p.type));
  const db = new FakeD1();
  const key = "idem-synthetic-acceptance-0001";
  const items = [{ product_id: pick.product.id, plan_id: pick.plan.plan_id, quantity: 1, bdt: 1, price: 1 }];
  const first = await post(items, db, key);
  assert.equal(first.status, 201, JSON.stringify(first.body));
  assert.equal(first.body.total_bdt, pick.plan.bdt, "client-sent price fields are ignored");
  const again = await post(items, db, key);
  assert.equal(again.body.duplicate, true);
  assert.equal(db.one("SELECT COUNT(*) AS n FROM orders").n, 1);
});

test("a shared plan is refused with 409 and writes nothing", { skip }, async () => {
  const pick = plans.find(p => p.type === "shared");
  if (!pick) return;
  const r = await post([{ product_id: pick.product.id, plan_id: pick.plan.plan_id, quantity: 1 }]);
  assert.equal(r.status, 409);
  assert.equal(r.db.one("SELECT COUNT(*) AS n FROM orders").n, 0);
});
