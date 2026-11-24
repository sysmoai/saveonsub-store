"""V22 Wave 1: discovery search (assets/search.js) relevance and commercial safety.

Runs the real browser script in a Node VM against the governed public catalog
(assets/catalog.js, or the staged _site copy when present). Restricted plan ids
come from pricebook.load_policy(), i.e. the same 57 held shared SKUs the
release gate checks. SOS_SEARCH_JS may point at a mutated copy (mutation test).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from pricebook import load_policy

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "search_vm.cjs"
SEARCH_JS = Path(os.environ.get("SOS_SEARCH_JS") or ROOT / "assets" / "search.js")
CATALOG_JS = ROOT / "_site" / "assets" / "catalog.js"
if not CATALOG_JS.is_file():
    CATALOG_JS = ROOT / "assets" / "catalog.js"
NODE = shutil.which("node")


def held_skus() -> set[tuple[str, str]]:
    """(product_id, plan_id) pairs; plan ids repeat across products, so pairs are the SKU unit."""
    policy = load_policy(ROOT / "ops" / "PRICING-V2-2026-09-17.json")
    return {(pid, row["plan_id"]) for pid, rule in policy["approved_products"].items()
            for row in rule.get("held_plans") or []}


def run(queries, extra_products=None, perf_runs=0):
    req = {"catalog_js": str(CATALOG_JS), "search_js": str(SEARCH_JS), "queries": queries,
           "extra_products": extra_products or [], "perf_runs": perf_runs}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(req, fh, ensure_ascii=False)
        path = fh.name
    try:
        proc = subprocess.run([NODE, str(HARNESS), path], capture_output=True, text=True, encoding="utf-8", check=True)
    finally:
        os.unlink(path)
    return json.loads(proc.stdout)


def q(text, **opts):
    return {"q": text, "opts": opts}


@unittest.skipUnless(NODE, "node is required for the search VM harness")
class SearchRelevance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queries = [
            q("ChatGPT Plus"), q("chatgtp"), q("midjorney"), q("canav"), q("chat gpt"),
            q("chobi"), q("gaan"), q("ভিডিও"), q("চ্যাটজিপিটি"), q("porashona"),
            q("zzzzqqqxx"), q("netflx"), q(""),
        ]
        cls.out = run(cls.queries)
        cls.by_q = {r["q"]: r for r in cls.out["results"]}
        cls.cat = {d["id"]: d["category"] for d in cls.out["index"]}

    def ids(self, text):
        return self.by_q[text]["ids"]

    def test_exact_name_ranks_first(self):
        self.assertEqual(self.ids("ChatGPT Plus")[0], "chatgpt-plus")

    def test_typo_tolerance(self):
        self.assertTrue(any(i.startswith("chatgpt") for i in self.ids("chatgtp")), self.ids("chatgtp"))
        self.assertEqual(self.ids("midjorney")[0], "midjourney")  # product outranks the bundle containing it
        self.assertTrue(any("canva" in i for i in self.ids("canav")), self.ids("canav"))

    def test_compound_query(self):
        self.assertTrue(self.ids("chat gpt") and self.ids("chat gpt")[0].startswith("chatgpt"), self.ids("chat gpt"))

    def test_banglish_and_bangla_use_cases(self):
        for text, category in (("chobi", "AI Image & Design"), ("gaan", "AI Voice & Music"),
                               ("ভিডিও", "AI Video"), ("porashona", "Education & Career")):
            ids = self.ids(text)
            self.assertTrue(ids, text)
            self.assertTrue(any(self.cat[i] == category for i in ids), (text, ids))
        self.assertTrue(any(i.startswith("chatgpt") for i in self.ids("চ্যাটজিপিটি")))

    def test_empty_and_no_result(self):
        self.assertEqual(self.ids("zzzzqqqxx"), [])
        self.assertEqual(self.by_q["zzzzqqqxx"]["dym"], [])
        self.assertTrue("netflix" in self.ids("netflx") or "netflix" in self.by_q["netflx"]["dym"])
        self.assertEqual(len(self.ids("")), len(self.out["index"]))

    def test_other_business_units_never_orderable(self):
        other = [d for d in self.out["index"] if d["id"].startswith("aips" + "-")]
        if "_site" in CATALOG_JS.parts:  # staged artifact: quarantine removed them entirely
            self.assertFalse(other)
        self.assertFalse([d["id"] for d in other if d["orderable"]])


@unittest.skipUnless(NODE, "node is required for the search VM harness")
class SearchCommercialSafety(unittest.TestCase):
    def test_no_restricted_sku_reaches_index_or_cards(self):
        skus = held_skus()
        self.assertGreaterEqual(len(skus), 57, "restricted inventory shrank; re-review this test")
        held = {plan for _, plan in skus}
        texts = ["shared", "starter shared", "team shared", "chatgpt", "canva", "gemini", "", "cheap"]
        texts += sorted(held)
        out = run([q(t) for t in texts] + [q(t, lang="bn") for t in texts[:4]])
        indexed = {(d["id"], pid) for d in out["index"] for pid in d["planIds"]}
        self.assertFalse(indexed & skus, sorted(indexed & skus)[:5])
        for r in out["results"]:
            self.assertNotIn("cartAdd", r["html"], r["q"])
            self.assertNotIn("onclick", r["html"], r["q"])
            leaked = [pid for pid in held if pid in r["html"]]
            self.assertFalse(leaked, (r["q"], leaked[:3]))
            self.assertNotRegex(r["html"], re.compile(r"shared", re.I), r["q"])

    def test_tampered_or_unverified_plans_fail_closed(self):
        base = {"category": "AI Assistants", "icon": "x", "seo": {}, "status": "live"}
        bad = [
            dict(base, id="t-shared-type", name="Tamper One", sellability="approved",
                 plans=[{"plan_id": "p1", "label": "L", "bdt": 100, "type": "shared"}]),
            dict(base, id="t-shared-id", name="Tamper Two", sellability="approved",
                 plans=[{"plan_id": "starter-shared-3", "label": "L", "bdt": 100, "type": "personal"}]),
            dict(base, id="t-zero", name="Tamper Three", sellability="approved",
                 plans=[{"plan_id": "p3", "label": "L", "bdt": 0, "type": "personal"}]),
            dict(base, id="t-string", name="Tamper Four", sellability="approved",
                 plans=[{"plan_id": "p4", "label": "L", "bdt": "100", "type": "personal"}]),
            dict(base, id="t-noid", name="Tamper Five", sellability="approved",
                 plans=[{"label": "L", "bdt": 100, "type": "personal"}]),
            dict(base, id="t-inquiry", name="Tamper Six", sellability="inquiry_only",
                 plans=[{"plan_id": "p6", "label": "L", "bdt": 100, "type": "personal"}]),
            dict(base, id="t-request", name="Tamper Seven", sellability="approved", request_price=True,
                 plans=[{"plan_id": "p7", "label": "L", "bdt": 100, "type": "personal"}]),
            dict(base, id="t-negative", name="Tamper Eight", sellability="approved",
                 plans=[{"plan_id": "p8", "label": "L", "bdt": -5, "type": "personal"}]),
        ]
        out = run([q("tamper"), q("tamper", avail="orderable"), q("tamper", maxBdt=500)], extra_products=bad)
        idx = {d["id"]: d for d in out["index"]}
        for p in bad:
            self.assertFalse(idx[p["id"]]["orderable"], p["id"])
            self.assertIsNone(idx[p["id"]]["minBdt"], p["id"])
        everything, orderable, budget = out["results"]
        self.assertEqual(len(everything["ids"]), len(bad))
        self.assertEqual(orderable["ids"], [])
        self.assertEqual(budget["ids"], [])
        self.assertEqual(everything["html"].count("Price on request"), len(bad))
        self.assertNotIn("৳", everything["html"])

    def test_filters_and_sort(self):
        # Synthetic approved products keep this independent of the committed (pre-build) catalog state.
        base = {"category": "AI Writing", "icon": "x", "seo": {}, "status": "live", "sellability": "approved"}
        synth = [dict(base, id=f"synth-{i}", name=f"Synthfilter {i}",
                      plans=[{"plan_id": f"s{i}", "label": "L", "bdt": bdt, "type": t}])
                 for i, (bdt, t) in enumerate(((300, "personal"), (900, "team"), (4000, "personal")))]
        out = run([q("", avail="orderable"), q("", maxBdt=500), q("", sort="price", avail="orderable"),
                   q("", type="team"), q("", avail="inquiry")], extra_products=synth)
        orderable, cheap, by_price, team, inquiry = out["results"]
        self.assertTrue({"synth-0", "synth-1", "synth-2"} <= set(orderable["ids"]))
        self.assertIn("synth-0", cheap["ids"])
        self.assertNotIn("synth-2", cheap["ids"])
        self.assertIn("synth-1", team["ids"])
        self.assertTrue(all(m and m > 0 for m in orderable["minBdt"]))
        self.assertTrue(all(m is not None and m <= 500 for m in cheap["minBdt"]))
        self.assertEqual(by_price["minBdt"], sorted(by_price["minBdt"]))
        types = {d["id"]: d["types"] for d in out["index"]}
        self.assertTrue(all("team" in types[i] for i in team["ids"]))
        self.assertTrue(all(m is None for m in inquiry["minBdt"]))

    def test_prices_match_governed_catalog(self):
        text = CATALOG_JS.read_text(encoding="utf-8")
        catalog = json.loads(re.search(r"const CATALOG = (.*);\s*$", text, re.S).group(1))
        expected = {}
        for p in catalog["products"]:
            if p.get("sellability") == "approved" and p.get("plans"):
                expected[p["id"]] = min(pl["bdt"] for pl in p["plans"])
        out = run([])
        got = {d["id"]: d["minBdt"] for d in out["index"] if d["orderable"]}
        self.assertEqual(got, expected)

    def test_search_keeps_no_history_and_makes_no_requests(self):
        src = SEARCH_JS.read_text(encoding="utf-8")
        for token in ("localStorage", "sessionStorage", "document.cookie", "fetch(", "XMLHttpRequest",
                      "sendBeacon", "gtag(", "fbq(", "cartAdd("):
            self.assertNotIn(token, src, token)

    def test_search_is_fast_on_slow_devices(self):
        out = run([], perf_runs=2000)
        self.assertLess(out["perf_ms"], 4000, out["perf_ms"])  # ~2 ms/query budget even with 4x CPU throttle


if __name__ == "__main__":
    unittest.main()
