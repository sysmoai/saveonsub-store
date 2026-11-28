"""After add-to-cart the toast offers a direct checkout link (EN and BN)."""
import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is required for the app.js VM test")
class ToastCheckoutLinkTest(unittest.TestCase):
    def test_checkout_link_after_add_to_cart(self):
        r = subprocess.run([NODE, str(HERE / "toast_checkout_link_vm.cjs")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
