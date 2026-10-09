import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'ops/commerce/tools/build_review_manifest.py'
SQL = ROOT / 'ops/commerce/001_catalog_content_foundation.sql'
_spec = importlib.util.spec_from_file_location('commerce_review_manifest', SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


class CommerceFoundationTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('CREATE TABLE operators(id TEXT PRIMARY KEY); CREATE TABLE orders(id TEXT PRIMARY KEY);')
        self.db.executescript(SQL.read_text(encoding='utf-8'))
        self.db.execute('INSERT INTO operators(id) VALUES (?)', ('emon',))

    def tearDown(self):
        self.db.close()

    def test_schema_has_all_11_operational_tables(self):
        rows = self.db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'commerce_%'").fetchall()
        self.assertEqual(len(rows), 11)

    def test_unverified_product_cannot_be_published(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("""INSERT INTO commerce_products(id,slug,title,category,kind,lifecycle,authorization,created_by,updated_by,created_at,updated_at)
              VALUES('p1','chatgpt-plus','ChatGPT Plus','AI','subscription','published','unknown','emon','emon','2026-10-09','2026-10-09')""")

    def test_order_cost_requires_evidence_for_verified(self):
        self.db.execute("INSERT INTO orders(id) VALUES ('order-1')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("""INSERT INTO commerce_cost_entries(id,order_id,kind,amount_minor,verification,created_at)
              VALUES('c1','order-1','provider_cost',100,'verified','2026-10-09')""")

    def test_audit_events_immutable(self):
        self.db.execute("""INSERT INTO commerce_audit_events(id,actor_type,actor_id,event_type,entity_type,entity_id,created_at)
          VALUES('e1','operator','emon','draft.created','product','p1','2026-10-09')""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM commerce_audit_events WHERE id='e1'")

    def test_manifest_does_not_copy_legacy_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'assets/social').mkdir(parents=True)
            (root/'ops').mkdir()
            (root/'assets/social/chatgpt-plus.png').write_bytes(b'example-poster')
            (root/'catalog.json').write_text(json.dumps({'products':[{'id':'chatgpt-plus','name':'ChatGPT Plus','category':'AI','plans':[{'bdt':499},{'bdt':999}]}]}))
            (root/'ops/PRICING-V2-2026-09-17.json').write_text(json.dumps({'revision':'pricing-v2-2026-09-17','approved_products':{'chatgpt-plus':{'plans':[{'bdt':3390}]}}}))
            actual = mod.build_manifest(root)
            self.assertEqual(actual['counts']['legacy_products'],1)
            self.assertEqual(actual['counts']['legacy_plans'],2)
            self.assertEqual(actual['counts']['existing_poster_files'],1)
            self.assertFalse(actual['items'][0]['publish_allowed'])
            self.assertNotIn('bdt',json.dumps(actual))


    def test_all_three_poster_formats_are_review_only(self):
        poster_file = ROOT / 'ops/commerce/tools/generate_review_posters.py'
        spec = importlib.util.spec_from_file_location('commerce_draft_posters', poster_file)
        poster_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(poster_mod)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            (base/'assets').mkdir()
            (base/'assets/logo.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" data-brand-lock="2026-08-19-approved"><text>LOCKED</text></svg>')
            (base/'catalog.json').write_text(json.dumps({'products':[{'id':'chatgpt-plus','name':'ChatGPT Plus','category':'AI Image & Design','plans':[{'bdt':499}]}]}))
            output=base/'poster_review'
            report=poster_mod.generate(base,output)
            self.assertEqual(report['posters'],3)
            self.assertTrue(all(not item['publish_allowed'] for item in report['items']))
            for item in report['items']:
                svg=(output/item['asset']).read_text()
                self.assertIn('INTERNAL REVIEW - NOT FOR PUBLICATION',svg)
                self.assertIn('AI IMAGE &amp; DESIGN',svg)
                self.assertIn('data:image/svg+xml;base64,',svg)
                self.assertNotIn('499',svg)

    def test_poster_generator_refuses_unlocked_logo(self):
        poster_file = ROOT / 'ops/commerce/tools/generate_review_posters.py'
        spec = importlib.util.spec_from_file_location('commerce_draft_posters_reject', poster_file)
        poster_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(poster_mod)
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            (base/'assets').mkdir()
            (base/'assets/logo.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            (base/'catalog.json').write_text(json.dumps({'products':[]}))
            with self.assertRaises(ValueError):
                poster_mod.generate(base,base/'out')


if __name__ == '__main__':
    unittest.main()
