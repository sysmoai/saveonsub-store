# SaveOnSub - Source and icon authority reconciliation

Date: 2026-09-22
Status: OPEN VISUAL RELEASE BLOCKERS. Working local derivatives are available; not a completed high-resolution brand library.
Source commit inspected: fcb7c1791526cf5c45f7735339f57d0eafeeba9e.

## Confirmed source facts

The exact bytes of assets/logo.svg were recovered and matched to Git blob SHA-1 e1279bdf965d5797a8b54a44e35c3e5d083cb9de. Its embedded PNG is 280 x 78 pixels, fully opaque, with SHA-256 cc716f9d83ba31be9a7eadc4525425810d82086a914136b678df991d0d94b5a2. This is raster artwork in an SVG container, not an editable vector-path original.

A direct Figma Plugin API inventory confirmed 15 pages, 70 variables, 9 text styles, 5 paint styles and 3 effect styles in file 2zkEcJbpk1NyJHBFi3o0Pw. The metadata-only document root returned only one page; that response is not a complete file inventory.

## Critical visual defects

1. Figma component 8:4, Icon/App/512, was rendered and visually inspected. It shows the obsolete outlined tag with a yellow dot, not the locked S/percentage/arrow artwork. Its previous APPROVED/EXACT label is not reliable. Other platform and maskable components must be individually rechecked; do not infer they pass from this inspection.
2. assets/favicon.svg and stage_deploy.py select the first 78 x 78 pixels of the 280 x 78 lockup. This includes part of the wordmark. The local test found 159 dark-navy wordmark pixels in that crop.
3. Large output dimensions, wrapper hashes and green CI do not prove original resolution or artwork correctness. Do not label upscaled versions as high-resolution originals.

## Verified local crop correction

For this exact immutable source only: crop [0,0,60,78], paste unchanged at [9,0] on a white 78 x 78 canvas. Columns 54 through 65 are the verified separator, with minimum RGB channel 251. The full source icon remains intact; the wordmark is excluded. The copied native ROI is pixel-identical and the corrected icon has zero dark-navy wordmark pixels under the same classifier.

Derived 16/32/48/64 PNGs and multi-size ICO were generated locally. 180/192/512 outputs are explicitly UPSCALED working candidates. A dedicated 512 maskable canvas uses the corrected square at 288 x 288 centered at [112,112]; its corner distance 203.646753 px is within the 204.8 px protected radius. No redraw, retyping, recoloring, tracing, background removal or generative upscaling was used.

## Original recovery status

File Library references were located for 1000108047.png, 1000108050.png and 1000108052.png, plus candidate 1000108051.png. The original file bytes were not materialized in this runtime. Do not assert their resolution, alpha channel, or pixel equivalence based on search captions. A black preview is not proof of transparency. Google Drive image-name searches did not locate matching originals in this pass.

Stacked, transparent, monochrome/reverse and true vector originals remain unreleased. Never create a look-alike to close the blocker.

## Write and release status

A subsequent Figma inspection call was blocked by the connector safety check. No Figma repair was applied in this pass. No pull request was merged, no website was deployed, and no live-site validation was completed. This audit is documentation only; it does not itself enforce a CI gate or change production assets.

## Required next work

- Repair the existing Figma icon and platform components using the verified source, retaining component IDs and the immutable horizontal artwork.
- Correct the repository icon crop and reconcile favicon wrapper/hash/routing rules in a reversible PR with no-wordmark pixel tests.
- Re-open icon visual QA for earlier ready/approved labels before publication; build success is not visual proof.
- Recover exact higher-resolution originals before promising high-resolution, transparent, print or editable-vector deliverables.
- Synchronize asset manifest, export labels, Figma, generated output and live website after explicit source validation.

References: W3C Web Application Manifest https://www.w3.org/TR/appmanifest/#icon-masks ; Google favicon guidance https://developers.google.com/search/docs/appearance/favicon-in-search . These describe formats and safe areas, not SaveOnSub approval status.
