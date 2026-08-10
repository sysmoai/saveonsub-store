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
    prepare(sql) {
      return {
        bind(...args) {
          return {
            async first() {
              if (sql.includes("FROM plan_runtime")) return records[args[0]] ?? null;
              return null;
            },
            async run() {
              return { success: true };
            },
          };
        },
      };
    },
  };
}

{
  const { res, body } = await call("/health", { headers: { "x-request-id": "test-health-0001" } }, { COMMERCE_MODE: "shadow", ENVIRONMENT: "test" });
  assert.equal(res.status, 200);
  assert.equal(body.mode, "shadow");
  assert.equal(body.database_bound, false);
  assert.equal(body.order_creation_enabled, false);
  assert.equal(body.request_id, "test-health-0001");
  assert.equal(res.headers.get("x-request-id"), "test-health-0001");
}

{
  const { res, body } = await call("/v1/catalog/version", { headers: { "x-request-id": "test-version-001" } }, {
    COMMERCE_MODE: "shadow",
    CATALOG_VERSION: "catalog-test",
    PRICE_VERSION: "price-test",
    PROVIDER_VERSION: "provider-test",
  });
  assert.equal(res.status, 200);
  assert.equal(body.catalog_version, "catalog-test");
  assert.equal(body.price_version, "price-test");
  assert.equal(body.provider_version, "provider-test");
}

{
  const { res, body } = await call(
    "/v1/quote",
    {
      method: "POST",
      headers: { "content-type": "application/json", "x-request-id": "test-quote-nodb" },
      body: JSON.stringify({ items: [{ plan_id: "demo--personal--1-month", quantity: 1, price_bdt: 1 }] }),
    },
    { COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 503);
  assert.equal(body.code, "SHADOW_DATABASE_NOT_BOUND");
  assert.equal(body.request_id, "test-quote-nodb");
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
      source_sha256: "test-source",
    },
  });
  const { res, body } = await call(
    "/v1/quote",
    {
      method: "POST",
      headers: { "content-type": "application/json", "x-request-id": "test-quote-auth" },
      body: JSON.stringify({ items: [{ plan_id: "demo--personal--1-month", quantity: 2, price_bdt: 1 }] }),
    },
    { DB, COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 200);
  assert.equal(body.total_bdt, 1500);
  assert.equal(body.items[0].unit_price_bdt, 750);
  assert.equal(body.order_creation_enabled, false);
  assert.equal(body.request_id, "test-quote-auth");
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
      source_sha256: "test-source",
    },
  });
  const { res, body } = await call(
    "/v1/plans/demo--personal--1-month/quote?quantity=2",
    { headers: { "x-request-id": "test-single-quote" } },
    { DB, COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 200);
  assert.equal(body.total_bdt, 1500);
  assert.equal(body.items.length, 1);
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
      headers: { "content-type": "application/json", "x-request-id": "test-blocked-01" },
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
    { method: "POST", headers: { "content-type": "application/json", "x-request-id": "test-order-off" }, body: "{}" },
    { COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 403);
  assert.equal(body.code, "ORDER_CREATION_DISABLED");
}

{
  const { res, body } = await call(
    "/v1/orders/public-token",
    { headers: { "x-request-id": "test-track-off" } },
    { COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 403);
  assert.equal(body.code, "ORDER_TRACKING_DISABLED");
}

{
  const { res, body } = await call(
    "/v1/admin/orders/123/payment-confirm",
    { method: "POST", headers: { "content-type": "application/json", "x-request-id": "test-admin-off" }, body: "{}" },
    { COMMERCE_MODE: "shadow" }
  );
  assert.equal(res.status, 403);
  assert.equal(body.code, "ADMIN_DISABLED");
}

console.log("commerce shadow tests passed");
