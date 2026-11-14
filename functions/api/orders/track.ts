import { json, readJson } from "../../lib/order-os/http";

interface Env { DB: D1Database }

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

// The order tracking token is a bearer secret. Query-string secrets may land in
// CDN/access logs, browser history, and referrer headers. Refuse GET instead of
// accepting ?token=... (never redirect a URL that might contain the secret).
// The caller sends POST JSON { tracking_token } to the same URL; the existing
// /api/orders CORS middleware already permits application/json for this path.
export const onRequestGet: PagesFunction<Env> = async () => {
  const response = json({ error: "USE_POST_WITH_TRACKING_TOKEN_IN_BODY" }, 405);
  response.headers.set("allow", "POST");
  return response;
};

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  // Fail before touching D1. Presence of an old URL token is always rejected;
  // never copy it into logs or echo it to the caller.
  const url = new URL(request.url);
  if (url.searchParams.has("token") || url.searchParams.has("tracking_token")) {
    return json({ error: "TRACKING_TOKEN_IN_URL_NOT_ALLOWED" }, 400);
  }
  if (!env.DB) return json({ error: "ORDER_BACKEND_NOT_CONFIGURED" }, 503);

  const body = await readJson(request, 4096);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const token = typeof body.tracking_token === "string" ? body.tracking_token : "";
  if (token.length < 40 || token.length > 200) {
    return json({ error: "INVALID_TRACKING_TOKEN" }, 400);
  }

  const hash = await sha256Hex(token);
  const order = await env.DB.prepare(`
    SELECT public_order_id, status, total_minor, currency, created_at, updated_at
    FROM orders WHERE tracking_token_hash = ?
  `).bind(hash).first<any>();

  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  return json({
    order_id: order.public_order_id,
    status: order.status,
    total_bdt: order.total_minor / 100,
    currency: order.currency,
    created_at: order.created_at,
    updated_at: order.updated_at,
  });
};
