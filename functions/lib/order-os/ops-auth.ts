import { verifyAccessRequest, type AccessEnv } from "./access-auth";
import { canTransition as workflowCanTransition, type Role } from "./order-workflow";
import { json } from "./http";

export interface OpsEnv extends AccessEnv {
  DB: D1Database;
}

export type Operator = {
  id: string;
  email: string;
  display_name: string;
  role: Role;
};

// Internal reason codes (log only) are mapped to a small set of client-facing
// answers so token/config details are never echoed back to the caller.
export class OpsAuthError extends Error {
  status: 401 | 403 | 503;
  publicCode: string;
  reason: string;
  constructor(status: 401 | 403 | 503, publicCode: string, reason: string) {
    super(reason);
    this.status = status;
    this.publicCode = publicCode;
    this.reason = reason;
  }
}

export async function requireOperator(request: Request, env: OpsEnv): Promise<Operator> {
  if (!env.DB) throw new OpsAuthError(503, "STAFF_BACKEND_NOT_CONFIGURED", "DB_NOT_CONFIGURED");

  let identity;
  try {
    identity = await verifyAccessRequest(request, env);
  } catch (e) {
    const reason = e instanceof Error ? e.message : "ACCESS_UNKNOWN";
    if (reason === "ACCESS_NOT_CONFIGURED") throw new OpsAuthError(503, "STAFF_BACKEND_NOT_CONFIGURED", reason);
    if (reason === "ACCESS_JWKS_UNAVAILABLE") throw new OpsAuthError(503, "STAFF_AUTH_UNAVAILABLE", reason);
    throw new OpsAuthError(401, "UNAUTHENTICATED", reason);
  }

  let operator: Operator | null;
  try {
    operator = await env.DB.prepare(
      "SELECT id, email, display_name, role FROM operators WHERE lower(email)=? AND active=1"
    ).bind(identity.email).first<Operator>();
  } catch {
    throw new OpsAuthError(503, "STAFF_BACKEND_UNAVAILABLE", "OPERATOR_LOOKUP_FAILED");
  }
  if (!operator) throw new OpsAuthError(403, "FORBIDDEN", "OPERATOR_NOT_AUTHORIZED");

  // Presence tracking is best-effort and must never block an authorised request.
  try {
    const ts = new Date().toISOString();
    await env.DB.prepare("UPDATE operators SET last_seen_at=?, updated_at=? WHERE id=?")
      .bind(ts, ts, operator.id).run();
  } catch {
    console.warn("operator_last_seen_update_failed");
  }
  return operator;
}

// Maps any error thrown while authenticating to a safe response.
export function authFailure(e: unknown): Response {
  if (e instanceof OpsAuthError) {
    console.warn("ops_auth_denied", e.reason);
    return json({ error: e.publicCode }, e.status);
  }
  console.error("ops_auth_unexpected");
  return json({ error: "STAFF_BACKEND_UNAVAILABLE" }, 503);
}

// Kept for existing imports; the rules live in order-workflow.ts.
export function canTransition(role: Operator["role"], from: string, to: string) {
  return workflowCanTransition(role, from, to);
}
