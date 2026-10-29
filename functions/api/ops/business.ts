import {
  requireOperator,
  authFailure,
  type OpsEnv,
} from "../../lib/order-os/ops-auth";
import { json } from "../../lib/order-os/http";

async function readInput(
  request: Request,
): Promise<Record<string, unknown> | null> {
  const reader = request.body?.getReader();
  if (!reader) return null;
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 4096) {
        await reader.cancel();
        return null;
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const value = JSON.parse(
      new TextDecoder("utf-8", { fatal: true }).decode(bytes),
    );
    return value && typeof value === "object" && !Array.isArray(value)
      ? value
      : null;
  } catch {
    return null;
  }
}

const financial = (role: string) => ["owner", "manager"].includes(role);
const kinds = ["lead", "task", "expense", "price_review"];
// Dhaka has a fixed UTC+06 offset. Date boundaries are always server-calculated.
export function monthBounds(month: string) {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return null;
  const [y, m] = month.split("-").map(Number);
  if (y < 2020 || y > 2100) return null;
  return [
    new Date(Date.UTC(y, m - 1, 1) - 21600000).toISOString(),
    new Date(Date.UTC(y, m, 1) - 21600000).toISOString(),
  ];
}
export const onRequestGet: PagesFunction<OpsEnv> = async ({ request, env }) => {
  let actor;
  try {
    actor = await requireOperator(request, env);
  } catch (e) {
    return authFailure(e);
  }
  const month =
    new URL(request.url).searchParams.get("month") ||
    new Date(Date.now() + 21600000).toISOString().slice(0, 7);
  const range = monthBounds(month);
  if (!range) return json({ error: "INVALID_MONTH" }, 400);
  try {
    const rows = await env.DB.prepare(
      `SELECT id,kind,title,details,status,amount_minor,created_by,decided_by,created_at,updated_at
      FROM business_records WHERE kind IN ('task','price_review') OR ?=1 OR (kind='lead' AND created_by=?)
      ORDER BY updated_at DESC,id LIMIT 200`,
    )
      .bind(financial(actor.role) ? 1 : 0, actor.id)
      .all();
    // Lead contact details and private finance never leave the API for unrelated roles.
    const records = (rows.results || []).map((r: any) => ({
      ...(financial(actor.role)
        ? r
        : {
            ...r,
            details: r.created_by === actor.id ? r.details : "",
            amount_minor: r.kind === "price_review" ? r.amount_minor : 0,
            created_by: undefined,
            decided_by: undefined,
          }),
      can_transition:
        actor.role !== "viewer" &&
        (financial(actor.role) || r.created_by === actor.id),
    }));
    const data: any = {
      ok: true,
      business_unit: "saveonsub",
      month,
      timezone: "Asia/Dhaka",
      operator: { id: actor.id, name: actor.display_name, role: actor.role },
      target_bdt: 300000,
      records,
      capabilities: {
        finance: financial(actor.role),
        write: actor.role !== "viewer",
        approve: actor.role === "owner",
      },
      integrations: [
        {
          name: "Order database",
          status:
            "Connected to this staff environment; canonical production unverified",
        },
        {
          name: "WhatsApp / Meta inbox",
          status: "No inbox adapter configured; human inbox only",
        },
        {
          name: "Search Console / SEO",
          status: "No analytics adapter configured; tasks and audits only",
        },
        {
          name: "AI usage telemetry",
          status: "Not connected; limits require a dated human observation",
        },
      ],
    };
    if (financial(actor.role)) {
      const receipts = await env.DB.prepare(
        `SELECT o.public_order_id AS reference,v.amount_minor,v.verified_at AS occurred_at,o.status
        FROM payment_verifications v JOIN orders o ON o.id=v.order_id
        WHERE v.voided_at IS NULL AND v.currency='BDT' AND v.verified_at>=? AND v.verified_at<?
        ORDER BY v.verified_at DESC,v.id LIMIT 501`,
      )
        .bind(...range)
        .all<any>();
      const totals = await env.DB.prepare(
        `SELECT COALESCE(SUM(CASE WHEN o.status<>'refunded' THEN v.amount_minor ELSE 0 END),0) AS sales_minor,
        COUNT(*) AS verified_receipts,COALESCE(SUM(CASE WHEN o.status='refunded' THEN v.amount_minor ELSE 0 END),0) AS refunded_order_minor
        FROM payment_verifications v JOIN orders o ON o.id=v.order_id
        WHERE v.voided_at IS NULL AND v.currency='BDT' AND v.verified_at>=? AND v.verified_at<?`,
      )
        .bind(...range)
        .first();
      const expenses = await env.DB.prepare(
        `SELECT id AS reference,amount_minor,updated_at AS occurred_at,title FROM business_records
        WHERE kind='expense' AND status='approved' AND updated_at>=? AND updated_at<? ORDER BY updated_at DESC LIMIT 501`,
      )
        .bind(...range)
        .all();
      const expenseTotal = await env.DB.prepare(
        `SELECT COALESCE(SUM(amount_minor),0) AS amount FROM business_records
        WHERE kind='expense' AND status='approved' AND updated_at>=? AND updated_at<?`,
      )
        .bind(...range)
        .first<any>();
      const queue = await env.DB.prepare(
        `SELECT status,COUNT(*) AS count FROM orders GROUP BY status`,
      ).all();
      const audit = await env.DB.prepare(
        `SELECT a.id,a.record_id,a.actor_id,a.action,a.from_status,a.to_status,a.created_at FROM business_audit a ORDER BY a.created_at DESC,a.id LIMIT 100`,
      ).all();
      data.finance = {
        ...totals,
        approved_expenses_minor: expenseTotal?.amount || 0,
        profit_minor: null,
        basis:
          "Active verified BDT receipts in Dhaka month, excluding orders currently marked refunded. Operational sales metric; not statutory accrual revenue or proof of refund settlement. Costs incomplete; profit unavailable.",
        ledger: [
          ...(receipts.results || []).map((r: any) => ({
            ...r,
            type: "verified_receipt",
          })),
          ...(expenses.results || []).map((r: any) => ({
            ...r,
            type: "approved_expense_record",
          })),
        ],
        ledger_truncated:
          (receipts.results || []).length > 500 ||
          (expenses.results || []).length > 500,
      };
      data.order_queue = queue.results || [];
      data.audit = audit.results || [];
    }
    return json(data);
  } catch {
    return json({ error: "BUSINESS_SCHEMA_UNAVAILABLE" }, 503);
  }
};

