// Existing SaveOnSub scheduled notification Worker; no second Worker is required.
// Only a settlement-attested, DB-verified paid order can reach the external alert
// destinations. Unpaid order claims never interrupt Ripon or EMON.
// @ts-ignore Wrangler bundles the adjacent .mjs module without declarations.
import { dispatchPaidAlerts } from "../../sos-paid-alerts.mjs";

interface Env {
  DB: D1Database;
  SOS_RIPON_ALERT_WEBHOOK?: string;
  SOS_EMON_ALERT_WEBHOOK?: string;
  SOS_PAID_ESCALATION_MINUTES?: string;
}

export default {
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil(dispatchPaidAlerts(env));
  }
};
