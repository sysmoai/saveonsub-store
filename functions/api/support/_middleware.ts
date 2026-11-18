// Customer ticket endpoints share the storefront-origin CORS rules of /api/orders.
// Cloudflare Access must BYPASS /api/support/tickets* exactly like /api/orders*
// (see ops/order-os/ACCESS-SETUP.md); nothing else on the staff host.
export { onRequest } from "../orders/_middleware";
