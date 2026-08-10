import assert from "node:assert/strict";
import worker from "./src/index.js";

async function call(path, init = {}, env = {}) {
  const req = new Request(`https://shadow.example${path}`, init);
  const res = await worker.fetch(req, env);
  const body = await res.json();
  return { res, body };
}

function mockDb(records) {
  return {
    prepare() {
      return {
        bind(planId) {
          return {
            async first() {
              return records[planId] ?? null;
            },
          };
        },
      };
    },
  };
}

{
  const { res, body } = await call("/health", {}, { COMMERCE_MODE: "shadow", ENVIRONMENT: "test" });
  assert.equal(res.status, 200);
  assert.equal(body.mode, "shadow");
  assert.equal(body.database_bound, false);
  assert.equal(body.order_creation_enabled, false);
}

{
  const { res, body } = await call(
    "/v1/quote",
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ items: [{ plan_id: "demo--personal--1-month", quantity: 1, price_bdt: 1 }] }),
    },
    { COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 503);
  assert.equal(body.code, "SHADOW_DATABASE_NOT_BOUND");
}

{
  const DB = mockDb({
    "demo--personal--1-month": {
      plan_id: "demo--personal--1-month",
      product_id: "demo",
      commercial_state: "allowed",
      price_bdt: 750,
      currency: "BDT",
      authority_ref: "test-authority",
    },
  });
  const { res, body } = await call(
    "/v1/quote",
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ items: [{ plan_id: "demo--personal--1-month", quantity: 2, price_bdt: 1 }] }),
    },
    { DB, COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 200);
  assert.equal(body.total_bdt, 1500);
  assert.equal(body.items[0].unit_price_bdt, 750);
  assert.equal(body.order_creation_enabled, false);
}

{
  const DB = mockDb({
    blocked: {
      plan_id: "blocked",
      product_id: "demo",
      commercial_state: "blocked",
      price_bdt: 100,
      currency: "BDT",
    },
  });
  const { res, body } = await call(
    "/v1/quote",
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ items: [{ plan_id: "blocked", quantity: 1 }] }),
    },
    { DB, COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 409);
  assert.equal(body.code, "PLAN_NOT_SELLABLE");
}

{
  const { res, body } = await call(
    "/v1/orders",
    { method: "POST", headers: { "content-type": "application/json" }, body: "{}" },
    { COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 403);
  assert.equal(body.code, "ORDER_CREATION_DISABLED");
}

console.log("commerce shadow tests passed");
