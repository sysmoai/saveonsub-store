"""Pinned founder brand masters must downscale evenly and must not be cropped."""
import base64
import hashlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import stage_deploy  # noqa: E402


class BrandIconSourceTests(unittest.TestCase):
    def test_pinned_bytes_and_checksum_file(self):
        sums = (ROOT / "brand_src" / "SHA256SUMS.txt").read_text(encoding="utf-8")
        expected = {
            stage_deploy.BRAND_ICON_SRC.name: stage_deploy.BRAND_ICON_SHA256,
            stage_deploy.BRAND_LOCKUP_SRC.name: stage_deploy.BRAND_LOCKUP_SHA256,
        }
        listed = {}
        for line in sums.splitlines():
            if not line.strip():
                continue
            digest, name = line.split(maxsplit=1)
            listed[name] = digest
            raw = (ROOT / "brand_src" / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        self.assertEqual(listed, expected)

    def test_hash_or_size_mismatch_refuses_to_build(self):
        with self.assertRaises(RuntimeError):
            stage_deploy._pinned_original(
                stage_deploy.BRAND_ICON_SRC, "0" * 64, (1254, 1254), "RGB"
            )
        with self.assertRaises(RuntimeError):
            stage_deploy._pinned_original(
                stage_deploy.BRAND_ICON_SRC,
                stage_deploy.BRAND_ICON_SHA256,
                (78, 78),
                "RGB",
            )

    def test_square_icon_is_even_downscale_not_header_crop(self):
        text = (ROOT / "assets" / "logo.svg").read_text(encoding="utf-8")
        match = re.search(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"', text)
        self.assertIsNotNone(match)
        header = Image.open(io.BytesIO(base64.b64decode(match.group(1)))).convert("RGB")
        cropped = header.crop((0, 0, header.height, header.height)).resize(
            (180, 180), Image.Resampling.LANCZOS
        )
        fresh = stage_deploy.render_square_icon(180)
        self.assertEqual(fresh.size, (180, 180))
        self.assertEqual(fresh.mode, "RGB")
        self.assertNotEqual(fresh.tobytes(), cropped.tobytes())
        # Full-square master keeps the dark corner. The old 78px crop is white there.
        self.assertLess(max(fresh.getpixel((0, 0))), 40)
        self.assertGreater(min(cropped.getpixel((0, 0))), 200)

    def test_favicon_sizes_match_direct_downscale(self):
        direct = {
            side: stage_deploy.render_square_icon(side) for side in (16, 32, 48)
        }
        # A second resample through 192px is how favicon-32 became blurry.
        via_192 = stage_deploy.render_square_icon(192).resize(
            (32, 32), Image.Resampling.LANCZOS
        )
        self.assertNotEqual(direct[32].tobytes(), via_192.tobytes())
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "favicon.ico"
            stage_deploy.write_favicon_ico(dest)
            with Image.open(dest) as ico:
                self.assertEqual(sorted(ico.ico.sizes()), [(16, 16), (32, 32), (48, 48)])
                for side in (16, 32, 48):
                    frame = ico.ico.getimage((side, side)).convert("RGB")
                    self.assertEqual(frame.tobytes(), direct[side].tobytes())

    def test_brand_src_is_not_a_public_directory(self):
        self.assertIn("brand_src", stage_deploy.EXCLUDE_DIRS)
        source = (ROOT / "stage_deploy.py").read_text(encoding="utf-8")
        self.assertNotIn("lockup.crop((0, 0, lockup.height, lockup.height))", source)


if __name__ == "__main__":
    unittest.main()
