#!/usr/bin/env python3
"""Git-reviewed media authoring helper for SAVEONSUB v3.

This is intentionally local/repository based. It never uploads to Cloudflare,
never reads API credentials, and never publishes a draft automatically.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import tempfile

from media_registry import DEFAULT_REGISTRY, load_media_registry


def write_registry(data: dict) -> None:
    DEFAULT_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=DEFAULT_REGISTRY.parent) as tmp:
        tmp.write(payload)
        temp_path = pathlib.Path(tmp.name)
    temp_path.replace(DEFAULT_REGISTRY)


def find_entry(data: dict, media_id: str) -> dict:
    matches = [e for e in data.get("entries", []) if isinstance(e, dict) and e.get("media_id") == media_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one media entry for {media_id!r}; found {len(matches)}")
    return matches[0]


def cmd_inventory(_: argparse.Namespace) -> int:
    data = load_media_registry()
    counts: dict[str, int] = {}
    providers: dict[str, int] = {}
    for entry in data.get("entries", []):
        state = str(entry.get("state") or "draft")
        provider = str(entry.get("provider") or entry.get("source") or "unknown")
        counts[state] = counts.get(state, 0) + 1
        providers[provider] = providers.get(provider, 0) + 1
    print(json.dumps({"entries": len(data.get("entries", [])), "states": counts, "providers": providers}, indent=2, sort_keys=True))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    data = load_media_registry()
    if any(isinstance(e, dict) and e.get("media_id") == args.media_id for e in data.get("entries", [])):
        raise SystemExit(f"media_id already exists: {args.media_id}")
    entry = {
        "media_id": args.media_id,
        "product_id": args.product_id,
        "plan_id": args.plan_id or None,
        "kind": args.kind,
        "role": args.role,
        "provider": args.provider,
        "source_id": args.source_id,
        "delivery_url": args.delivery_url or None,
        "alt": {"en": args.alt_en or "", "bn": args.alt_bn or ""},
        "caption": {"en": args.caption_en or "", "bn": args.caption_bn or ""},
        "width": args.width,
        "height": args.height,
        "duration_seconds": args.duration_seconds,
        "sort_order": args.sort_order,
        "state": "draft",
        "visibility": "private",
        "authority_ref": None,
    }
    data.setdefault("entries", []).append(entry)
    write_registry(data)
    print(f"created private draft media entry: {args.media_id}")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    data = load_media_registry()
    entry = find_entry(data, args.media_id)
    if entry.get("state") == "retired":
        raise SystemExit("retired media cannot return to review without a new media identity")
    entry["state"] = "reviewed"
    entry["visibility"] = "private"
    write_registry(data)
    print(f"marked media reviewed/private: {args.media_id}")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    data = load_media_registry()
    entry = find_entry(data, args.media_id)
    if entry.get("state") != "reviewed":
        raise SystemExit("media must be reviewed before approval")
    entry["state"] = "approved"
    entry["visibility"] = "public"
    entry["authority_ref"] = args.authority_ref
    write_registry(data)
    print(f"approved media for public normalization: {args.media_id}")
    return 0


def cmd_retire(args: argparse.Namespace) -> int:
    data = load_media_registry()
    entry = find_entry(data, args.media_id)
    entry["state"] = "retired"
    entry["visibility"] = "private"
    write_registry(data)
    print(f"retired media entry: {args.media_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    inventory = sub.add_parser("inventory")
    inventory.set_defaults(func=cmd_inventory)

    add = sub.add_parser("add-draft")
    add.add_argument("--media-id", required=True)
    add.add_argument("--product-id", required=True)
    add.add_argument("--plan-id")
    add.add_argument("--kind", choices=["image", "video", "graphic", "document"], required=True)
    add.add_argument("--role", required=True)
    add.add_argument("--provider", choices=["local", "cloudflare_images", "cloudflare_stream", "r2"], required=True)
    add.add_argument("--source-id", required=True)
    add.add_argument("--delivery-url")
    add.add_argument("--alt-en")
    add.add_argument("--alt-bn")
    add.add_argument("--caption-en")
    add.add_argument("--caption-bn")
    add.add_argument("--width", type=int)
    add.add_argument("--height", type=int)
    add.add_argument("--duration-seconds", type=int)
    add.add_argument("--sort-order", type=int, default=0)
    add.set_defaults(func=cmd_add)

    review = sub.add_parser("review")
    review.add_argument("--media-id", required=True)
    review.set_defaults(func=cmd_review)

    approve = sub.add_parser("approve")
    approve.add_argument("--media-id", required=True)
    approve.add_argument("--authority-ref", required=True)
    approve.set_defaults(func=cmd_approve)

    retire = sub.add_parser("retire")
    retire.add_argument("--media-id", required=True)
    retire.set_defaults(func=cmd_retire)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
