import { verifyAccessRequest, type AccessEnv } from "./access-auth";

export interface OpsEnv extends AccessEnv {
  DB: D1Database;
}

export type Operator = {
  id: string;
  email: string;
  display_name: string;
  role: "owner" | "manager" | "fulfillment" | "support" | "viewer";
};

export async function requireOperator(request: Request, env: OpsEnv): Promise<Operator> {
  if (!env.DB) throw new Error("DB_NOT_CONFIGURED");
  const identity = await verifyAccessRequest(request, env);

  const operator = await env.DB.prepare(
    "SELECT id, email, display_name, role FROM operators WHERE lower(email)=? AND active=1"
  ).bind(identity.email).first<Operator>();

  if (!operator) throw new Error("OPERATOR_NOT_AUTHORIZED");

  await env.DB.prepare("UPDATE operators SET last_seen_at=?, updated_at=? WHERE id=?")
    .bind(new Date().toISOString(), new Date().toISOString(), operator.id)
    .run();

  return operator;
}

export function canTransition(role: Operator["role"], from: string, to: string) {
  if (role === "viewer") return false;
  if (role === "support") return to === "support_open" || to === "completed";
  if (role === "fulfillment") {
    return [
      "payment_review->assigned",
      "payment_confirmed->assigned",
      "assigned->fulfilling",
      "fulfilling->delivered",
      "delivered->completed",
      "delivered->support_open",
    ].includes(`${from}->${to}`);
  }
  return true;
}
