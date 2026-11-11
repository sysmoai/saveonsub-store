#!/usr/bin/env python3
"""Fail-closed release audit of the staged ``_site`` + public page manifest.

Read-only. Run after ``build_site.py`` (CI runs it after the other staged gates).
Each check is a negative test the CEO master (V12 §8) asks for:

  private-files  no build source, ops data, ledgers or other-unit files in _site
  whatsapp       every WhatsApp link goes to the one SaveOnSub number
  links          every internal link resolves to a staged page (Cloudflare Pages rules)
  sitemap        every sitemap URL exists, is indexable and self-canonical; no duplicates
  canonical      indexable pages: one canonical on saveonsub.com, unique <title>
  hreflang       EN/BN alternates are reciprocal
  schema         JSON-LD parses; no Review/AggregateRating; each Offer price is visible
  aips           other-unit (aips-*) pages show no BDT price

``--manifest PATH`` also writes the page manifest (page id, intent, canonical,
locale, index, sitemap, schema types, inbound links, offer count, build SHA).
The manifest holds public page facts only; keep it out of git (it is regenerated).
"""
from __future__ import annotations

import collections
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
BASE = "https://saveonsub.com"
WA_NUMBER = "8801305869242"

PRIVATE = re.compile(
    r"(^|/)(catalog\.json|aips-live\.json|package(-lock)?\.json|requirements\.txt|vercel\.json)$"
    r"|\.(py|sh|psv|csv|xlsx|sql|toml|env|md)$|(^|/)\.env|(^|/)ops/|(^|/)tests/|(^|/)marketing/"
    r"|universe-(families|registry)|product-coverage|page-manifest",
    re.I,
)
HREF = re.compile(r'\bhref=(["\'])([^"\']+)\1')
WA = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp://send\?phone=)\+?(\d+)")
CANON = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]*>', re.I)
HREF_ATTR = re.compile(r'href=["\']([^"\']+)["\']')
ALT = re.compile(r'<link[^>]+rel=["\']alternate["\'][^>]+hreflang=["\']([^"\']+)["\'][^>]+href=["\']([^"\']+)["\']', re.I)
NOINDEX = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.I)
TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
LDJSON = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")
BDT = re.compile(r"৳\s?([\d,]+)")
BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
# A displayed Bangladesh mobile number (Latin or Bangla digits, +880/880/0 prefix).
BD_PHONE = re.compile(r"(?<!\d)(?:\+?880[\s-]?|0)(1[3-9]\d{2})[\s-]?(\d{6})(?!\d)")


def url_of(page: Path) -> str:
    rel = page.relative_to(SITE).as_posix()
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[:-len('index.html')]}"
    return f"{BASE}/{rel[:-len('.html')]}"


def resolve(page: Path, href: str) -> Path | None | bool:
    """Staged file for an internal link; False if external/non-page; None if missing.

    Mirrors browsers (``..`` above the root clamps to the root) and Cloudflare Pages
    (``/x`` serves ``x.html`` or ``x/index.html``; ``/d/`` serves ``d/index.html``).
    """
    href = href.split("#", 1)[0].split("?", 1)[0]
    for host in (BASE, "https://www.saveonsub.com"):
        if href == host or href.startswith(host + "/"):
            href = href[len(host):] or "/"
            break
    else:
        if re.match(r"^[a-z][a-z0-9+.-]*:|^//", href, re.I):
            return False
    if not href:
        return False
    if "${" in href or "{{" in href:
        return False  # client-side template, resolved at runtime
    trailing = href.endswith("/")
    base = "/" + page.parent.relative_to(SITE).as_posix()
    joined = posixpath.normpath(href if href.startswith("/") else posixpath.join(base, href))
    rel = joined.lstrip("/")
    if rel == ".":
        rel = ""
    if trailing or not rel:
        candidates = [f"{rel}/index.html" if rel else "index.html"]
    elif not Path(rel).suffix:
        candidates = [rel + ".html", rel + "/index.html"]
    elif rel.endswith(".html"):
        candidates = [rel]
    else:
        return False if (SITE / rel).is_file() else None
    for c in candidates:
        if (SITE / c).is_file():
            return SITE / c
    return None


