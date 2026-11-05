"""About pages must describe SaveOnSub only: no sister-business origin story or unsupported order counts."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["about.html", "bn/about.html", "build_trust.py"]
BANNED = ["AI Premium Shop", "aipremiumshop.com", "aipremium.tools", "orders later", "1,600"]


class AboutSaveOnSubOnly(unittest.TestCase):
    def test_no_cross_business_or_count_claims(self):
        for name in FILES:
            text = (ROOT / name).read_text(encoding="utf-8")
            for banned in BANNED:
                self.assertNotIn(banned, text, f"{name} contains {banned!r}")


if __name__ == "__main__":
    unittest.main()
