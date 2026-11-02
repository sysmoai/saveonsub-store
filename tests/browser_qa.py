#!/usr/bin/env python3
"""Local browser QA of the staged _site artifact (not part of the CI build).

Serves _site/ with Cloudflare-Pages-style clean URLs, then uses Playwright
Chromium to check priority pages at the directive's widths: HTTP status,
console errors, horizontal overflow, header logo/favicon/theme-color, the
/all category chips, keyboard focus visibility and an axe-core WCAG 2.x AA scan.

Usage: python tests/browser_qa.py [--axe path/to/axe.min.js] [--shots DIR]
Writes a JSON report to stdout. Exit 1 if any hard check fails.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
WIDTHS = [320, 360, 390, 768, 1024, 1440, 1920]
PAGES = ["/", "/all", "/p/chatgpt-plus", "/c/ai-assistants", "/checkout", "/privacy",
         "/faq", "/contact", "/bn", "/bn/all", "/warranty", "/refund", "/404"]


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        p = pathlib.Path(path)
        # Like Cloudflare Pages, /bn serves bn.html even though a bn/ directory exists.
        if not p.is_file() and pathlib.Path(path.rstrip("/\\") + ".html").is_file():
            self.path = self.path.split("?")[0] + ".html"
        elif not p.exists():
            self.path = "/404.html"
        return super().send_head()

    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(CleanURLHandler, directory=str(SITE))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--axe")
    ap.add_argument("--shots")
    args = ap.parse_args()
    httpd, base = serve()
    report = {"base": base, "pages": [], "axe": [], "chips": None, "keyboard": None, "fail": []}
    shots = pathlib.Path(args.shots) if args.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width in WIDTHS:
            ctx = browser.new_context(viewport={"width": width, "height": 900})
            page = ctx.new_page()
            errors: list[str] = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errors.append(str(e)))
            for path in PAGES:
                errors.clear()
                resp = page.goto(base + path, wait_until="load")
                page.wait_for_timeout(150)
                info = page.evaluate("""() => ({
                  overflow: document.documentElement.scrollWidth - window.innerWidth,
                  logo: (document.querySelector('header .logo img, .logo img')||{}).currentSrc || null,
                  logoAlt: (document.querySelector('.logo img')||{}).alt || null,
                  logoW: (document.querySelector('.logo img')||{}).naturalWidth || 0,
                  theme: (document.querySelector('meta[name=theme-color]')||{}).content || null,
                  icon: [...document.querySelectorAll('link[rel~=icon]')].map(l=>l.getAttribute('href')),
                  lang: document.documentElement.lang,
                })""")
                # External font/CDN failures are not page bugs in an offline local preview.
                local_errors = [e for e in errors if "127.0.0.1" in e or "Failed to load resource" not in e]
                row = {"width": width, "path": path, "status": resp.status if resp else None,
                       "console_errors": local_errors, **info}
                report["pages"].append(row)
                if row["overflow"] > 1:
                    report["fail"].append(f"overflow {row['overflow']}px at {width} {path}")
                if local_errors:
                    report["fail"].append(f"console error at {width} {path}: {local_errors[:2]}")
                if path != "/404" and row["status"] != 200:
                    report["fail"].append(f"status {row['status']} at {path}")
                if not row["logoW"]:
                    report["fail"].append(f"logo not rendered at {width} {path}")
                if shots and path in ("/", "/all", "/p/chatgpt-plus", "/bn") and width in (390, 1440):
                    page.screenshot(path=str(shots / f"{path.strip('/').replace('/', '_') or 'home'}-{width}.png"), full_page=False)
            ctx.close()

        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(base + "/all", wait_until="load")
        report["chips"] = page.evaluate("""() => ({
          chips: [...document.querySelectorAll('#chips .chip')].map(b=>b.textContent.trim()),
          gridCards: document.querySelectorAll('#grid > *').length,
          bundleCards: document.querySelectorAll('#bgrid > *').length,
          catalogProducts: CATALOG.products.length,
        })""")
        c = report["chips"]
        if c["gridCards"] + c["bundleCards"] != c["catalogProducts"]:
            report["fail"].append(f"/all shows {c['gridCards']}+{c['bundleCards']} of {c['catalogProducts']} products")

        page.goto(base + "/", wait_until="load")
        focus = []
        for _ in range(6):
            page.keyboard.press("Tab")
            focus.append(page.evaluate("""() => { const e=document.activeElement; const s=getComputedStyle(e);
              return {tag:e.tagName, text:(e.textContent||e.getAttribute('aria-label')||'').trim().slice(0,40),
                      outline:s.outlineStyle!=='none' && s.outlineWidth!=='0px', shadow:s.boxShadow!=='none'} }"""))
        report["keyboard"] = focus
        if not all(f["outline"] or f["shadow"] for f in focus):
            report["fail"].append("keyboard focus not visible on some of the first 6 tab stops")

        if args.axe:
            axe_src = pathlib.Path(args.axe).read_text(encoding="utf-8")
            for path in ["/", "/all", "/p/chatgpt-plus", "/checkout", "/privacy", "/bn"]:
                page.goto(base + path, wait_until="load")
                page.add_script_tag(content=axe_src)
                res = page.evaluate("""async () => { const r = await axe.run(document,
                    {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});
                    return r.violations.map(v=>({id:v.id, impact:v.impact, nodes:v.nodes.length}))}""")
                report["axe"].append({"path": path, "violations": res})
        browser.close()
    httpd.shutdown()
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 1 if report["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