def visible_amounts(text: str) -> set[str]:
    body = TAGS.sub(" ", SCRIPT_STYLE.sub(" ", text)).translate(BN_DIGITS)
    return {m.replace(",", "") for m in BDT.findall(body)}


def walk_types(node, out: list, offers: list):
    if isinstance(node, dict):
        t = node.get("@type")
        for x in (t if isinstance(t, list) else [t]):
            if x:
                out.append(x)
        if t == "Offer" or (isinstance(t, list) and "Offer" in t):
            offers.append(node)
        for v in node.values():
            walk_types(v, out, offers)
    elif isinstance(node, list):
        for v in node:
            walk_types(v, out, offers)


def intent(rel: str) -> str:
    r = rel[3:] if rel.startswith("bn/") else rel
    if r in ("index.html", "bn.html", ""):
        return "home"
    for prefix, name in (("p/aips-", "other-unit-inquiry"), ("modes/", "other-unit-inquiry"), ("p/", "product"),
                         ("c/", "category"), ("blog/", "guide"), ("guides/", "guide")):
        if r.startswith(prefix):
            return name
    if r in ("refund.html", "privacy.html", "terms.html", "warranty.html"):
        return "policy"
    if r in ("checkout.html", "order.html", "track.html"):
        return "transaction"
    if r in ("prices.html", "all.html", "offers.html", "students.html", "quiz.html", "tools.html"):
        return "listing-or-chooser"
    return "info"


