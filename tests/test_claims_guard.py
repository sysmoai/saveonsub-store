"""T018-04: exec003_claims_guard fails (never rewrites) on blocked claims."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import exec003_claims_guard as guard  # noqa: E402

PAGE = '<!DOCTYPE html><html><head><title>X</title></head><body><main>{}</main></body></html>'


def scan(body, rel="p/x.html"):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PAGE.format(body), encoding="utf-8")
        return [name for _, name, _ in guard.scan_site(Path(d))]


class ClaimsGuardTest(unittest.TestCase):
    def test_planted_traction_fails_cli(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "p").mkdir()
            (Path(d) / "p" / "x.html").write_text(PAGE.format("3000 customers served"), encoding="utf-8")
            rc = subprocess.run([sys.executable, str(ROOT / "exec003_claims_guard.py"), d], capture_output=True).returncode
            self.assertEqual(rc, 1)
            before = (Path(d) / "p" / "x.html").read_text(encoding="utf-8")
            self.assertIn("3000 customers served", before)  # fail, not rewrite

    def test_blocked_families(self):
        cases = {
            "traction": ["156+ orders", "3,000+ Bangladeshis", "#1 seller", "২১১+ অর্ডার", "best-selling plan"],
            "same_day": ["refunds same-day", "একই দিনে ফেরত"],
            "warranty_replacement": ["warranty with replacement in 1 hour", "1-hour replacement", "১ ঘণ্টার মধ্যে রিপ্লেসমেন্ট", "7-day warranty", "৭ দিন গ্যারান্টি"],
            "minute_sla": ["delivered in 5–15 min", "৫–১৫ মিনিট"],
            "bn_warranty_included": ["বিকাশে, ওয়ারেন্টিসহ"],
            "pay_after_testing": ["Use Pay-After-Testing", "pay after testing"],
            "price_match": ["Price-match guarantee", "প্রাইস-ম্যাচ গ্যারান্টি", "আমরা ম্যাচ করব", "We match it + 5% off"],
            "save_percent": ["SAVE 77%", "-37% সাশ্রয়", "অফিসিয়াল দামের চেয়ে অনেক কম"],
            "customer_owned_official": ["100% customer-owned", "Every subscription is official", "১০০% গ্রাহক-নিয়ন্ত্রিত"],
        }
        for family, samples in cases.items():
            for sample in samples:
                with self.subTest(sample=sample):
                    self.assertIn(family, scan(sample))

    def test_clean_and_cautionary_copy_passes(self):
        self.assertEqual(scan("Price on request. Timing and coverage are confirmed in writing before payment. "
                              "Chat for 2 users on a team plan is a provider feature."), [])

    def test_prefill_meta_and_jsonld_are_scanned(self):
        body = '<a href="https://wa.me/8801305869242?text=Refund%20same%20day">x</a>'
        self.assertIn("same_day", scan(body))

    def test_rewritten_link_target_fails(self):
        self.assertIn("rewritten_link_target", scan('<a href="support terms.html">x</a>'))

    def test_refund_exemption_is_exact_cell_only(self):
        rights = "<table><tr><td>Same day</td><td>Same day, to your bKash/Nagad</td></tr></table>"
        self.assertEqual(scan(rights, "refund.html"), [])
        self.assertIn("same_day", scan("<table><tr><td>Same day refunds always</td></tr></table>", "refund.html"))
        self.assertIn("same_day", scan("<p>Same day</p>", "refund.html"))
        self.assertIn("same_day", scan(rights, "faq.html"))


if __name__ == "__main__":
    unittest.main()
