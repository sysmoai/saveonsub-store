"""Price-governing scripts are network-first in the service worker.

A stale cached catalog.js beside a freshly fetched page made the cart guard
reject the new price after the 2026-11-25 price release (first click did nothing).
"""
import re
import unittest
from pathlib import Path

SW = (Path(__file__).resolve().parents[1] / "sw.js").read_text(encoding="utf-8")


class ServiceWorkerFreshCatalog(unittest.TestCase):
    def test_catalog_and_app_are_network_first(self):
        m = re.search(r"const FRESH = new Set\(\[(.*?)\]\)", SW)
        self.assertIsNotNone(m)
        self.assertIn("'/assets/catalog.js'", m.group(1))
        self.assertIn("'/assets/app.js'", m.group(1))
        self.assertRegex(SW, r"if \(req\.mode === 'navigate' \|\| fresh\)")

    def test_fresh_branch_fetches_before_cache(self):
        branch = SW[SW.index("|| fresh)"):SW.index("} else {")]
        self.assertLess(branch.index("fetch(req)"), branch.index("caches.match(req)"))

    def test_other_assets_stay_stale_while_revalidate(self):
        tail = SW[SW.index("} else {"):]
        self.assertLess(tail.index("caches.match(req)"), tail.index("fetch(req)"))


if __name__ == "__main__":
    unittest.main()
