export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });

export const nowIso = () => new Date().toISOString();

export async function readJson(request: Request, limit = 4096): Promise<Record<string, unknown> | null> {
  const declared = Number(request.headers.get("content-length") || 0);
  if (declared > limit) return null;
  try {
    const text = await request.text();
    if (text.length > limit) return null;
    const value = JSON.parse(text);
    return value && typeof value === "object" && !Array.isArray(value) ? value : null;
  } catch {
    return null;
  }
}

// Storage-layer invariants (see ops/order-os/schema.sql triggers and unique
// indexes) surface as D1 errors. Map the known ones to stable client codes and
// never echo raw database text.
export function writeFailure(e: unknown): Response {
  const text = String(e instanceof Error ? e.message : e);
  if (text.includes("TERMINAL_ORDER_IMMUTABLE")) return json({ error: "TERMINAL_STATE_IMMUTABLE" }, 409);
  if (text.includes("PAYMENT_NOT_VERIFIED")) return json({ error: "PAYMENT_NOT_VERIFIED" }, 409);
  if (text.includes("txn_ref_hash")) return json({ error: "DUPLICATE_PAYMENT_REFERENCE" }, 409);
  if (text.includes("payment_verifications.order_id")) return json({ error: "ALREADY_VERIFIED" }, 409);
  console.error("order_write_failed");
  return json({ error: "WRITE_FAILED" }, 503);
}