export const onRequestPost: PagesFunction<OpsEnv> = async ({
  request,
  env,
}) => {
  let actor;
  try {
    actor = await requireOperator(request, env);
  } catch (e) {
    return authFailure(e);
  }
  if (actor.role === "viewer") return json({ error: "FORBIDDEN" }, 403);
  if (
    request.headers.get("origin") &&
    request.headers.get("origin") !== new URL(request.url).origin
  )
    return json({ error: "CROSS_ORIGIN_DENIED" }, 403);
  if (
    !(request.headers.get("content-type") || "").startsWith("application/json")
  )
    return json({ error: "JSON_REQUIRED" }, 415);
  const input = await readInput(request);
  if (
    !input ||
    Object.keys(input).some(
      (k) =>
        ![
          "action",
          "kind",
          "title",
          "details",
          "amount_bdt",
          "id",
          "status",
          "expected_status",
        ].includes(k),
    )
  )
    return json({ error: "INVALID_INPUT" }, 400);
  const ts = new Date().toISOString();
  try {
    if (input.action === "create") {
      const kind = String(input.kind || ""),
        title = String(input.title || "").trim(),
        details = String(input.details || "").trim();
      const amount = Number(input.amount_bdt || 0),
        minor = Math.round(amount * 100);
      if (
        !kinds.includes(kind) ||
        title.length < 2 ||
        title.length > 160 ||
        details.length > 1200 ||
        !Number.isSafeInteger(minor) ||
        minor < 0 ||
        minor > 100000000 ||
        Math.abs(amount * 100 - minor) > 0.00001
      )
        return json({ error: "INVALID_FIELDS" }, 400);
      if (
        ["expense", "price_review"].includes(kind) &&
        (!financial(actor.role) || minor <= 0)
      )
        return json({ error: "FINANCE_ROLE_AND_AMOUNT_REQUIRED" }, 403);
      const id = crypto.randomUUID(),
        status = ["expense", "price_review"].includes(kind)
          ? "pending"
          : "open";
      await env.DB.batch([
        env.DB.prepare(
          `INSERT INTO business_records(id,kind,title,details,status,amount_minor,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)`,
        ).bind(
          id,
          kind,
          title,
          details,
          status,
          ["expense", "price_review"].includes(kind) ? minor : 0,
          actor.id,
          ts,
          ts,
        ),
        env.DB.prepare(
          `INSERT INTO business_audit(id,record_id,actor_id,action,to_status,created_at) VALUES(?,?,?,'create',?,?)`,
        ).bind(crypto.randomUUID(), id, actor.id, status, ts),
      ]);
      return json(
        { ok: true, id, status, external_action_executed: false },
        201,
      );
    }
    if (input.action !== "transition")
      return json({ error: "INVALID_ACTION" }, 400);
    const record = await env.DB.prepare(
      "SELECT * FROM business_records WHERE id=?",
    )
      .bind(String(input.id || ""))
      .first<any>();
    if (!record) return json({ error: "NOT_FOUND" }, 404);
    if (record.status !== input.expected_status)
      return json({ error: "STALE_STATE" }, 409);
    const to = String(input.status || "");
    const approval = ["expense", "price_review"].includes(record.kind);
    if (approval) {
      if (actor.role !== "owner" || record.created_by === actor.id)
        return json({ error: "INDEPENDENT_OWNER_APPROVAL_REQUIRED" }, 403);
      if (record.status !== "pending" || !["approved", "rejected"].includes(to))
        return json({ error: "INVALID_TRANSITION" }, 409);
    } else {
      if (record.created_by !== actor.id && !financial(actor.role))
        return json({ error: "FORBIDDEN" }, 403);
      if (
        !["open", "working", "blocked", "done"].includes(to) ||
        record.status === to
      )
        return json({ error: "INVALID_TRANSITION" }, 409);
    }
    const result = await env.DB.batch([
      env.DB.prepare(
        `INSERT INTO business_audit(id,record_id,actor_id,action,from_status,to_status,created_at)
        SELECT ?,id,?,'transition',status,?,? FROM business_records WHERE id=? AND status=?`,
      ).bind(crypto.randomUUID(), actor.id, to, ts, record.id, record.status),
      env.DB.prepare(
        "UPDATE business_records SET status=?,decided_by=?,updated_at=? WHERE id=? AND status=?",
      ).bind(to, approval ? actor.id : null, ts, record.id, record.status),
    ]);
    if (!result[1].meta.changes) return json({ error: "STALE_STATE" }, 409);
    return json({ ok: true, status: to, external_action_executed: false });
  } catch {
    return json({ error: "BUSINESS_WRITE_FAILED" }, 503);
  }
};
