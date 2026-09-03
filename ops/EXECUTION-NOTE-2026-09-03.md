# Execution Note — 2026-09-03

The working SaveOnSub website is an existing organic/revenue asset. Source-level safety, truth, branding and deployment controls may be improved continuously, but changes to canonical URLs, information architecture, ranking content intent, DNS/origin, or checkout behavior require a measured baseline and rollback plan.

Current external release boundary: canonical `saveonsub.com` is served through Cloudflare Pages, while the stored Cloudflare API token returns HTTP 401. GitHub and Vercel are authenticated in the current operator environment; Cloudflare account administration is not. Do not claim a canonical release succeeded until `saveonsub.com` is directly verified.
