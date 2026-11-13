"""The source catalog must not carry unsupported traction or ranking claims.

Build-time cohort scripts used to strip "211+ orders" / "#1 seller" text from
the generated HTML, which left the claims alive in catalog.json. Any build path
that skipped a patch would have republished them, so the source itself is
checked here (CEO claims matrix, 2026-11-11).
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNED = re.compile(r"\d[\d,]*\+\s*(?:happy\s+|satisfied\s+)?(?:orders|customers|buyers)\b|#1 seller|"
                    r"AIPS special|zero sharing|best single-AI value", re.I)


def strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "bestseller_rank":
                continue
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)
    elif isinstance(o, str):
        yield o


class SourceCatalogClaims(unittest.TestCase):
    def test_no_traction_claims_in_source(self):
        data = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        hits = [s[:80] for s in strings(data) if BANNED.search(s)]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
