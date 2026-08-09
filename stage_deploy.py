#!/usr/bin/env python3
"""Stage an explicit public copy of SAVEONSUB into ./_site.

The repository root is never publishable. Internal strategy, source data, scripts,
pricing provenance and control records must not enter Cloudflare Pages output.
Runtime JSON is fail-closed: browser code may fetch only files listed in
PUBLIC_JSON_ALLOWLIST.
"""
import glob
import os
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / '_site'

EXCLUDE_DIRS = {
    '.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
    '__pycache__', 'node_modules', 'marketing', 'reports', 'docs', '_site'
}
EXCLUDE_EXT = {
    '.py', '.md', '.sh', '.pyc', '.log', '.bak', '.orig-backup', '.toml', '.json'
}
EXCLUDE_FILES = {
    '.replit', '.gitignore', '.env.example', 'package.json', 'package-lock.json',
    'vercel.json', 'AGENTS.md'
}

# Public JSON must be deliberately named here. Empty is correct until a reviewed
# browser feature genuinely requires a JSON endpoint. site.webmanifest is not .json.
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


def main():
    os.chdir(ROOT)

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

    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()

    copied = 0
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
            copied += 1

    leaks = []
    for file in DEST.rglob('*'):
        if not file.is_file():
            continue
        rel = file.relative_to(DEST).as_posix()
        if rel in PUBLIC_JSON_ALLOWLIST:
            continue
        if file.suffix.lower() in EXCLUDE_EXT or file.name in EXCLUDE_FILES:
            leaks.append(rel)
        if any(part in EXCLUDE_DIRS for part in file.relative_to(DEST).parts):
            leaks.append(rel)

    size = sum(file.stat().st_size for file in DEST.rglob('*') if file.is_file())
    print(f'staged {copied} files, {size/1024/1024:.2f} MB -> {DEST}')

    if leaks:
        print(f'REFUSING TO DEPLOY - {len(leaks)} internal file(s) staged:')
        for rel in sorted(set(leaks))[:50]:
            print(f'  {rel}')
        return 1

    if not (DEST / 'index.html').exists():
        print('REFUSING TO DEPLOY - no index.html in staged output')
        return 1

    print('staging clean; runtime JSON allowlist verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
