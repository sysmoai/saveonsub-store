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

Public icon/OG files are copied byte-for-byte from assets/brand/, the hash-pinned
export of brand kit v1.0 (private repo sysmoai/saveonsub-brand-system). They are
never resized or redrawn here, so the deprecated tilted price-tag + ৳ identity and
the legacy SOS-007 black-corner tile cannot reappear.
"""
import glob
import json
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / '_site'
BRAND_LOCK = 'data-brand-lock="2026-08-19-approved"'

EXCLUDE_DIRS = {'.git', '.github', '.vercel', '.wrangler', '.astro', '.next', '.local',
                '__pycache__', 'node_modules', 'marketing', 'reports', '_site',
                'ops',  # internal business files (cohort facts, SEO copy); never public
                'tests',  # repo test harness; served publicly in fca3dd7, never needed live
                'functions', 'workers', 'staff-ui'}  # Order OS backend + staff console: separate private project only
EXCLUDE_EXT = {'.py', '.md', '.sh', '.pyc', '.log', '.bak', '.orig-backup', '.toml',
               '.ts', '.tsx', '.sql', '.yml', '.yaml', '.jsonc', '.mjs', '.cjs', '.map',
               '.pem', '.key', '.p12', '.sqlite', '.db', '.ipynb'}
# '.git' is a *file* (gitdir pointer) in worktrees/submodules; EXCLUDE_DIRS only covers the directory form.
EXCLUDE_FILES = {'.git', '.replit', '.gitignore', '.env.example', 'catalog.json',
                 'package.json', 'package-lock.json', 'vercel.json', 'AGENTS.md',
                 'aips-live.json',  # other business unit's price source; never public
                 'requirements.txt', '.gitattributes'}  # build/dev metadata, not site content
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
        # Brand kit v1.0 navy N1 replaces the unsourced #102634 browser chrome colour.
        new = new.replace('name="theme-color" content="#102634"', 'name="theme-color" content="#082034"')
        new = re.sub(r'https://saveonsub\.com/assets/social/[^\"\'\s<]+\.png', 'https://saveonsub.com/assets/og-image.png', new)
        if new != old:
            page.write_text(new, encoding='utf-8')
            changed += 1
    print(f"brand lock applied to {changed} HTML file(s)")


# Brand kit v1.0 (SOS-CEO-20261102-002) publication files. They are exported
# byte-for-byte from the private saveonsub-brand-system repo into assets/brand/
# and copied here unchanged; nothing is resized, redrawn or typeset at build time.
PINNED_BRAND_FILES = {
    'apple-touch-icon-180.png': ('apple-touch-icon.png', (180, 180)),
    'pwa-icon-192.png': ('icon-192.png', (192, 192)),
    'pwa-icon-512.png': ('icon-512.png', (512, 512)),
    'pwa-icon-maskable-192.png': ('icon-maskable-192.png', (192, 192)),
    'pwa-icon-maskable-512.png': ('icon-maskable-512.png', (512, 512)),
    'og-image-1200x630.png': ('og-image.png', (1200, 630)),
}


def build_public_brand_derivatives():
    """Publish pinned brand-kit icons/OG and verify every byte against brand-export.json."""
    import hashlib
    from PIL import Image

    assets = DEST / 'assets'
    brand = assets / 'brand'
    record_path = brand / 'brand-export.json'
    if not record_path.is_file():
        raise RuntimeError('assets/brand/brand-export.json missing; run saveonsub-brand-system export_web.py')
    record = json.loads(record_path.read_text(encoding='utf-8'))['files']
    for name, meta in record.items():
        path = brand / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
            raise RuntimeError(f'pinned brand file missing or altered: assets/brand/{name}')

    for src, (dst, dims) in PINNED_BRAND_FILES.items():
        shutil.copyfile(brand / src, assets / dst)
        with Image.open(assets / dst) as im:
            if im.size != dims:
                raise RuntimeError(f'bad brand derivative dimensions: {dst}={im.size}, expected={dims}')
    # Browsers request /favicon.ico by default; serve the kit's 16/32/48 M1 icon.
    shutil.copyfile(brand / 'favicon.ico', DEST / 'favicon.ico')

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
        'background_color': '#082034',
        'theme_color': '#082034',
        'lang': 'en-BD',
        'icons': [
            {'src': '/assets/favicon.svg', 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any'},
            {'src': '/assets/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/assets/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/assets/icon-maskable-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'maskable'},
            {'src': '/assets/icon-maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('pinned brand kit v1.0 icons/OG published (hash-verified, not resized)')


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
            if fn.startswith(('.env', '.dev.vars', 'wrangler.')):
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
        if (f.suffix.lower() in EXCLUDE_EXT or f.name in EXCLUDE_FILES
                or f.name.startswith(('.env', '.dev.vars', 'wrangler.'))):
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
