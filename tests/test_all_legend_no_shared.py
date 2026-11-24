"""V23: the /all and /bn/all legend must not advertise shared-access badges.

Shared plans are restricted (held) and are never sold from the listing, so a
"shared" legend chip is a claim about products customers cannot buy.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AllLegendNoShared(unittest.TestCase):
    def test_static_all_pages_have_no_shared_legend(self):
        for rel in ("all.html", "bn/all.html"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            sub = re.findall(r'<p class="sub">.*?</p>', text, flags=re.S)
            self.assertTrue(sub, rel)
            legend = sub[0]
            self.assertNotIn("shared-low", legend, rel)
            self.assertNotIn("shared-med", legend, rel)
            self.assertIn('class="tos official"', legend, rel)


if __name__ == "__main__":
    unittest.main()
