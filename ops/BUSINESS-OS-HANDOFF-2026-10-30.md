# SaveOnSub Business OS — shared technical SSOT

Date: 2026-10-30, Asia/Dhaka. Scope: SaveOnSub ONLY. No private business records belong in this public repository.

## Ownership and source

- Codex branch: `codex/business-os-2026-10-30`.
- Parent: `feature/sos-payment-first-manual-rails-2026-10-28` at `9108133` (draft PR #71, stacked on #67/#66/#65).
- Codex owns `staff-ui/business.*`, `functions/api/ops/business.ts`, `ops/order-os/business-schema.sql`, business tests and this handoff.
- Claude retains brand PR #74 and Meta PR #73. Neither was merged, edited or deployed by this work.
- Coordination was sent to the existing SaveOnSub Claude project; Claude confirmed no deployed admin and no conflicting edits in the owned files. Its account indicator is a point-in-time observation, not monitored telemetry.
- Repository is the technical SSOT; the dedicated private SaveOnSub D1 is the operational SSOT after activation. Local synthetic SQLite is QA evidence only. No customer, statement, supplier-cost, credential or sister-business records were imported.

## Implemented behavior

- Private staff home: `business.html`, with overview, CRM, orders/payments, operating ledger, product-price proposals, growth tasks, agent work, approvals/audit and connection status.
- Target fixed to **BDT 300,000 monthly REVENUE**, not net profit. Reporting uses Asia/Dhaka calendar boundaries.
- Sales metric: all active verified BDT receipts in the selected month, excluding orders currently marked refunded. Unpaid claims never count. This is an operational receipts-based sales measure, not statutory revenue recognition. Historical status changes can restate the figure. Refund status is not proof of settled money movement.
- Ledger combines verified receipts and independently approved expense records. Profit stays unavailable because complete COGS, fees, refund settlements and expenses are not connected. This is not a full double-entry accounting package.
- Persisted leads and tasks with server-authorized state changes. Owner/manager can see CRM; other staff see their own leads. Viewer cannot write. Unrelated roles cannot see finance, private lead details or audit actor identities.
- Expense and price-review proposals require a different owner to approve/reject. Decisions are immutable, with atomic compare-and-set updates and append-only audit. Approving a price proposal does not publish it. Expense approval records accounting intent/evidence; it does not pay anyone.
- Existing protected payment receipt/claim/fulfillment UI and server state machine are retained. Business UI links to `orders.html` and `catalog.html`.
- No WhatsApp inbox, Meta inbox, Search Console or AI quota API is connected. Connections tab says so. Growth/agent tasks work; telemetry and external delivery are not simulated as live.
- Staff responses use existing Access JWT verification + active operator lookup. No credential or auth bypass was added to deployable functions. Streamed body limit, same-origin mutation checks, DOM text rendering and no-store/noindex headers are included.
- `.local/` is ignored by Git and excluded from the public storefront staging pipeline. The dashboard/private SQL/API/tests are also excluded from `_site/`. Exact currently locked logo bytes are copied into staff assets; PR #74's pending replacement is untouched.

## Verification (local)

- **94/94** real-handler security/workflow tests passed: minted synthetic RSA JWTs and SQLite, including five new business scenarios for auth/redaction, independent approval, stale races, bounded input and Dhaka revenue boundaries.
- Existing commerce schema tests: **7/7** passed.
- JavaScript syntax, price checks, repository audit, preflight and Order OS audit passed.
- `wrangler@4 pages functions build functions` compiled successfully, without credentials or deployment.
- Canonical `build_site.py` completed successfully on inherited HOLD data. This does **not** make the catalog saleable or authorize release.
- Public stage after the final `.local` exclusion: no `.local`, staff UI, ops, functions, workers, tests or SQLite/SQL/TS/MJS in the public artifact. Approved staff logo bytes equal the locked source.
- Browser at `http://127.0.0.1:8788/business.html`: synthetic lead created, moved to working, independent synthetic expense approved and present in the ledger; audit showed each action. Server restarted and browser reloaded: CRM and expense decision persisted. Desktop screenshot is local-only under `.local/`.
- Fixed two inherited test-fixture issues: redaction tests now actually satisfy receipt attestation, rather than exercising refused verification; audit checks paid alert queueing in the verified-payment handler, not unpaid public submission.
- Remote CI and Cloudflare-hosted staging acceptance must be verified separately. Local tests do not establish live Access configuration, operator enrollment, D1 bindings, notification delivery or production health.

## Run the isolated review locally

Requires installed Node 24 (built-in TypeScript and SQLite).

```powershell
node --import ./tests/order-os/register.mjs tests/order-os/business-local.mjs
```

Open `http://127.0.0.1:8788/business.html`. The loopback-only test server uses generated TEST keys, an injected synthetic owner and a persistent `.local/business-synthetic.sqlite`. All displayed transactions and operators are synthetic. It is NOT a production login or supported deployment server. Never expose it on a LAN, tunnel or public host. No production code imports this server or the test harness.

```powershell
node --import ./tests/order-os/register.mjs --test tests/order-os/*.test.mjs
python -m unittest discover -s tests -p test_commerce_ssot.py -q
python audit_order_os.py
```

## Ordered activation gates

1. Review this stacked diff and dependencies #65/#66/#67/#71. Issue **#69 remains open**: the inherited source has zero sellable governed plans. Do not restore stale/shared/unauthorized offers. Obtain SKU rights, current prices, costs and support terms from the owner before enabling sales.
2. CEO approves a **separate** `saveonsub-staff-staging` Pages project and **dedicated** `saveonsub-order-os` D1 on the approved account. No new VPS or paid service required by this code. Free-tier eligibility and account quotas must be checked before creating resources. Never bind another business's DB or bucket.
3. Owner confirms exact staff identity/roles and Access application/audience. Protect the entire staff host (including preview aliases) before real data. Keep owner receipt verification narrow; do not silently promote Ripon or any AI identity. Actual role enrollment/new access requires approval.
4. Back up any existing dedicated DB. Review/apply `schema.sql`, `ops/commerce/001_catalog_content_foundation.sql`, then additive `business-schema.sql` in staging. Verify existing table compatibility first. The business extension does not rewrite old rows. Private media needs a separately approved SOS-only R2 binding if that module is activated; dashboard alone does not need R2.
5. Set `DB`, `TEAM_DOMAIN`, `POLICY_AUD` through the authorized account, never in source/chat. Existing `wrangler.order-os.toml` intentionally has no live DB ID. Do not guess identifiers or use the storefront project. D1 bindings, Access policy changes and remote migrations remain owner-gated.
6. Before release, test the actual Cloudflare Access login, invalid/expired JWT, active roles, denial of sister-business identities, CRM redaction, owner/manager finance, self-approval rejection, lost races, audit persistence, duplicate references, rollback/restore and private-source exclusion. Set up two distinct authorized reviewers for independent financial approval; one owner can approve a manager's request, but cannot approve their own.
7. Repair the canonical deployment credential only through owner-approved credential handling. Run the canonical approved pipeline and exact-project smoke tests. A main merge can auto-deploy; **do not merge or deploy without an explicit release record**. Existing website stays untouched by this branch.
8. Connect verified SOS-only WhatsApp/Meta destinations, approved notification hooks and Search Console property only after authorization. Test delivery and deduplication with synthetic data. An open logged-in browser is not an API connection. No automated spend, customer send, credential delivery or refund is authorized by dashboard approval buttons.

## Rollback and limits

- No production rollout occurred, so current rollback is simply to stop the local review and leave the draft unmerged. Local synthetic records remain in the ignored SQLite file.
- For a future staging release, retain previous Pages deployment and DB backup before migrations. Roll back code first; preserve audit/financial records. Do not drop business tables to undo UI code.
- Records list is capped at the most recent 200; audit at 100, ledger detail at 501 per source with truncation notice. Financial totals use uncapped SQL aggregates. Full history search/pagination/export is future work; no bulk customer export endpoint is supplied.
- No scheduled task runner, live agent execution, usage-limit enforcement, recurring marketing publication or full accounting close is claimed.
- Cloudflare D1 is available on Free with limits; usage exceeding free quotas fails rather than implying unlimited infrastructure. Review current official pricing: https://developers.cloudflare.com/d1/platform/pricing/ and limits: https://developers.cloudflare.com/d1/platform/limits/ . No spend or subscription was created.
