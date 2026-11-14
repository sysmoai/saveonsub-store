"use strict";
// Private staging ticket desk. Server-side Cloudflare Access + role checks remain the authority;
// this UI only hides controls a role cannot use. All text is rendered with textContent.
const $ = (id) => document.getElementById(id);
let role = null, tickets = [], current = null;

function notice(m, bad = false) { const el = $("message"); el.textContent = m; el.className = "message" + (bad ? " error" : ""); }
async function api(path, options = {}) {
  const r = await fetch(path, { cache: "no-store", credentials: "same-origin", ...options });
  let p; try { p = await r.json(); } catch { throw new Error("Protected backend unavailable or returned invalid JSON"); }
  if (!r.ok) throw new Error(p.error || "HTTP " + r.status);
  return p;
}
const post = (path, body) => api(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
const mayReply = () => ["owner", "manager", "support"].includes(role);
const mayAssign = () => ["owner", "manager"].includes(role);

function td(text) { const c = document.createElement("td"); c.textContent = String(text ?? "—"); return c; }
function setRole(r) {
  role = r || null;
  $("operator").textContent = "Authenticated role: " + (role || "unknown");
  $("newForm").classList.toggle("desk-hidden", !mayReply());
  $("new-lock").classList.toggle("desk-hidden", mayReply());
  $("replyForm").classList.toggle("desk-hidden", !mayReply());
  $("actions").classList.toggle("desk-hidden", !mayReply());
  $("assignWrap").classList.toggle("desk-hidden", !mayAssign());
  $("assignBtn").classList.toggle("desk-hidden", !mayAssign());
}
function renderRows() {
  const tb = $("rows"); tb.textContent = "";
  tickets.forEach((t) => {
    const tr = document.createElement("tr");
    const id = td((t.escalated ? "⚠ " : "") + t.ticket_id); if (t.escalated) id.className = "tk-esc";
    tr.appendChild(id); tr.appendChild(td(t.category)); tr.appendChild(td(t.status)); tr.appendChild(td(t.order_id || (t.verification === "unverified" ? "no order" : "—")));
    const b = document.createElement("button"); b.type = "button"; b.textContent = "Open"; b.addEventListener("click", () => openTicket(t.ticket_id));
    const c = document.createElement("td"); c.appendChild(b); tr.appendChild(c); tb.appendChild(tr);
  });
  if (!tickets.length) { const tr = document.createElement("tr"); const c = td("No tickets visible to this role."); c.colSpan = 5; tr.appendChild(c); tb.appendChild(tr); }
}
async function refresh() {
  try {
    const s = $("filter").value;
    const d = await api("/api/ops/tickets?limit=100" + (s ? "&status=" + encodeURIComponent(s) : ""));
    setRole(d.operator && d.operator.role); tickets = d.tickets || []; renderRows(); notice("Protected ticket queue loaded.");
  } catch (e) { setRole(null); tickets = []; renderRows(); notice("Protected backend not ready: " + e.message, true); }
}
async function openTicket(id) {
  try {
    const d = await api("/api/ops/tickets/" + encodeURIComponent(id));
    current = d.ticket.ticket_id;
    $("detail").classList.remove("desk-hidden"); $("codeBox").classList.add("desk-hidden");
    $("detail-sub").textContent = d.ticket.ticket_id + " · " + d.ticket.category + " · " + d.ticket.status;
    $("meta").textContent = [
      "Order: " + (d.ticket.order_id || "none"),
      "Verification: " + d.ticket.verification + (d.ticket.verification_method ? " (" + d.ticket.verification_method + ")" : ""),
      "Customer: " + (d.ticket.customer_name || "hidden for this role"),
      "Assigned: " + (d.ticket.assigned_to || "unassigned"),
      d.ticket.escalated ? "ESCALATED: " + (d.ticket.escalation_reason || "") : ""
    ].filter(Boolean).join(" · ");
    const th = $("thread"); th.textContent = "";
    d.messages.forEach((m) => {
      const b = document.createElement("div"); b.className = "tk-bubble " + m.from;
      const w = document.createElement("small"); w.textContent = m.from + (m.by ? " (" + m.by + ")" : "") + " · " + m.type + " · " + String(m.at).replace("T", " ").slice(0, 16);
      const p = document.createElement("p"); p.textContent = m.body || "";
      b.appendChild(w); b.appendChild(p); th.appendChild(b);
    });
  } catch (e) { notice(e.message, true); }
}
async function act(body, okMsg) {
  if (!current) return;
  try { const r = await post("/api/ops/tickets/" + encodeURIComponent(current), body); notice(okMsg); await refresh(); await openTicket(current); return r; }
  catch (e) { notice(e.message, true); }
}
$("filter").addEventListener("change", refresh);
$("replyForm").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const b = {}; if ($("replyText").value.trim()) b.message = $("replyText").value; if ($("replyStatus").value) b.status = $("replyStatus").value;
  if (!Object.keys(b).length) return notice("Write a reply or choose a status.", true);
  const r = await act(b, "Saved."); if (r) $("replyText").value = "";
});
$("escBtn").addEventListener("click", () => { const v = $("escReason").value.trim(); if (!v) return notice("Escalation needs a reason.", true); act({ escalate: v }, "Escalated."); });
$("assignBtn").addEventListener("click", () => { const v = $("assignTo").value.trim(); if (!v) return notice("Enter an operator id.", true); act({ assign_to: v }, "Assigned."); });
$("rotateBtn").addEventListener("click", async () => {
  const r = await act({ rotate_code: true }, "New code issued; the old code no longer works.");
  if (r && r.access_code) { $("codeVal").textContent = r.access_code; $("codeBox").classList.remove("desk-hidden"); }
});
$("newForm").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const order = $("n_order").value.trim();
  const body = { category: $("n_cat").value, subject: $("n_subj").value, message: $("n_msg").value };
  if (order) { body.order_id = order; body.verification_method = $("n_method").value; body.verified = $("n_verified").checked; }
  try {
    const r = await post("/api/ops/tickets", body);
    $("newId").textContent = r.ticket_id; $("newCodeVal").textContent = r.access_code; $("newCode").classList.remove("desk-hidden");
    $("n_msg").value = ""; $("n_subj").value = ""; notice("Ticket created (" + r.verification + ")."); refresh();
  } catch (e) { notice(e.message, true); }
});
refresh();
