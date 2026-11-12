"""Run real tracking JS in a sandboxed Node VM (no network / no customers)."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is required for synthetic browser smoke test")
class AdsConsentBrowserVm(unittest.TestCase):
    def test_meta_ga4_optout_lifecycle(self):
        p = subprocess.run(
            [NODE, str(ROOT / "tests" / "ads_consent_vm.cjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(p.returncode, 0, p.stdout + "\n" + p.stderr)
        self.assertIn("PASS: synthetic Meta Pixel + GA4 opt-out lifecycle", p.stdout)


if __name__ == "__main__":
    unittest.main()
