#!/usr/bin/env python3
"""Stage a publishable copy of the site into ./_site  —  python stage_deploy.py

Why this exists
---------------
`wrangler pages deploy .` publishes the REPO ROOT. That would ship every build
script, catalog.json (internal pricing precedence, competitor watchlist, survey
method) and internal strategy docs (PRICING-DECISIONS-PROPOSED-10.md,
marketing/FB-POST-BANK.md) to the public site.

_redirects does NOT save you: Cloudflare Pages serves a static file that exists
BEFORE redirect rules are evaluated, so `/*.py /404.html 404` never fires for a
.py file that was actually uploaded.

So we build an allowlisted copy and deploy that instead. Local runs and CI both
call this script, so the two can never drift apart.
"""
import os, shutil, pathlib, sys, re, glob

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / '_site'

EXCLUDE_DIRS = {'.git', '.github', '.vercel', '.wrangler', '.astro', '.next',
                '__pycache__', 'node_modules', 'marketing', 'reports', '_site'}
EXCLUDE_EXT = {'.py', '.md', '.sh', '.pyc', '.log', '.bak', '.orig-backup', '.toml'}
EXCLUDE_FILES = {'.replit', '.gitignore', '.env.example', 'catalog.json',
                 'package.json', 'package-lock.json', 'vercel.json', 'AGENTS.md'}


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
            if rel in keep:
                pass  # explicitly required at runtime
            elif fn in EXCLUDE_FILES or pathlib.Path(fn).suffix.lower() in EXCLUDE_EXT:
                continue
            out = DEST / rel_base / fn
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pathlib.Path(base) / fn, out)
            copied += 1

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
    print(f"staged {copied} files, {size/1024/1024:.2f} MB -> {DEST}")

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
