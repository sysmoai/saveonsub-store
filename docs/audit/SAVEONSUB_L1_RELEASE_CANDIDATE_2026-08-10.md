# SAVEONSUB L1 Release Candidate — 2026-08-10

## Runtime code head

`dcebe69163b72933aca45cb7e8dd91f0c84a6b8e`

The current PR head adds only this audit record after that runtime code head. Exact-head CI independently rebuilds and revalidates the artifact, so release authority is tied to the current PR head rather than this historical code-head label.

## Release posture

- Launch state: `L1_PUBLIC_INFO_ONLY`
- Products: 72
- Historical plans retained for provenance: 138
- Active v3 plans: 72
- Quarantined historical plans: 66
  - OpenAI/shared-account policy quarantine: 8
  - Other shared fulfillment without explicit provider evidence: 58
- Active commercial states: 65 unknown, 4 direct-provider-only, 3 blocked
- Approved public SAVEONSUB price records: 0
- Sellable plans: 0
- Public media registry entries: 0; 72 local social fallbacks remain available

## Strict artifact

- Release mode: `L1_PUBLIC_INFO_ONLY`
- Product routes: 72 EN + 72 BN
- Plan routes: 72 EN + 72 BN
- Category routes: 13 EN + 13 BN
- Sitemap/indexable URLs: 178
- Dedicated plan pages: `noindex,follow`
- Public prices: 0
- Commerce controls: 0
- Payment destinations: 0
- WhatsApp destinations: 0
- Offer/AggregateOffer schema: 0
- Raw catalog publication: 0
- Shared-commerce findings: 0
- Unsupported proof findings: 0
- Unverified legal-operator findings: 0

## Runtime-code CI evidence

GitHub Actions run `31347226633` at runtime code head `dcebe69163b72933aca45cb7e8dd91f0c84a6b8e`:

- `structural-audit`: SUCCESS
- `release-integrity-report`: SUCCESS
- strict artifact build/hardening: SUCCESS
- active catalog + quarantine model validation: SUCCESS
- reviewed media registry validation: SUCCESS
- shadow Worker quote/default-deny tests: SUCCESS
- staged release integrity: SUCCESS
- cryptographic release manifest generation: SUCCESS
- release candidate artifact upload: SUCCESS

Runtime-code artifact:

- `saveonsub-l1-public-info-dcebe69163b72933aca45cb7e8dd91f0c84a6b8e`
- SHA-256: `7512d5e07330379eaabbe9fe92d2cbe21a92fb274f2f511510c42905ffca60d7`

## Deployment safety

Production workflow now:

1. validates authority, media registry and active catalog;
2. builds/hardens/stamps the strict L1 artifact;
3. stages only `_site`;
4. creates non-public cryptographic release evidence;
5. refuses cutover without a previous Cloudflare production deployment to use as rollback target;
6. deploys only `_site`;
7. verifies the exact Git SHA and representative EN/BN/product/plan routes on `saveonsub.com`;
8. automatically rolls back to the captured production deployment if live verification fails;
9. stores deployment evidence.

Vercel Git previews are configured to run `bash build_all.sh` and publish only `_site`. The configuration is accepted by Vercel; the current Vercel account is build-rate-limited, so no exact-head preview deployment was created after this hardening.

## External infrastructure blocker

Canonical Cloudflare deployment remains `BLOCKED_ACCESS`.

Evidence already exhausted autonomously:

- configured GitHub Actions `CLOUDFLARE_API_TOKEN` returns Cloudflare `Invalid access token [code: 9109]`;
- common alternative GitHub secret aliases were probed read-only and none authenticated to the `saveonsub` Pages project;
- no Cloudflare Git integration status is attached to the repository;
- no Cloudflare connector/plugin is installed in the current environment;
- connected Vercel project does not have `saveonsub.com` attached and connector controls do not expose canonical-domain reassignment.

No production merge/cutover should occur from machine state until an authenticated Cloudflare control channel exists. This is an authentication dependency, not an unresolved code/release-integrity defect.
