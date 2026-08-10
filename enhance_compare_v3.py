#!/usr/bin/env python3
"""Add progressive, non-commercial product comparison to strict SAVEONSUB L1 catalogs."""
from __future__ import annotations

from build_public_info_v3 import DEST

COMPARE_JS = r'''/* SAVEONSUB rendered-card comparison: descriptive facts only */
(function(){
  const MAX=3;
  const idFor=card=>{const link=card.querySelector('.ctas a[href]');if(!link)return'';const parts=(link.getAttribute('href')||'').split('/').filter(Boolean);return(parts[parts.length-1]||'').replace(/\.html$/,'');};
  const text=(card,selector)=>{const node=card.querySelector(selector);return node?node.textContent.trim():'';};
  const href=card=>{const link=card.querySelector('.ctas a[href]');return link?link.getAttribute('href')||'':'';};
  function init(root){
    const grid=document.getElementById('catalog-grid');
    if(!grid)return;
    const panel=root.querySelector('[data-compare-panel]');
    const status=root.querySelector('[data-compare-status]');
    const table=root.querySelector('[data-compare-table]');
    const clear=root.querySelector('[data-compare-clear]');
    if(!panel||!status||!table||!clear)return;
    const cards=Array.from(grid.querySelectorAll('.pcard'));
    const byId=new Map(cards.map(card=>[idFor(card),card]).filter(([id])=>id));
    const selected=[];
    const isBn=document.documentElement.lang.toLowerCase().startsWith('bn');
    function copy(card){return{id:idFor(card),name:text(card,'h3'),category:text(card,'.cat'),status:text(card,'.tos'),url:href(card)};}
    function buttonFor(card){return card.querySelector('[data-compare-toggle]');}
    function syncButtons(){cards.forEach(card=>{const button=buttonFor(card);if(!button)return;const active=selected.includes(idFor(card));button.setAttribute('aria-pressed',active?'true':'false');button.textContent=active?(isBn?'তুলনা থেকে সরান':'Remove'):(isBn?'তুলনা করুন':'Compare');button.disabled=!active&&selected.length>=MAX;});}
    function setUrl(){const next=new URL(location.href);if(selected.length)next.searchParams.set('compare',selected.join(','));else next.searchParams.delete('compare');history.replaceState(null,'',next.pathname+(next.search?next.search:''));}
    function render(){
      const items=selected.map(id=>byId.get(id)).filter(Boolean).map(copy);
      panel.hidden=items.length===0;
      status.textContent=isBn?`${items.length}টি টুল নির্বাচিত (সর্বোচ্চ ${MAX})`:`${items.length} selected (max ${MAX})`;
      table.replaceChildren();
      if(items.length){
        const caption=document.createElement('caption');caption.textContent=isBn?'নির্বাচিত টুল তুলনা':'Selected tool comparison';table.appendChild(caption);
        const head=document.createElement('thead');const hr=document.createElement('tr');const blank=document.createElement('th');blank.scope='col';blank.textContent=isBn?'বিষয়':'Field';hr.appendChild(blank);
        items.forEach(item=>{const th=document.createElement('th');th.scope='col';const a=document.createElement('a');a.href=item.url;a.textContent=item.name;th.appendChild(a);hr.appendChild(th);});head.appendChild(hr);table.appendChild(head);
        const body=document.createElement('tbody');
        [[isBn?'ক্যাটাগরি':'Category','category'],[isBn?'প্রোভাইডার স্ট্যাটাস':'Provider status','status']].forEach(([label,key])=>{const tr=document.createElement('tr');const th=document.createElement('th');th.scope='row';th.textContent=label;tr.appendChild(th);items.forEach(item=>{const td=document.createElement('td');td.textContent=item[key];tr.appendChild(td);});body.appendChild(tr);});
        table.appendChild(body);
      }
      clear.disabled=items.length===0;syncButtons();setUrl();
    }
    cards.forEach(card=>{const ctas=card.querySelector('.ctas');if(!ctas||buttonFor(card))return;const button=document.createElement('button');button.type='button';button.className='btn btn-ghost btn-sm';button.setAttribute('data-compare-toggle','');button.setAttribute('aria-pressed','false');button.addEventListener('click',()=>{const id=idFor(card);const index=selected.indexOf(id);if(index>=0)selected.splice(index,1);else if(selected.length<MAX)selected.push(id);render();});ctas.appendChild(button);});
    clear.addEventListener('click',()=>{selected.splice(0);render();const first=cards[0]&&buttonFor(cards[0]);if(first)first.focus();});
    const initial=(new URLSearchParams(location.search).get('compare')||'').split(',').filter(Boolean);
    initial.forEach(id=>{if(byId.has(id)&&selected.length<MAX&&!selected.includes(id))selected.push(id);});
    render();root.hidden=false;
  }
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-compare-root]').forEach(init));
})();
'''

