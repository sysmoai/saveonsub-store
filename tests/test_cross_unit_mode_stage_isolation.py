"""Regression controls for SaveOnSub public build business-unit isolation.

This test performs only source inspection; it does not publish or deploy.
The public stage must not include pages that belong to another business unit.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "stage_deploy.py"
SITEMAP = ROOT / "sitemap.xml"


def deploy_exclude_prefixes():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXCLUDE_PREFIXES"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("EXCLUDE_PREFIXES not found in staging script")


class CrossUnitPublicStageIsolation(unittest.TestCase):
    def test_sos_staging_has_explicit_legacy_mode_exclusion(self):
        prefixes = deploy_exclude_prefixes()
        self.assertIn("modes/aips-", prefixes)

    def test_each_remaining_legacy_mode_is_covered(self):
        prefixes = deploy_exclude_prefixes()
        for page in (ROOT / "modes").glob("aips-*.html"):
            path = page.relative_to(ROOT).as_posix()
            with self.subTest(path=path):
                self.assertTrue(path.startswith(prefixes))

    def test_stage_copier_enforces_prefixes(self):
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("if rel.startswith(EXCLUDE_PREFIXES):", script)

    def test_sitemap_does_not_promote_other_unit_modes(self):
        content = SITEMAP.read_text(encoding="utf-8")
        self.assertNotIn("/modes/aips-", content)


if __name__ == "__main__":
    unittest.main()
