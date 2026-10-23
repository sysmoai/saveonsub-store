// Single source of truth for the Order OS state machine and role permissions.
// Pure functions only: no I/O, so the rules are unit-testable and the same rule
// set is used by every endpoint. The database triggers in ops/order-os/schema.sql
// enforce the hard invariants again at the storage layer.

export type Role = "owner" | "manager" | "fulfillment" | "support" | "viewer";

export const ORDER_STATUSES = [
  "submitted", "payment_review", "payment_confirmed", "assigned", "fulfilling",
  "delivered", "support_open", "completed", "cancelled", "refunded",
] as const;
export type OrderStatus = (typeof ORDER_STATUSES)[number];

export const TERMINAL_STATUSES = new Set<string>(["cancelled", "refunded"]);

// Ordinary edges. Anything not listed here is not an ordinary transition.
// payment_review -> payment_confirmed exists only through the payment
// verification endpoint; payment_confirmed -> assigned only through claim.
const EDGES: Record<string, string[]> = {
  submitted: ["payment_review", "cancelled"],
  payment_review: ["payment_confirmed", "cancelled"],
  payment_confirmed: ["assigned", "refunded"],
  assigned: ["fulfilling", "refunded"],
  fulfilling: ["delivered", "refunded"],
  delivered: ["completed", "support_open", "refunded"],
  support_open: ["completed", "fulfilling", "refunded"],
  completed: ["support_open", "refunded"],
  cancelled: [],
  refunded: [],
};

// Edges that have a dedicated, stricter endpoint and are refused on the generic one.
const DEDICATED: Record<string, string> = {
  "payment_review->payment_confirmed": "USE_PAYMENT_VERIFICATION",
  "payment_confirmed->assigned": "USE_CLAIM",
};

// Edges restricted roles may take. owner/manager may take every ordinary edge.
const ROLE_EDGES: Record<Exclude<Role, "owner" | "manager">, string[]> = {
  fulfillment: [
    "assigned->fulfilling",
    "fulfilling->delivered",
    "delivered->completed",
    "delivered->support_open",
    "support_open->fulfilling",
  ],
  // Support can open and close support cases on delivered work. Cancel, refund,
  // payment and fulfilment edges stay with managers. Whether support may mark a
  // case completed is flagged for CEO confirmation in ops/CLAUDE-RECOVERY-STATE.md.
  support: [
    "delivered->support_open",
    "completed->support_open",
    "support_open->completed",
  ],
  viewer: [],
};

export type TransitionDecision =
  | { ok: true }
  | { ok: false; status: 403 | 409; code: string };

export function isOrderStatus(value: string): value is OrderStatus {
  return (ORDER_STATUSES as readonly string[]).includes(value);
}

export function isPrivileged(role: Role) {
  return role === "owner" || role === "manager";
}

export function decideTransition(role: Role, from: string, to: string): TransitionDecision {
  if (!isOrderStatus(from) || !isOrderStatus(to)) return { ok: false, status: 409, code: "INVALID_TRANSITION" };
  if (role === "viewer") return { ok: false, status: 403, code: "TRANSITION_FORBIDDEN" };
  if (TERMINAL_STATUSES.has(from)) return { ok: false, status: 409, code: "TERMINAL_STATE_IMMUTABLE" };
  if (from === to) return { ok: false, status: 409, code: "INVALID_TRANSITION" };
  const edge = `${from}->${to}`;
  if (!EDGES[from].includes(to)) return { ok: false, status: 409, code: "INVALID_TRANSITION" };
  if (DEDICATED[edge]) return { ok: false, status: 409, code: DEDICATED[edge] };
  if (isPrivileged(role)) return { ok: true };
  if (!ROLE_EDGES[role].includes(edge)) return { ok: false, status: 403, code: "TRANSITION_FORBIDDEN" };
  return { ok: true };
}

export function canTransition(role: Role, from: string, to: string) {
  return decideTransition(role, from, to).ok;
}

// States from which an unassigned order may be claimed. payment_review is
// deliberately absent: nobody starts fulfilment before payment is verified.
export const CLAIMABLE_STATUSES = [
  "payment_confirmed", "assigned", "fulfilling", "delivered", "support_open", "completed",
] as const;

export function canClaim(role: Role) {
  return role === "owner" || role === "manager" || role === "fulfillment";
}
