// G3: month gross margin = verified receipts - refunds sent - recorded order costs.
// Owner/manager only. Asia/Dhaka month boundaries. Orders paid in the month
// without any cost entry are counted, so an incomplete cost ledger is visible
// instead of silently inflating profit. Not statutory accounting.
import { requireOperator, authFailure, type OpsEnv } from "../../../lib/order-os/ops-auth";
import { json } from "../../../lib/order-os/http";
import { dhakaMonthBounds, dhakaToday } from "../../../lib/order-os/money";

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!["owner", "manager"].includes(operator.role)) return json({ error: "FORBIDDEN" }, 403);

  const month = new URL(request.url).searchParams.get("month") || dhakaToday().slice(0, 7);
  const bounds = dhakaMonthBounds(month);
  if (!bounds) return json({ error: "INVALID_MONTH" }, 400);

  try {
    const paid = await env.DB.prepare(`SELECT COUNT(*) AS orders, COALESCE(SUM(v.amount_minor),0) AS receipts
        FROM payment_verifications v WHERE v.voided_at IS NULL AND v.verified_at >= ? AND v.verified_at < ?`)
      .bind(bounds.start, bounds.end).first<{ orders: number; receipts: number }>();
    const costs = await env.DB.prepare(`SELECT COALESCE(SUM(c.amount_minor),0) AS n FROM order_costs c
        JOIN payment_verifications v ON v.order_id=c.order_id AND v.voided_at IS NULL
        WHERE v.verified_at >= ? AND v.verified_at < ?`)
      .bind(bounds.start, bounds.end).first<{ n: number }>();
    const missing = await env.DB.prepare(`SELECT COUNT(*) AS n FROM payment_verifications v
        WHERE v.voided_at IS NULL AND v.verified_at >= ? AND v.verified_at < ?
          AND NOT EXISTS (SELECT 1 FROM order_costs c WHERE c.order_id=v.order_id)`)
      .bind(bounds.start, bounds.end).first<{ n: number }>();
    const refunds = await env.DB.prepare(`SELECT COALESCE(SUM(amount_minor),0) AS n FROM order_refunds
        WHERE created_at >= ? AND created_at < ?`)
      .bind(bounds.start, bounds.end).first<{ n: number }>();

    const receipts = Number(paid?.receipts || 0);
    const costMinor = Number(costs?.n || 0);
    const refundMinor = Number(refunds?.n || 0);
    return json({
      ok: true,
      month,
      timezone: "Asia/Dhaka",
      paid_orders: Number(paid?.orders || 0),
      verified_receipts_minor: receipts,
      refunds_sent_minor: refundMinor,
      order_costs_minor: costMinor,
      gross_margin_minor: receipts - refundMinor - costMinor,
      paid_orders_without_cost: Number(missing?.n || 0),
      complete: Number(missing?.n || 0) === 0,
      note: "Excludes ads, tools and other business expenses (see business ledger).",
    });
  } catch {
    return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503);
  }
};
