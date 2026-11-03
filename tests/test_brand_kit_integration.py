"""Brand kit v1.0 integration: pinned files, wrappers and staged output stay byte-exact."""
import base64
import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"
SITE = ROOT / "_site"
EMBEDDED = re.compile(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BrandKitIntegration(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((BRAND / "brand-export.json").read_text(encoding="utf-8"))

    def test_export_record_matches_files(self):
        self.assertEqual(self.record["decision_record"], "SOS-CEO-20261102-002")
        self.assertRegex(self.record["source_commit"], r"^[0-9a-f]{40}$")
        for name, meta in self.record["files"].items():
            self.assertEqual(sha((BRAND / name).read_bytes()), meta["sha256"], name)

    def test_no_unrecorded_files_in_brand_dir(self):
        on_disk = {p.name for p in BRAND.iterdir() if p.is_file()} - {"brand-export.json"}
        self.assertEqual(on_disk, set(self.record["files"]))

    def _embedded(self, svg: str) -> bytes:
        text = (ROOT / "assets" / svg).read_text(encoding="utf-8")
        self.assertIn('data-brand-lock="2026-08-19-approved"', text)
        return base64.b64decode(EMBEDDED.search(text).group(1))

    def test_logo_wrapper_embeds_reverse_wordmark_exactly(self):
        self.assertEqual(self._embedded("logo.svg"), (BRAND / "wordmark-reverse-600w.png").read_bytes())

    def test_favicon_wrapper_embeds_m1_favicon_exactly(self):
        self.assertEqual(self._embedded("favicon.svg"), (BRAND / "favicon-48.png").read_bytes())

    def test_no_legacy_sos007_bytes(self):
        legacy = "681858ffbe873a1377735ddc8cea8c916c0f01b48a27a81d924f525c014201f9"
        for path in (ROOT / "assets").rglob("*.png"):
            self.assertNotEqual(sha(path.read_bytes()), legacy, path)

    @unittest.skipUnless((SITE / "index.html").is_file(), "run build_site.py first")
    def test_staged_icons_are_pinned_bytes(self):
        pairs = {
            "assets/apple-touch-icon.png": "apple-touch-icon-180.png",
            "assets/icon-192.png": "pwa-icon-192.png",
            "assets/icon-512.png": "pwa-icon-512.png",
            "assets/icon-maskable-512.png": "pwa-icon-maskable-512.png",
            "assets/og-image.png": "og-image-1200x630.png",
            "assets/favicon-32.png": "favicon-32.png",
            "favicon.ico": "favicon.ico",
        }
        for staged, pinned in pairs.items():
            self.assertEqual((SITE / staged).read_bytes(), (BRAND / pinned).read_bytes(), staged)
        manifest = json.loads((SITE / "assets" / "site.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["theme_color"], "#082034")
        self.assertIn("maskable", {icon.get("purpose") for icon in manifest["icons"]})
        self.assertIn('name="theme-color" content="#082034"', (SITE / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
