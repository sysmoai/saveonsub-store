"""Synthetic tests: portfolio research rows never become SaveOnSub offers by themselves."""
import json
import tempfile
import unittest
from pathlib import Path

from universe_registry import build, family_key


class UniverseRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        data = root / "artifacts" / "aips-landing" / "data"
        data.mkdir(parents=True)
        rows = [
            {"id": "a", "brand": "ChatGPT", "accessType": "personal", "sourceUrl": "https://openai.com", "price": 1, "category": "ai-assistant"},
            {"id": "b", "brand": "ChatGPT", "accessType": "shared", "sourceUrl": "https://openai.com", "price": 1, "category": "ai-assistant"},
            {"id": "c", "brand": "Zapier", "accessType": "personal", "sourceUrl": "https://zapier.com", "price": 1, "category": "ai-workspace"},
            {"id": "d", "brand": "Mystery", "accessType": "personal", "category": "ai-workspace"},
            {"id": "e", "brand": "AIPS", "accessType": "bundle", "sourceUrl": "", "category": "bundles"},
        ]
        (data / "products.json").write_text(json.dumps({"products": rows}), encoding="utf-8")
        (data / "services.json").write_text(json.dumps([{"slug": "setup", "name": "Setup", "priceBdt": 9}]), encoding="utf-8")
        self.root = root
        self.catalog = {"products": [{"id": "chatgpt-plus", "name": "ChatGPT Plus", "category": "AI Assistants"}]}
        self.policy = {"approved_products": {"chatgpt-plus": {"mode": "fixed", "plans": [{"label": "P", "bdt": 1, "access_type": "personal"}]}}}

    def tearDown(self):
        self.tmp.cleanup()

    def records(self):
        return {r["source_id"]: r for r in build(self.root, self.catalog, self.policy)[1]["records"]}

    def test_family_key_strips_tier_words(self):
        self.assertEqual("chatgpt", family_key("ChatGPT Plus"))
        self.assertEqual("otter", family_key("Otter.ai Pro"))
        self.assertEqual("pika", family_key("Pika Labs"))

    def test_classification(self):
        r = self.records()
        self.assertEqual("APPROVED_SELLABLE", r["a"]["classification"])
        self.assertEqual("INQUIRY_ONLY", r["b"]["classification"])
        self.assertIn("provider_rights_review", r["b"]["flags"])
        self.assertEqual("RESEARCH_ONLY", r["c"]["classification"])
        self.assertEqual("NEEDS_FACT_VERIFICATION", r["d"]["classification"])
        self.assertIn("other_unit_package", r["e"]["flags"])
        self.assertEqual("RESEARCH_ONLY", r["setup"]["classification"])

    def test_no_source_record_dropped(self):
        self.assertEqual(6, build(self.root, self.catalog, self.policy)[0]["summary"]["source_records_total"])

    def test_atlas_rows_classified(self):
        atlas = self.root / "atlas.psv"
        atlas.write_text("\n".join([
            "# categories: 0 AI Chat & Assistants;1 AI Agents & Automation",
            "# status/access: 0 Live/Personal;1 Not-sellable/Customer-owned;2 Planned/Shared",
            "ChatGPT Plus — Personal|0|0|chatgpt.com", "Palantir|1|1|palantir.com",
            "Student Pack|0|2|aipremiumshop.com", "Zapier|1|2|zapier.com"]) + "\n", encoding="utf-8")
        public, private = build(self.root, self.catalog, self.policy, atlas)
        recs = {r["brand"]: r for r in private["records"] if r["source"] == "aips-atlas"}
        self.assertEqual("APPROVED_SELLABLE", recs["ChatGPT Plus — Personal"]["classification"])
        self.assertIn("not_sellable_per_source", recs["Palantir"]["flags"])
        self.assertIn("other_unit_package", recs["Student Pack"]["flags"])
        self.assertEqual(4, public["summary"]["sources"]["aips-atlas"]["records"])
        # Zapier also has an unflagged personal row, so the family-level flag set is empty.
        self.assertEqual([], next(f for f in public["families"] if f["family"] == "zapier")["flags_all"])
        self.assertIn("not_sellable_per_source", next(f for f in public["families"] if f["family"] == "palantir")["flags_all"])

    def test_seed_rows_rejoined_and_classified(self):
        seeds = self.root / "seeds.txt"
        seeds.write_text("\n".join([
            "# letters: A AI Chat, Reasoning & Assistants; L AI Productivity, Documents & Meetings",
            "A: ChatGPT; Kimi", "L: tl; dv; Granola"]) + "\n", encoding="utf-8")
        public, private = build(self.root, self.catalog, self.policy, None, seeds)
        recs = {r["brand"]: r for r in private["records"] if r["source"] == "research-seeds"}
        self.assertEqual(["ChatGPT", "Kimi", "tl;dv", "Granola"], list(recs))
        self.assertEqual("INQUIRY_ONLY", recs["ChatGPT"]["classification"])
        self.assertEqual("NEEDS_FACT_VERIFICATION", recs["Kimi"]["classification"])
        self.assertEqual(["tl;dv"], public["summary"]["review_exceptions"])
        chat = next(f for f in public["families"] if f["family"] == "chatgpt")
        self.assertEqual("APPROVED_SELLABLE", chat["status"])

    def test_source_prices_never_copied(self):
        public, private = build(self.root, self.catalog, self.policy)
        blob = json.dumps([public, private])
        self.assertNotIn("price", blob.lower().replace("pricing", ""))


if __name__ == "__main__":
    unittest.main()
