# SaveOnSub - Live Measurement Gap and Rollout Verification (Review Only)

Checked: 2026-11-10 (Asia/Dhaka)
Status: DRAFT / NOT DEPLOYED / NO PRODUCTION CHANGES

## Independently verified

Fresh public URL fetch at https://saveonsub.com/ with cache tolerance 0:
- Main homepage and https://saveonsub.com/p/chatgpt-plus served content.
- https://saveonsub.com/assets/measurement.js served older content, missing GitHub's new order-submit and Meta attribution logic.
- https://saveonsub.com/assets/meta-pixel.js returned HTTP 404.
- https://saveonsub.com/assets/ga4.js returned HTTP 404.

These observations show tested public assets are not serving the PR #114 tracking implementation. They do NOT establish exact Cloudflare deployment SHA, absence of another tracker, actual browser cookie behavior or received Meta/GA4 events.

## Source and QA

- Main PR #114 merged: https://github.com/sysmoai/saveonsub-store/pull/114
- This draft #116 corrects explicit-consent gating and adds a synthetic Node browser lifecycle test and static regression assertions.
- GitHub Actions at commit 61519170556aebed177db8fd15126f147ffdbb48: https://github.com/sysmoai/saveonsub-store/actions/runs/42737581358 - success.
- CI pass is NOT permission to merge or publish.
- The canonical release workflow in main remains disabled under the owner-approved release freeze. No deploy without exact-SHA CEO authorization and verified release/rollback topology.

## Owner-approved release and QA checklist (not performed)

1. Establish exact reviewed SHA; verify canonical Cloudflare source route, current deployed SHA, and rollback plan.
2. After separately authorized merge/release, confirm HTTP 200 and JavaScript MIME/content parity for /assets/measurement.js, /assets/meta-pixel.js and /assets/ga4.js; verify script inclusion and cache behavior.
3. Inspect fresh browser with local storage cleared: undecided, Decline, GPC, DNT must not fire Meta/GA; Accept once; reset must revoke; reaccept/reload should behave correctly. Synthetic test alone is not sufficient.
4. With tester consent run Meta Events Manager Test Events and GA4 DebugView; verify PageView, ViewContent, Contact, Lead events correspond to real actions. Click or checkout must not count as Purchase.
5. Confirm Purchase only after merchant-verified SaveOnSub payment, correct event IDs, deduplication and privacy-safe matching. Never print payment credentials.
6. Smoke-test exact Cloudflare domain, prices, SEO canonicals, source exclusion and rollback.
7. Keep paid Meta acquisition on HOLD until provider rights, actual contribution margin and meta account data source pass. Related launch gate in draft PR #118.

No production deploy, merge, spend, billing, DNS, customer data or provider account write.
