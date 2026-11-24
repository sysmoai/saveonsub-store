"""V27: provider USD list prices that fact files could not confirm are not rendered."""
import re
import unittest
from pathlib import Path

import conversion_upgrade as cu

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


class UnverifiedProviderUsd(unittest.TestCase):
    def test_refs_fail_closed(self):
        refs = cu.official_refs()
        for pid in cu.UNVERIFIED_PROVIDER_USD:
            self.assertIn(pid, refs, pid)
            self.assertIsNone(refs[pid]["usd"], pid)
        self.assertEqual(refs["chatgpt-plus"]["usd"], 20)

    @unittest.skipUnless((SITE / "p" / "chatgpt-business.html").exists(), "needs built _site")
    def test_built_pages_have_no_usd_reference(self):
        for pid in cu.UNVERIFIED_PROVIDER_USD:
            for loc in ("p", "bn/p"):
                page = SITE / loc / f"{pid}.html"
                if not page.exists():
                    continue
                text = re.sub(r"<script.*?</script>", "", page.read_text(encoding="utf-8"), flags=re.S)
                self.assertNotIn("Provider list price", text, page)
                self.assertNotIn("provider list reference", text, page)
                self.assertNotIn("প্রোভাইডারের তালিকা মূল্য", text, page)
                self.assertNotIn("প্রোভাইডারের লিস্ট প্রাইস", text, page)
                self.assertIsNone(re.search(r"becomes \$|হয়ে যায় \$", text), page)


if __name__ == "__main__":
    unittest.main()
