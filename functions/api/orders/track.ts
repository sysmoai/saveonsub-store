interface Env { DB: D1Database }

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  if (!env.DB) return json({ error: "ORDER_BACKEND_NOT_CONFIGURED" }, 503);
  const url = new URL(request.url);
  const token = url.searchParams.get("token") || "";
  if (token.length < 40 || token.length > 200) return json({ error: "INVALID_TRACKING_TOKEN" }, 400);

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
