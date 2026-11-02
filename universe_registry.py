#!/usr/bin/env python3
"""Global product-universe registry: other portfolio catalogs -> SaveOnSub crosswalk.

Reads research sources locally (never into a model context) and classifies every
source record against SaveOnSub's own catalog and CEO pricebook:

  APPROVED_SELLABLE        family + access type sold under the SaveOnSub pricebook
  INQUIRY_ONLY             family exists on SaveOnSub, but no approved plan for it
  RESEARCH_ONLY            not a SaveOnSub product (or another unit's own package)
  NEEDS_FACT_VERIFICATION  no official provider URL in the source

Source prices, sales copy, warranties, contacts and claims are NEVER read into
the output: SaveOnSub price authority is only ops/PRICING-V2-*.json.
BLOCKED_PROVIDER_POLICY / DISCONTINUED need verified provider evidence and are
assigned by reviewers, not inferred here; shared-access rows carry a review flag.

Usage:
  python universe_registry.py --aips <AI-Premium-Shop checkout> [--atlas FILE.psv] [--private-out FILE]

--atlas takes a compact pipe-separated export of the AIPS ATLAS Notion database
(name|category index|status/access index|website host; the legend is in the
file's # header lines). Price columns are never exported.

Writes the family-level, public-safe crosswalk to ops/seo/control/universe-families.json.
The record-level registry (with source ids) goes only to --private-out.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog.json"
POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
PUBLIC_OUT = ROOT / "ops" / "seo" / "control" / "universe-families.json"
AIPS_PRODUCTS = Path("artifacts/aips-landing/data/products.json")
AIPS_SERVICES = Path("artifacts/aips-landing/data/services.json")

TRAILING = {"pro", "premium", "plus", "max", "go", "business", "core", "career", "elements",
            "ai", "agent", "labs", "cloud", "credits", "team", "lite", "standard", "ultra", "basic",
            "starter", "enterprise", "20x", "5x", "io", "new", "app", "personal", "shared", "portfolio"}
# Source names that reduce to a different spelling of an already-known family.
FAMILY_ALIAS = {"adobe firefly": "adobe", "adobe creative": "adobe", "adobe express": "adobe express",
                "github copilot": "github", "mistral le chat": "le chat", "notion ai notion": "notion",
                "opusclip": "opus", "supergrok": "grok", "xai grok": "grok", "microsoft copilot": "microsoft",
                "microsoft copilot azure": "microsoft", "minimax hailuo": "hailuo", "freepik magnific": "freepik",
                "alibaba qwen": "qwen", "veed": "veed", "google deepmind gemini": "google",
                "meta ai llama": "meta", "playht playai": "playht", "bolt": "bolt", "claude fable 5 api": "claude",
                "claude opus 4 6": "claude", "higgsfield ultra": "higgsfield", "higgsfield plus": "higgsfield"}
# SaveOnSub ids whose product name does not reduce to the provider family name.
SOS_FAMILY = {"supergrok": "grok", "mistral-pro": "le chat", "github-copilot": "github",
              "copilot-pro": "microsoft", "adobe-firefly": "adobe", "adobe-creative-cloud": "adobe",
              "opus-clip": "opus", "google-ai-pro": "google", "google-ai-plus": "google",
              "notion-ai": "notion"}
# Source category -> capability group (V13 section 4); refined per family later.
CAPABILITY = {
    "ai-assistant": "AI Chat, Reasoning & Assistants", "ai-image": "AI Image Generation & Editing",
    "ai-design": "Graphic Design, Branding & Creative Assets", "ai-video": "AI Video Generation",
    "ai-voice-music": "AI Voice, Speech & Music", "ai-code": "AI Coding Assistants & IDEs",
    "ai-writing": "AI Writing, Editing & Copywriting", "ai-workspace": "AI Productivity, Documents & Meetings",
    "bundles": "Bundles",
    "AI Business & Data": "AI Data Analytics, BI & Research", "API & Model Platforms": "AI APIs, Model Platforms & Developer Cloud",
    "AI Search": "AI Search, Research & Deep Research", "AI Productivity & Workspace": "AI Productivity, Documents & Meetings",
    "AI Chat & Assistants": "AI Chat, Reasoning & Assistants", "AI Audio & Voice": "AI Voice, Speech & Music",
    "AI Agents & Automation": "AI Agents, Automation & Workflows", "AI Research & Study": "AI Search, Research & Deep Research",
    "AI Marketing & SEO": "AI Marketing, Advertising & SEO", "AI Design & Presentation": "AI Presentations, Slides & Knowledge",
    "AI Code & Dev": "AI Coding Assistants & IDEs", "AI Image": "AI Image Generation & Editing",
    "AI Assistants": "AI Chat, Reasoning & Assistants", "AI Image & Design": "AI Image Generation & Editing",
    "AI Video": "AI Video Generation", "AI Voice & Music": "AI Voice, Speech & Music",
    "AI Code & Dev": "AI Coding Assistants & IDEs", "AI Writing": "AI Writing, Editing & Copywriting",
    "Workspace & Productivity": "AI Productivity, Documents & Meetings",
}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️]+")


def family_key(name: str) -> str:
    n = EMOJI.sub("", str(name or "")).lower()
    n = re.split(r"\s+—\s+|\s*\(", n)[0]
    n = re.sub(r"\.(ai|com|dev|app)\b", "", n)
    words = re.sub(r"[^a-z0-9]+", " ", n).split()
    while len(words) > 1 and words[-1] in TRAILING:
        words.pop()
    words = [w for i, w in enumerate(words) if i == 0 or w not in ("premium", "cloud")]
    key = " ".join(words)
    return FAMILY_ALIAS.get(key, key)


ATLAS_ACCESS = {"shared": "shared", "personal": "personal", "customer-owned": "personal", "official": "official"}


def load_atlas(path: Path) -> list[dict]:
    """Parse the compact ATLAS export into source rows shaped like the AIPS catalog."""
    legend, rows = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# categories:") or line.startswith("# status/access:"):
            key = "cat" if "categories" in line else "st"
            legend[key] = dict(item.strip().split(" ", 1) for item in line.split(":", 1)[1].split(";"))
        elif line.strip() and not line.startswith("#"):
            name, cat, st, host = (line.split("|") + ["", "", "", ""])[:4]
            status, access = legend["st"][st].split("/")
            rows.append({"id": f"atlas:{len(rows)}", "brand": name, "name": name, "category": legend["cat"][cat],
                         "accessType": "bundle" if "aipremiumshop.com" in host else ATLAS_ACCESS.get(access.lower(), "unknown"),
                         "sourceUrl": f"https://{host}" if host else "", "source_status": status,
                         "other_unit": "aipremiumshop.com" in host})
    return rows


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def sos_families(catalog: dict, policy: dict) -> dict[str, dict]:
    book = policy.get("approved_products") or {}
    fams: dict[str, dict] = {}
    for p in catalog.get("products", []):
        pid = p["id"]
        if pid.startswith(("aips-", "bundle-")):
            continue
        key = SOS_FAMILY.get(pid, family_key(p["name"]))
        rule = book.get(pid) or {}
        f = fams.setdefault(key, {"sos_products": [], "access_types": set(), "category": p.get("category")})
        f["sos_products"].append(pid)
        if rule.get("mode") == "fixed":
            f["access_types"].update(pl.get("access_type", "personal") for pl in rule.get("plans", []))
    return fams


def classify(row: dict, fam: dict | None) -> tuple[str, list[str]]:
    flags = []
    access = row.get("accessType") or "unknown"
    if access == "shared":
        flags.append("provider_rights_review")
    if row.get("source_status") == "Not-sellable":
        flags.append("not_sellable_per_source")
    if row.get("other_unit"):
        flags.append("other_unit_package")
        return "RESEARCH_ONLY", flags
    if row.get("brand") == "AIPS" or access in ("bundle", "service") or "Setup Service" in str(row.get("brand")):
        flags.append("other_unit_package" if row.get("brand") == "AIPS" else "service_candidate")
        return "RESEARCH_ONLY", flags
    if fam is None:
        if not row.get("sourceUrl"):
            return "NEEDS_FACT_VERIFICATION", flags
        return "RESEARCH_ONLY", flags
    if access in fam["access_types"]:
        return "APPROVED_SELLABLE", flags
    return "INQUIRY_ONLY", flags


def build(aips_root: Path, catalog: dict, policy: dict, atlas: Path | None = None) -> tuple[dict, dict]:
    rows = json.loads((aips_root / AIPS_PRODUCTS).read_text(encoding="utf-8"))["products"]
    for r in rows:
        r["_source"] = "aips-products"
    atlas_rows = load_atlas(atlas) if atlas else []
    for r in atlas_rows:
        r["_source"] = "aips-atlas"
    rows = rows + atlas_rows
    services = json.loads((aips_root / AIPS_SERVICES).read_text(encoding="utf-8"))
    services = services if isinstance(services, list) else services.get("services", [])
    fams = sos_families(catalog, policy)

    records, families = [], {}
    for row in rows:
        key = family_key(row.get("brand") or row.get("name"))
        fam = fams.get(key)
        status, flags = classify(row, fam)
        review = []
        if fam is None and status != "RESEARCH_ONLY" or (fam is None and "other_unit_package" not in flags):
            review = difflib.get_close_matches(key, list(fams), n=2, cutoff=0.8)
        records.append({
            "source": row["_source"], "source_id": row.get("id"), "family": key,
            "brand": row.get("brand"), "provider": row.get("provider"), "tier": row.get("tier"),
            "category": row.get("category"), "access_type": row.get("accessType"),
            "official_url": row.get("sourceUrl"), "source_date": row.get("lastVerifiedDate"),
            "classification": status, "flags": flags, "fuzzy_review": review,
            "sos_products": (fam or {}).get("sos_products", []),
        })
        f = families.setdefault(key, {
            "family": key, "brand": row.get("brand"), "provider": row.get("provider"),
            "official_url": row.get("sourceUrl"),
            "capability_group": CAPABILITY.get(row.get("category"), "Unmapped"),
            "sos_products": (fam or {}).get("sos_products", []),
            "source_records": 0, "classifications": collections.Counter(), "fuzzy_review": review,
            "flags_all": None,
        })
        # A flag holds for the family only when every one of its source records carries it.
        f["flags_all"] = set(flags) if f["flags_all"] is None else f["flags_all"] & set(flags)
        f["source_records"] += 1
        f["classifications"][status] += 1
        f["official_url"] = f["official_url"] or row.get("sourceUrl")

    for svc in services:
        records.append({"source": "aips-services", "source_id": svc.get("slug"), "family": "service:" + str(svc.get("slug")),
                        "brand": svc.get("name"), "classification": "RESEARCH_ONLY", "flags": ["service_candidate"]})

    for key, fam in fams.items():
        if key not in families:
            families[key] = {"family": key, "brand": None, "provider": None, "official_url": None,
                             "capability_group": CAPABILITY.get(fam["category"], fam["category"]),
                             "sos_products": fam["sos_products"], "source_records": 0,
                             "classifications": {}, "fuzzy_review": [], "sos_only": True}

    for f in families.values():
        f["flags_all"] = sorted(f.get("flags_all") or [])
        f["classifications"] = dict(f["classifications"])
        cls = f["classifications"]
        f["status"] = ("APPROVED_SELLABLE" if cls.get("APPROVED_SELLABLE") else
                       "INQUIRY_ONLY" if cls.get("INQUIRY_ONLY") else
                       "SOS_ONLY" if f.get("sos_only") else
                       "NEEDS_FACT_VERIFICATION" if cls.get("NEEDS_FACT_VERIFICATION") and not cls.get("RESEARCH_ONLY") else
                       "RESEARCH_ONLY")

    by = lambda items, k: dict(collections.Counter(x.get(k) for x in items).most_common())
    product_records = [r for r in records if r["source"] != "aips-services"]
    summary = {
        "sources": {"aips-products": {"records": len(rows) - len(atlas_rows), "sha256_16": sha(aips_root / AIPS_PRODUCTS)},
                    **({"aips-atlas": {"records": len(atlas_rows), "sha256_16": sha(atlas)}} if atlas else {}),
                    "aips-services": {"records": len(services), "sha256_16": sha(aips_root / AIPS_SERVICES)}},
        "source_records_total": len(records),
        "unique_source_brands": len({r["brand"] for r in product_records}),
        "families_by_source": {src: len({r["family"] for r in records if r["source"] == src})
                               for src in ("aips-products", "aips-atlas", "aips-services")},
        "atlas_only_families": sorted({r["family"] for r in records if r["source"] == "aips-atlas"}
                                      - {r["family"] for r in records if r["source"] == "aips-products"}),
        "families_total": len(families),
        "families_by_status": by(list(families.values()), "status"),
        "records_by_classification": by(records, "classification"),
        "records_by_access_type": by(product_records, "access_type"),
        "families_by_capability_group": by(list(families.values()), "capability_group"),
        "sos_families_matched": sum(1 for f in families.values() if f["sos_products"] and f["source_records"]),
        "sos_families_without_source": sorted(k for k, f in families.items() if f.get("sos_only")),
        "fuzzy_review": {k: f["fuzzy_review"] for k, f in families.items() if f["fuzzy_review"] and not f["sos_products"]},
        "unclassified_records": sum(1 for r in records if not r.get("classification")),
    }
    public = {"summary": summary,
              "families": sorted(families.values(), key=lambda f: (f["capability_group"], f["family"]))}
    return public, {"summary": summary, "records": records}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aips", required=True, type=Path)
    ap.add_argument("--atlas", type=Path)
    ap.add_argument("--private-out", type=Path)
    a = ap.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    public, private = build(a.aips, catalog, policy, a.atlas)
    if public["summary"]["unclassified_records"]:
        raise SystemExit("[universe] unclassified source records")
    PUBLIC_OUT.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUT.write_text(json.dumps(public, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.private_out:
        a.private_out.write_text(json.dumps(private, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = public["summary"]
    print(f"[universe] {s['source_records_total']} source records, {s['unique_source_brands']} brands, "
          f"{s['families_total']} families; {s['families_by_status']}; records {s['records_by_classification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
