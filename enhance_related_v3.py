#!/usr/bin/env python3
"""Add deterministic same-category exploration to strict SAVEONSUB L1 product pages."""
from __future__ import annotations

from build_public_info_v3 import DEST, esc
from catalog_model import load_catalog
from routes_v3 import slugify

MAX_PEERS = 4


def peers_for(products: list[dict], product: dict) -> list[dict]:
    same = [p for p in products if p.get("category") == product.get("category")]
    if len(same) <= 1:
        return []
    index = next(i for i, item in enumerate(same) if item.get("id") == product.get("id"))
    ordered = same[index + 1 :] + same[:index]
    return ordered[:MAX_PEERS]


def section(product: dict, peers: list[dict], language: str) -> str:
    bn = language == "bn"
    category = str(product.get("category") or "")
    category_slug = slugify(category)
    prefix = "/bn" if bn else ""
    cards = []
    for peer in peers:
        name = str(peer.get("name") or peer.get("id") or "").replace("🎁 ", "")
        cards.append(
            f'<a class="tcard" href="{prefix}/p/{esc(peer["id"])}.html" '
            f'aria-label="{esc(("একই ক্যাটাগরি: " if bn else "Same category: ") + name)}">'
            f'<span class="cat">{esc(category)}</span><h3>{esc(name)}</h3>'
            f'<span class="small">{"একই ক্যাটাগরি" if bn else "Same category"}</span></a>'
        )
    count = len(cards)
    empty = "" if count else f'<p class="sub">{"এই ক্যাটাগরিতে বর্তমানে অন্য কোনো টুল নেই।" if bn else "There are currently no other tools in this category."}</p>'
    grid = f'<div class="grid g4 mt2">{"".join(cards)}</div>' if cards else ""
    return (
        f'<section class="mt3" data-related-tools data-related-category="{esc(category)}" data-related-count="{count}">'
        f'<div style="display:flex;align-items:end;justify-content:space-between;gap:12px;flex-wrap:wrap">'
        f'<div><span class="pill">{"আরও দেখুন" if bn else "Explore more"}</span>'
        f'<h2>{"একই ক্যাটাগরির টুল" if bn else "Tools in the same category"}</h2></div>'
        f'<a class="btn btn-ghost btn-sm" href="{prefix}/c/{esc(category_slug)}.html">'
        f'{"ক্যাটাগরি দেখুন" if bn else "View category"} →</a></div>{empty}{grid}</section>'
    )


def inject_product_page(product: dict, language: str, peers: list[dict]) -> int:
    bn = language == "bn"
    rel = f"bn/p/{product['id']}.html" if bn else f"p/{product['id']}.html"
    path = DEST / rel
    if not path.is_file():
        raise RuntimeError(f"strict product page missing: {rel}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if "data-related-tools" in text:
        return 0
    marker = '<section class="mt3"><div class="notice">'
    position = text.rfind(marker)
    if position < 0:
        raise RuntimeError(f"product correction section marker missing: {rel}")
    new = text[:position] + section(product, peers, language) + text[position:]
    path.write_text(new, encoding="utf-8")
    return 1


def enhance_related() -> dict[str, int]:
    if not DEST.is_dir():
        raise RuntimeError("_public_v3 missing; run build_public_info_v3.py first")
    catalog = load_catalog()
    products = catalog.get("products", [])
    pages = 0
    peer_links = 0
    zero_peer_pages = 0
    for product in products:
        peers = peers_for(products, product)
        peer_links += len(peers) * 2
        if not peers:
            zero_peer_pages += 2
        pages += inject_product_page(product, "en", peers)
        pages += inject_product_page(product, "bn", peers)
    return {
        "related_product_pages_enhanced": pages,
        "same_category_peer_links": peer_links,
        "zero_peer_pages": zero_peer_pages,
    }


def main() -> int:
    print("enhanced strict L1 same-category exploration:", enhance_related())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
