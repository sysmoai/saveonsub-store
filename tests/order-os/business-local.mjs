// Loopback-only SYNTHETIC review server. Never a deployment entry point.
// Runs real Pages Functions + JWT verification with generated TEST keys and local SQLite.
import { createServer } from "node:http";
import { readFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { resolve, extname } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { makeWorld, handler, signJwt, OPERATORS } from "./harness.mjs";
const root = resolve(import.meta.dirname, "../..");
const local = resolve(root, ".local");
mkdirSync(local, { recursive: true });
const path = resolve(local, "business-synthetic.sqlite");
const fresh = !existsSync(path);
const w = await makeWorld();
w.db.db.close();
w.db.db = new DatabaseSync(path);
w.db.db.exec(readFileSync(resolve(root, "ops/order-os/schema.sql"), "utf8"));
w.db.db.exec(
  readFileSync(resolve(root, "ops/order-os/business-schema.sql"), "utf8"),
);
const ts = new Date().toISOString();
for (const [name, op] of Object.entries(OPERATORS))
  w.db.run(
    "INSERT OR IGNORE INTO operators(id,email,display_name,role,active,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
    op.id,
    op.email,
    "TEST " + name,
    op.role,
    op.active ?? 1,
    ts,
    ts,
  );
if (fresh) {
  const a = w.seedOrder({ status: "payment_confirmed", total: 150000 });
  w.db.run(
    "UPDATE payment_verifications SET verified_at=? WHERE order_id=?",
    ts,
    a.id,
  );
  w.seedOrder({ total: 59900 });
  await w.call("api/ops/business.ts", "onRequestPost", "manager", {
    body: {
      action: "create",
      kind: "expense",
      title: "SYNTHETIC: review invoice",
      details: "Synthetic test evidence only",
      amount_bdt: 125,
    },
  });
  await w.call("api/ops/business.ts", "onRequestPost", "owner", {
    body: {
      action: "create",
      kind: "task",
      title: "Codex: verify Business OS release",
      details:
        "Synthetic local task. Production blocked by D1, Access and owner release approval.",
    },
  });
}
const mime = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
};
const server = createServer(async (req, res) => {
  const origin = "http://127.0.0.1:8788";
  if (req.headers.host !== "127.0.0.1:8788") {
    res.writeHead(403);
    return res.end("LOOPBACK_ONLY");
  }
  if (req.headers.origin && req.headers.origin !== origin) {
    res.writeHead(403);
    return res.end("ORIGIN_DENIED");
  }
  try {
    const url = new URL(req.url, origin);
    if (url.pathname.startsWith("/api/")) {
      let file,
        params = {};
      if (url.pathname === "/api/ops/business") file = "api/ops/business.ts";
      else if (url.pathname === "/api/ops/orders")
        file = "api/ops/orders/index.ts";
      else {
        const m = url.pathname.match(
          /^\/api\/ops\/orders\/([^/]+)\/(events|claim|status|payment-verification|reversal)$/,
        );
        if (m) {
          file = `api/ops/orders/[orderId]/${m[2]}.ts`;
          params = { orderId: decodeURIComponent(m[1]) };
        }
      }
      if (!file) {
        res.writeHead(404);
        return res.end(
          JSON.stringify({ error: "NOT_CONNECTED_IN_LOCAL_REVIEW" }),
        );
      }
      let chunks = [],
        size = 0;
      for await (const chunk of req) {
        size += chunk.length;
        if (size > 8192) {
          res.writeHead(413);
          return res.end();
        }
        chunks.push(chunk);
      }
      const headers = new Headers({
        "content-type": "application/json",
        "cf-access-jwt-assertion": await signJwt(w.keys, {
          email: OPERATORS.owner.email,
        }),
      });
      if (req.headers.origin) headers.set("origin", req.headers.origin);
      const request = new Request(url, {
        method: req.method,
        headers,
        ...(["GET", "HEAD"].includes(req.method)
          ? {}
          : { body: Buffer.concat(chunks) }),
      });
      const fn = await handler(
        file,
        req.method === "GET" ? "onRequestGet" : "onRequestPost",
      );
      if (!fn) {
        res.writeHead(405);
        return res.end();
      }
      const response = await fn({ request, env: w.env, params });
      let data = await response.json();
      if (file === "api/ops/business.ts" && req.method === "GET" && response.ok)
        data.environment_label =
          "LOCAL SYNTHETIC REVIEW · persistent test database · no live customer data";
      res.writeHead(response.status, Object.fromEntries(response.headers));
      return res.end(JSON.stringify(data));
    }
    const name =
      url.pathname === "/"
        ? "business.html"
        : decodeURIComponent(url.pathname).replace(/^\//, "");
    const file = resolve(root, "staff-ui", name);
    if (
      !file.startsWith(resolve(root, "staff-ui") + "/") &&
      !file.startsWith(resolve(root, "staff-ui") + "\\")
    ) {
      res.writeHead(404);
      return res.end();
    }
    if (!existsSync(file) || !statSync(file).isFile()) {
      res.writeHead(404);
      return res.end();
    }
    res.writeHead(200, {
      "content-type": mime[extname(file)] || "application/octet-stream",
      "cache-control": "no-store",
      "content-security-policy":
        "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
      "x-content-type-options": "nosniff",
    });
    res.end(readFileSync(file));
  } catch (e) {
    console.error(e.message);
    res.writeHead(500);
    res.end("LOCAL_REVIEW_ERROR");
  }
});
server.listen(8788, "127.0.0.1", () =>
  console.log("Synthetic review: http://127.0.0.1:8788/business.html"),
);
