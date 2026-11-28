"""Both checkout pages: order message, add-ons, quantity, order ID, empty-cart note."""
import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is required for the checkout VM test")
class CheckoutFlowTest(unittest.TestCase):
    def test_checkout_flow_in_both_languages(self):
        r = subprocess.run([NODE, str(HERE / "checkout_flow_vm.cjs")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