def audit(manifest_path: Path | None = None, warnings: list[str] | None = None) -> list[str]:
    warnings = [] if warnings is None else warnings
    errors: list[str] = []
    files = [p for p in SITE.rglob("*") if p.is_file()]
    for f in files:
        rel = f.relative_to(SITE).as_posix()
        if PRIVATE.search(rel):
            errors.append(f"private-files: {rel} is staged")
    pages = sorted(p for p in files if p.suffix == ".html")
    info = {}
    inbound = collections.Counter()
    for page in pages:
        rel = page.relative_to(SITE).as_posix()
        text = page.read_text(encoding="utf-8")
        for num in WA.findall(text):
            if num != WA_NUMBER:
                errors.append(f"whatsapp: {rel} links to {num}")
        # Displayed numbers too (incl. meta/OG text): SaveOnSub shows one contact number only.
        for a, b in set(BD_PHONE.findall(text.translate(BN_DIGITS))):
            if "880" + a + b != WA_NUMBER:
                errors.append(f"contact-display: {rel} shows 0{a}{b}")
        for _q, href in HREF.findall(text):
            if href.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
                continue
            tgt = resolve(page, href)
            if tgt is None:
                errors.append(f"links: {rel} -> {href} (missing)")
            elif tgt and tgt != page:
                inbound[tgt.relative_to(SITE).as_posix()] += 1
        canons = [HREF_ATTR.search(c).group(1) for c in CANON.findall(text) if HREF_ATTR.search(c)]
        types: list = []
        offers: list = []
        for blob in LDJSON.findall(text):
            try:
                walk_types(json.loads(blob), types, offers)
            except json.JSONDecodeError as exc:
                errors.append(f"schema: {rel} JSON-LD does not parse ({exc.msg})")
        for bad in ("AggregateRating", "Review"):
            if bad in types:
                errors.append(f"schema: {rel} has {bad} without measured evidence")
        if offers:
            shown = visible_amounts(text)
            for o in offers:
                price = str(o.get("price", "")).split(".")[0]
                if o.get("priceCurrency") not in (None, "BDT"):
                    errors.append(f"schema: {rel} Offer currency {o.get('priceCurrency')}")
                if price and price not in shown:
                    errors.append(f"schema: {rel} Offer price {price} not visible on page")
        if intent(rel) == "other-unit-inquiry" and visible_amounts(text):
            if rel.startswith("modes/") or rel.startswith("bn/modes/"):
                warnings.append(f"aips: {rel} shows a BDT estimate (open CEO item ISO-001)")
            else:
                errors.append(f"aips: {rel} shows a BDT price")
        title = TITLE.search(text)
        info[rel] = {
            "url": url_of(page), "canonical": canons, "noindex": bool(NOINDEX.search(text)),
            "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "",
            "alternates": {h.lower(): u for h, u in ALT.findall(text)},
            "types": sorted(set(types)), "offers": len(offers),
        }
    indexable = {}
    for rel, i in info.items():
        if i["noindex"] or rel in ("404.html", "offline.html"):
            continue
        if len(i["canonical"]) != 1:
            errors.append(f"canonical: {rel} has {len(i['canonical'])} canonical tags")
            continue
        c = i["canonical"][0]
        if not c.startswith(BASE + "/"):
            errors.append(f"canonical: {rel} canonical off-domain {c}")
        if c == i["url"]:
            indexable[c] = rel
    titles = collections.defaultdict(list)
    for c, rel in indexable.items():
        titles[info[rel]["title"]].append(rel)
    for t, rels in titles.items():
        if len(rels) > 1:
            errors.append(f"canonical: duplicate title on {len(rels)} indexable pages: {', '.join(rels[:3])}")
    by_url = {i["url"]: rel for rel, i in info.items()}
    for rel, i in info.items():
        if rel not in indexable.values():
            continue
        for lang, alt in i["alternates"].items():
            if lang == "x-default" or alt == i["url"]:
                continue
            other = by_url.get(alt)
            if other is None:
                errors.append(f"hreflang: {rel} {lang} -> {alt} (missing page)")
            elif i["url"] not in info[other]["alternates"].values():
                errors.append(f"hreflang: {rel} -> {other} not reciprocal")
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8") if (SITE / "sitemap.xml").exists() else ""
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    if not locs:
        errors.append("sitemap: sitemap.xml missing or empty")
    for loc, n in collections.Counter(locs).items():
        if n > 1:
            errors.append(f"sitemap: duplicate {loc}")
        rel = by_url.get(loc)
        if rel is None:
            errors.append(f"sitemap: {loc} has no staged page")
        elif loc not in indexable:
            errors.append(f"sitemap: {loc} is noindex or not self-canonical")
    if manifest_path:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        rows = []
        for rel, i in sorted(info.items()):
            rows.append({
                "page_id": rel, "url": i["url"], "intent": intent(rel), "locale": "bn" if rel.startswith("bn") else "en",
                "canonical": i["canonical"][0] if i["canonical"] else None, "index": i["url"] in indexable,
                "in_sitemap": i["url"] in locs, "title": i["title"], "schema_types": i["types"],
                "offers": i["offers"], "inbound_internal_links": inbound.get(rel, 0), "build_sha": sha,
            })
        manifest_path.write_text(json.dumps({"pages": len(rows), "indexable": len(indexable), "sitemap": len(locs),
                                             "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    return errors


def main(argv: list[str]) -> int:
    out = None
    if "--manifest" in argv:
        out = Path(argv[argv.index("--manifest") + 1])
    if not SITE.is_dir():
        print("[release-audit] FAIL — _site missing; run build_site.py first")
        return 1
    warnings: list[str] = []
    errors = audit(out, warnings)
    for w in warnings:
        print("  WARN " + w)
    if errors:
        groups = collections.Counter(e.split(":", 1)[0] for e in errors)
        print(f"[release-audit] FAIL — {len(errors)} problem(s): {dict(groups)}")
        for e in errors[:60]:
            print("  " + e)
        return 1
    print("[release-audit] PASS — private files, WhatsApp, links, sitemap, canonical, hreflang, schema, AIPS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
