const BASE_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
  "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
};

function requestId(request) {
  const supplied = String(request.headers.get("x-request-id") || "").trim();
  if (/^[A-Za-z0-9._:-]{8,128}$/.test(supplied)) return supplied;
  return crypto.randomUUID();
}

function response(status, payload, rid) {
  const headers = new Headers(BASE_HEADERS);
  if (rid) headers.set("x-request-id", rid);
  return new Response(JSON.stringify(payload), { status, headers });
}

function mode(env) {
  return String(env.COMMERCE_MODE || "shadow").toLowerCase();
}

async function readJson(request) {
  const contentType = request.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    throw new Error("JSON_REQUIRED");
  }
  return request.json();
}

function normalizeItems(value) {
  if (!Array.isArray(value) || value.length < 1 || value.length > 25) {
    throw new Error("INVALID_ITEMS");
  }
  return value.map((item) => {
    const planId = String(item?.plan_id || "").trim();
    const quantity = Number(item?.quantity ?? 1);
    if (!planId || !Number.isInteger(quantity) || quantity < 1 || quantity > 10) {
      throw new Error("INVALID_ITEM");
    }
    return { plan_id: planId, quantity };
  });
}

async function getPlanRuntime(db, planId) {
  return db
    .prepare(
      `SELECT plan_id, product_id, commercial_state, price_bdt, currency,
              effective_from, effective_to, authority_ref, source_sha256
         FROM plan_runtime
        WHERE plan_id = ?1
        LIMIT 1`
    )
    .bind(planId)
    .first();
}

async function auditQuote(env, rid, resultCode, itemCount, totalBdt, sourceSha) {
  if (!env.DB) return;
  try {
    const statement = env.DB.prepare(
      `INSERT OR REPLACE INTO quote_audit
        (request_id, result_code, item_count, total_bdt, source_sha256, created_at)
       VALUES (?1, ?2, ?3, ?4, ?5, CURRENT_TIMESTAMP)`
    );
    const bound = statement.bind(rid, resultCode, itemCount, totalBdt, sourceSha || null);
    if (typeof bound.run === "function") await bound.run();
  } catch (error) {
    console.error(JSON.stringify({
      event: "quote_audit_write_failed",
      request_id: rid,
      error_class: error instanceof Error ? error.name : "UnknownError",
    }));
  }
}

async function quoteResponse(env, rid, status, code, payload, itemCount, totalBdt = null, sourceSha = null) {
  await auditQuote(env, rid, code, itemCount, totalBdt, sourceSha);
  return response(status, { ...payload, request_id: rid }, rid);
}

async function buildQuote(env, items, rid) {
  if (!env.DB) {
    return quoteResponse(env, rid, 503, "SHADOW_DATABASE_NOT_BOUND", {
      ok: false,
      code: "SHADOW_DATABASE_NOT_BOUND",
      message: "Server-authoritative quote data is not configured.",
      shadow: true,
    }, items.length);
  }

  const lines = [];
  let total = 0;
  let sourceSha = null;
  for (const item of items) {
    const runtime = await getPlanRuntime(env.DB, item.plan_id);
    if (!runtime) {
      return quoteResponse(env, rid, 409, "PLAN_NOT_CONFIGURED", {
        ok: false,
        code: "PLAN_NOT_CONFIGURED",
        plan_id: item.plan_id,
        shadow: true,
      }, items.length);
    }
    if (runtime.commercial_state !== "allowed") {
      return quoteResponse(env, rid, 409, "PLAN_NOT_SELLABLE", {
        ok: false,
        code: "PLAN_NOT_SELLABLE",
        plan_id: item.plan_id,
        commercial_state: runtime.commercial_state || "unknown",
        shadow: true,
      }, items.length, null, runtime.source_sha256 || null);
    }
    if (!Number.isInteger(runtime.price_bdt) || runtime.price_bdt < 0 || runtime.currency !== "BDT") {
      return quoteResponse(env, rid, 409, "PRICE_NOT_AUTHORIZED", {
        ok: false,
        code: "PRICE_NOT_AUTHORIZED",
        plan_id: item.plan_id,
        shadow: true,
      }, items.length, null, runtime.source_sha256 || null);
    }
    const lineTotal = runtime.price_bdt * item.quantity;
    if (!Number.isSafeInteger(lineTotal)) {
      return quoteResponse(env, rid, 422, "TOTAL_OVERFLOW", {
        ok: false,
        code: "TOTAL_OVERFLOW",
        shadow: true,
      }, items.length);
    }
    total += lineTotal;
    if (!Number.isSafeInteger(total)) {
      return quoteResponse(env, rid, 422, "TOTAL_OVERFLOW", {
        ok: false,
        code: "TOTAL_OVERFLOW",
        shadow: true,
      }, items.length);
    }
    sourceSha = runtime.source_sha256 || sourceSha;
    lines.push({
      plan_id: runtime.plan_id,
      product_id: runtime.product_id,
      quantity: item.quantity,
      unit_price_bdt: runtime.price_bdt,
      line_total_bdt: lineTotal,
      currency: "BDT",
      authority_ref: runtime.authority_ref || null,
    });
  }

  return quoteResponse(env, rid, 200, "QUOTE_OK", {
    ok: true,
    shadow: true,
    authoritative: true,
    currency: "BDT",
    total_bdt: total,
    items: lines,
    order_creation_enabled: false,
  }, items.length, total, sourceSha);
}

