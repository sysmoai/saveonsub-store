// T018-02: the public order API prices only from the governed public catalog.
// During the EXEC-010 HOLD every product is Price on Request, so no order can be
// created — including the formerly re-priced ChatGPT Plus and Google AI Pro plans.
import { test } from "node:test";
import assert from "node:assert/strict";
import { FakeD1, handler, restoreFetch } from "./harness.mjs";

async function post(items, db = new FakeD1()) {
  globalThis.fetch = async () => ({ ok: true, json: async () => ({ success: true }) }); // Turnstile stub
  try {
    const fn = await handler("api/orders/index.ts", "onRequestPost");
    const request = new Request("https://staging.test/api/orders", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        idempotency_key: `idem-${Math.random().toString(36).slice(2)}-xxxxxxxxxxxx`,
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

test("ChatGPT Plus plus-1m is refused with 409 during HOLD (EXEC-010 D2)", async () => {
  const r = await post([{ product_id: "chatgpt-plus", plan_id: "plus-1m", quantity: 1 }]);
  assert.equal(r.status, 409);
  assert.equal(r.body.error, "UNKNOWN_OR_UNAVAILABLE_PLAN");
});

test("Google AI Pro google-ai-pro-1m is refused with 409 (EXEC-010 D1 Price on Request)", async () => {
  const r = await post([{ product_id: "google-ai-pro", plan_id: "google-ai-pro-1m", quantity: 1 }]);
  assert.equal(r.status, 409);
});

test("a refused order writes nothing", async () => {
  const r = await post([{ product_id: "chatgpt-go", plan_id: "chatgpt-go-1m", quantity: 1 }]);
  assert.equal(r.status, 409);
  assert.equal(r.db.one("SELECT COUNT(*) AS n FROM orders").n, 0);
  assert.equal(r.db.one("SELECT COUNT(*) AS n FROM order_events").n, 0);
});

test("no product in the governed catalog is orderable during HOLD", async () => {
  const { listGovernedPlans } = await import("../../functions/lib/order-os/catalog-policy.ts");
  assert.deepEqual(listGovernedPlans(), []);
});
