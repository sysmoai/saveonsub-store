"""Logo-system icons are copied byte-for-byte from the pinned SOS-007 exports."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import stage_deploy  # noqa: E402


def _content_margins(image: Image.Image) -> tuple[int, int, int, int]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    xs, ys = [], []
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 20 and not (red > 245 and green > 245 and blue > 245):
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), width - 1 - max(xs), height - 1 - max(ys)


class BrandIconSourceTests(unittest.TestCase):
    def test_pinned_bytes_and_checksum_file(self):
        sums = (ROOT / "brand_src" / "SHA256SUMS.txt").read_text(encoding="utf-8")
        listed = {}
        for line in sums.splitlines():
            if not line.strip():
                continue
            digest, name = line.split(maxsplit=1)
            listed[name] = digest
            raw = (ROOT / "brand_src" / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        on_disk = {
            path.relative_to(ROOT / "brand_src").as_posix()
            for path in (ROOT / "brand_src").rglob("*")
            if path.is_file() and path.name != "SHA256SUMS.txt"
        }
        self.assertEqual(set(listed), on_disk)
        self.assertEqual(
            hashlib.sha256(stage_deploy.BRAND_ICON_SRC.read_bytes()).hexdigest(),
            stage_deploy.BRAND_ICON_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(stage_deploy.BRAND_LOCKUP_SRC.read_bytes()).hexdigest(),
            stage_deploy.BRAND_LOCKUP_SHA256,
        )
        for name, digest in stage_deploy.BRAND_WEB_ICONS.items():
            self.assertEqual(listed[f"web/{name}"], digest)

    def test_hash_mismatch_refuses_to_build(self):
        with self.assertRaises(RuntimeError):
            stage_deploy._pinned_bytes(stage_deploy.BRAND_LOCKUP_SRC, "0" * 64)
        with self.assertRaises(RuntimeError):
            stage_deploy._pinned_original(
                stage_deploy.BRAND_LOCKUP_SRC,
                stage_deploy.BRAND_LOCKUP_SHA256,
                (78, 78),
                "RGB",
            )

    def test_web_icons_are_copied_not_resized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            stage_deploy.install_pinned_web_icons(assets, root)
            for name, digest in stage_deploy.BRAND_WEB_ICONS.items():
                copied = (assets / name).read_bytes()
                source = (stage_deploy.BRAND_SRC / "web" / name).read_bytes()
                self.assertEqual(copied, source)
                self.assertEqual(hashlib.sha256(copied).hexdigest(), digest)
            self.assertEqual((root / "favicon.ico").read_bytes(), (assets / "favicon.ico").read_bytes())
            with Image.open(root / "favicon.ico") as ico:
                self.assertEqual(set(ico.ico.sizes()), stage_deploy.FAVICON_ICO_SIZES)

    def test_icon_treatments_match_logo_system(self):
        favicon = Image.open(stage_deploy.BRAND_SRC / "web" / "favicon-32.png")
        self.assertEqual(favicon.size, (32, 32))
        self.assertEqual(favicon.getpixel((0, 0))[3], 0)
        apple = Image.open(stage_deploy.BRAND_SRC / "web" / "apple-touch-icon.png")
        self.assertEqual(apple.size, (180, 180))
        self.assertEqual(apple.getpixel((0, 0)), (255, 255, 255, 255))
        maskable = Image.open(stage_deploy.BRAND_SRC / "web" / "icon-maskable-512.png")
        self.assertEqual(maskable.size, (512, 512))
        left, top, right, bottom = _content_margins(maskable)
        # Android's maskable safe zone is the center 80%, so every margin is at least 10%.
        for margin in (left, top, right, bottom):
            self.assertGreaterEqual(margin / 512, 0.10)

    def test_manifest_has_one_maskable_icon(self):
        maskable = [
            icon for icon in stage_deploy.BRAND_MANIFEST_ICONS
            if icon.get("purpose") == "maskable"
        ]
        self.assertEqual(len(maskable), 1)
        self.assertEqual(maskable[0]["src"], "/assets/icon-maskable-512.png")
        self.assertEqual(maskable[0]["sizes"], "512x512")

    def test_brand_src_is_not_a_public_directory(self):
        self.assertIn("brand_src", stage_deploy.EXCLUDE_DIRS)
        source = (ROOT / "stage_deploy.py").read_text(encoding="utf-8")
        self.assertNotIn("lockup.crop((0, 0, lockup.height, lockup.height))", source)
        cache_safe = (ROOT / "cache_safe_brand.py").read_text(encoding="utf-8")
        self.assertNotIn("resize((32, 32)", cache_safe)
        self.assertIn("BRAND_WEB_ICONS", cache_safe)


if __name__ == "__main__":
    unittest.main()
