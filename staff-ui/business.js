"use strict";
const byId = (id) => document.getElementById(id);
const money = (minor) =>
  "৳" +
  new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(
    Number(minor) / 100,
  );
let state = null;
const titles = {
  overview: "Business overview",
  orders: "Orders & payments",
  crm: "Customer relationships",
  finance: "Finance ledger",
  pricing: "Product & pricing",
  growth: "SEO & marketing",
  agents: "Agent operations",
  approvals: "Approvals & audit",
  connections: "Connections",
};
function view(name) {
  document.querySelectorAll(".view").forEach((e) => (e.hidden = e.id !== name));
  document.querySelectorAll("[data-view]").forEach((e) => {
    if (e.dataset.view === name) e.setAttribute("aria-current", "page");
    else e.removeAttribute("aria-current");
  });
  byId("viewTitle").textContent = titles[name];
}
document
  .querySelectorAll("[data-view],[data-go]")
  .forEach((e) =>
    e.addEventListener("click", () => view(e.dataset.view || e.dataset.go)),
  );
function notice(text, error = false) {
  byId("notice").textContent = text;
  byId("notice").classList.toggle("error", error);
}
async function api(options) {
  const r = await fetch(
    "/api/ops/business" +
      (options ? "" : "?month=" + encodeURIComponent(byId("month").value)),
    { cache: "no-store", credentials: "same-origin", ...(options || {}) },
  );
  let b;
  try {
    b = await r.json();
  } catch {
    throw Error(
      "Staff backend did not return JSON. Sign in through the protected staff host.",
    );
  }
  if (!r.ok) throw Error(b.error || "BACKEND_UNAVAILABLE");
  return b;
}
function text(tag, value, cls) {
  const e = document.createElement(tag);
  e.textContent = String(value ?? "");
  if (cls) e.className = cls;
  return e;
}
function rows(id, data, cols) {
  const body = byId(id);
  body.replaceChildren();
  for (const item of data) {
    const tr = document.createElement("tr");
    cols.forEach((k) => tr.append(text("td", k(item))));
    body.append(tr);
  }
  if (!data.length) {
    const tr = document.createElement("tr"),
      td = text("td", "No accessible records in this environment.");
    td.colSpan = cols.length;
    tr.append(td);
    body.append(tr);
  }
}
function recordList(id, records) {
  const root = byId(id);
  root.replaceChildren();
  if (!records.length) {
    root.append(text("p", "No accessible records yet.", "empty"));
    return;
  }
  for (const r of records) {
    const el = text("div", "", "record");
    el.append(
      text("div", r.kind.replace("_", " ") + " · " + r.status, "tag"),
      text("h3", r.title),
    );
    if (r.details) el.append(text("p", r.details));
    if (r.amount_minor) el.append(text("p", money(r.amount_minor)));
    const actions = text("div", "", "actions");
    let choices = [];
    if (state.capabilities.write) {
      if (["expense", "price_review"].includes(r.kind)) {
        if (
          state.capabilities.approve &&
          r.status === "pending" &&
          r.created_by !== state.operator.id
        )
          choices = ["approved", "rejected"];
      } else if (r.can_transition)
        choices = ["open", "working", "blocked", "done"].filter(
          (s) => s !== r.status,
        );
    }
    choices.forEach((status) => {
      const b = text("button", status);
      b.type = "button";
      b.addEventListener("click", async () => {
        b.disabled = true;
        try {
          await api({
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({
              action: "transition",
              id: r.id,
              expected_status: r.status,
              status,
            }),
          });
          await refresh();
          notice("State recorded. No external action executed.");
        } catch (e) {
          notice(e.message, true);
          b.disabled = false;
        }
      });
      actions.append(b);
    });
    el.append(actions);
    root.append(el);
  }
}
function render() {
  const s = state;
  byId("identity").textContent = s.operator.name + " · " + s.operator.role;
  byId("environment").textContent =
    s.environment_label ||
    "Authenticated staff environment · production unverified";
  const f = s.finance;
  byId("sales").textContent = f ? money(f.sales_minor) : "Restricted";
  byId("remaining").textContent = f
    ? money(Math.max(0, 30000000 - f.sales_minor))
    : "Restricted";
  byId("progress").value = f ? f.sales_minor / 100 : 0;
  byId("progressLabel").textContent = f
    ? ((f.sales_minor / 30000000) * 100).toFixed(1) + "% of monthly target"
    : "Owner / manager access required";
  byId("pace").textContent = f
    ? "Period: " + s.month + " · Asia/Dhaka · no guaranteed forecast"
    : "Finance metrics are restricted by role.";
  const count = (status) =>
    (s.order_queue || []).find((x) => x.status === status)?.count || 0;
  byId("reviewCount").textContent = f ? count("payment_review") : "Restricted";
  byId("pendingCount").textContent =
    s.records.filter((r) => r.status === "pending").length +
    " pending reviews (loaded records)";
  const tasks = s.records.filter((r) => r.kind === "task");
  recordList("overviewTasks", tasks.slice(0, 4));
  recordList("taskList", tasks);
  recordList(
    "growthList",
    tasks.filter((r) => r.title.startsWith("Growth:")),
  );
  recordList(
    "leadList",
    s.records.filter((r) => r.kind === "lead"),
  );
  recordList(
    "priceList",
    s.records.filter((r) => r.kind === "price_review"),
  );
  recordList(
    "approvalList",
    s.records.filter((r) => ["expense", "price_review"].includes(r.kind)),
  );
  byId("financeBasis").textContent = f
    ? f.basis
    : "Owner or manager access required.";
  byId("expenseTotal").textContent = f
    ? "Approved expense records: " +
      money(f.approved_expenses_minor) +
      (f.ledger_truncated
        ? " · Detail list truncated; totals include all records."
        : "")
    : "";
  rows("ledgerRows", f?.ledger || [], [
    (r) => r.reference,
    (r) => r.type.replaceAll("_", " "),
    (r) => money(r.amount_minor),
    (r) => r.occurred_at,
  ]);
  rows("auditRows", s.audit || [], [
    (r) => r.created_at,
    (r) => r.actor_id,
    (r) => r.action,
    (r) => (r.from_status || "new") + " → " + r.to_status,
  ]);
  const queue = byId("orderQueue");
  queue.replaceChildren();
  for (const r of s.order_queue || []) {
    const a = text("article", "");
    a.append(
      text("span", r.status.replaceAll("_", " ")),
      text("strong", r.count),
    );
    queue.append(a);
  }
  const connections = byId("integrationList");
  connections.replaceChildren();
  for (const i of s.integrations) {
    const e = text("div", "", "record");
    e.append(text("h3", i.name), text("p", i.status));
    connections.append(e);
  }
  document.querySelectorAll("form").forEach((form) => {
    const isFinance = ["expense", "price_review"].includes(form.dataset.kind);
    form
      .querySelectorAll("button,input,textarea")
      .forEach(
        (e) =>
          (e.disabled =
            !s.capabilities.write || (isFinance && !s.capabilities.finance)),
      );
  });
}
async function refresh() {
  notice("Loading verified staff records…");
  try {
    state = await api();
    render();
    notice(
      state.environment_label ||
        "Protected database loaded. External integrations and historical imports remain unverified.",
    );
  } catch (e) {
    state = null;
    byId("identity").textContent = "Staff identity not verified";
    byId("environment").textContent = "Disconnected · actions locked";
    document
      .querySelectorAll("form button")
      .forEach((b) => (b.disabled = true));
    ["sales", "remaining", "reviewCount"].forEach(
      (id) => (byId(id).textContent = "Unavailable"),
    );
    byId("progress").value = 0;
    byId("progressLabel").textContent = "Connection unavailable";
    document.querySelectorAll(".record").forEach((e) => e.remove());
    byId("ledgerRows").replaceChildren();
    byId("auditRows").replaceChildren();
    byId("orderQueue").replaceChildren();
    byId("financeBasis").textContent =
      "Finance unavailable until authenticated refresh succeeds.";
    byId("expenseTotal").textContent = "";
    notice(
      "Connection blocked: " +
        e.message +
        ". No demo fallback or inferred revenue.",
      true,
    );
  }
}
document.querySelectorAll("form").forEach((form) =>
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state) return;
    const d = new FormData(form),
      b = form.querySelector("button");
    b.disabled = true;
    try {
      await api({
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          action: "create",
          kind: form.dataset.kind,
          title: (d.get("prefix") || "") + d.get("title"),
          details: d.get("details") || "",
          amount_bdt: d.get("amount_bdt") || 0,
        }),
      });
      form.reset();
      await refresh();
      notice(
        "Record saved to this staff database. No publication, message or money movement executed.",
      );
    } catch (err) {
      notice(err.message, true);
    } finally {
      b.disabled = !state;
    }
  }),
);
byId("month").value = new Date(Date.now() + 21600000).toISOString().slice(0, 7);
byId("refresh").addEventListener("click", refresh);
byId("month").addEventListener("change", refresh);
refresh();
