#!/usr/bin/env python3
"""Harden generated _public_v3 for a strict L1 information-only release.

The repository compatibility runtime deliberately keeps legacy function names so
old committed pages do not crash during migration. The strict public L1 artifact
does not need those names at all. This post-build step replaces its browser
runtime with an information-only implementation and removes legacy commerce
redirect vocabulary before release validation/staging.
"""
from __future__ import annotations

import pathlib

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


def main() -> int:
    if not PUBLIC.is_dir():
        raise SystemExit("_public_v3 missing; run build_public_info_v3.py first")
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "app.js").write_text(APP_JS, encoding="utf-8")
    (PUBLIC / "_redirects").write_text(REDIRECTS, encoding="utf-8")
    print("hardened _public_v3: information-only app.js + non-commerce redirects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
