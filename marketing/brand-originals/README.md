# SaveOnSub brand originals (CEO-provided 2026-10-29)

Exact files the CEO supplied on 2026-10-29. Never edit, recolor, redraw or regenerate them.
They are registered in the Drive sheet "SAVEONSUB — Brand Asset Registry & Creative QA SSOT v1.0"
(tab 01 SOURCE ASSETS) as SOS-007..SOS-010, status CEO_PROVIDED_2026-10-29 / PENDING_LOCK.
They do not match the hashes of SOS-001..006 in that registry.

| ID | File | Use |
|---|---|---|
| SOS-007 | SOS-007_round_icon_teal_on_white_1254.png | Round icon. Corners are black: mask to the circle before use. Source of `assets/favicon.svg`. |
| SOS-008 | SOS-008_stacked_logo_icon_wordmark_1254_rgba.png | Stacked logo for square posts and profile covers. |
| SOS-009 | SOS-009_horizontal_lockup_icon_wordmark_2172x724.png | Primary horizontal lockup. Source of `assets/logo.svg` (margins trimmed, white padding on the left so the left square is exactly the icon, scaled to 312 px tall). |
| SOS-010 | SOS-010_wordmark_only_2172x724_rgba.png | Wordmark only. |

`stage_deploy.py` builds every public raster (apple-touch, PWA, OG) from `assets/logo.svg`, so those PNGs need no manual export.
Verify with `sha256sum -c SHA256SUMS.txt`.
