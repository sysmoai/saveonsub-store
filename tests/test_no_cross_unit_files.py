"""The public SaveOnSub repository must not track another business unit's data files."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("aips-live.json",)


class NoCrossUnitFiles(unittest.TestCase):
    def test_not_tracked(self):
        try:
            tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("not a git checkout")
        bad = [f for f in tracked if Path(f).name in FORBIDDEN]
        self.assertFalse(bad, f"cross-unit data tracked in public repo: {bad}")

    def test_gitignored(self):
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for name in FORBIDDEN:
            self.assertIn(name, gi)

    def test_stage_deploy_still_excludes(self):
        src = (ROOT / "stage_deploy.py").read_text(encoding="utf-8")
        for name in FORBIDDEN:
            self.assertIn(name, src)


if __name__ == "__main__":
    unittest.main()
