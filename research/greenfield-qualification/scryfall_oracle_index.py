#!/usr/bin/env python3
"""Build a deterministic Scryfall Oracle-ID index from a bulk payload.

Scryfall currently publishes the Oracle Cards bulk source as gzip-compressed
JSONL, but the qualification boundary also accepts a plain JSON array so a
proxy or future source format cannot silently produce an empty/partial index.
The parser validates the payload before emitting any evidence.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except (OSError, EOFError) as exc:
            raise SystemExit(f"invalid gzip Scryfall payload: {exc}") from exc
    elif raw.lstrip()[:1] not in (b"[", b"{"):
        raise SystemExit(f"unsupported Scryfall payload magic: {raw[:2].hex()}")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"Scryfall payload is not UTF-8: {exc}") from exc


def rows_from_text(text: str) -> Iterable[dict[str, Any]]:
    stripped = text.lstrip()
    if stripped.startswith("["):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSON array: {exc}") from exc
        if not isinstance(value, list):
            raise SystemExit("Scryfall JSON payload is not an array")
        rows = value
    else:
        rows = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSONL row {line_number}: {exc}") from exc
    for row_number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise SystemExit(f"Scryfall row {row_number} is not an object")
        oracle_id = row.get("oracle_id")
        if not isinstance(oracle_id, str) or not oracle_id:
            raise SystemExit(f"Scryfall row {row_number} has no oracle_id")
        yield row


def index_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_oracle: dict[str, dict[str, Any]] = {}
    row_count = 0
    for card in rows:
        row_count += 1
        oracle_id = card["oracle_id"]
        compact = {
            "name": card.get("name"),
            "oracle_id": oracle_id,
            "scryfall_id": card.get("id"),
            "commander_legality": (card.get("legalities") or {}).get("commander"),
            "color_identity": card.get("color_identity"),
            "type_line": card.get("type_line"),
        }
        old = by_oracle.get(oracle_id)
        if old is None or (compact.get("scryfall_id") or "") < (old.get("scryfall_id") or ""):
            by_oracle[oracle_id] = compact
    if not row_count or not by_oracle:
        raise SystemExit("empty Scryfall Oracle index")
    return sorted(by_oracle.values(), key=lambda row: (row["oracle_id"], (row.get("name") or "").casefold()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--bulk-updated-at", required=True)
    parser.add_argument("--bulk-download-uri", required=True)
    args = parser.parse_args()

    cards = index_rows(rows_from_text(payload_text(args.payload)))
    result = {
        "schema": "commander-simulator-next.scryfall-oracle-index.v2",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "bulk_updated_at": args.bulk_updated_at,
        "bulk_download_uri": args.bulk_download_uri,
        "payload_sha256": sha256(args.payload),
        "oracle_identity_count": len(cards),
        "cards": cards,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"oracle_identity_count": len(cards), "payload_sha256": result["payload_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
