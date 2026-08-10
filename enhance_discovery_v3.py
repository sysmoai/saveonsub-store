#!/usr/bin/env python3
"""Add progressive, information-only catalog discovery to strict SAVEONSUB L1."""
from __future__ import annotations

import pathlib

from build_public_info_v3 import DEST

DISCOVERY_JS = r'''/* SAVEONSUB rendered-card discovery: no catalog payload, no commerce data */
(function(){
  const norm=value=>(value||'').toLocaleLowerCase().replace(/\s+/g,' ').trim();
  const uniq=values=>Array.from(new Set(values.filter(Boolean))).sort((a,b)=>a.localeCompare(b));
  function label(card,selector){const node=card.querySelector(selector);return node?node.textContent.trim():'';}
  function setOptions(select,values,allLabel){
    const current=select.value;
    select.replaceChildren(new Option(allLabel,''));
    values.forEach(value=>select.add(new Option(value,value)));
    if(Array.from(select.options).some(o=>o.value===current)) select.value=current;
  }
  function init(root){
    const grid=document.getElementById('catalog-grid');
    if(!grid) return;
    const cards=Array.from(grid.querySelectorAll('.pcard'));
    const q=root.querySelector('[data-discovery-q]');
    const cat=root.querySelector('[data-discovery-category]');
    const state=root.querySelector('[data-discovery-state]');
    const sort=root.querySelector('[data-discovery-sort]');
    const clear=root.querySelector('[data-discovery-clear]');
    const count=root.querySelector('[data-discovery-count]');
    const empty=root.querySelector('[data-discovery-empty]');
    if(!q||!cat||!state||!sort||!clear||!count||!empty) return;
    const isBn=document.documentElement.lang.toLowerCase().startsWith('bn');
    const categories=uniq(cards.map(card=>label(card,'.cat')));
    const states=uniq(cards.map(card=>label(card,'.tos')));
    setOptions(cat,categories,isBn?'সব ক্যাটাগরি':'All categories');
    setOptions(state,states,isBn?'সব স্ট্যাটাস':'All statuses');
    const params=new URLSearchParams(location.search);
    q.value=params.get('q')||'';
    if(categories.includes(params.get('category')||'')) cat.value=params.get('category')||'';
    if(states.includes(params.get('status')||'')) state.value=params.get('status')||'';
    if(['name-asc','name-desc'].includes(params.get('sort')||'')) sort.value=params.get('sort')||'';
    function apply(){
      const query=norm(q.value), category=cat.value, status=state.value;
      let visible=cards.filter(card=>{
        const matchesQuery=!query||norm(card.textContent).includes(query);
        const matchesCategory=!category||label(card,'.cat')===category;
        const matchesStatus=!status||label(card,'.tos')===status;
        const show=matchesQuery&&matchesCategory&&matchesStatus;
        card.hidden=!show;
        return show;
      });
      if(sort.value){
        const dir=sort.value==='name-desc'?-1:1;
        visible.sort((a,b)=>dir*label(a,'h3').localeCompare(label(b,'h3')));
        visible.forEach(card=>grid.appendChild(card));
      } else {
        cards.forEach(card=>grid.appendChild(card));
      }
      count.textContent=isBn?`${visible.length}টি ফলাফল`:`${visible.length} results`;
      empty.hidden=visible.length!==0;
      clear.disabled=!q.value&&!cat.value&&!state.value&&!sort.value;
      const next=new URL(location.href);
      [['q',q.value.trim()],['category',cat.value],['status',state.value],['sort',sort.value]].forEach(([key,value])=>value?next.searchParams.set(key,value):next.searchParams.delete(key));
      history.replaceState(null,'',next.pathname+(next.search?next.search:''));
    }
    [q,cat,state,sort].forEach(control=>control.addEventListener(control===q?'input':'change',apply));
    clear.addEventListener('click',()=>{q.value='';cat.value='';state.value='';sort.value='';apply();q.focus();});
    document.addEventListener('keydown',event=>{
      if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&!/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement&&document.activeElement.tagName||'')){
        event.preventDefault();q.focus();
      }
    });
    root.hidden=false;
    apply();
  }
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-discovery]').forEach(init));
})();
'''

