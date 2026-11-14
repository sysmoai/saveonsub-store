"use strict";
/* Customer support ticket page. Inert until assets/order-config.js sets apiBase
   (and turnstileSiteKey for creating tickets). No secrets live here. The access
   code is kept in memory only: it is never written to storage or to the URL. */
(function () {
  var cfg = window.SOS_ORDER_CONFIG || {};
  var root = document.getElementById("sp-app");
  if (!root) return;
  var T = root.getAttribute("data-lang") === "en" ? {
    off: "The online ticket system is not switched on yet. Please message us on WhatsApp for now.",
    sending: "Sending…", sent: "Ticket created. Save the access code below — it is shown only once.",
    notfound: "No ticket matches that ID and code. Check both and try again.",
    bot: "Please complete the security check first.", fail: "Something went wrong. Please try again or use WhatsApp.",
    you: "You", support: "Support", wait: "Waiting for support", status: { open: "Open", waiting_customer: "Waiting for your reply", waiting_staff: "Waiting for support", resolved: "Resolved", closed: "Closed" },
    closed: "This ticket is closed. Please open a new one.", replied: "Reply sent.", many: "This order already has the maximum number of open tickets.", msg: "Please write a message."
  } : {
    off: "অনলাইন টিকেট সিস্টেম এখনো চালু হয়নি। এখন WhatsApp-এ জানান।",
    sending: "পাঠানো হচ্ছে…", sent: "টিকেট তৈরি হয়েছে। নিচের অ্যাক্সেস কোডটি সংরক্ষণ করুন — এটি শুধু একবার দেখানো হয়।",
    notfound: "এই আইডি ও কোডের সাথে কোনো টিকেট মেলেনি। দুটোই আবার দেখে চেষ্টা করুন।",
    bot: "আগে নিরাপত্তা যাচাই সম্পন্ন করুন।", fail: "কিছু ভুল হয়েছে। আবার চেষ্টা করুন বা WhatsApp ব্যবহার করুন।",
    you: "আপনি", support: "সাপোর্ট", wait: "সাপোর্টের অপেক্ষায়", status: { open: "খোলা", waiting_customer: "আপনার উত্তরের অপেক্ষায়", waiting_staff: "সাপোর্টের অপেক্ষায়", resolved: "সমাধান হয়েছে", closed: "বন্ধ" },
    closed: "টিকেটটি বন্ধ। নতুন টিকেট খুলুন।", replied: "উত্তর পাঠানো হয়েছে।", many: "এই অর্ডারে খোলা টিকেটের সীমা পূর্ণ।", msg: "একটি বার্তা লিখুন।"
  };
  var $ = function (id) { return document.getElementById(id); };
  var live = !!cfg.apiBase;
  var tsToken = "", current = null;

  function say(el, text, bad) { el.textContent = text; el.className = "sp-msg" + (bad ? " sp-bad" : ""); }
  if (!live) { $("sp-off").hidden = false; $("sp-off").textContent = T.off; root.classList.add("sp-inert"); }
  [].forEach.call(root.querySelectorAll("form"), function (f) {
    [].forEach.call(f.elements, function (el) { if (!live) el.disabled = true; });
  });
  if (!live) return;

  function api(path, opts) {
    return fetch(String(cfg.apiBase).replace(/\/+$/, "") + path, Object.assign({ cache: "no-store", credentials: "omit" }, opts))
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (b) { return { status: r.status, body: b }; }); });
  }
  function errText(r) {
    if (r.status === 404) return T.notfound;
    var e = (r.body && r.body.error) || "";
    if (e === "BOT_CHECK_REQUIRED" || e === "BOT_CHECK_FAILED") return T.bot;
    if (e === "TOO_MANY_OPEN_TICKETS") return T.many;
    if (e === "TICKET_CLOSED") return T.closed;
    if (e === "MESSAGE_REQUIRED") return T.msg;
    return T.fail;
  }

  // Turnstile (public site key only). Loaded lazily, only when configured.
  if (cfg.turnstileSiteKey) {
    var s = document.createElement("script");
    s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"; s.async = true;
    s.onload = function () {
      window.turnstile.render("#sp-ts", { sitekey: cfg.turnstileSiteKey, callback: function (t) { tsToken = t; } });
    };
    document.head.appendChild(s);
  }

  $("sp-new").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var out = $("sp-new-msg"), btn = $("sp-new-go");
    if (!tsToken) return say(out, T.bot, true);
    btn.disabled = true; say(out, T.sending);
    api("/api/support/tickets", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({
      turnstile_token: tsToken, tracking_token: $("sp-track").value.trim(), category: $("sp-cat").value,
      subject: $("sp-subj").value, message: $("sp-text").value }) })
      .then(function (r) {
        btn.disabled = false;
        if (window.turnstile) { try { window.turnstile.reset(); } catch (e) {} } tsToken = "";
        if (r.status !== 201) return say(out, errText(r), true);
        say(out, T.sent);
        $("sp-created").hidden = false;
        $("sp-created-id").textContent = r.body.ticket_id;
        $("sp-created-code").textContent = r.body.access_token;
        $("sp-new").reset();
      }).catch(function () { btn.disabled = false; say(out, T.fail, true); });
  });

  function render(b) {
    current.status = b.status;
    $("sp-status").textContent = (T.status[b.status] || b.status);
    var box = $("sp-thread"); box.textContent = "";
    b.messages.forEach(function (m) {
      var d = document.createElement("div"); d.className = "sp-bubble " + (m.from === "you" ? "sp-you" : "sp-sup");
      var who = document.createElement("b"); who.textContent = m.from === "you" ? T.you : T.support;
      var p = document.createElement("p"); p.textContent = m.body;
      var at = document.createElement("time"); at.textContent = String(m.at || "").replace("T", " ").slice(0, 16);
      d.appendChild(who); d.appendChild(p); d.appendChild(at); box.appendChild(d);
    });
    $("sp-ticket").hidden = false;
    $("sp-reply").hidden = b.status === "closed";
  }
  $("sp-find").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var id = $("sp-id").value.trim().toUpperCase(), code = $("sp-code").value.trim(), out = $("sp-find-msg");
    say(out, T.sending);
    api("/api/support/tickets/status?ticket=" + encodeURIComponent(id), { headers: { "x-ticket-token": code } }).then(function (r) {
      if (r.status !== 200) { $("sp-ticket").hidden = true; return say(out, errText(r), true); }
      current = { id: id, code: code }; say(out, ""); render(r.body);
    }).catch(function () { say(out, T.fail, true); });
  });
  $("sp-reply").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var out = $("sp-reply-msg"), text = $("sp-reply-text").value;
    if (!current) return;
    api("/api/support/tickets/status", { method: "POST", headers: { "content-type": "application/json", "x-ticket-token": current.code },
      body: JSON.stringify({ ticket: current.id, message: text }) }).then(function (r) {
      if (r.status !== 200) return say(out, errText(r), true);
      $("sp-reply-text").value = ""; say(out, T.replied);
      return api("/api/support/tickets/status?ticket=" + encodeURIComponent(current.id), { headers: { "x-ticket-token": current.code } })
        .then(function (g) { if (g.status === 200) render(g.body); });
    }).catch(function () { say(out, T.fail, true); });
  });
})();
