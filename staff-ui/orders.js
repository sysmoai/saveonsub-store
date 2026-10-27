"use strict";

// Protected staging desk. Server-side Cloudflare Access + role checks remain the authority.
// No stored credentials, payment account numbers, OTPs, private statements or customer screenshots.
const $ = (id) => document.getElementById(id);
let operatorRole = null;
let selected = null;
let orders = [];

function notice(message, error = false) {
  const el = $("message");
  el.textContent = message;
  el.className = "message" + (error ? " error" : "");
}

function cell(text) {
  const el = document.createElement("td");
  el.textContent = String(text ?? "—");
  return el;
}

function optionButton(label, action, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.disabled = disabled;
  button.addEventListener("click", action);
  return button;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    credentials: "same-origin",
    ...options
  });
  let payload;
  try { payload = await response.json(); }
  catch { throw new Error("Protected backend unavailable or returned invalid JSON"); }
  if (!response.ok) throw new Error(payload.error || "HTTP " + response.status);
  return payload;
}

const mayClaim = () => ["owner", "manager", "fulfillment"].includes(operatorRole);

function setRole(role) {
  operatorRole = role || null;
  $("operator").textContent = "Authenticated role: " + (operatorRole || "unknown");
  const mayVerify = role === "owner"; // default backend verifier policy
  $("verifyForm").classList.toggle("desk-hidden", !mayVerify);
  $("review-lock").classList.toggle("desk-hidden", mayVerify);
  $("review-lock").textContent = mayVerify
    ? ""
    : "This role cannot attest to funds received. Owner permission required; no role bypass.";
  $("claim-role").textContent = mayClaim()
    ? "Claim and fulfillment actions are available only for server-authorized orders."
    : "This identity cannot claim or deliver orders. Do not change its role without CEO review.";
}

function choose(order) {
  if (operatorRole !== "owner" || order.status !== "payment_review") return;
  selected = order;
  $("order_id").value = order.public_order_id;
  $("selectedOrder").textContent =
    order.public_order_id + " · expected " + (Number(order.total_minor) / 100).toFixed(2) +
    " " + (order.currency || "BDT") + " (do not use this number instead of checking receipt)";
  if (["bkash", "nagad", "rocket", "bank_transfer"].includes(order.payment_method)) {
    $("provider").value = order.payment_method;
  }
  $("amount_bdt").value = "";
  $("transaction_id").value = "";
  $("evidence_ref").value = "";
  $("receipt_confirmed").checked = false;
  notice("Selected pending order. Verify a real incoming credit in your receiving account before submitting.");
  $("verifyForm").scrollIntoView({ behavior: "smooth", block: "center" });
}

async function changeOrder(order, action) {
  const endpoint = action === "claim"
    ? "/api/ops/orders/" + encodeURIComponent(order.public_order_id) + "/claim"
    : "/api/ops/orders/" + encodeURIComponent(order.public_order_id) + "/status";
  const body = action === "claim"
    ? undefined
    : JSON.stringify({ status: action, expected_status: order.status });
  notice("Submitting operator action…");
  try {
    await api(endpoint, { method: "POST", ...(body ? { headers: { "content-type": "application/json" }, body } : {}) });
    notice("Order action accepted by protected backend. Refreshing current server state.");
    await refresh();
  } catch (error) {
    notice("Action blocked: " + error.message, true);
  }
}

function render() {
  const root = $("orderRows");
  root.replaceChildren();
  $("count").textContent = orders.length + " orders";
  if (!orders.length) {
    const tr = document.createElement("tr");
    const c = cell("No orders returned by this filter. This does not prove zero historical customer sales.");
    c.colSpan = 6; tr.appendChild(c); root.appendChild(tr);
    return;
  }
  for (const order of orders) {
    const tr = document.createElement("tr");
    tr.appendChild(cell(order.public_order_id));
    const status = cell(order.status);
    status.className = order.status === "payment_review" ? "status-pending" : "status-paid";
    tr.appendChild(status);
    const value = Number(order.total_minor);
    tr.appendChild(cell(Number.isFinite(value) ? (value / 100).toFixed(2) + " " + order.currency : "—"));
    tr.appendChild(cell(order.payment_method || "—"));
    tr.appendChild(cell(order.assigned_operator_id ? "Assigned" : "Unclaimed"));

    const actions = document.createElement("td");
    const row = document.createElement("div");
    row.className = "order-row-actions";

    if (operatorRole === "owner" && order.status === "payment_review") {
      row.appendChild(optionButton("Review receipt", () => choose(order)));
    }
    if (mayClaim() && order.status === "payment_confirmed" && !order.assigned_operator_id) {
      row.appendChild(optionButton("Claim paid order", () => changeOrder(order, "claim")));
    }
    if (mayClaim() && order.status === "assigned") {
      row.appendChild(optionButton("Start fulfillment", () => changeOrder(order, "fulfilling")));
    }
    if (mayClaim() && order.status === "fulfilling") {
      row.appendChild(optionButton("Mark delivered", () => changeOrder(order, "delivered")));
    }
    if (!row.children.length) row.textContent = "No action for this role/state";
    actions.appendChild(row);
    tr.appendChild(actions);
    root.appendChild(tr);
  }
}

async function refresh() {
  try {
    const status = $("filter").value;
    const data = await api("/api/ops/orders?limit=100" + (status ? "&status=" + encodeURIComponent(status) : ""));
    setRole(data.operator?.role);
    orders = Array.isArray(data.orders) ? data.orders : [];
    render();
    notice("Protected order queue loaded. Pending payments do not trigger urgent alerts.");
  } catch (error) {
    setRole(null);
    orders = [];
    render();
    notice("Protected backend not ready: " + error.message, true);
  }
}

$("verifyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  if (operatorRole !== "owner" || !selected || selected.status !== "payment_review") {
    notice("Owner-only payment review: choose a pending order first.", true);
    return;
  }
  if (!$("receipt_confirmed").checked) {
    notice("Actual receiving-account credit must be checked first.", true);
    return;
  }
  const provider = $("provider").value;
  const amount = Number($("amount_bdt").value);
  if (!Number.isFinite(amount) || amount <= 0) {
    notice("Enter exact amount from the receiving account.", true);
    return;
  }
  const payload = {
    provider,
    transaction_id: $("transaction_id").value.trim(),
    amount_bdt: amount,
    currency: "BDT",
    evidence_ref: $("evidence_ref").value.trim(),
    receipt_confirmed: true,
    receipt_source: provider === "bank_transfer" ? "bank_statement" : "receiving_account_history"
  };
  const btn = $("verifyButton");
  btn.disabled = true;
  try {
    const result = await api("/api/ops/orders/" + encodeURIComponent(selected.public_order_id) + "/payment-verification", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
    form.reset();
    selected = null;
    $("order_id").value = "";
    $("selectedOrder").textContent = "Choose an unpaid order below";
    $("filter").value = "payment_confirmed";
    await refresh();
    notice(result.staff_notification === "queued_not_sent"
      ? "Payment verified; paid-order alert QUEUED (delivery not yet confirmed)."
      : "Verification accepted. Check notification outbox delivery separately.");
  } catch (error) {
    notice("Funds NOT marked received: " + error.message, true);
  } finally {
    btn.disabled = false;
  }
});

$("refresh").addEventListener("click", refresh);
$("filter").addEventListener("change", refresh);
setRole(null);
refresh();