DISCOVERY_CSS = r'''.discovery-panel{margin:24px 0;border:1px solid var(--line);background:var(--bg2);border-radius:var(--radius);padding:18px}.discovery-grid{display:grid;grid-template-columns:minmax(0,2fr) repeat(3,minmax(145px,1fr));gap:12px;align-items:end}.discovery-field{display:grid;gap:6px}.discovery-field label{color:var(--muted);font-size:12px;font-weight:800;letter-spacing:.25px}.discovery-field input,.discovery-field select{width:100%;min-height:44px;border:1px solid var(--line);border-radius:10px;background:var(--bg3);color:var(--ink);padding:10px 12px;font:inherit}.discovery-field input:focus-visible,.discovery-field select:focus-visible,.discovery-panel button:focus-visible{outline:3px solid var(--cyan);outline-offset:2px}.discovery-meta{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:12px;color:var(--muted);font-size:14px}.discovery-empty{padding:24px;border:1px dashed var(--line);border-radius:var(--radius);text-align:center;color:var(--muted);margin-top:18px}.pcard[hidden]{display:none!important}@media(max-width:760px){.discovery-grid{grid-template-columns:1fr 1fr}.discovery-search{grid-column:1/-1}}@media(max-width:480px){.discovery-grid{grid-template-columns:1fr}.discovery-search{grid-column:auto}}'''


def panel(language: str) -> str:
    bn = language == "bn"
    return (
        '<section class="discovery-panel" data-discovery hidden aria-label="'
        + ('ক্যাটালগ খুঁজুন ও ফিল্টার করুন' if bn else 'Search and filter catalog')
        + '"><div class="discovery-grid">'
        '<div class="discovery-field discovery-search"><label for="discovery-q">'
        + ('সাবস্ক্রিপশন খুঁজুন' if bn else 'Search subscriptions')
        + '</label><input id="discovery-q" type="search" autocomplete="off" data-discovery-q aria-controls="catalog-grid" placeholder="'
        + ('নাম, ক্যাটাগরি বা স্ট্যাটাস লিখুন' if bn else 'Name, category or status')
        + '"></div>'
        '<div class="discovery-field"><label for="discovery-category">'
        + ('ক্যাটাগরি' if bn else 'Category')
        + '</label><select id="discovery-category" data-discovery-category aria-controls="catalog-grid"><option value="">'
        + ('সব ক্যাটাগরি' if bn else 'All categories')
        + '</option></select></div>'
        '<div class="discovery-field"><label for="discovery-state">'
        + ('প্রোভাইডার স্ট্যাটাস' if bn else 'Provider status')
        + '</label><select id="discovery-state" data-discovery-state aria-controls="catalog-grid"><option value="">'
        + ('সব স্ট্যাটাস' if bn else 'All statuses')
        + '</option></select></div>'
        '<div class="discovery-field"><label for="discovery-sort">'
        + ('সাজান' if bn else 'Sort')
        + '</label><select id="discovery-sort" data-discovery-sort aria-controls="catalog-grid"><option value="">'
        + ('মূল ক্রম' if bn else 'Default order')
        + '</option><option value="name-asc">A → Z</option><option value="name-desc">Z → A</option></select></div>'
        '</div><div class="discovery-meta"><span data-discovery-count role="status" aria-live="polite"></span>'
        '<button class="btn btn-ghost btn-sm" type="button" data-discovery-clear disabled>'
        + ('ফিল্টার মুছুন' if bn else 'Clear filters')
        + '</button></div><div class="discovery-empty" data-discovery-empty hidden>'
        + ('কোনো ফলাফল পাওয়া যায়নি। অন্য শব্দ বা ফিল্টার চেষ্টা করুন।' if bn else 'No results found. Try another search or filter.')
        + '</div></section>'
    )


def enhance_catalog_page(rel: str, language: str) -> int:
    path = DEST / rel
    if not path.is_file():
        raise RuntimeError(f"catalog page missing: {rel}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if 'data-discovery' in text:
        return 0
    marker = '<div class="grid g3 mt3">'
    if marker not in text:
        raise RuntimeError(f"catalog grid marker missing: {rel}")
    new = text.replace(marker, panel(language) + '<div class="grid g3 mt3" id="catalog-grid">', 1)
    if '/assets/discovery.css' not in new:
        new = new.replace('</head>', '<link rel="stylesheet" href="/assets/discovery.css"></head>', 1)
    if '/assets/discovery.js' not in new:
        new = new.replace('</body>', '<script src="/assets/discovery.js"></script></body>', 1)
    path.write_text(new, encoding="utf-8")
    return 1


def enhance_discovery() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    assets = DEST / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "discovery.js").write_text(DISCOVERY_JS, encoding="utf-8")
    (assets / "discovery.css").write_text(DISCOVERY_CSS, encoding="utf-8")
    result = {
        "discovery_assets_written": 2,
        "english_catalog_enhanced": enhance_catalog_page("all.html", "en"),
        "bangla_catalog_enhanced": enhance_catalog_page("bn/all.html", "bn"),
    }
    return result


def main() -> int:
    print("enhanced strict L1 catalog discovery:", enhance_discovery())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
