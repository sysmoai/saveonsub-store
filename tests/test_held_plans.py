"""CEO card A (14 Nov 2026): held shared plans take no new orders anywhere on the staged site."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pricebook import load_policy  # noqa: E402

POLICY = ROOT / "ops" / "PRICING-V2-2026-09-17.json"
HELD = json.loads((ROOT / "ops" / "HELD-PLANS-2026-11-14.json").read_text(encoding="utf-8"))["held_plans"]
SITE = ROOT / "_site"


class EffectivePricebook(unittest.TestCase):
    def test_held_plans_removed_but_pricebook_file_untouched(self):
        raw = json.loads(POLICY.read_text(encoding="utf-8"))["approved_products"]
        eff = load_policy(POLICY)["approved_products"]
        for pid, ids in HELD.items():
            raw_ids = {p["plan_id"] for p in raw[pid]["plans"]}
            eff_ids = {p["plan_id"] for p in eff[pid]["plans"]}
            self.assertTrue(set(ids) <= raw_ids, pid)  # still in the CEO-approved file
            self.assertFalse(set(ids) & eff_ids, pid)  # gone from every build and audit
            self.assertEqual({h["plan_id"] for h in eff[pid]["held_plans"]}, set(ids))
            if set(ids) == raw_ids:  # fully held product fails closed to inquiry
                self.assertEqual("inquiry", eff[pid]["mode"], pid)
            else:
                self.assertTrue(eff[pid]["plans"], f"{pid} keeps its non-held plans")

    def test_all_shared_credential_offers_restricted_by_default(self):
        """A CEO-approved price does not grant provider permission to share logins."""
        raw = json.loads(POLICY.read_text(encoding="utf-8"))["approved_products"]
        effective = load_policy(POLICY)["approved_products"]
        seen_shared = 0
        for pid, rule in raw.items():
            shared = {p["plan_id"] for p in rule.get("plans") or []
                      if p.get("access_type") == "shared"}
            active = {p["plan_id"] for p in effective[pid].get("plans") or []}
            held = {p["plan_id"] for p in effective[pid].get("held_plans") or []}
            seen_shared += len(shared)
            self.assertFalse(shared & active, pid)
            self.assertTrue(shared <= held, pid)
            if shared and not active:
                self.assertEqual("inquiry", effective[pid]["mode"], pid)
        self.assertGreater(seen_shared, 0)

    def test_sku_count_metadata_matches_rows(self):
        raw = json.loads(POLICY.read_text(encoding="utf-8"))
        count = sum(len(x.get("plans") or []) for x in raw["approved_products"].values())
        self.assertEqual(raw["commercial_hold"]["approved_sku_count"], count)
        js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("planId.length>0 && pl.plan_id===planId", js)
        self.assertNotIn("!planId || pl.plan_id===undefined", js)

    def test_canonical_sku_count_mismatch_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = d / "PRICING-V2-2026-09-17.json"
            p.write_text(json.dumps({
                "commercial_hold": {"approved_sku_count": 2},
                "approved_products": {"x": {"mode": "fixed", "plans": [
                    {"plan_id": "a", "label": "A", "bdt": 1, "access_type": "shared"}
                ]}}
            }), encoding="utf-8")
            (d / "HELD-PLANS-2026-11-14.json").write_text(
                json.dumps({"held_plans": {"x": ["a"]}}), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "approved_sku_count mismatch"):
                load_policy(p)

    def test_v40_holds_preserved_and_business_shared_held(self):
        # Four prior CEO card-A holds must remain, plus the new 17 Nov
        # provider-rights HOLD and the eight below-cost personal plans and two
        # Cursor plans closed to new customers (25 Nov 2026); never broaden or silently drop these IDs.
        self.assertEqual(HELD, {
            "chatgpt-plus": [
                "starter-shared-6-8-users-1-month",
                "premium-shared-2-3-users-1-month",
            ],
            "chatgpt-pro": ["premium-shared-5-6-1-month"],
            "claude-pro": ["premium-shared-2-3-1-month"],
            "chatgpt-business": ["premium-shared-2-3-1-month"],
            "runway": ["standard-personal-625-credits-1-month", "pro-personal-2250-credits-1-month", "unlimited-personal-1-month"],
            "replit-core": ["core-personal-1-month"],
            "cursor": ["cursor-pro-personal-1-month", "pro-personal-3x-credits-1-month"],
            "suno": ["pro-personal-500-songs-1-month", "premier-personal-2000-songs-1-month"],
            "github-copilot": ["pro-personal-your-github-1-month"],
            "elevenlabs": ["starter-personal-30k-chars-1-month"],
        })

    def test_unknown_held_plan_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "p.json").write_text(json.dumps({"approved_products": {"x": {"mode": "fixed", "plans": [
                {"plan_id": "a", "label": "A", "bdt": 1}]}}}), encoding="utf-8")
            (d / "HELD-PLANS-2026-11-14.json").write_text(json.dumps({"held_plans": {"x": ["nope"]}}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_policy(d / "p.json")

    def test_missing_canonical_held_file_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "PRICING-V2-2026-09-17.json"
            p.write_text(json.dumps({"approved_products": {"x": {"mode": "fixed", "plans": [
                {"plan_id": "a", "label": "A", "bdt": 1}]}}}), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "required HOLD manifest missing"):
                load_policy(p)

    def test_invalid_canonical_held_manifest_fails_closed(self):
        import tempfile
        for bad in ("{", '{"held_plans": {}}', '{"held_plans": {"x": []}}'):
            with self.subTest(manifest=bad), tempfile.TemporaryDirectory() as d:
                d = Path(d)
                p = d / "PRICING-V2-2026-09-17.json"
                p.write_text(json.dumps({"approved_products": {"x": {"mode": "fixed", "plans": [
                    {"plan_id": "a", "label": "A", "bdt": 1}]}}}), encoding="utf-8")
                (d / "HELD-PLANS-2026-11-14.json").write_text(bad, encoding="utf-8")
                with self.assertRaises(SystemExit):
                    load_policy(p)

    def test_no_held_file_means_no_hold(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "p.json"
            p.write_text(json.dumps({"approved_products": {"x": {"mode": "fixed", "plans": [
                {"plan_id": "a", "label": "A", "bdt": 1}]}}}), encoding="utf-8")
            self.assertEqual(len(load_policy(p)["approved_products"]["x"]["plans"]), 1)


@unittest.skipUnless((SITE / "p" / "chatgpt-plus.html").exists(), "run python build_site.py first")
class StagedSite(unittest.TestCase):
    def test_held_plans_absent_from_catalog_js_pages_and_llms(self):
        raw = json.loads(POLICY.read_text(encoding="utf-8"))["approved_products"]
        js = (SITE / "assets" / "catalog.js").read_text(encoding="utf-8")
        for pid, ids in HELD.items():
            price_of = {p["plan_id"]: p["bdt"] for p in raw[pid]["plans"]}
            for plan_id in ids:
                self.assertNotIn(f'"plan_id":"{plan_id}"', self._entry(js, pid), (pid, plan_id))
            for rel in (f"p/{pid}.html", f"bn/p/{pid}.html"):
                page = (SITE / rel).read_text(encoding="utf-8")
                shown = {int(x.replace(",", "")) for x in re.findall(r"৳\s?([\d,]+)", page)}
                for plan_id in ids:
                    self.assertNotIn(price_of[plan_id], shown, f"{rel}: held plan price still shown")
                self.assertNotIn(f"cartAdd('{pid}','{raw[pid]['plans'][0]['label']}'", page)
                self.assertIn('data-held-plans="1"', page, rel)

    @staticmethod
    def _entry(js, pid):
        i = js.index(f'"id":"{pid}"')
        j = js.find('"id":"', i + 10)
        return js[i:j if j > 0 else len(js)]

    def test_sticky_from_price_uses_remaining_plans(self):
        page = (SITE / "p" / "chatgpt-plus.html").read_text(encoding="utf-8")
        bar = re.search(r'class="bb-price">([^<]*)', page).group(1)
        self.assertEqual(bar, "৳3,390")

    def test_notice_does_not_re_advertise_a_held_plan(self):
        for rel in ("p/chatgpt-plus.html", "bn/p/claude-pro.html"):
            page = (SITE / rel).read_text(encoding="utf-8")
            note = re.search(r'data-held-plans="1">(.*?)</div>', page, re.S).group(1)
            self.assertNotRegex(note, r"[0-9০-৯]|৳|<a |<button")


if __name__ == "__main__":
    unittest.main()
