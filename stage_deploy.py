#!/usr/bin/env python3
"""Stage a publishable copy of the site into ./_site  —  python stage_deploy.py

Why this exists
---------------
`wrangler pages deploy .` publishes the REPO ROOT. That would ship every build
script, catalog.json (internal pricing precedence, competitor watchlist, survey
method) and internal strategy docs to the public site.

_redirects does NOT save you: Cloudflare Pages serves a static file that exists
BEFORE redirect rules are evaluated, so a source file that was actually uploaded
may still become public.

So we build an allowlisted copy and deploy that instead. Local runs and CI both
call this script, so the two can never drift apart.

Brand lock
----------
The CEO-approved SaveOnSub mark dated 2026-08-19 is canonical. Generated HTML in
this static repository historically contains a typeset SAVE<em>ON</em>SUB fallback.
During staging we replace that fallback with the approved master-derived lockup
from /assets/logo.svg on every deployed page.

All public raster brand derivatives are also rebuilt from the locked SVG wrappers
at staging time. This means old PNG exports can be removed from source control and
can never reintroduce the deprecated tilted price-tag + ৳ identity.
"""
import base64
import glob
import io
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / '_site'
BRAND_LOCK = 'data-brand-lock="2026-08-19-approved"'

EXCLUDE_DIRS = {'.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
                '__pycache__', 'node_modules', 'marketing', 'reports', '_site'}
EXCLUDE_EXT = {'.py', '.md', '.sh', '.pyc', '.log', '.bak', '.orig-backup', '.toml'}
EXCLUDE_FILES = {'.replit', '.gitignore', '.env.example', 'catalog.json',
                 'package.json', 'package-lock.json', 'vercel.json', 'AGENTS.md'}
EXCLUDE_PREFIXES = ('assets/social/',)


