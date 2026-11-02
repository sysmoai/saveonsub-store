#!/usr/bin/env python3
"""Build and publish cache-safe SaveOnSub brand assets from the locked master."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import pathlib
import re
import shutil
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "_site"
ASSETS = SITE / "assets"
SOURCE = ASSETS / "logo.svg"
MANIFEST = ASSETS / "site.webmanifest"
BRAND_LOCK = 'data-brand-lock="2026-08-19-approved"'
DATA_RE = re.compile(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"')


def transparentize_white_matte(image: Image.Image) -> Image.Image:
    """Remove only the white matte; preserve approved colored artwork geometry."""
    src = image.convert("RGB")
    out = Image.new("RGBA", src.size)
    dst = []
    for r, g, b in src.get_flattened_data():
        alpha = 255 - min(r, g, b)
        if alpha <= 5:
            dst.append((255, 255, 255, 0))
            continue
        if alpha >= 48:
            dst.append((r, g, b, 255))
            continue
        a = alpha / 255.0
        rr = max(0, min(255, round((r - 255 * (1 - a)) / a)))
        gg = max(0, min(255, round((g - 255 * (1 - a)) / a)))
        bb = max(0, min(255, round((b - 255 * (1 - a)) / a)))
        dst.append((rr, gg, bb, alpha))
    out.putdata(dst)
    return out


def build_transparent_logo(svg_text: str) -> tuple[pathlib.Path, str]:
    match = DATA_RE.search(svg_text)
    if not match:
        raise SystemExit("CACHE-SAFE BRAND ERROR — approved SVG has no embedded PNG master")
    try:
        raw_png = base64.b64decode(match.group(1), validate=True)
        source = Image.open(io.BytesIO(raw_png))
        source.load()
    except Exception as exc:
        raise SystemExit(f"CACHE-SAFE BRAND ERROR — cannot decode approved PNG master: {exc}")
    rgba = transparentize_white_matte(source)
    stable = ASSETS / "logo-transparent.png"
    rgba.save(stable, format="PNG", optimize=True)
    raw = stable.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    immutable = ASSETS / f"logo-{digest[:16]}.png"
    shutil.copy2(stable, immutable)
    if immutable.read_bytes() != raw:
        raise SystemExit("CACHE-SAFE BRAND ERROR — immutable PNG changed during copy")
    return immutable, digest


def build_favicon_png() -> pathlib.Path:
    """Copy the hash-pinned logo-system favicon. Do not resize icon-192."""
    from stage_deploy import BRAND_SRC, BRAND_WEB_ICONS, _pinned_bytes
    name = "favicon-32.png"
    try:
        raw = _pinned_bytes(BRAND_SRC / "web" / name, BRAND_WEB_ICONS[name])
    except Exception as exc:
        raise SystemExit(f"CACHE-SAFE BRAND ERROR — pinned favicon-32.png rejected: {exc}")
    out = ASSETS / name
    out.write_bytes(raw)
    if out.read_bytes() != raw:
        raise SystemExit("CACHE-SAFE BRAND ERROR — favicon-32.png changed while copying")
    return out


def normalize_manifest() -> None:
    """Remove the fragile SVG favicon reintroduced by the staging generator."""
    if not MANIFEST.is_file():
        raise SystemExit("CACHE-SAFE BRAND ERROR — staged site.webmanifest missing")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"CACHE-SAFE BRAND ERROR — invalid staged manifest: {exc}")
    icons = manifest.get("icons")
    if not isinstance(icons, list):
        raise SystemExit("CACHE-SAFE BRAND ERROR — staged manifest icons missing")
    icons = [icon for icon in icons if icon.get("src") != "/assets/favicon.svg"]
    required = {"/assets/icon-192.png", "/assets/icon-512.png", "/assets/icon-maskable-512.png"}
    present = {icon.get("src") for icon in icons}
    if not required.issubset(present):
        raise SystemExit("CACHE-SAFE BRAND ERROR — approved PWA PNG icons missing from manifest")
    maskable = [
        icon for icon in icons
        if icon.get("src") == "/assets/icon-maskable-512.png" and icon.get("purpose") == "maskable"
    ]
    if len(maskable) != 1:
        raise SystemExit("CACHE-SAFE BRAND ERROR — manifest is missing the maskable 512 icon")
    manifest["icons"] = icons
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if "favicon.svg" in MANIFEST.read_text(encoding="utf-8"):
        raise SystemExit("CACHE-SAFE BRAND ERROR — manifest still references favicon.svg")


def main() -> int:
    if not SITE.is_dir() or not SOURCE.is_file():
        print("CACHE-SAFE BRAND ERROR — run stage_deploy.py first")
        return 1
    raw_svg = SOURCE.read_bytes()
    try:
        svg_text = raw_svg.decode("utf-8")
    except UnicodeDecodeError:
        print("CACHE-SAFE BRAND ERROR — staged logo is not UTF-8 SVG")
        return 1
    if BRAND_LOCK not in svg_text:
        print("CACHE-SAFE BRAND ERROR — staged logo is not the approved brand-locked asset")
        return 1

    immutable, digest = build_transparent_logo(svg_text)
    favicon = build_favicon_png()
    normalize_manifest()
    immutable_rel = f"assets/{immutable.name}"

    changed = 0
    referenced = 0
    for page in SITE.rglob("*.html"):
        old = page.read_text(encoding="utf-8", errors="strict")
        new = old.replace("assets/logo.svg", immutable_rel)
        new = re.sub(r'([./]*assets/)favicon\.svg', r'\1favicon-32.png', new)
        if new != old:
            page.write_text(new, encoding="utf-8")
            changed += 1
        if immutable_rel in new:
            referenced += 1

    stale_logo = []
    stale_favicon = []
    for page in SITE.rglob("*.html"):
        body = page.read_text(encoding="utf-8", errors="strict")
        if "assets/logo.svg" in body:
            stale_logo.append(page.relative_to(SITE).as_posix())
        if "favicon.svg" in body:
            stale_favicon.append(page.relative_to(SITE).as_posix())
    if stale_logo:
        print(f"CACHE-SAFE BRAND ERROR — {len(stale_logo)} HTML page(s) still reference mutable logo.svg")
        return 1
    if stale_favicon:
        print(f"CACHE-SAFE BRAND ERROR — {len(stale_favicon)} HTML page(s) still reference favicon.svg")
        return 1
    if referenced == 0:
        print("CACHE-SAFE BRAND ERROR — transparent immutable logo is not referenced by staged HTML")
        return 1
    if not favicon.is_file():
        print("CACHE-SAFE BRAND ERROR — favicon-32.png was not generated")
        return 1

    print(f"cache-safe approved transparent logo: /{immutable_rel}")
    print("stable transparent logo: /assets/logo-transparent.png")
    print("approved PNG favicon: /assets/favicon-32.png")
    print("manifest normalized to approved standalone PNG icons")
    print(f"logo_png_sha256={digest}")
    print(f"rewrote {changed} HTML file(s); immutable transparent logo referenced by {referenced} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
