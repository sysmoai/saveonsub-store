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

The header lockup served on pages stays the approved 2026-08-19 logo.svg
wrapper. cache_safe_brand.py turns that wrapper into the cache-busted header
PNG. Square icons and the OG-card logo are not cut out of that 280x78 raster.
They are even LANCZOS downscales of the hash-pinned founder originals in
brand_src/ (registry SOS-007 icon and SOS-009 lockup, both CEO_PROVIDED /
PENDING_LOCK). The build refuses to continue if those bytes change, and
brand_src/ is never copied into the public artifact. The deprecated tilted
price-tag + ৳ identity stays blocked by the SVG gate below.
"""
import base64
import glob
import hashlib
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
                '__pycache__', 'node_modules', 'marketing', 'reports', '_site',
                'ops', 'brand_src'}  # internal files and founder brand masters; never public
EXCLUDE_EXT = {'.py', '.md', '.sh', '.pyc', '.log', '.bak', '.orig-backup', '.toml'}
EXCLUDE_FILES = {'.replit', '.gitignore', '.env.example', 'catalog.json',
                 'package.json', 'package-lock.json', 'vercel.json', 'AGENTS.md',
                 'aips-live.json'}  # other business unit's price source; never public
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


BRAND_SRC = ROOT / 'brand_src'
# Registry SOS-007. CEO_PROVIDED / PENDING_LOCK. 1254x1254 RGB, white mark on a dark square.
BRAND_ICON_SRC = BRAND_SRC / 'SOS-LOCKED-20261023-04_Circular_Icon_White_Over_Dark_1254x1254.png'
BRAND_ICON_SHA256 = '681858ffbe873a1377735ddc8cea8c916c0f01b48a27a81d924f525c014201f9'
# Registry SOS-009. CEO_PROVIDED / PENDING_LOCK. 2172x724 RGB horizontal lockup.
BRAND_LOCKUP_SRC = BRAND_SRC / 'SOS-009_horizontal_lockup_2172x724.png'
BRAND_LOCKUP_SHA256 = 'c12510d3dc75ad876b7dc2ff390ddc891dd0513364b05bdc406eaf0385d29e06'


def _pinned_original(path: pathlib.Path, sha256: str, size: tuple, mode: str = 'RGB'):
    """Open a founder-original brand file only when its bytes match the pin."""
    from PIL import Image
    if not path.is_file():
        raise RuntimeError(f'brand original missing: {path}')
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != sha256:
        raise RuntimeError(
            f'brand original hash mismatch: {path.name} (expected {sha256}, got {digest})'
        )
    image = Image.open(io.BytesIO(raw))
    image.load()
    if image.mode != mode or image.size != size:
        raise RuntimeError(
            f'brand original mode/size mismatch: {path.name} {image.mode} {image.size}, '
            f'expected {mode} {size}'
        )
    return image


def render_square_icon(size: int):
    """Evenly downscale the pinned square icon. Never crop, upscale, or recolour."""
    from PIL import Image
    icon = _pinned_original(BRAND_ICON_SRC, BRAND_ICON_SHA256, (1254, 1254), 'RGB')
    if icon.width != icon.height:
        raise RuntimeError(f'refusing to crop non-square brand icon {icon.size}')
    if size < 1 or size > icon.width:
        raise RuntimeError(f'refusing to upscale or invent brand icon size {size}')
    return icon.resize((size, size), Image.Resampling.LANCZOS)


def write_favicon_ico(dest: pathlib.Path):
    """Write a root ICO whose 16/32/48 frames are each downscaled from the master."""
    icon = _pinned_original(BRAND_ICON_SRC, BRAND_ICON_SHA256, (1254, 1254), 'RGB')
    # Pillow thumbnails each requested size from this image. Passing the master,
    # not a 48px intermediate, keeps 16 and 32 one step away from the original.
    icon.save(
        dest,
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    return dest


def build_public_brand_derivatives():
    """Create public icons and the OG card from hash-pinned brand_src originals.

    Square icons are even LANCZOS downscales of the 1254px SOS-007 master.
    The OG logo is an even downscale of the 2172px SOS-009 lockup. Neither is
    cropped, recoloured, or taken from the 280x78 header raster. Header HTML
    still uses the approved logo.svg wrapper.
    """
    from PIL import Image, ImageDraw

    assets = DEST / 'assets'
    assets.mkdir(parents=True, exist_ok=True)

    icon = _pinned_original(BRAND_ICON_SRC, BRAND_ICON_SHA256, (1254, 1254), 'RGB')
    lockup = _pinned_original(BRAND_LOCKUP_SRC, BRAND_LOCKUP_SHA256, (2172, 724), 'RGB')
    resample = Image.Resampling.LANCZOS
    if icon.width != icon.height:
        raise RuntimeError(f'refusing to crop non-square brand icon {icon.size}')

    # Stable filenames. /assets/*.png is cached for 7 days and sw.js is
    # stale-while-revalidate. A filename or query change is what busts
    # returning visitors; that stays deferred because the pages and the
    # favicon-32.png quality-gate string still use these paths.
    for name, side in (
        ('favicon-32.png', 32),
        ('apple-touch-icon.png', 180),
        ('icon-192.png', 192),
        ('icon-512.png', 512),
    ):
        rendered = icon.resize((side, side), resample)
        rendered.save(assets / name, format='PNG', optimize=True)
        with Image.open(assets / name) as saved:
            if saved.convert('RGB').tobytes() != rendered.tobytes():
                raise RuntimeError(f'{name} pixels changed while saving')
    write_favicon_ico(DEST / 'favicon.ico')
    with Image.open(DEST / 'favicon.ico') as ico:
        if sorted(ico.ico.sizes()) != [(16, 16), (32, 32), (48, 48)]:
            raise RuntimeError(f'favicon.ico sizes missing: {sorted(ico.ico.sizes())}')
        for side in (16, 32, 48):
            frame = ico.ico.getimage((side, side)).convert('RGB')
            direct = icon.resize((side, side), resample)
            if frame.tobytes() != direct.tobytes():
                raise RuntimeError(f'favicon.ico {side}px is not an even downscale of the pinned icon')

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
    if scale > 1:
        raise RuntimeError(f'refusing to upscale OG lockup (scale={scale})')
    size = (max(1, round(lockup.width * scale)), max(1, round(lockup.height * scale)))
    logo_big = lockup.resize(size, resample).convert('RGBA')
    aspect_error = abs((logo_big.width / logo_big.height) - (lockup.width / lockup.height))
    if aspect_error > 0.01:
        raise RuntimeError(f'OG logo aspect changed: {logo_big.size} from {lockup.size}')
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

    # Staged manifest references only derivatives produced above plus the locked SVG.
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
            {'src': '/assets/favicon.svg', 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any'},
            {'src': '/assets/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/assets/apple-touch-icon.png', 'sizes': '180x180', 'type': 'image/png', 'purpose': 'any'},
        ],
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    expected = {
        'favicon-32.png': (32, 32),
        'apple-touch-icon.png': (180, 180),
        'icon-192.png': (192, 192),
        'icon-512.png': (512, 512),
        'og-image.png': (1200, 630),
    }
    for name, dims in expected.items():
        with Image.open(assets / name) as im:
            if im.size != dims:
                raise RuntimeError(f'bad brand derivative dimensions: {name}={im.size}, expected={dims}')
    print('pinned brand icon/OG derivatives rebuilt from brand_src (SOS-007 and SOS-009, PENDING_LOCK)')


def main():
    os.chdir(ROOT)
    keep = runtime_fetched_json()
    if keep:
        print(f"runtime-fetched JSON (kept): {sorted(keep)}")

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()

    copied = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_base = pathlib.Path(base).relative_to(ROOT)
        for fn in files:
            rel = (rel_base / fn).as_posix().lstrip('./')
            if rel.startswith(EXCLUDE_PREFIXES):
                continue
            if rel in keep:
                pass
            elif fn in EXCLUDE_FILES or pathlib.Path(fn).suffix.lower() in EXCLUDE_EXT:
                continue
            out = DEST / rel_base / fn
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pathlib.Path(base) / fn, out)
            copied += 1

    apply_brand_lock()

    # Brand regression checks happen before derivatives are produced.
    for rel in ('assets/logo.svg', 'assets/favicon.svg'):
        f = DEST / rel
        if not f.exists():
            print(f"REFUSING TO DEPLOY — missing locked brand asset: {rel}")
            return 1
        s = f.read_text(encoding='utf-8', errors='replace')
        if BRAND_LOCK not in s:
            print(f"REFUSING TO DEPLOY — unapproved brand asset: {rel}")
            return 1
        if '>৳<' in s or 'rotate(-12' in s:
            print(f"REFUSING TO DEPLOY — deprecated logo artwork detected: {rel}")
            return 1

    try:
        build_public_brand_derivatives()
    except Exception as exc:
        print(f"REFUSING TO DEPLOY — approved brand derivative build failed: {exc}")
        return 1

    # Fail loudly rather than publish something internal.
    leaks = []
    for f in DEST.rglob('*'):
        if not f.is_file():
            continue
        rel = f.relative_to(DEST).as_posix()
        if rel in keep:
            continue
        if f.suffix.lower() in EXCLUDE_EXT or f.name in EXCLUDE_FILES:
            leaks.append(rel)
        if any(part in EXCLUDE_DIRS for part in f.relative_to(DEST).parts):
            leaks.append(rel)

    size = sum(f.stat().st_size for f in DEST.rglob('*') if f.is_file())
    print(f"staged {copied} source files, {size/1024/1024:.2f} MB public output -> {DEST}")

    if leaks:
        print(f"REFUSING TO DEPLOY — {len(leaks)} internal file(s) staged:")
        for l in leaks[:20]:
            print(f"  {l}")
        return 1

    index = DEST / 'index.html'
    if not index.exists():
        print("REFUSING TO DEPLOY — no index.html in staged output")
        return 1

    print("staging clean")
    return 0


if __name__ == '__main__':
    sys.exit(main())
