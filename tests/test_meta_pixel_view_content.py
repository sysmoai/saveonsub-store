"""Meta Pixel ViewContent must carry the lowest published BDT price of a product page."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is required for synthetic browser smoke test")
class MetaPixelViewContentVm(unittest.TestCase):
    def test_view_content_value_follows_published_offers(self):
        p = subprocess.run(
            [NODE, str(ROOT / "tests" / "meta_pixel_view_content_vm.cjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(p.returncode, 0, p.stdout + "\n" + p.stderr)
        self.assertIn("PASS: synthetic Meta Pixel ViewContent value", p.stdout)


if __name__ == "__main__":
    unittest.main()
