"""GA4 view_item must carry the lowest published BDT price of a product page."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is required for synthetic browser smoke test")
class Ga4ViewItemVm(unittest.TestCase):
    def test_view_item_value_follows_published_offers(self):
        p = subprocess.run(
            [NODE, str(ROOT / "tests" / "ga4_view_item_vm.cjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(p.returncode, 0, p.stdout + "\n" + p.stderr)
        self.assertIn("PASS: synthetic GA4 view_item value", p.stdout)


if __name__ == "__main__":
    unittest.main()
