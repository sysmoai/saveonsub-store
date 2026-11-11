// G4: owner-reviewed renewal worklist, NOT an outbound-contact list.
// Founder currently consults WhatsApp conversations/personal notes for expiry;
// only an owner-attested provider evidence event qualifies as provider-confirmed.
// All contact details are intentionally omitted until a separate consent gate exists.
import { requireOperator, authFailure, type OpsEnv } from "../../../lib/order-os/ops-auth";
import { json } from "../../../lib/order-os/http";
import { addDays, addCalendarMonthsClamped, dhakaToday } from "../../../lib/order-os/money";

const VERIFIED_SOURCES = new Set(["provider_dashboard", "provider_confirmation"]);

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!["owner", "manager", "fulfillment"].includes(operator.role)) return json({ error: "FORBIDDEN" }, 403);

  const url = new URL(request.url);
  const asked = Number(url.searchParams.get("days") || 7);
  const days = Number.isFinite(asked) ? Math.min(Math.max(Math.floor(asked), 0), 60) : 7;
  const today = dhakaToday();
  const until = addDays(today, days);
  const from = addDays(today, -14); // retain recently missed dates for human review

  // Legacy periods lack a provenance event and MUST remain needs_review.
  // The last event must cover the CURRENT dates, so an edit cannot inherit an old attestation.
  let sql = `SELECT o.public_order_id,o.status,p.service_starts_on,p.service_ends_on,
      (SELECT product_name_snapshot || ' / ' || plan_name_snapshot FROM order_items i
         WHERE i.order_id=o.id ORDER BY i.id LIMIT 1) AS item,
      (SELECT e.payload_json FROM order_events e
         WHERE e.order_id=o.id AND e.event_type='service_period_set'
         ORDER BY e.id DESC LIMIT 1) AS latest_period_event
    FROM order_service_periods p JOIN orders o ON o.id=p.order_id
    WHERE p.service_ends_on BETWEEN ? AND ? AND o.status NOT IN ('cancelled','refunded')`;
  const binds: unknown[] = [from, until];
  if (operator.role === "fulfillment") {
    sql += " AND o.assigned_operator_id=?";
    binds.push(operator.id);
  }
  sql += " ORDER BY p.service_ends_on ASC LIMIT 200";

  let rows;
  try { rows = await env.DB.prepare(sql).bind(...binds).all<any>(); }
  catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }

  const renewals: Record<string, unknown>[] = [];
  const needs_review: Record<string, unknown>[] = [];
  for (const r of rows.results || []) {
    let evidence: Record<string, unknown> = {};
    try {
      evidence = typeof r.latest_period_event === "string" ? JSON.parse(r.latest_period_event) : {};
      if (!evidence || typeof evidence !== "object" || Array.isArray(evidence)) evidence = {};
    } catch { evidence = {}; }

    const datesMatch = evidence.from === r.service_starts_on && evidence.to === r.service_ends_on;
    const confirmed = datesMatch && evidence.expiry_verified === true
      && typeof evidence.expiry_source === "string" && VERIFIED_SOURCES.has(evidence.expiry_source)
      && typeof evidence.expiry_evidence_ref === "string"
      && evidence.expiry_evidence_ref.startsWith("r2:sos/private/");
    const estimated = datesMatch
      && evidence.expiry_verified === false
      && evidence.expiry_source === "calculated_from_activation"
      && evidence.expiry_calculation_basis === "activation_date"
      && evidence.expiry_calculated_ends_on === r.service_ends_on
      && Number.isInteger(evidence.expiry_duration_value)
      && (
        (evidence.expiry_duration_unit === "days"
          && evidence.expiry_duration_value >= 1 && evidence.expiry_duration_value <= 400
          && addDays(r.service_starts_on, evidence.expiry_duration_value) === r.service_ends_on)
        || (evidence.expiry_duration_unit === "calendar_months"
          && evidence.expiry_duration_value >= 1 && evidence.expiry_duration_value <= 12
          && addCalendarMonthsClamped(r.service_starts_on, evidence.expiry_duration_value) === r.service_ends_on)
      );
    const row = {
      public_order_id: r.public_order_id,
      status: r.status,
      item: r.item,
      service_starts_on: r.service_starts_on,
      service_ends_on: r.service_ends_on,
      days_left: Math.round((Date.parse(`${r.service_ends_on}T00:00:00Z`) -
        Date.parse(`${today}T00:00:00Z`)) / 86400000),
      expiry_source: datesMatch && typeof evidence.expiry_source === "string"
        ? evidence.expiry_source : "unknown",
      expiry_evidence_state: confirmed ? "provider_confirmed" : estimated ? "estimated" : "needs_review",
      expiry_date_is_estimate: estimated,
      ...(estimated ? {
        expiry_calculation_basis: "activation_date",
        expiry_duration_unit: evidence.expiry_duration_unit,
        expiry_duration_value: evidence.expiry_duration_value,
      } : {}),
      renewal_contact_consent: "not_verified",
      outreach_allowed: false,
    };
    // No customer phone, email or name in either queue. Staff must look up
    // the protected order and separately confirm consent before outreach.
    (confirmed ? renewals : needs_review).push(row);
  }
  return json({
    ok: true, today, until, renewals, needs_review,
    outreach_enabled: false,
    notice: "Internal review only. No automatic renewal contact without recorded channel consent.",
  });
};
