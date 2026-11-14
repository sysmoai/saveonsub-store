// The customer ticket API is on the protected staff host and is called by the
// separate storefront origin. Its x-ticket-token header must pass a browser
// CORS preflight; widening CORS on /api/orders is explicitly not permitted.
import { test } from "node:test";
import assert from "node:assert/strict";
import { handler } from "./harness.mjs";

const supportCors = await handler("api/support/_middleware.ts", "onRequest");
const ordersCors = await handler("api/orders/_middleware.ts", "onRequest");
const url = "https://ops.saveonsub.com/api/support/tickets/status?ticket=SOS-T-TEST";
const origins = ["https://saveonsub.com", "https://www.saveonsub.com"];

const req = (method, origin, extra = {}) => new Request(url, {
  method,
  headers: { ...(origin ? { Origin: origin } : {}), ...extra },
});

const invoke = async (fn, request) => {
  let calls = 0;
  const response = await fn({
    request,
    next: async () => {
      calls++;
      return new Response('{"ok":true}', {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    },
  });
  return { response, calls };
};

test("ticket CORS preflight allows x-ticket-token for exactly the two canonical storefront origins", async () => {
  for (const origin of origins) {
    const { response, calls } = await invoke(supportCors, req("OPTIONS", origin, {
      "Access-Control-Request-Method": "GET",
      "Access-Control-Request-Headers": "x-ticket-token, content-type",
    }));
    assert.equal(response.status, 204);
    assert.equal(calls, 0, "OPTIONS must not invoke the ticket handler");
    assert.equal(response.headers.get("access-control-allow-origin"), origin);
    assert.equal(response.headers.get("access-control-allow-methods"), "GET, POST, OPTIONS");
    const allowed = response.headers.get("access-control-allow-headers").toLowerCase()
      .split(",").map(s => s.trim());
    assert.ok(allowed.includes("x-ticket-token"));
    assert.ok(allowed.includes("content-type"));
    assert.equal(response.headers.get("vary"), "Origin");
  }
});

test("cross-origin ticket GET and POST retain the narrow allowlist and token header", async () => {
  for (const method of ["GET", "POST"]) {
    const { response, calls } = await invoke(supportCors, req(method, origins[0], {
      "x-ticket-token": "synthetic-not-real",
    }));
    assert.equal(response.status, 200);
    assert.equal(calls, 1);
    assert.equal(response.headers.get("access-control-allow-origin"), origins[0]);
    assert.match(response.headers.get("access-control-allow-headers"), /x-ticket-token/i);
  }
});

test("unapproved origins receive 403 and never execute the handler, preflight or actual request", async () => {
  for (const origin of ["https://not-saveonsub.example", "null", "http://saveonsub.com"]) {
    for (const method of ["OPTIONS", "GET", "POST"]) {
      const { response, calls } = await invoke(supportCors, req(method, origin, {
        "Access-Control-Request-Headers": "x-ticket-token",
      }));
      assert.equal(response.status, 403, `${origin} / ${method}`);
      assert.equal(calls, 0);
      assert.equal(response.headers.get("access-control-allow-origin"), null);
      assert.equal(response.headers.get("access-control-allow-headers"), null);
    }
  }
});

test("orders endpoint CORS is unchanged and does not permit the ticket-token header", async () => {
  const { response, calls } = await invoke(ordersCors, req("OPTIONS", origins[0], {
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "x-ticket-token",
  }));
  assert.equal(response.status, 204);
  assert.equal(calls, 0);
  assert.equal(response.headers.get("access-control-allow-headers"), "content-type");
});

test("requests without Origin or from the staff host keep same-origin behavior", async () => {
  const { response: noOrigin, calls: a } = await invoke(supportCors, req("GET", null));
  assert.equal(noOrigin.status, 200);
  assert.equal(a, 1);
  assert.equal(noOrigin.headers.get("access-control-allow-origin"), null);

  const { response: same, calls: b } = await invoke(supportCors, req("GET", "https://ops.saveonsub.com"));
  assert.equal(same.status, 200);
  assert.equal(b, 1);
  assert.equal(same.headers.get("access-control-allow-origin"), null);
});
