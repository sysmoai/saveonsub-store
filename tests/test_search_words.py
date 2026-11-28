"""Everyday Bangla and Banglish wording still finds products."""
import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is required for the search VM test")
class SearchWordsTest(unittest.TestCase):
    def test_everyday_wording(self):
        r = subprocess.run([NODE, str(HERE / "search_words_vm.cjs")],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
