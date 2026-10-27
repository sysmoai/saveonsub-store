import { requireOperator, authFailure, type OpsEnv } from "../../../../lib/order-os/ops-auth";
import { json, nowIso, readJson, writeFailure } from "../../../../lib/order-os/http";

// The only way an order reaches payment_confirmed.
//
// A customer-submitted reference (orders.payment_reference) is a claim, not
// proof. A verifier (owner/manager) attests that settled money for exactly this
// order total was seen in the provider's receiving personal-account history or bank statement, and supplies the
// provider reference themselves. We keep a hash (duplicate detection) and the
// last four characters (operator recognition) - never the full reference.
//
// Who may verify: the CEO (owner) only, by default. PAYMENT_VERIFIER_ROLES can
// widen this to "owner,manager" and nothing else; support/fulfillment/viewer
// can never verify. Every verification must cite settlement evidence
// (evidence_ref): a private R2 object (r2:sos/private/...) or a merchant
// statement id (stmt:...). A screenshot or any URL is not settlement evidence.

const PROVIDERS = new Set(["bkash", "nagad", "rocket", "bank_transfer"]);
const TXN_PATTERN = /^[A-Z0-9][A-Z0-9_-]{5,39}$/;
const MAX_BDT = 10_000_000;
const EVIDENCE_REF = /^(?:r2:sos\/private\/[A-Za-z0-9][A-Za-z0-9._\/-]{0,199}|stmt:[A-Za-z0-9][A-Za-z0-9._:-]{3,119})$/;
const SCREENSHOT = /\.(?:png|jpe?g|webp|gif|heic|bmp)$/i;

type VerifierEnv = OpsEnv & { PAYMENT_VERIFIER_ROLES?: string };

export function paymentVerifierRoles(env: VerifierEnv): Set<string> {
  const roles = new Set(["owner"]);
  for (const role of String(env.PAYMENT_VERIFIER_ROLES || "").split(",")) {
    if (role.trim() === "manager") roles.add("manager");
  }
  return roles;
}

export function validEvidenceRef(ref: string) {
  return EVIDENCE_REF.test(ref) && !ref.includes("..") && !SCREENSHOT.test(ref);
}

async function sha256Hex(input: string) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

