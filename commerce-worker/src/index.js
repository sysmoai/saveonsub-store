const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "x-content-type-options": "nosniff",
};

function response(status, payload) {
  return new Response(JSON.stringify(payload), { status, headers: JSON_HEADERS });
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
              effective_from, effective_to, authority_ref
         FROM plan_runtime
        WHERE plan_id = ?1
        LIMIT 1`
    )
    .bind(planId)
    .first();
}

async function buildQuote(env, items) {
  if (!env.DB) {
    return response(503, {
      ok: false,
      code: "SHADOW_DATABASE_NOT_BOUND",
      message: "Server-authoritative quote data is not configured.",
      shadow: true,
    });
  }

  const lines = [];
  let total = 0;
  for (const item of items) {
    const runtime = await getPlanRuntime(env.DB, item.plan_id);
    if (!runtime) {
      return response(409, { ok: false, code: "PLAN_NOT_CONFIGURED", plan_id: item.plan_id, shadow: true });
    }
    if (runtime.commercial_state !== "allowed") {
      return response(409, {
        ok: false,
        code: "PLAN_NOT_SELLABLE",
        plan_id: item.plan_id,
        commercial_state: runtime.commercial_state || "unknown",
        shadow: true,
      });
    }
    if (!Number.isInteger(runtime.price_bdt) || runtime.price_bdt < 0 || runtime.currency !== "BDT") {
      return response(409, { ok: false, code: "PRICE_NOT_AUTHORIZED", plan_id: item.plan_id, shadow: true });
    }
    const lineTotal = runtime.price_bdt * item.quantity;
    if (!Number.isSafeInteger(lineTotal)) {
      return response(422, { ok: false, code: "TOTAL_OVERFLOW", shadow: true });
    }
    total += lineTotal;
    if (!Number.isSafeInteger(total)) {
      return response(422, { ok: false, code: "TOTAL_OVERFLOW", shadow: true });
    }
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

  return response(200, {
    ok: true,
    shadow: true,
    authoritative: true,
    currency: "BDT",
    total_bdt: total,
    items: lines,
    order_creation_enabled: false,
  });
}

export default {
  async fetch(request, env) {
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
      });
    }

    if (request.method === "GET" && url.pathname === "/v1/capabilities") {
      return response(200, {
        ok: true,
        mode: currentMode,
        quote: "shadow",
        orders: "disabled",
        payments: "disabled",
        fulfillment: "disabled",
      });
    }

    if (request.method === "POST" && url.pathname === "/v1/quote") {
      try {
        const body = await readJson(request);
        const items = normalizeItems(body.items);
        return await buildQuote(env, items);
      } catch (error) {
        const code = error instanceof Error ? error.message : "INVALID_REQUEST";
        return response(400, { ok: false, code, shadow: true });
      }
    }

    if (request.method === "POST" && url.pathname === "/v1/orders") {
      return response(403, {
        ok: false,
        code: "ORDER_CREATION_DISABLED",
        message: "Order creation is intentionally disabled in shadow mode.",
        shadow: true,
      });
    }

    return response(404, { ok: false, code: "NOT_FOUND" });
  },
};
