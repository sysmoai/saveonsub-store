#!/usr/bin/env python3
"""Create review-only SVG posters for every legacy product using the exact brand-locked logo."""
import argparse
import base64
import hashlib
import html
import json
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

FORMATS = {'feed_4x5': (1080, 1350), 'square_1x1': (1080, 1080), 'story_9x16': (1080, 1920)}

def render_poster(product, logo_base64, shape, source_sha):
    width, height = shape
    pid = product['id']
    title = str(product.get('name', pid))
    category = str(product.get('category', 'Digital services'))
    lines = textwrap.wrap(title, width=20, break_long_words=False, break_on_hyphens=False) or [title]
    if len(lines) > 3:
        lines = lines[:2] + [lines[2][:16].rstrip() + '...']
    title_y = int(height * .42)
    chunks = '\n'.join(
        '<tspan x="88" dy="%s">%s</tspan>' % ('0' if i == 0 else '92', html.escape(line))
        for i, line in enumerate(lines)
    )
    cat = html.escape(category[:60])
    safe_id = html.escape(pid)
    height_margin = int(height * .1)
    text_y = title_y + 92 * (len(lines) - 1) + 88
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Internal SaveOnSub creative draft for {html.escape(title)}">
<defs>
  <linearGradient id="bg" x2="1" y2="1"><stop offset="0" stop-color="#102634"/><stop offset=".57" stop-color="#0b2835"/><stop offset="1" stop-color="#007E70"/></linearGradient>
  <radialGradient id="glow"><stop stop-color="#4be4c4" stop-opacity=".22"/><stop offset="1" stop-color="#4be4c4" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{width}" height="{height}" fill="url(#bg)"/>
<circle cx="{width-50}" cy="{int(height*.26)}" r="440" fill="url(#glow)"/>
<circle cx="{width+120}" cy="{int(height*.33)}" r="260" fill="none" stroke="#8bead8" stroke-width="2" opacity=".18"/>
<circle cx="{width+120}" cy="{int(height*.33)}" r="338" fill="none" stroke="#8bead8" stroke-width="2" opacity=".13"/>
<rect x="70" y="66" width="940" height="138" rx="22" fill="#ffffff"/>
<image href="data:image/svg+xml;base64,{logo_base64}" x="95" y="76" width="420" height="112" preserveAspectRatio="xMinYMid meet"/>
<text x="90" y="{height_margin+153}" font-family="Arial, sans-serif" font-weight="700" font-size="30" fill="#91ecdc">{cat.upper()}</text>
<text x="88" y="{title_y}" font-family="Arial, sans-serif" font-weight="800" font-size="78" fill="#fff">{chunks}</text>
<text x="90" y="{text_y}" font-family="Arial, sans-serif" font-size="36" fill="#c9eee8">Compare plans, access methods and current terms.</text>
<line x1="88" x2="992" y1="{height-310}" y2="{height-310}" stroke="#79e3cb" stroke-opacity=".35" stroke-width="2"/>
<text x="90" y="{height-244}" font-family="Arial, sans-serif" font-size="32" fill="#e1f8f3">SaveOnSub.com</text>
<text x="90" y="{height-184}" font-family="Arial, sans-serif" font-size="25" fill="#bfe5dc">Availability, price and provider terms require verification.</text>
<rect x="70" y="{height-112}" width="940" height="56" rx="12" fill="#f2c57c"/>
<text x="540" y="{height-75}" text-anchor="middle" font-family="Arial, sans-serif" font-size="25" font-weight="700" fill="#2d2a23">INTERNAL REVIEW - NOT FOR PUBLICATION</text>
<metadata>tenant=SOS;product={safe_id};sha={source_sha};status=DRAFT</metadata>
</svg>'''

def generate(root: Path, output: Path):
    logo_path = root / 'assets/logo.svg'
    logo = logo_path.read_bytes()
    if b'data-brand-lock="2026-08-19-approved"' not in logo:
        raise ValueError('Approved locked SaveOnSub logo marker missing. Stop generation.')
    ET.fromstring(logo)
    encoded = base64.b64encode(logo).decode('ascii')
    source = root / 'catalog.json'
    products = json.loads(source.read_text(encoding='utf-8'))['products']
    seen = set()
    entries = []
    for product in products:
        pid = product['id']
        if pid in seen or not pid.replace('-', '').isalnum() or '/' in pid:
            raise ValueError('Unsafe or duplicate product ID')
        seen.add(pid)
        for name, dims in FORMATS.items():
            target = output / name / (pid + '.svg')
            target.parent.mkdir(parents=True, exist_ok=True)
            vector = render_poster(product, encoded, dims, hashlib.sha256(source.read_bytes()).hexdigest()[:16])
            ET.fromstring(vector)
            target.write_text(vector, encoding='utf-8')
            entries.append({'product_id':pid,'format':name,'asset':str(target.relative_to(output)),
                            'state':'DRAFT_HOLD','publish_allowed':False})
    report = {'tenant':'SOS','status':'INTERNAL_DRAFTS_NOT_APPROVED','products':len(products),
              'formats':list(FORMATS),'posters':len(entries),'items':entries}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3])
    parser.add_argument('--out',type=Path,default=None)
    args=parser.parse_args()
    root=args.root.resolve()
    dest=(args.out or root/'ops/commerce/exports/poster_review').resolve()
    if dest==root/'_site' or (root/'_site') in dest.parents:
        raise SystemExit('Never publish draft posters to _site')
    print(json.dumps({k:v for k,v in generate(root,dest).items() if k!='items'}))

if __name__=='__main__':main()
