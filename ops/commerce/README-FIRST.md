# SaveOnSub Commerce SSOT — Phase 1 implementation

**State: PRIVATE DEVELOPMENT BRANCH. NOT DEPLOYED.**

This extends existing Order OS draft PR #50 without replacing the revenue-producing static site. The existing 72 legacy products and 138 plans are historical records, not proof of current provider authorization or sellable prices.

## Authoritative data ownership

| System | Canonical responsibility |
| --- | --- |
| Dedicated SOS Cloudflare D1 | Orders, events, products/plans, approvals, inventory, verified costs, content, agent jobs, media metadata and audit trail |
| Private SOS Cloudflare R2 | Images, original posters, video media, export versions and rights evidence pointers |
| GitHub saveonsub-store | Python generators, code, deployments, data contracts, migrations, tests and approved build snapshots |
| SaveOnSub Drive | Governance and CEO-approved decision evidence |
| Slack | Sanitized tasks, links, handoffs, alerts and approvals; NOT the order ledger |
| Replaceable Cloud PC and CORTEX | Sandboxed AI research, content drafts, development branches, tests; NOT the sole source of business records |

Customer passwords, OTP, supplier secrets, API keys and complete payment credentials must stay out of ordinary database tables, chat, Slack, Git and unprotected Drive files.

## Implemented as development code

1. ops/commerce/001_catalog_content_foundation.sql: 11 additive business tables after the existing order-os/schema.sql.
2. Staff GET/POST /api/ops/catalog: authenticated D1 draft listing and creation; body strict validation; all products start unverified and unpublishable; event logged.
3. Staff GET/POST /api/ops/media: private R2 draft image upload with 8MB limit, MIME signature check, SHA-256 digest, rights metadata, compensating cleanup and audit. Authenticated media preview at /api/ops/media/:assetId. Short video POST /api/ops/media/videos supports private 12MiB draft MP4/WebM/MOV files only, no transcoding or automatic publication; larger videos require resumable multipart upload in Phase 2.
4. staff-ui/catalog.html, catalog.css, catalog.js: mobile-first working source UI for draft product descriptions, private image and short-video upload, and authenticated media listing. NOT YET DEPLOYED; staff-ui directory is excluded from public static staging.
5. Review-only legacy product/poster importer: does not copy unverified historical BDT prices, and marks every product HOLD.
6. Brand-locked poster batch generator: three SVG draft variants (4:5, 1:1, 9:16) per product. It embeds unchanged approved assets/logo.svg bytes, excludes prices and displays INTERNAL REVIEW - NOT FOR PUBLICATION.
7. Independent GitHub Actions check: SQLite constraints, catalog hold gate, all 72 poster presence checks, JavaScript syntax, Cloudflare Pages Functions bundling and short-lived draft poster ZIP-like workflow artifact.

## Missing before safe public activation

- Connected Cloudflare owner administration and exact Pages saveonsub production SHA/rollback proof; current assistant only has GitHub code writes.
- CEO authorized dedicated D1 staging/production databases, dedicated private R2 bucket and backup/restore rehearsal.
- Cloudflare Access protecting BOTH staff UI and /api/ops/*, plus verified MFA, Access JWT issuer/audience and D1 role entry for Emon and Ripon. Never share CEO password.
- Work out a secure allowlisted way to stage the staff UI only AFTER the Access rule exists. Exclusion is intentional and safety preserving.
- PR #45 SOP, PR #50 Order OS, PR #51 static boundary, and this stacked PR must be reviewed together. Provider fact freshness currently blocks the general build. Refresh from official source, never only bump timestamps.
- Only publish products whose provider use/resale rights, pricing, inventory, refund/warranty and image rights have been approved with evidence.
- Video processing and larger/4K video uploads require secure resumable/multipart R2 flow plus media validation/transcoding. Phase 1 accepts private small draft MP4/WebM/MOV up to 12 MiB; other media are held until a verified pipeline exists.
- Full product-media association, image transformations, human review and CEO-controlled publishing automation remain next implementation milestones.
- Real customer paid-order/payment/COGS/refund data has not been reconciled; 200,000 BDT monthly net and Google #1 are unachieved business targets, not guarantees.

## First safe acceptance test

1. Emon signs in to /ops with individual MFA; Ripon uses his own account on iPhone 13 Pro; anonymous request receives 401; viewer mutation receives 403.
2. Create a draft service, verify D1 record and append-only audit. Published flag remains false, even if malicious payload requests a price or publish action.
3. Upload an authorized test PNG, compare hash in D1 and private R2; verify anonymous download fails and all public EXIF/rights checks gate release.
4. Generate three review-only poster SVGs per legacy product. Test locked logo, safe wording, clear nonpublishable watermark, integrity and formats.
5. Exercise Order OS synthetic transaction and manual payment confirmation including idempotency, support, renewal, event history, refund restrictions and outbox retries.
6. Verify Pages Functions preview, exact domain deploy SHA, searchable product URL preservation, rollback, cost alerts and backup restore before any live release.

## Revenue truth

Verified order contribution = collected settled BDT minus verified provider purchase cost, FX/payment fees, variable fulfilment and support, refunds and expected losses. Monthly net = total verified contribution minus genuine fixed overhead and applicable adjustments. UNKNOWN cost means UNKNOWN profit. Ripon's personal bike/loan and separate SYSmoAI/AIPS finances never enter the SOS company accounts.

## Review commands from repository root

python -m unittest discover -s tests -p test_commerce_ssot.py -v
python ops/commerce/tools/build_review_manifest.py
python ops/commerce/tools/generate_review_posters.py

All generated drafts stay under ops/commerce/exports, excluded from the customer website.

References:
Order OS PR: https://github.com/sysmoai/saveonsub-store/pull/50
Staging security PR: https://github.com/sysmoai/saveonsub-store/pull/51
Parent epic: https://github.com/sysmoai/saveonsub-store/issues/52
SOS Permission Manifest: https://docs.google.com/document/d/12yJMRy5BnO_gmKhdXrFjZHpefvm_ksjkr3vvaurpTK4/edit

No production or financial permission is conveyed by this document.
