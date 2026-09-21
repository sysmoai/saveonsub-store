# SaveOnSub Brand Source of Truth

This directory is the machine/handoff layer for the locked SaveOnSub brand system.

## Start here

| User | Read first | Then use |
|---|---|---|
| Designer | `BRAND-SYSTEM.md` | Figma Brand Master + this manifest |
| Developer | `AGENTS.md` | `brand/manifest.json` platform routes |
| AI agent | `brand/AI-BRAND-INSTRUCTIONS.md` | `brand/manifest.json` |
| Marketing operator | `BRAND-SYSTEM.md` | approved master/derivative for the intended surface |

## Authority order

1. Explicit CEO brand-lock decision
2. `BRAND-SYSTEM.md`
3. Locked master asset bytes / brand-lock marker
4. `brand/manifest.json`
5. `AGENTS.md` production constraints
6. `stage_deploy.py` derivative implementation
7. Figma visual documentation

If two layers disagree, stop. Do not choose the one that looks most convenient.

## Production asset routing

| Surface | Asset |
|---|---|
| Website header | `assets/logo.svg` |
| Website footer | `assets/logo.svg` |
| Browser SVG favicon | `assets/favicon.svg` |
| Browser / search PNG fallback | `assets/icon-192.png` |
| Apple touch icon | `assets/apple-touch-icon.png` |
| PWA 192 | `assets/icon-192.png` |
| PWA 512 | `assets/icon-512.png` |
| PWA maskable 512 | `assets/icon-maskable-512.png` — generated at build |
| Open Graph / social preview | `assets/og-image.png` — generated at build |
| Schema.org logo | `assets/logo.svg` |

For the authoritative current mapping, parse `brand/manifest.json`; this table is a human convenience view.

## Master assets

### Horizontal lockup
`assets/logo.svg`

This is a locked SVG wrapper containing the approved artwork. It is not a true editable vector-path master.

### Primary icon
`assets/favicon.svg`

This is the locked square icon wrapper used as the approved icon source route.

## Generated derivatives

Public raster derivatives are rebuilt by `stage_deploy.py` from the locked master artwork. Do not maintain competing hand-made production versions.

The dedicated maskable icon uses the exact approved icon square at 288×288, centered at (112,112) on a 512×512 white canvas. The logo artwork itself is not redrawn.

## Currently blocked exact originals

These are intentionally not fabricated:

- exact stacked/vertical production master;
- exact transparent full-logo original;
- true editable vector-path master.

See `brand/manifest.json > blocked` for machine-readable status and required agent behavior.

## Figma

Brand Master file key:

`2zkEcJbpk1NyJHBFi3o0Pw`

Figma is the visual documentation and export workspace. It must mirror the locked source truth, not silently replace it.

Current documented platform component includes:

`Icon/Maskable/512`

## AI use

AI systems must read:

1. `BRAND-SYSTEM.md`
2. `brand/manifest.json`
3. `brand/AI-BRAND-INSTRUCTIONS.md`

before mutating any SaveOnSub visual identity.

The basic rule is simple:

> Never recreate the SaveOnSub logo from a prompt or from memory. Reference the approved asset.

## Validate before a brand/code change

Run:

`python validate_brand_manifest.py`

The canonical `build_site.py` pipeline also runs this validator first and fails closed if locked master bytes, platform routing, blocked-source governance or derivative rules drift.

## Updating the system

For a normal platform derivative change:

1. keep master artwork untouched;
2. update manifest routing if required;
3. update deterministic generation logic;
4. update Figma documentation;
5. run validation/quality gates;
6. use a PR before production.

For a master logo change, an explicit CEO brand decision is required first.