def runtime_fetched_json():
    """Any *.json the shipped site fetches at runtime must NOT be excluded."""
    keep = set()
    for f in glob.glob('**/*.html', recursive=True) + glob.glob('**/*.js', recursive=True):
        if any(p in f.replace('\\', '/').split('/') for p in EXCLUDE_DIRS):
            continue
        try:
            s = open(f, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for m in re.finditer(r"""fetch\(\s*['"`]([^'"`]+\.json)""", s):
            keep.add(m.group(1).lstrip('/'))
    return keep


def apply_brand_lock():
    """Enforce the approved logo/icon on every staged HTML document."""
    replacement = ('<img src="/assets/logo.svg" alt="SaveOnSub.com" '
                   'data-brand-lock="2026-08-19-approved" '
                   'style="display:block;width:155px;max-width:42vw;height:auto">')
    changed = 0
    for page in DEST.rglob('*.html'):
        try:
            old = page.read_text(encoding='utf-8')
        except OSError:
            continue
        new = old.replace('SAVE<em>ON</em>SUB', replacement)
        new = re.sub(r'https://saveonsub\.com/assets/social/[^\"\'\s<]+\.png', 'https://saveonsub.com/assets/og-image.png', new)
        if new != old:
            page.write_text(new, encoding='utf-8')
            changed += 1
    print(f"brand lock applied to {changed} HTML file(s)")


def _embedded_png(svg_path: pathlib.Path):
    """Return the exact PNG embedded in one approved SVG wrapper."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            'Pillow is required to create approved public brand derivatives. '
            'Install dependencies before staging.'
        ) from exc

    text = svg_path.read_text(encoding='utf-8', errors='strict')
    if BRAND_LOCK not in text:
        raise RuntimeError(f'unapproved brand wrapper: {svg_path}')
    m = re.search(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"', text)
    if not m:
        raise RuntimeError(f'approved embedded PNG missing: {svg_path}')
    raw = base64.b64decode(m.group(1), validate=True)
    return Image.open(io.BytesIO(raw)).convert('RGBA')


def _font(size: int):
    from PIL import ImageFont
    candidates = (
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def build_public_brand_derivatives():
    """Create public PNG/PWA/OG assets only from approved locked wrappers."""
    from PIL import Image, ImageDraw

    assets = DEST / 'assets'
    assets.mkdir(parents=True, exist_ok=True)

    lockup = _embedded_png(assets / 'logo.svg')
    icon = lockup.crop((0, 0, lockup.height, lockup.height))
    resample = Image.Resampling.LANCZOS

    # Browser / iOS / PWA derivatives. The artwork is never redrawn: these are
    # resizes of the approved embedded icon.
    icon.resize((180, 180), resample).save(assets / 'apple-touch-icon.png', optimize=True)
    icon.resize((192, 192), resample).save(assets / 'icon-192.png', optimize=True)
    icon.resize((512, 512), resample).save(assets / 'icon-512.png', optimize=True)

    # Social preview: compose the exact approved lockup with approved brand lines.
    # The logo itself is not recreated or typeset.
    bg = (244, 247, 247)      # approved light neutral #F4F7F7
    navy = (16, 38, 52)       # approved navy #102634
    teal = (0, 126, 112)      # approved teal #007E70
    white = (255, 255, 255)
    og = Image.new('RGB', (1200, 630), bg)
    draw = ImageDraw.Draw(og)
    draw.rounded_rectangle((92, 92, 1108, 382), radius=18, fill=white)

    max_w, max_h = 1000, 260
    scale = min(max_w / lockup.width, max_h / lockup.height)
    size = (max(1, round(lockup.width * scale)), max(1, round(lockup.height * scale)))
    logo_big = lockup.resize(size, resample)
    x = (1200 - logo_big.width) // 2
    y = 105 + (250 - logo_big.height) // 2
    og.paste(logo_big, (x, y), logo_big)

    headline = 'Verified Savings. Real Human Support.'
    subline = 'Before You Subscribe, Check SaveOnSub.'
    f1, f2 = _font(43), _font(29)
    b1 = draw.textbbox((0, 0), headline, font=f1)
    b2 = draw.textbbox((0, 0), subline, font=f2)
    draw.text(((1200 - (b1[2]-b1[0]))/2, 456), headline, font=f1, fill=navy)
    draw.text(((1200 - (b2[2]-b2[0]))/2, 535), subline, font=f2, fill=teal)
    og.save(assets / 'og-image.png', optimize=True)

    # Keep the manifest on robust standalone PNG icons. favicon.svg is an
    # externally-dependent SVG crop and must not be reintroduced here.
    manifest_path = assets / 'site.webmanifest'
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            manifest = {}
    manifest.update({
        'name': 'SaveOnSub — Premium Subscriptions at BD Prices',
        'short_name': 'SaveOnSub',
        'start_url': '/?utm_source=pwa',
        'scope': '/',
        'display': 'standalone',
        'background_color': '#102634',
        'theme_color': '#102634',
        'lang': 'en-BD',
        'icons': [
            {'src': '/assets/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
            {'src': '/assets/apple-touch-icon.png', 'sizes': '180x180', 'type': 'image/png', 'purpose': 'any'},
        ],
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    expected = {
        'apple-touch-icon.png': (180, 180),
        'icon-192.png': (192, 192),
        'icon-512.png': (512, 512),
        'og-image.png': (1200, 630),
    }
    for name, dims in expected.items():
        with Image.open(assets / name) as im:
            if im.size != dims:
                raise RuntimeError(f'bad brand derivative dimensions: {name}={im.size}, expected={dims}')
    print('approved raster/PWA/OG derivatives rebuilt from locked masters')


def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)

    runtime_json = runtime_fetched_json()
    copied = 0
    total_bytes = 0
    for src in ROOT.rglob('*'):
        if not src.is_file():
            continue
        rel = src.relative_to(ROOT)
        rel_posix = rel.as_posix()
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel_posix in EXCLUDE_FILES:
            continue
        if src.suffix.lower() in EXCLUDE_EXT and rel_posix not in runtime_json:
            continue
        if any(rel_posix.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
        total_bytes += src.stat().st_size

    apply_brand_lock()
    build_public_brand_derivatives()
    print(f'staged {copied} source files, {total_bytes / 1024 / 1024:.2f} MB public output -> {DEST}')
    print('staging clean')
    return 0


if __name__ == '__main__':
    sys.exit(main())
