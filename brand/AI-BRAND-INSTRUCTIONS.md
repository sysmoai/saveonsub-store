# SaveOnSub — AI Brand Instructions

Status: **MANDATORY for any AI/automation touching SaveOnSub branding**  
Brand lock: **2026-08-19**  
Machine map: `brand/manifest.json`  
Human policy: `BRAND-SYSTEM.md`  
Production guardrails: `AGENTS.md`

## 1. Mandatory preflight

Before creating, editing, exporting, deploying, reviewing, or describing a SaveOnSub brand asset:

1. Read `BRAND-SYSTEM.md`.
2. Read `brand/manifest.json`.
3. Read this file.
4. Resolve the requested surface through `manifest.platformRouting`.
5. Confirm the selected asset is not listed in `manifest.blocked`.
6. If code or production output will change, use a reversible branch/PR and run repository quality gates.

If any of these steps cannot be completed, do not claim that an output is the exact approved brand asset.

## 2. Master artwork is immutable

The approved SaveOnSub identity is locked. The master icon contains the established price-tag / percentage / circular-arrow S construction and the approved wordmark lockup.

Never:

- redraw or regenerate the logo;
- prompt an image model to recreate the logo;
- auto-trace the raster artwork and call the trace an approved vector;
- re-typeset the wordmark with a font;
- change the percentage symbol, tag hole, arrow, S geometry, spacing or proportions;
- recolor the locked artwork;
- add outlines, shadows, gradients, 3D effects, badges, mascots or decorative marks to the master;
- stretch or non-uniformly scale the master;
- substitute a generic price tag, shield, lock, currency symbol or letter-S mark;
- use the deprecated tilted price-tag + ৳ identity.

The locked master paths are defined by `brand/manifest.json`. Do not guess alternate filenames.

## 3. Master vs derivative

A **master** is an approved locked source identified as a master in `brand/manifest.json`.

A **derivative** is a platform-specific output created from a master without changing the master artwork.

Allowed examples include:

- deterministic square raster resizing;
- the documented maskable 512 canvas with the exact icon square centered at the manifest-defined geometry;
- placing the exact lockup inside a social/Open Graph composition;
- exporting a Figma component that contains the exact approved artwork.

A derivative must never be relabeled as a master or original.

## 4. Blocked assets

If the manifest lists an asset as `blocked-source-required`:

- do not recreate it from memory;
- do not rebuild it from screenshots;
- do not re-type the wordmark;
- do not remove a background and call the result an original;
- do not trace it into vector paths and call the trace approved.

Recover or request the exact approved source. Until then, use another approved production route if the requested surface permits it.

## 5. Platform routing

Always use `brand/manifest.json > platformRouting`.

Examples:

- website header/footer → the canonical horizontal lockup;
- browser SVG favicon → the canonical icon wrapper;
- PNG/search fallback → the designated approved raster derivative;
- PWA any-purpose icons → the designated 192/512 outputs;
- PWA maskable → the dedicated maskable derivative;
- social sharing → the Open Graph derivative.

Do not copy random historical files into production because they look similar.

## 6. Figma rules

Figma is the human visual/export workspace and must mirror the locked repository/source truth.

When operating in Figma:

- reuse existing approved components;
- use exact source bytes/artwork where available;
- keep deterministic component names;
- document master vs derivative status;
- keep export filenames consistent with the manifest;
- never manually redraw the logo;
- never convert a platform derivative into the new brand master;
- if Figma and the locked master bytes conflict, stop and resolve the conflict before proceeding.

Current Figma file key is recorded in `brand/manifest.json`.

## 7. Code and web rules

When editing website or application code:

- reference canonical asset paths rather than embedding duplicate copies;
- preserve the required brand-lock marker on locked wrappers;
- keep browser/PWA metadata aligned with the manifest;
- keep `stage_deploy.py` as the deterministic public derivative generator unless an explicitly approved architecture change replaces it;
- never bypass brand regression checks;
- do not publish internal brand-management files merely because they exist in the repository.

A preview deployment is not canonical-live proof. Follow `AGENTS.md` and `DEPLOY.md`.

## 8. Social and marketing creative rules

You may design layouts around an exact approved logo/icon, including approved background, typography, campaign copy, product imagery and composition.

You may not modify the master mark itself.

For any public claim, follow the evidence-gated rules in `BRAND-SYSTEM.md`. Never use another business unit's proof, customer data, logo or contact details as SaveOnSub proof.

## 9. Business-unit firewall

SaveOnSub must remain operationally and visually distinct from AIPS, AITP, AIPT, SYSmoAI and other portfolio brands.

Do not:

- reuse another unit's logo or branded creative as SaveOnSub;
- silently import another unit's contact number or proof;
- infer shared customer/order/review counts;
- treat filenames beginning with another brand prefix as approved SaveOnSub assets without explicit classification.

## 10. Change-control rule

Changing a locked master is not routine design work.

A master change requires an explicit CEO brand decision and then a coordinated update to:

1. the exact master asset;
2. `BRAND-SYSTEM.md`;
3. `brand/manifest.json`;
4. Figma Brand Master;
5. derivative generation rules;
6. tests / quality gates;
7. website and other active surfaces.

Do not update only one layer.

## 11. Agent completion checklist

Before saying a SaveOnSub branding task is complete, confirm:

- correct manifest route used;
- no blocked source was fabricated;
- master artwork unchanged;
- output size/format matches the intended surface;
- Figma/GitHub mapping is documented when applicable;
- automated checks passed for code changes;
- production-live status is described accurately.

If an exact source is unavailable, report the blocker explicitly instead of producing a look-alike.
