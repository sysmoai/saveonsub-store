"""Every priced product page shows support/refund terms before payment, with no invented promise."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
MARK = 'data-coverage-block="1"'


def catalog():
    t = (SITE / "assets" / "catalog.js").read_text(encoding="utf-8")
    i = t.index("const CATALOG = ") + len("const CATALOG = ")
    return {p["id"]: p for p in json.JSONDecoder().raw_decode(t[i:])[0]["products"]}


@unittest.skipUnless((SITE / "p" / "chatgpt-plus.html").exists(), "run python build_site.py first")
class CoverageDisclosure(unittest.TestCase):
    def test_every_priced_product_page_has_one_block_in_both_languages(self):
        cat = catalog()
        n = 0
        for d in ("p", "bn/p"):
            for f in (SITE / d).glob("*.html"):
                p = cat.get(f.stem)
                if p and p.get("plans"):
                    t = f.read_text(encoding="utf-8")
                    self.assertEqual(t.count(MARK), 1, str(f))
                    blk = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)
                    up = "../" if d == "p" else "../../"
                    self.assertIn(f'href="{up}refund"', blk)
                    self.assertIn(f'href="{up}warranty"', blk)
                    self.assertNotIn(".html", blk)  # clean URLs only (link_hygiene)
                    n += 1
        self.assertGreaterEqual(n, 100)

    def test_no_invented_period_or_guarantee(self):
        cfg = json.loads((ROOT / "ops/seo/control/coverage-periods.json").read_text(encoding="utf-8"))
        t = (SITE / "p" / "chatgpt-plus.html").read_text(encoding="utf-8")
        blk = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)
        self.assertIn("confirmed in writing for your order before you pay", blk) if not cfg else None
        self.assertNotRegex(blk, r"\b\d+\s*(day|days|hour|hours|month)\b")
        for bad in ("guarantee", "lifetime", "official reseller", "authorized"):
            self.assertNotIn(bad, blk.lower())

    def test_every_plan_listed_and_only_shared_rows_carry_provider_disclosure(self):
        cat = catalog()
        for d, marker in (("p", "not provided or endorsed by"), ("bn/p", "দেয় না বা অনুমোদন করে না")):
            for pid in ("chatgpt-plus", "claude-pro", "canva-pro"):
                t = (SITE / d / f"{pid}.html").read_text(encoding="utf-8")
                blk = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)
                for pl in cat[pid]["plans"]:
                    row = re.search(r'<li data-plan-id="' + re.escape(pl["plan_id"]) + r'">.*?</li>', blk, re.S)
                    self.assertIsNotNone(row, f"{pid}/{pl['plan_id']} row missing")
                    self.assertEqual(marker in row.group(0), pl["type"] == "shared", f"{d}/{pid}/{pl['plan_id']}")

    def test_plan_specific_period_only_from_config(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("cd", ROOT / "coverage_disclosure.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        prod = catalog()["chatgpt-plus"]
        first = prod["plans"][0]["plan_id"]
        cfg = {"chatgpt-plus": {first: {"en": "TEST-PERIOD-X", "bn": "টেস্ট"}}}
        html = mod.block("en", prod, cfg)
        self.assertEqual(html.count("TEST-PERIOD-X"), 1)
        self.assertEqual(html.count("confirmed in writing for your order before you pay"), len(prod["plans"]) - 1)

    def test_whatsapp_cta_uses_official_number_only(self):
        t = (SITE / "p" / "google-ai-pro.html").read_text(encoding="utf-8")
        blk = re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)
        self.assertIn("https://wa.me/8801305869242", blk)
        self.assertEqual(len(re.findall(r"wa\.me/(\d+)", blk)), 1)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless((SITE / "p" / "chatgpt-plus.html").exists(), "run python build_site.py first")
class ProviderSharingTerms(unittest.TestCase):
    """Shared rows of OpenAI/Anthropic products cite the provider's own sharing rule, dated and linked."""

    cfg = json.loads((ROOT / "ops/seo/control/provider-sharing-terms.json").read_text(encoding="utf-8"))

    def block(self, d, pid):
        t = (SITE / d / f"{pid}.html").read_text(encoding="utf-8")
        return re.search(r'<section[^>]*' + re.escape(MARK) + r'.*?</section>', t, re.S).group(0)

    def test_shared_rows_cite_provider_rule_in_both_languages(self):
        for pid, rule in ((k, v) for k, v in self.cfg.items() if not k.startswith("_")):
            for d, lang in (("p", "en"), ("bn/p", "bn")):
                blk = self.block(d, pid)
                shared = [li for li in re.findall(r"<li .*?</li>", blk, re.S) if "Shared" in li or "শেয়ার্ড" in li]
                self.assertTrue(shared, pid)
                for li in shared:
                    self.assertIn(rule["source_url"], li)
                    self.assertIn(rule[lang].replace("&", "&amp;"), li)  # exact dated sentence from the config

    def test_personal_rows_carry_no_sharing_warning(self):
        for d in ("p", "bn/p"):
            blk = self.block(d, "chatgpt-plus")
            personal = [li for li in re.findall(r"<li .*?</li>", blk, re.S) if "shared" not in li.split(">")[0]]
            self.assertTrue(personal)
            for li in personal:
                self.assertNotIn("openai.com/policies", li)

    def test_sources_are_official_https(self):
        for k, v in self.cfg.items():
            if k.startswith("_"):
                continue
            self.assertTrue(v["source_url"].startswith("https://"))
            self.assertRegex(v["source_url"], r"openai\.com|anthropic\.com")
