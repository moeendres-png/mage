#!/usr/bin/env python3
"""Resolve canonical project identities against a pinned Scryfall Oracle index.

This is an identity join, not behavioral card-name dispatch. Resolution is
case-sensitive after Unicode NFC normalization and surrounding-whitespace
removal. Zero or multiple Oracle IDs for a source name fail closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "commander-simulator-next.oracle-identity-resolution.v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("oracle_name must be a non-empty string")
    return unicodedata.normalize("NFC", value.strip())


def _optional_canonical_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("optional identity discriminator must be a non-empty string")
    return unicodedata.normalize("NFC", value.strip())


def resolve(source_path: Path, index_path: Path, expected_count: int | None = None) -> dict[str, Any]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    cards = index.get("cards")
    if not isinstance(cards, list):
        raise ValueError("Scryfall index must contain a cards list")

    by_name: dict[str, set[str]] = defaultdict(set)
    by_face_name: dict[str, set[str]] = defaultdict(set)
    index_metadata: dict[str, dict[str, Any]] = {}
    for card in cards:
        name = _canonical_name(card.get("name"))
        oracle_id = card.get("oracle_id")
        if not isinstance(oracle_id, str) or not oracle_id:
            raise ValueError("Scryfall index card is missing oracle_id")
        by_name[name].add(oracle_id)
        for face_name in card.get("face_names") or []:
            by_face_name[_canonical_name(face_name)].add(oracle_id)
        index_metadata[oracle_id] = {
            "commander_legality": card.get("commander_legality"),
            "color_identity": card.get("color_identity"),
            "type_line": card.get("type_line"),
        }

    source_records: list[dict[str, str]] = []
    seen_card_ids: set[str] = set()
    for line_number, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        card_id = record.get("card_id")
        if not isinstance(card_id, str) or not card_id:
            raise ValueError(f"source line {line_number} is missing card_id")
        if card_id in seen_card_ids:
            raise ValueError(f"duplicate source card_id: {card_id}")
        seen_card_ids.add(card_id)
        source_records.append({
            "card_id": card_id,
            "oracle_name": _canonical_name(record.get("oracle_name")),
            "type_line": _optional_canonical_text(record.get("type_line")),
            "admission_kind": record.get("admission_kind"),
        })

    missing: list[dict[str, str]] = []
    ambiguous: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    for record in source_records:
        matches = sorted(by_name.get(record["oracle_name"], set()))
        resolution = "EXACT_NFC_ORACLE_NAME_UNIQUE_IN_PINNED_BULK"
        if not matches:
            matches = sorted(by_face_name.get(record["oracle_name"], set()))
            resolution = "EXACT_NFC_CARD_FACE_NAME_UNIQUE_IN_PINNED_BULK"
        if not matches:
            missing.append(record)
            continue
        if len(matches) > 1 and record["type_line"] is not None:
            matches = [oracle_id for oracle_id in matches
                       if _optional_canonical_text(index_metadata[oracle_id].get("type_line"))
                       == record["type_line"]]
            resolution = "EXACT_NFC_ORACLE_NAME_AND_TYPE_LINE_UNIQUE_IN_PINNED_BULK"
        if len(matches) > 1 and record["admission_kind"] == "PHYSICAL_DECK_CARD":
            matches = [oracle_id for oracle_id in matches
                       if not (index_metadata[oracle_id].get("type_line") or "").startswith("Token ")
                       and (index_metadata[oracle_id].get("type_line") or "") not in {"Card", "Emblem"}]
            resolution = "EXACT_NFC_ORACLE_NAME_UNIQUE_NON_TOKEN_PHYSICAL_DECK_CARD"
        if len(matches) != 1:
            ambiguous.append({**record, "candidate_oracle_ids": matches})
            continue
        oracle_id = matches[0]
        resolved.append({
            **record,
            "oracle_id": oracle_id,
            **index_metadata[oracle_id],
            "resolution": resolution,
        })

    distinct_oracle_ids = sorted({record["oracle_id"] for record in resolved})
    count_matches = expected_count is None or len(source_records) == expected_count
    status = "PASS" if count_matches and not missing and not ambiguous and len(resolved) == len(source_records) else "FAIL"
    return {
        "schema": SCHEMA,
        "status": status,
        "source": {
            "path": source_path.name,
            "sha256": _sha256(source_path),
            "record_count": len(source_records),
            "expected_count": expected_count,
            "expected_count_matches": count_matches,
        },
        "scryfall_index": {
            "path": index_path.name,
            "sha256": _sha256(index_path),
            "source_head": index.get("source_head"),
            "source_tree": index.get("source_tree"),
            "bulk_updated_at": index.get("bulk_updated_at"),
            "payload_sha256": index.get("payload_sha256"),
            "oracle_identity_count": index.get("oracle_identity_count"),
        },
        "resolution_policy": {
            "normalization": "UNICODE_NFC_AND_TRIM",
            "case_sensitive": True,
            "fuzzy_matching": False,
            "alias_matching": False,
            "ambiguous_name_discriminator": "EXACT_NFC_TYPE_LINE",
            "exact_card_face_name_matching": True,
            "physical_deck_token_exclusion": True,
            "unique_oracle_id_required": True,
            "behavior_promotion": False,
        },
        "counts": {
            "source_records": len(source_records),
            "resolved_records": len(resolved),
            "distinct_oracle_ids": len(distinct_oracle_ids),
            "missing": len(missing),
            "ambiguous": len(ambiguous),
        },
        "resolved": resolved,
        "missing": missing,
        "ambiguous": ambiguous,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args()
    result = resolve(args.source, args.index, args.expected_count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], **result["counts"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
