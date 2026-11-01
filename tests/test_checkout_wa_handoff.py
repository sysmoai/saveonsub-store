"""Integrate no-network Node browser simulation into existing Python CI."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CheckoutHandoff(unittest.TestCase):
    def test_synthetic_checkout_handoff_survives_cart_clear(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not available in this runner")
        run = subprocess.run(
            [node, str(ROOT / "tests/checkout_handoff_synthetic.mjs"), str(ROOT)],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(0, run.returncode, run.stdout + "\n" + run.stderr)
        self.assertIn("PASS: synthetic order snapshot preserved", run.stdout)
