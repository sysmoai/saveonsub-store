// G3: per-order cost ledger. Owner records, owner/manager read. Append-only.
import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { json, nowIso, readJson } from "../../../../lib/order-os/http";
import { EVIDENCE_REF, bdtToMinor } from "../../../../lib/order-os/money";

const FINANCE_READERS = new Set(["owner", "manager"]);

async function loadOrder(env: OpsEnv, publicId: string) {
  return env.DB.prepare("SELECT id,status,total_minor,currency FROM orders WHERE public_order_id=?")
    .bind(publicId).first<{ id: string; status: string; total_minor: number; currency: string }>();
}

async function summary(env: OpsEnv, orderId: string, totalMinor: number) {
  const rows = await env.DB.prepare(`SELECT id,entry_type,category,supplier_label,amount_minor,currency,
      evidence_ref,note,recorded_by,created_at FROM order_costs WHERE order_id=? ORDER BY created_at, id`)
    .bind(orderId).all<any>();
  const entries = rows.results || [];
  const costMinor = entries.reduce((s: number, e: any) => s + Number(e.amount_minor), 0);
  const refund = await env.DB.prepare("SELECT COALESCE(SUM(amount_minor),0) AS n FROM order_refunds WHERE order_id=?")
    .bind(orderId).first<{ n: number }>();
  const refundMinor = Number(refund?.n || 0);
  return {
    entries,
    order_total_minor: totalMinor,
    refunded_minor: refundMinor,
    cost_minor: costMinor,
    gross_margin_minor: totalMinor - refundMinor - costMinor,
    cost_recorded: entries.length > 0,
  };
}

export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!FINANCE_READERS.has(operator.role)) return json({ error: "FORBIDDEN" }, 403);

  try {
    const order = await loadOrder(env, String(params.orderId || ""));
    if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
    return json({ ok: true, order_id: String(params.orderId), ...(await summary(env, order.id, order.total_minor)) });
  } catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
};

export const onRequestPost: PagesFunction<OpsEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (operator.role !== "owner") return json({ error: "FORBIDDEN" }, 403);
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "FORBIDDEN_ORIGIN" }, 403);

  const body = await readJson(request);
  if (!body) return json({ error: "INVALID_JSON" }, 400);
  const entryType = body.entry_type === "correction" ? "correction" : body.entry_type === undefined || body.entry_type === "cost" ? "cost" : "";
  if (!entryType) return json({ error: "INVALID_ENTRY_TYPE" }, 400);
  const category = typeof body.category === "string" ? body.category : "supplier";
  if (!["supplier", "payment_fee", "other"].includes(category)) return json({ error: "INVALID_CATEGORY" }, 400);
  const supplier = typeof body.supplier_label === "string" ? body.supplier_label.trim() : "";
  if (supplier.length < 2 || supplier.length > 80) return json({ error: "SUPPLIER_LABEL_REQUIRED" }, 400);
  const amountMinor = bdtToMinor(body.amount_bdt, { allowNegative: entryType === "correction" });
  if (amountMinor === null) return json({ error: "INVALID_AMOUNT" }, 400);
  const evidence = typeof body.evidence_ref === "string" && body.evidence_ref.trim() ? body.evidence_ref.trim() : null;
  if (evidence && !EVIDENCE_REF.test(evidence)) return json({ error: "INVALID_EVIDENCE_REF" }, 400);
  const note = typeof body.note === "string" ? body.note.slice(0, 300) : null;
  if (entryType === "correction" && !note) return json({ error: "CORRECTION_NOTE_REQUIRED" }, 400);

  let order;
  try { order = await loadOrder(env, String(params.orderId || "")); }
  catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  // Costs belong to orders whose payment was verified (or later states).
  if (["submitted", "payment_review", "cancelled"].includes(order.status)) return json({ error: "ORDER_NOT_PAID" }, 409);

  const ts = nowIso();
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO order_costs(id,order_id,entry_type,category,supplier_label,amount_minor,currency,evidence_ref,note,recorded_by,created_at)
        VALUES (?,?,?,?,?,?,'BDT',?,?,?,?)`)
        .bind(crypto.randomUUID(), order.id, entryType, category, supplier, amountMinor, evidence, note, operator.id, ts),
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        VALUES (?,'cost_recorded','operator',?,?,?)`)
        .bind(order.id, operator.id, JSON.stringify({ entry_type: entryType, category, amount_minor: amountMinor }), ts),
    ]);
  } catch {
    console.error("order_cost_write_failed");
    return json({ error: "WRITE_FAILED" }, 503);
  }
  return json({ ok: true, order_id: String(params.orderId), ...(await summary(env, order.id, order.total_minor)) }, 201);
};
