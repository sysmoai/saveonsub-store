#!/usr/bin/env python3
"""Offline-only inventory for CEO review; NEVER publishes legacy catalog prices."""
import argparse
import hashlib
import json
from pathlib import Path


def build_manifest(root: Path):
    legacy_path = root / 'catalog.json'
    pricing_path = root / 'ops' / 'PRICING-V2-2026-09-17.json'
    legacy = json.loads(legacy_path.read_text(encoding='utf-8'))
    pricing = json.loads(pricing_path.read_text(encoding='utf-8'))
    approved = pricing.get('approved_products', {})
    products = legacy.get('products', [])
    if not isinstance(products, list):
        raise ValueError('catalog.products must be a list')
    output = []
    seen = set()
    for product in products:
        pid = product['id']
        if pid in seen or '/' in pid or '\\' in pid or pid.startswith('.'):
            raise ValueError('duplicate or invalid product ID: ' + pid)
        seen.add(pid)
        poster = root / 'assets' / 'social' / (pid + '.png')
        exists = poster.is_file()
        policy = approved.get(pid, {})
        approved_plans = policy.get('plans') or []
        output.append({
            'id': pid,
            'title': product.get('name', pid),
            'category': product.get('category', 'Uncategorized'),
            'legacy_plan_count': len(product.get('plans', [])),
            'approved_register_plan_count': len(approved_plans),
            'legacy_poster': 'assets/social/' + pid + '.png' if exists else None,
            'poster_sha256': hashlib.sha256(poster.read_bytes()).hexdigest() if exists else None,
            'sales_approval': 'HOLD',
            'publish_allowed': False,
            'provider_terms_verified': False,
            'media_rights_verified': False,
            'needs_ceo_review': True,
        })
    return {
        'tenant': 'SOS',
        'source': 'catalog.json',
        'source_sha256': hashlib.sha256(legacy_path.read_bytes()).hexdigest(),
        'governed_pricing_revision': pricing.get('revision'),
        'status': 'REVIEW_ONLY_NOT_LIVE',
        'counts': {
            'legacy_products': len(output),
            'legacy_plans': sum(p['legacy_plan_count'] for p in output),
            'existing_poster_files': sum(p['legacy_poster'] is not None for p in output),
            'missing_poster_files': sum(p['legacy_poster'] is None for p in output),
            'products_in_governed_register': sum(p['approved_register_plan_count'] > 0 for p in output),
        },
        'items': output,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    out = (args.out or root / 'ops' / 'commerce' / 'exports' / 'review_manifest.json').resolve()
    if out == root / '_site' or (root / '_site') in out.parents:
        raise SystemExit('Refusing to put review-only supplier/catalog data in _site')
    manifest = build_manifest(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(out), 'counts': manifest['counts'], 'status': manifest['status']}))


if __name__ == '__main__':
    main()