export const onRequestPost: PagesFunction<VerifierEnv> = async ({ request, env, params }) => {
  let operator;
  try { operator = await requireOperator(request, env); }
  catch (e) { return authFailure(e); }
  if (!paymentVerifierRoles(env).has(operator.role)) return json({ error: "PAYMENT_VERIFICATION_FORBIDDEN" }, 403);

  const body = await readJson(request);
  if (!body) return json({ error: "INVALID_JSON" }, 400);

  const provider = typeof body.provider === "string" ? body.provider : "";
  const txn = typeof body.transaction_id === "string" ? body.transaction_id.trim().toUpperCase() : "";
  const amountBdt = typeof body.amount_bdt === "number" ? body.amount_bdt : NaN;
  const currency = typeof body.currency === "string" ? body.currency.toUpperCase() : "BDT";
  const note = typeof body.evidence_note === "string" ? body.evidence_note.trim().slice(0, 300) : "";
  const evidenceRef = typeof body.evidence_ref === "string" ? body.evidence_ref.trim() : "";
  const receiptConfirmed = body.receipt_confirmed === true;
  const receiptSource = typeof body.receipt_source === "string" ? body.receipt_source : "";
  if (!evidenceRef) return json({ error: "EVIDENCE_REF_REQUIRED" }, 400);
  if (!validEvidenceRef(evidenceRef)) return json({ error: "INVALID_EVIDENCE_REF" }, 400);
  if (!PROVIDERS.has(provider)) return json({ error: "INVALID_PROVIDER" }, 400);
  // Only an authorized human checking an actual incoming receipt may attest.
  if (!receiptConfirmed) return json({ error: "RECEIPT_ATTESTATION_REQUIRED" }, 400);
  if ((provider === "bank_transfer" && receiptSource !== "bank_statement") ||
      (provider !== "bank_transfer" && receiptSource !== "receiving_account_history")) {
    return json({ error: "INVALID_RECEIPT_SOURCE" }, 400);
  }
  if (!TXN_PATTERN.test(txn)) return json({ error: "INVALID_TRANSACTION_REFERENCE" }, 400);
  if (!Number.isFinite(amountBdt) || amountBdt <= 0 || amountBdt > MAX_BDT) return json({ error: "INVALID_AMOUNT" }, 400);
  const amountMinor = Math.round(amountBdt * 100);
  if (Math.abs(amountBdt * 100 - amountMinor) > 1e-6) return json({ error: "INVALID_AMOUNT" }, 400);

  const orderId = String(params.orderId || "");
  let order;
  try {
    order = await env.DB.prepare("SELECT id,status,total_minor,currency,payment_method,payment_reference FROM orders WHERE public_order_id=?")
      .bind(orderId).first<any>();
  } catch { return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503); }
  if (!order) return json({ error: "ORDER_NOT_FOUND" }, 404);
  if (order.status !== "payment_review") return json({ error: "NOT_AWAITING_PAYMENT", status: order.status }, 409);
  if (order.payment_method !== provider) return json({ error: "PAYMENT_METHOD_MISMATCH" }, 409);
  // The expected total is deliberately not echoed back: the verifier must read it off the statement.
  if (currency !== order.currency || amountMinor !== order.total_minor) return json({ error: "AMOUNT_OR_CURRENCY_MISMATCH" }, 409);

  const customerRef = String(order.payment_reference || "").trim().toUpperCase();
  const matchesCustomer = customerRef !== "" && customerRef === txn ? 1 : 0;
  const hash = await sha256Hex(`${provider}:${txn}`);
  const last4 = txn.slice(-4);
  const verificationId = crypto.randomUUID();
  const ts = nowIso();

  // 1) verification row  2) audit event  3) status change - one atomic batch.
  // Duplicate references and re-verification are rejected by unique indexes;
  // the status trigger refuses payment_confirmed without row (1).
  try {
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO payment_verifications
        (id,order_id,provider,txn_ref_hash,txn_ref_last4,amount_minor,currency,matches_customer_reference,evidence_note,evidence_ref,receipt_source,verified_by,verified_at)
        SELECT ?,id,?,?,?,total_minor,currency,?,?,?,?,?,? FROM orders WHERE id=? AND status='payment_review' AND total_minor=? AND currency=?`)
        .bind(verificationId, provider, hash, last4, matchesCustomer, note || null, evidenceRef, receiptSource, operator.id, ts, order.id, order.total_minor, order.currency),
      env.DB.prepare(`INSERT INTO order_events(order_id,event_type,actor_type,actor_id,payload_json,created_at)
        SELECT order_id,'payment_verified','operator',?,?,? FROM payment_verifications WHERE id=?`)
        .bind(operator.id, JSON.stringify({ provider, last4, amount_minor: amountMinor, matches_customer_reference: !!matchesCustomer, receipt_source: receiptSource }), ts, verificationId),
      env.DB.prepare("UPDATE orders SET status='payment_confirmed',priority=0,payment_confirmed_at=?,updated_at=? WHERE id=? AND status='payment_review'")
        .bind(ts, ts, order.id),
      env.DB.prepare(`INSERT INTO notification_outbox
        (order_id,channel,destination_key,template_key,payload_json,priority,status,attempt_count,next_attempt_at,created_at,updated_at)
        SELECT id,'webhook','sos-ripon','paid_order_priority',?,0,'pending',0,?,?,?
        FROM orders WHERE id=? AND status='payment_confirmed'`)
        .bind(JSON.stringify({ order_id: orderId, amount_minor: amountMinor, currency, provider }), ts, ts, ts, order.id),
    ]);
  } catch (e) { return writeFailure(e); }

  return json({
    ok: true,
    order_id: orderId,
    status: "payment_confirmed",
    staff_notification: "queued_not_sent",
    verification: { provider, last4, amount_minor: amountMinor, matches_customer_reference: !!matchesCustomer, verified_at: ts },
  });
};
