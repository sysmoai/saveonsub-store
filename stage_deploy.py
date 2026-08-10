#!/usr/bin/env python3
"""Stage an explicit public copy of SAVEONSUB into ./_site.

Default mode preserves the existing repository staging behavior for migration
compatibility. `--public-v3` is the strict L1 path: it stages only the generated
`_public_v3` artifact and refuses internal JSON/control/backend/preview content.

The repository root is never publishable.
"""
from __future__ import annotations

import argparse
import glob
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / '_site'
PUBLIC_V3 = ROOT / '_public_v3'

EXCLUDE_DIRS = {
    '.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
    '__pycache__', 'node_modules', 'marketing', 'reports', 'docs', '_site',
    '_preview_v3', '_public_v3', 'commerce-worker'
}
EXCLUDE_EXT = {
    '.py', '.md', '.sh', '.pyc', '.log', '.bak', '.orig-backup', '.toml', '.json'
}
EXCLUDE_FILES = {
    '.replit', '.gitignore', '.env.example', 'package.json', 'package-lock.json',
    'vercel.json', 'AGENTS.md'
}

PUBLIC_JSON_ALLOWLIST = set()


def runtime_fetched_json():
    """Return JSON paths referenced by shipped HTML/JS browser fetch() calls."""
    requested = set()
    paths = glob.glob('**/*.html', recursive=True) + glob.glob('**/*.js', recursive=True)
    for path in paths:
        parts = path.replace('\\', '/').split('/')
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        try:
            text = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for match in re.finditer(r"""fetch\(\s*['"`]([^'"`]+\.json)""", text):
            requested.add(match.group(1).lstrip('/'))
    return requested


def reset_dest():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()


def inspect_staged(*, allowlisted_json: set[str] | None = None):
    allowlisted_json = allowlisted_json or set()
    leaks = []
    for file in DEST.rglob('*'):
        if not file.is_file():
            continue
        rel = file.relative_to(DEST).as_posix()
        if rel in allowlisted_json:
            continue
        if file.suffix.lower() == '.json':
            leaks.append(rel)
        if file.suffix.lower() in EXCLUDE_EXT or file.name in EXCLUDE_FILES:
            leaks.append(rel)
        if any(part in EXCLUDE_DIRS for part in file.relative_to(DEST).parts):
            leaks.append(rel)

    size = sum(file.stat().st_size for file in DEST.rglob('*') if file.is_file())
    count = sum(1 for file in DEST.rglob('*') if file.is_file())
    print(f'staged {count} files, {size/1024/1024:.2f} MB -> {DEST}')

    if leaks:
        print(f'REFUSING TO DEPLOY - {len(set(leaks))} internal/disallowed file(s) staged:')
        for rel in sorted(set(leaks))[:50]:
            print(f'  {rel}')
        return 1

    required = ['index.html', 'sitemap.xml', 'robots.txt', 'sw.js', 'assets/app.js', 'assets/style.css']
    missing = [rel for rel in required if not (DEST / rel).is_file()]
    if missing:
        print('REFUSING TO DEPLOY - required public file(s) missing:')
        for rel in missing:
            print(f'  {rel}')
        return 1
    return 0


def stage_legacy():
    requested_json = runtime_fetched_json()
    unauthorized_json = requested_json - PUBLIC_JSON_ALLOWLIST
    if unauthorized_json:
        print('REFUSING TO DEPLOY - browser code fetches non-allowlisted JSON:')
        for path in sorted(unauthorized_json):
            print(f'  {path}')
        return 1

    missing_allowlisted = [p for p in PUBLIC_JSON_ALLOWLIST if not pathlib.Path(p).is_file()]
    if missing_allowlisted:
        print('REFUSING TO DEPLOY - PUBLIC_JSON_ALLOWLIST contains missing file(s):')
        for path in sorted(missing_allowlisted):
            print(f'  {path}')
        return 1

    reset_dest()
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_base = pathlib.Path(base).relative_to(ROOT)
        for filename in files:
            rel = (rel_base / filename).as_posix().lstrip('./')
            suffix = pathlib.Path(filename).suffix.lower()
            if rel in PUBLIC_JSON_ALLOWLIST:
                pass
            elif filename in EXCLUDE_FILES or suffix in EXCLUDE_EXT:
                continue
            out = DEST / rel_base / filename
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pathlib.Path(base) / filename, out)

    result = inspect_staged(allowlisted_json=PUBLIC_JSON_ALLOWLIST)
    if result:
        return result
    print('legacy staging clean; runtime JSON allowlist verified')
    return 0


def stage_public_v3():
    if not PUBLIC_V3.is_dir():
        print('REFUSING TO DEPLOY - _public_v3 missing; run build_public_info_v3.py first')
        return 1
    manifest = PUBLIC_V3 / 'BUILD-MANIFEST.txt'
    if not manifest.is_file():
        print('REFUSING TO DEPLOY - _public_v3/BUILD-MANIFEST.txt missing')
        return 1
    manifest_text = manifest.read_text(encoding='utf-8', errors='replace')
    required_manifest = {
        'release_mode=L1_PUBLIC_INFO_ONLY',
        'public_prices=0',
        'commerce_controls=0',
        'payment_destinations=0',
        'whatsapp_destinations=0',
    }
    missing = [line for line in sorted(required_manifest) if line not in manifest_text]
    if missing:
        print('REFUSING TO DEPLOY - strict public-v3 manifest is not fail-closed:')
        for line in missing:
            print(f'  missing {line}')
        return 1

    reset_dest()
    shutil.copytree(PUBLIC_V3, DEST, dirs_exist_ok=True)
    result = inspect_staged()
    if result:
        return result

    forbidden_paths = [
        DEST / 'catalog.json',
        DEST / 'aips-live.json',
        DEST / 'assets' / 'catalog.js',
        DEST / 'checkout.html',
        DEST / 'track.html',
        DEST / 'commerce-worker',
        DEST / '_preview_v3',
    ]
    present = [p.relative_to(DEST).as_posix() for p in forbidden_paths if p.exists()]
    if present:
        print('REFUSING TO DEPLOY - protected/commerce path present in strict public-v3 artifact:')
        for rel in present:
            print(f'  {rel}')
        return 1

    print('strict L1 public-information staging clean')
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-v3', action='store_true', help='stage only generated _public_v3 L1 artifact')
    args = parser.parse_args()
    os.chdir(ROOT)
    return stage_public_v3() if args.public_v3 else stage_legacy()


if __name__ == '__main__':
    sys.exit(main())
