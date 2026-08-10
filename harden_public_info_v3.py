#!/usr/bin/env python3
"""Harden generated _public_v3 for a strict L1 information-only release.

The repository compatibility runtime and stylesheet deliberately retain legacy
selectors/function names so old committed pages do not break during migration.
The strict public L1 artifact does not need that vocabulary. This post-build
step replaces its browser runtime with an information-only implementation,
removes legacy commerce redirects, neutralizes unused shared-plan CSS selectors,
and redacts unsupported numeric social-proof phrases inherited from legacy copy.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / "_public_v3"
ASSETS = PUBLIC / "assets"

APP_JS = r'''/* SAVEONSUB L1 public-information runtime */
const SUPPORT_EMAIL = "support@saveonsub.com";

function navToggle(){
  const links=document.querySelector('.navlinks');
  if(links) links.classList.toggle('open');
}

function supportMailto(subject, body){
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject||'SAVEONSUB support')}&body=${encodeURIComponent(body||'')}`;
}

function copyText(text,label){
  if(!navigator.clipboard) return;
  navigator.clipboard.writeText(text).then(()=>showNotice(label||'Copied'));
}

function showNotice(message){
  let node=document.getElementById('sos-notice');
  if(!node){
    node=document.createElement('div');
    node.id='sos-notice';
    node.setAttribute('role','status');
    node.style.cssText='position:fixed;left:50%;bottom:20px;transform:translateX(-50%);z-index:9999;padding:10px 14px;border-radius:10px;background:#103433;color:#f2fbfa;border:1px solid #14d4b8';
    document.body.appendChild(node);
  }
  node.textContent=message;
  node.hidden=false;
  clearTimeout(node._timer);
  node._timer=setTimeout(()=>{node.hidden=true},2200);
}

function suggestBangla(){
  try{
    if((document.documentElement.lang||'').startsWith('bn')) return;
    if(localStorage.getItem('sos_lang_dismissed')) return;
    const langs=navigator.languages||[navigator.language||''];
    if(!langs.some(l=>(l||'').toLowerCase().startsWith('bn'))) return;
    const alt=document.querySelector('link[hreflang="bn-bd"]');
    if(!alt||!alt.href||alt.href===location.href) return;
    const bar=document.createElement('div');
    bar.setAttribute('role','region');
    bar.setAttribute('aria-label','ভাষা');
    bar.style.cssText='position:fixed;left:12px;right:12px;bottom:12px;z-index:9998;max-width:520px;margin:0 auto;background:#103433;border:1px solid #14d4b8;border-radius:14px;padding:12px 14px;display:flex;align-items:center;gap:12px;color:#f2fbfa';
    bar.innerHTML='<span style="flex:1">🇧🇩 বাংলায় দেখতে চান?</span><a class="btn btn-primary btn-sm" href="'+alt.href+'">বাংলায় দেখুন</a><button type="button" aria-label="বন্ধ করুন" style="background:none;border:0;color:inherit;font-size:18px;cursor:pointer">✕</button>';
    bar.querySelector('button').addEventListener('click',()=>{try{localStorage.setItem('sos_lang_dismissed','1')}catch(e){}bar.remove();});
    bar.querySelector('a').addEventListener('click',()=>{try{localStorage.setItem('sos_lang_dismissed','1')}catch(e){}});
    document.body.appendChild(bar);
  }catch(e){}
}

if('serviceWorker' in navigator){
  window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}

document.addEventListener('DOMContentLoaded',suggestBangla);
'''

REDIRECTS = '''/home / 301
/shop /all.html 301
/products /all.html 301
'''

# The strict artifact may inherit factual-looking numeric claims from old FAQ or
# descriptive copy (for example "100+ users"). Without evidence binding those
# counts are not publishable. Preserve the noun/context, remove only the number.
UNSUPPORTED_PROOF_RE = re.compile(
    r"\b[0-9]{2,}\+?\s*(orders|customers|users)\b",
    re.IGNORECASE,
)


def redact_unsupported_proof(text: str) -> tuple[str, int]:
    return UNSUPPORTED_PROOF_RE.subn(lambda m: m.group(1), text)


def harden_stylesheet() -> int:
    path = ASSETS / "style.css"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    # These classes are unused by the strict L1 pages. Rename them instead of
    # deleting arbitrary CSS blocks, which keeps the inherited stylesheet valid
    # while removing shared-commerce vocabulary from the release artifact.
    new = text.replace("shared-low", "legacy-risk-low").replace("shared-med", "legacy-risk-med")
    path.write_text(new, encoding="utf-8")
    return int(new != text)


def harden_html() -> tuple[int, int]:
    replacements = 0
    robots_hardened = 0
    for path in PUBLIC.rglob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        new, count = redact_unsupported_proof(text)
        replacements += count
        if path.relative_to(PUBLIC).as_posix() == "404.html":
            new, robots_count = re.subn(
                r'<meta name="robots" content="index,follow">',
                '<meta name="robots" content="noindex,follow">',
                new,
                count=1,
            )
            robots_hardened += robots_count
        if new != text:
            path.write_text(new, encoding="utf-8")
    return replacements, robots_hardened


def main() -> int:
    if not PUBLIC.is_dir():
        raise SystemExit("_public_v3 missing; run build_public_info_v3.py first")
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "app.js").write_text(APP_JS, encoding="utf-8")
    (PUBLIC / "_redirects").write_text(REDIRECTS, encoding="utf-8")
    css_hardened = harden_stylesheet()
    proof_redactions, robots_hardened = harden_html()
    print(
        "hardened _public_v3: information-only app.js + non-commerce redirects + "
        f"css_hardened={css_hardened} unsupported_proof_redactions={proof_redactions} "
        f"robots_hardened={robots_hardened}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
