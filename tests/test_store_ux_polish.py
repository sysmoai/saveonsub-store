"""Every menu offers a language switch, Bangla pages stay Bangla, homes offer search."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import store_ux_polish as ux  # noqa: E402

NAV = ('<nav><div class="navlinks">\n  <a href="all">Subscriptions</a>\n'
       '  <div class="navdrop"><div class="dropmenu"><a href="c/x">X</a></div></div>\n'
       '</div><div class="navright"></div></nav>')
HOME = NAV + '<div class="heroctas"><a href="all">Browse</a></div>'
PAGES = {"index.html", "bn.html", "all.html", "bn/all.html", "checkout.html", "bn/checkout.html",
         "p/demo.html", "bn/p/demo.html", "faq.html", "blog/index.html", "blog/bangla-guide.html"}


class StoreUxPolishTest(unittest.TestCase):
    def test_relative_links(self):
        self.assertEqual(ux.relative_url("bn/p/demo.html", "p/demo.html"), "../bn/p/demo")
        self.assertEqual(ux.relative_url("p/demo.html", "bn/p/demo.html"), "../../p/demo")
        self.assertEqual(ux.relative_url("bn.html", "index.html"), "bn")
        self.assertEqual(ux.relative_url("bn.html", "bn/p/demo.html"), "../../bn")
        self.assertEqual(ux.relative_url("index.html", "bn.html"), "./")
        self.assertEqual(ux.relative_url("index.html", "bn/all.html"), "../")

    def test_switch_goes_inside_the_menu_once(self):
        out = ux.add_switch(NAV, "p/demo.html", PAGES)
        start, end = ux.nav_span(out)
        self.assertIn('href="../bn/p/demo" lang="bn"', out[start:end])
        self.assertEqual(ux.add_switch(out, "p/demo.html", PAGES), out)

    def test_switch_without_a_twin_goes_to_the_other_home(self):
        self.assertIn('href="../bn" lang="bn"', ux.add_switch(NAV, "blog/index.html", PAGES))
        bangla_guide = '<html lang="bn">' + NAV
        self.assertIn('href="../" lang="en"', ux.add_switch(bangla_guide, "blog/bangla-guide.html", PAGES))

    def test_not_found_page_switch_is_root_absolute(self):
        self.assertIn('href="/bn" lang="bn"', ux.add_switch(NAV, "404.html", PAGES))

    def test_bangla_page_links_stay_bangla(self):
        page = ('<a href="../all#bundles">B</a><a href="../../p/demo?x=1">D</a>'
                '<button onclick="location.href=\'../checkout\'">C</button>'
                '<a href="../faq">F</a><a href="https://wa.me/1">W</a><a href="../all" lang="en">E</a>')
        out = ux.keep_bangla(page.replace("../../p/demo", "../p/demo"), "bn/checkout.html", PAGES)
        self.assertIn('href="all#bundles"', out)
        self.assertIn('href="p/demo?x=1"', out)
        self.assertIn("location.href='checkout'", out)
        self.assertIn('href="../faq"', out)  # no Bangla twin staged: unchanged
        self.assertIn('href="https://wa.me/1"', out)
        self.assertIn('href="../all" lang="en"', out)

    def test_english_pages_are_not_rewritten(self):
        page = '<html lang="en"><a href="all">A</a>'
        self.assertEqual(ux.keep_bangla(page, "faq.html", PAGES), page)

    def test_home_search_uses_the_language_list(self):
        en = ux.polish(HOME, "index.html", PAGES)
        bn = ux.polish(HOME, "bn.html", PAGES)
        self.assertIn('action="/all" method="get"', en)
        self.assertIn('action="/bn/all" method="get"', bn)
        self.assertEqual(ux.polish(en, "index.html", PAGES), en)
        self.assertEqual(ux.polish(bn, "bn.html", PAGES), bn)
        self.assertNotIn("homesearch", ux.polish(HOME, "faq.html", PAGES))


if __name__ == "__main__":
    unittest.main()
