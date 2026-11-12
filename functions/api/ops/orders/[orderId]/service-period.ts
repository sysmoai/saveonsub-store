// G4: record when a delivered subscription ends, so renewals can be followed up.
import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { json, nowIso, readJson } from "../../../../lib/order-os/http";
import { addDays, addCalendarMonthsClamped, isIsoDate } from "../../../../lib/order-os/money";

const SERVICE_STATUSES = new Set(["delivered", "support_open", "completed"]);
const EXPIRY_SOURCES = new Set(["unknown", "whatsapp_note", "manual_note", "calculated_from_activation", "provider_dashboard", "provider_confirmation"]);
const VERIFIED_EXPIRY_SOURCES = new Set(["provider_dashboard", "provider_confirmation"]);
const PRIVATE_PROVIDER_REF = /^r2:sos\/private\/[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$/;
const MAX_PERIOD_DAYS = 400;

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!["owner", "manager", "fulfillment"].includes(operator.role)) return json({ error: "FORBIDDEN" }, 403);
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "FORBIDDEN_ORIGIN" }, 403);

  const body = await readJson(request);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const starts = body.service_starts_on;
  const ends = body.service_ends_on;
  if (!isIsoDate(starts) || !isIsoDate(ends) || ends <= starts) return json({ error: "INVALID_SERVICE_PERIOD" }, 400);
  if (ends > addDays(starts, MAX_PERIOD_DAYS)) return json({ error: "SERVICE_PERIOD_TOO_LONG" }, 400);

  // Missing or conversation-derived evidence is never upgraded silently.
  // Provider-attested dates require an owner confirmation and a private evidence pointer.
  // The pointer must identify a real, protected provider record in the release workflow.
  const expirySource = typeof body.expiry_source === "string" ? body.expiry_source : "unknown";
  const expiryEvidenceRef = typeof body.expiry_evidence_ref === "string" ? body.expiry_evidence_ref.trim() : "";
  if (!EXPIRY_SOURCES.has(expirySource)) return json({ error: "INVALID_EXPIRY_SOURCE" }, 400);
  const providerVerified = VERIFIED_EXPIRY_SOURCES.has(expirySource);
  const calculated = expirySource === "calculated_from_activation";
  const durationUnit = body.expiry_duration_unit;
  const durationValue = body.expiry_duration_value;
  let estimatedEnd: string | null = null;
  if (calculated) {
    // Never silently translate "one month" into 30 days.
    if (durationUnit !== "days" && durationUnit !== "calendar_months") {
      return json({ error: "CALCULATION_UNIT_REQUIRED" }, 400);
    }
    const limit = durationUnit === "days" ? 400 : 12;
    if (!Number.isInteger(durationValue) || durationValue < 1 || durationValue > limit) {
      return json({ error: "INVALID_CALCULATION_DURATION" }, 400);
    }
    estimatedEnd = durationUnit === "days"
      ? addDays(starts, durationValue)
      : addCalendarMonthsClamped(starts, durationValue);
    if (!estimatedEnd || estimatedEnd !== ends) return json({ error: "CALCULATED_END_MISMATCH" }, 400);
  } else if (durationUnit !== undefined || durationValue !== undefined) {
    return json({ error: "UNEXPECTED_CALCULATION_FIELDS" }, 400);
  }
  if (providerVerified && operator.role !== "owner") return json({ error: "EXPIRY_VERIFICATION_FORBIDDEN" }, 403);
  if (providerVerified && (!PRIVATE_PROVIDER_REF.test(expiryEvidenceRef) || expiryEvidenceRef.includes(".."))) {
    return json({ error: "PROVIDER_EXPIRY_EVIDENCE_REQUIRED" }, 400);
  }
  if (!providerVerified && expiryEvidenceRef) return json({ error: "UNVERIFIED_EXPIRY_EVIDENCE_FORBIDDEN" }, 400);

  let order;
  try {
    order = await env.DB.prepare("SELECT id,status,assigned_operator_id FROM orders WHERE public_order_id=?")
      .bind(String(params.orderId || "")).first<any>();
  } catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  if (!SERVICE_STATUSES.has(order.status)) return json({ error: "ORDER_NOT_DELIVERED" }, 409);
  if (operator.role === "fulfillment" && order.assigned_operator_id !== operator.id) {
    return json({ error: "NOT_ASSIGNED_OPERATOR" }, 403);
  }

  const ts = nowIso();
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO order_service_periods(order_id,service_starts_on,service_ends_on,set_by,updated_at)
        VALUES (?,?,?,?,?)
        ON CONFLICT(order_id) DO UPDATE SET service_starts_on=excluded.service_starts_on,
          service_ends_on=excluded.service_ends_on, set_by=excluded.set_by, updated_at=excluded.updated_at`)
        .bind(order.id, starts, ends, operator.id, ts),
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        VALUES (?,'service_period_set','operator',?,?,?)`)
        .bind(order.id, operator.id, JSON.stringify({
          from: starts, to: ends, expiry_source: expirySource,
          expiry_verified: providerVerified,
          ...(providerVerified ? { expiry_evidence_ref: expiryEvidenceRef } : {}),
          ...(calculated ? {
            expiry_calculation_basis: "activation_date",
            expiry_duration_unit: durationUnit,
            expiry_duration_value: durationValue,
            expiry_calculated_ends_on: estimatedEnd
          } : {})
        }), ts),
    ]);
  } catch {
    console.error("service_period_write_failed");
    return json({ error: "WRITE_FAILED" }, 503);
  }
  return json({
    ok: true, order_id: String(params.orderId),
    service_starts_on: starts, service_ends_on: ends,
    expiry_evidence_state: providerVerified ? "provider_confirmed" : calculated ? "estimated" : "needs_review",
    expiry_date_is_estimate: calculated,
    renewal_outreach_allowed: false,
  });
};
