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
            self.assertTrue(eff[pid]["plans"], f"{pid} keeps its non-held plans")

    def test_only_the_four_v40_tiers_are_held(self):
        self.assertEqual(sum(len(v) for v in HELD.values()), 4)
        self.assertEqual(set(HELD), {"chatgpt-plus", "chatgpt-pro", "claude-pro"})

    def test_unknown_held_plan_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "p.json").write_text(json.dumps({"approved_products": {"x": {"mode": "fixed", "plans": [
                {"plan_id": "a", "label": "A", "bdt": 1}]}}}), encoding="utf-8")
            (d / "HELD-PLANS-2026-11-14.json").write_text(json.dumps({"held_plans": {"x": ["nope"]}}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_policy(d / "p.json")

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