async function dispatch(request, env, rid) {
  const url = new URL(request.url);
  const currentMode = mode(env);

  if (request.method === "GET" && url.pathname === "/health") {
    return response(200, {
      ok: true,
      service: "saveonsub-commerce",
      environment: env.ENVIRONMENT || "shadow",
      mode: currentMode,
      database_bound: Boolean(env.DB),
      order_creation_enabled: false,
      request_id: rid,
    }, rid);
  }

  if (request.method === "GET" && url.pathname === "/v1/capabilities") {
    return response(200, {
      ok: true,
      mode: currentMode,
      quote: "shadow",
      orders: "disabled",
      tracking: "disabled",
      admin: "disabled",
      payments: "disabled",
      fulfillment: "disabled",
      request_id: rid,
    }, rid);
  }

  if (request.method === "GET" && url.pathname === "/v1/catalog/version") {
    return response(200, {
      ok: true,
      mode: currentMode,
      catalog_version: env.CATALOG_VERSION || null,
      price_version: env.PRICE_VERSION || null,
      provider_version: env.PROVIDER_VERSION || null,
      request_id: rid,
    }, rid);
  }

  if (request.method === "POST" && url.pathname === "/v1/quote") {
    try {
      const body = await readJson(request);
      const items = normalizeItems(body.items);
      return await buildQuote(env, items, rid);
    } catch (error) {
      const code = error instanceof Error ? error.message : "INVALID_REQUEST";
      return quoteResponse(env, rid, 400, code, { ok: false, code, shadow: true }, 0);
    }
  }

  const singleQuote = url.pathname.match(/^\/v1\/plans\/([^/]+)\/quote$/);
  if (request.method === "GET" && singleQuote) {
    let planId;
    try {
      planId = decodeURIComponent(singleQuote[1]);
    } catch {
      return quoteResponse(env, rid, 400, "INVALID_PLAN_ID", { ok: false, code: "INVALID_PLAN_ID", shadow: true }, 0);
    }
    const quantity = Number(url.searchParams.get("quantity") || "1");
    try {
      const items = normalizeItems([{ plan_id: planId, quantity }]);
      return await buildQuote(env, items, rid);
    } catch (error) {
      const code = error instanceof Error ? error.message : "INVALID_REQUEST";
      return quoteResponse(env, rid, 400, code, { ok: false, code, shadow: true }, 0);
    }
  }

  if (request.method === "POST" && url.pathname === "/v1/orders") {
    return response(403, {
      ok: false,
      code: "ORDER_CREATION_DISABLED",
      message: "Order creation is intentionally disabled in shadow mode.",
      shadow: true,
      request_id: rid,
    }, rid);
  }

  if (url.pathname.startsWith("/v1/orders/")) {
    return response(403, {
      ok: false,
      code: "ORDER_TRACKING_DISABLED",
      message: "Order tracking/contact mutation is not enabled in shadow mode.",
      shadow: true,
      request_id: rid,
    }, rid);
  }

  if (url.pathname === "/v1/admin" || url.pathname.startsWith("/v1/admin/")) {
    return response(403, {
      ok: false,
      code: "ADMIN_DISABLED",
      message: "Administrative mutation routes are not enabled in the shadow service.",
      shadow: true,
      request_id: rid,
    }, rid);
  }

  return response(404, { ok: false, code: "NOT_FOUND", request_id: rid }, rid);
}

export default {
  async fetch(request, env) {
    const rid = requestId(request);
    const started = Date.now();
    let res;
    try {
      res = await dispatch(request, env, rid);
    } catch (error) {
      console.error(JSON.stringify({
        event: "unhandled_request_error",
        request_id: rid,
        route: new URL(request.url).pathname,
        error_class: error instanceof Error ? error.name : "UnknownError",
      }));
      res = response(500, { ok: false, code: "INTERNAL_ERROR", request_id: rid }, rid);
    }
    console.log(JSON.stringify({
      event: "request_complete",
      request_id: rid,
      method: request.method,
      route: new URL(request.url).pathname,
      status: res.status,
      latency_ms: Date.now() - started,
      mode: mode(env),
    }));
    return res;
  },
};
