# P0 Truth Migration Changelog — 2026-09-03

Migration commit: `dec314e3937f1859d87ebe226381f8a7401fa753`

Verified result:
- 190 source/generated customer-facing files corrected.
- 250 insertions / 250 deletions; no URL relocation was performed.
- Wrong Bangla payment/support number corrected to +880 1305-869242.
- Blanket `100% official, customer-owned` positioning replaced with explicit Official / Personal / Shared labeling.
- Overbroad shared-access privacy guarantees replaced with access-method-specific caution.
- Unsupported Bangladesh legal conclusions removed.
- Stale OpenAI Bangladesh payment claim removed and current billing wording introduced.
- Retired ChatGPT ৳350 sales wording corrected to current ৳499 references where applicable.
- Unsupported homepage bestseller/order-count blocks replaced by factual product/support messaging.
- FAQ title count aligned to 30.
- Homepage Bangla hreflang corrected to `/bn.html` in source/generation path.
- Public staging validation passed after migration.

A permanent `truth_guard.py` is now part of deployment preflight through `check_prices.py` so known P0 regressions fail both Vercel and Cloudflare build paths.
