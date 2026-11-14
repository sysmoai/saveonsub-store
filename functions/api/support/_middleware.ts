// Customer ticket calls use a different request header from the order API:
// browsers preflight x-ticket-token before GET/POST /api/support/tickets/status.
// Keep the SAME narrowly allowlisted storefront origins, blocked-origin behavior,
// methods and other protections as /api/orders, but expose the ticket header
// only on the customer support path. Never widen /api/orders CORS.
import { onRequest as ordersCors, STOREFRONT_ORIGINS } from "../orders/_middleware";

export const onRequest: PagesFunction = async (context) => {
  const response = await ordersCors(context);
  const origin = context.request.headers.get("origin");

  // Don't change a forbidden response or attach headers to an unrelated origin.
  if (!origin || !STOREFRONT_ORIGINS.has(origin) ||
      response.headers.get("access-control-allow-origin") !== origin) {
    return response;
  }

  // Response headers may be immutable; clone rather than modifying the original.
  // This covers both OPTIONS preflight and actual GET/POST responses.
  const out = new Response(response.body, response);
  out.headers.set("access-control-allow-headers", "content-type, x-ticket-token");
  return out;
};
