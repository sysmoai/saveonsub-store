// G1: the public order endpoints (/api/orders, /api/orders/track) live on the
// staff Pages project but are called by the storefront on saveonsub.com.
// Only the canonical storefront origins may call them cross-origin. Requests
// from any other browser origin are refused before the handler runs.
// Cloudflare Access must BYPASS exactly these two paths; everything else on the
// staff host stays behind Access (see ops/order-os/ACCESS-SETUP.md).

export const STOREFRONT_ORIGINS = new Set(["https://saveonsub.com", "https://www.saveonsub.com"]);

const corsHeaders = (origin: string) => ({
  "access-control-allow-origin": origin,
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type",
  "access-control-max-age": "600",
  vary: "Origin",
});

export const onRequest: PagesFunction = async ({ request, next }) => {
  const origin = request.headers.get("origin");
  const sameOrigin = origin === new URL(request.url).origin;
  const allowed = origin && STOREFRONT_ORIGINS.has(origin);

  if (request.method === "OPTIONS") {
    if (!allowed) return new Response(null, { status: 403, headers: { vary: "Origin" } });
    return new Response(null, { status: 204, headers: corsHeaders(origin) });
  }
  if (origin && !allowed && !sameOrigin) {
    return new Response(JSON.stringify({ error: "ORIGIN_NOT_ALLOWED" }), {
      status: 403,
      headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", vary: "Origin" },
    });
  }

  const response = await next();
  if (!allowed) return response;
  const out = new Response(response.body, response);
  for (const [k, v] of Object.entries(corsHeaders(origin))) out.headers.set(k, v);
  return out;
};