COMPARE_CSS = r'''.compare-panel{margin:18px 0 26px;border:1px solid var(--line);border-radius:var(--radius);background:var(--bg2);padding:18px}.compare-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.compare-scroll{overflow:auto;margin-top:12px}.compare-table{width:100%;min-width:520px;border-collapse:collapse}.compare-table caption{text-align:left;font-weight:800;margin-bottom:8px}.compare-table th,.compare-table td{border:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}.compare-table th{background:var(--bg3)}.compare-table a{color:var(--cyan);font-weight:800}.pcard .ctas{display:flex;gap:8px;flex-wrap:wrap}.pcard [data-compare-toggle][aria-pressed="true"]{border-color:var(--cyan);box-shadow:0 0 0 1px var(--cyan) inset}@media(max-width:600px){.compare-panel{padding:14px}.compare-table{min-width:460px}}'''


def compare_panel(language: str) -> str:
    bn = language == "bn"
    return (
        '<section class="compare-panel" data-compare-root hidden aria-labelledby="compare-title">'
        '<div class="compare-head"><div><h2 id="compare-title">'
        + ('টুল তুলনা করুন' if bn else 'Compare tools')
        + '</h2><p class="sub" data-compare-status role="status" aria-live="polite"></p></div>'
        '<button class="btn btn-ghost btn-sm" type="button" data-compare-clear disabled>'
        + ('সব সরান' if bn else 'Clear comparison')
        + '</button></div><div class="compare-scroll"><table class="compare-table" data-compare-table></table></div></section>'
    )


def enhance_catalog(rel: str, language: str) -> int:
    path = DEST / rel
    if not path.is_file():
        raise RuntimeError(f"catalog page missing for compare: {rel}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if 'data-compare-root' in text:
        return 0
    marker = '<div class="grid g3 mt3" id="catalog-grid">'
    if marker not in text:
        raise RuntimeError(f"catalog-grid marker missing for compare: {rel}")
    new = text.replace(marker, compare_panel(language) + marker, 1)
    if '/assets/compare.css' not in new:
        new = new.replace('</head>', '<link rel="stylesheet" href="/assets/compare.css"></head>', 1)
    if '/assets/compare.js' not in new:
        new = new.replace('</body>', '<script src="/assets/compare.js"></script></body>', 1)
    path.write_text(new, encoding="utf-8")
    return 1


def update_service_worker() -> int:
    path = DEST / "sw.js"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    new = text
    anchor = "'/assets/discovery.css'"
    for asset in ("/assets/compare.js", "/assets/compare.css"):
        quoted = f"'{asset}'"
        if quoted not in new:
            if anchor not in new:
                raise RuntimeError(f"service worker core anchor missing while adding {asset}")
            new = new.replace(anchor, f"{anchor},{quoted}", 1)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return 1
    return 0


def enhance_compare() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    assets = DEST / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "compare.js").write_text(COMPARE_JS, encoding="utf-8")
    (assets / "compare.css").write_text(COMPARE_CSS, encoding="utf-8")
    return {
        "compare_assets_written": 2,
        "english_catalog_enhanced": enhance_catalog("all.html", "en"),
        "bangla_catalog_enhanced": enhance_catalog("bn/all.html", "bn"),
        "service_worker_updated": update_service_worker(),
    }


def main() -> int:
    print("enhanced strict L1 product comparison:", enhance_compare())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
