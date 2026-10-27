// SaveOnSub-only dispatch module for the EXISTING order-notifications Worker; staging until CEO approval.
// Delivery is at-least-once. The receiver should dedupe by delivery_key.
// No customer PII, credential, wallet account or payment reference is sent.

const PAID_STATUSES = "'payment_confirmed','assigned','fulfilling','delivered','support_open','completed'";
const MAX_ATTEMPTS = 5;

export async function dispatchPaidAlerts(env, clock = new Date(), send = fetch) {
  if (!env.DB) return { processed: 0, skipped: "db_not_configured" };
  const now = clock.toISOString();
  const stale = new Date(clock.getTime() - 15 * 60_000).toISOString();
  const escalationMinutes = Number(env.SOS_PAID_ESCALATION_MINUTES || 15);
  const minutes = Number.isFinite(escalationMinutes) ? Math.min(Math.max(escalationMinutes, 5), 120) : 15;
  const cutoff = new Date(clock.getTime() - minutes * 60_000).toISOString();

  // A paid order unclaimed past the configured window is a *separate* CEO alert.
  // A unique index on order_id/template/destination prevents duplicate escalation.
  await env.DB.prepare(`INSERT OR IGNORE INTO notification_outbox
    (order_id,channel,destination_key,template_key,payload_json,priority,status,attempt_count,next_attempt_at,created_at,updated_at)
    SELECT o.id,'webhook','sos-emon','paid_order_unclaimed','{}',0,'pending',0,?,?,?
    FROM orders o WHERE o.status='payment_confirmed' AND o.assigned_operator_id IS NULL
      AND o.payment_confirmed_at IS NOT NULL AND o.payment_confirmed_at<=?
      AND EXISTS (SELECT 1 FROM payment_verifications v WHERE v.order_id=o.id AND v.voided_at IS NULL
        AND v.amount_minor=o.total_minor AND v.currency=o.currency)`)
    .bind(now, now, now, cutoff).run();

  // Recover a worker crash before acknowledgement. A successful remote request
  // followed by a worker crash may yield a duplicate; delivery_key is stable.
  await env.DB.prepare(`UPDATE notification_outbox SET status='failed',last_error='stale_sending',updated_at=?
    WHERE template_key IN ('paid_order_priority','paid_order_unclaimed') AND status='sending' AND updated_at<?`)
    .bind(now, stale).run();

  // Never dispatch an old priority alert against a refunded/cancelled order.
  await env.DB.prepare(`UPDATE notification_outbox SET status='dead',last_error='order_ineligible',updated_at=?
    WHERE template_key IN ('paid_order_priority','paid_order_unclaimed')
      AND status IN ('pending','failed') AND order_id IN (
        SELECT id FROM orders WHERE status IN ('cancelled','refunded'))`)
    .bind(now).run();

  const rows = (await env.DB.prepare(`SELECT n.id,n.destination_key,n.template_key,n.attempt_count,
    o.public_order_id,o.total_minor,o.currency,v.provider
    FROM notification_outbox n JOIN orders o ON o.id=n.order_id
    JOIN payment_verifications v ON v.order_id=o.id AND v.voided_at IS NULL
      AND v.amount_minor=o.total_minor AND v.currency=o.currency
    WHERE n.template_key IN ('paid_order_priority','paid_order_unclaimed')
      AND n.status IN ('pending','failed') AND n.next_attempt_at<=?
      AND o.status IN (${PAID_STATUSES})
    ORDER BY n.priority ASC,n.created_at ASC,n.id ASC LIMIT 20`)
    .bind(now).all()).results || [];
  let sent = 0, failed = 0, skipped = 0;
  for (const row of rows) {
    const rawWebhook = row.destination_key === "sos-ripon"
      ? env.SOS_RIPON_ALERT_WEBHOOK
      : row.destination_key === "sos-emon" ? env.SOS_EMON_ALERT_WEBHOOK : null;
    // No webhook configured = leave pending, never claim delivered.
    let destination;
    try {
      destination = rawWebhook ? new URL(rawWebhook) : null;
    } catch { destination = null; }
    if (!destination || destination.protocol !== "https:") { skipped++; continue; }
    const claimed = await env.DB.prepare(`UPDATE notification_outbox SET status='sending',
      attempt_count=attempt_count+1,updated_at=? WHERE id=? AND status IN ('pending','failed')`)
      .bind(now, row.id).run();
    if (claimed.meta.changes !== 1) continue;
    const deliveryKey = `sos-paid-${row.id}`;
    const isEscalation = row.template_key === "paid_order_unclaimed";
    // The payload is rebuilt from allowlisted DB fields, not untrusted payload_json.
    const message = {
      text: isEscalation
        ? `SaveOnSub PAID ORDER UNCLAIMED: ${row.public_order_id} (BDT ${(row.total_minor / 100).toFixed(2)}). Check SOS staff console.`
        : `SaveOnSub VERIFIED PAID ORDER: ${row.public_order_id} (BDT ${(row.total_minor / 100).toFixed(2)}). Fulfillment action required.`,
      event: isEscalation ? "saveonsub.paid_unclaimed" : "saveonsub.payment_verified",
      order_id: row.public_order_id,
      currency: row.currency,
      provider: row.provider,
      delivery_key: deliveryKey,
    };
    try {
      const response = await send(destination.toString(), {
        method: "POST",
        headers: { "content-type": "application/json", "x-sos-event-id": deliveryKey },
        body: JSON.stringify(message),
      });
      if (!response.ok) throw new Error("destination_rejected");
      await env.DB.prepare(`UPDATE notification_outbox SET status='sent',sent_at=?,last_error=NULL,updated_at=?
        WHERE id=? AND status='sending'`).bind(now, now, row.id).run();
      sent++;
    } catch {
      // Bounded exponential retry. Never log webhook tokens, PII or references.
      const attempt = Number(row.attempt_count) + 1;
      const dead = attempt >= MAX_ATTEMPTS;
      const retryAt = new Date(clock.getTime() + Math.min(60, 2 ** attempt) * 60_000).toISOString();
      await env.DB.prepare(`UPDATE notification_outbox SET status=?,last_error='delivery_failed',
        next_attempt_at=?,updated_at=? WHERE id=? AND status='sending'`)
        .bind(dead ? "dead" : "failed", retryAt, now, row.id).run();
      failed++;
    }
  }
  return { processed: sent + failed, sent, failed, skipped };
}

