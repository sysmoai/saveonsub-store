// Server-side, role-specific shaping of order data. The staff UI is never
// trusted to hide anything: fields a role must not see are removed here, before
// the response is built.
import type { Role } from "./order-workflow";

type OrderRow = Record<string, unknown> & {
  customer_name?: string | null;
  customer_phone?: string | null;
  customer_email?: string | null;
  assigned_operator_id?: string | null;
  status?: string;
};

// Support may see a customer's contact details only for orders in a
// post-delivery support state or assigned to them. Other orders show a
// masked name and no contact data. (Role policy unrecorded: least privilege
// applied, widening it needs CEO approval.)
const SUPPORT_CONTACT_STATUSES = new Set(["delivered", "support_open", "completed"]);

const maskName = (name?: string | null) => {
  const first = (name || "").trim().charAt(0);
  return first ? `${first.toUpperCase()}.` : null;
};

export function shapeOrderRow(role: Role, operatorId: string, row: OrderRow): OrderRow {
  const out: OrderRow = { ...row };
  if (role === "owner" || role === "manager") return out;

  if (role === "fulfillment") {
    // Needs a name and an email to deliver access; never the phone number.
    out.customer_phone = null;
    return out;
  }

  if (role === "support") {
    const related = SUPPORT_CONTACT_STATUSES.has(String(row.status)) || row.assigned_operator_id === operatorId;
    if (!related) {
      out.customer_name = maskName(row.customer_name);
      out.customer_phone = null;
      out.customer_email = null;
    }
    return out;
  }

  // viewer (and any unknown role): queue shape only.
  out.customer_name = null;
  out.customer_phone = null;
  out.customer_email = null;
  out.assigned_operator_id = null;
  return out;
}

type EventRow = {
  event_type: string;
  actor_type: string;
  actor_id: string | null;
  payload_json: string;
  created_at: string;
};

// Payload keys that carry no customer or free-text data.
const SAFE_PAYLOAD_KEYS = ["from", "to", "item_count", "provider", "amount_minor", "matches_customer_reference"];

function parsePayload(raw: string): Record<string, unknown> {
  try {
    const value = JSON.parse(raw);
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

export function shapeEvent(role: Role, ev: EventRow) {
  if (role === "owner" || role === "manager") {
    return { ...ev, payload: parsePayload(ev.payload_json), payload_json: undefined };
  }
  const base = { event_type: ev.event_type, actor_type: ev.actor_type, created_at: ev.created_at };
  if (role === "viewer") return base;
  const payload = parsePayload(ev.payload_json);
  const safe: Record<string, unknown> = {};
  for (const key of SAFE_PAYLOAD_KEYS) if (key in payload) safe[key] = payload[key];
  return { ...base, payload: safe };
}
