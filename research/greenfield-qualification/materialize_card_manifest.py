#!/usr/bin/env python3
"""Materialize a deduplicated Oracle-ID union from available requirements.

Descriptor-only files are intentionally not treated as card rows.  This keeps
the actual-card gate fail-closed when a Drive export or official precon
fragment is unavailable rather than silently promoting card names or counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_oracle_ids(value: Any, output: set[str]) -> None:
    if isinstance(value, dict):
        oracle_id = value.get("oracle_id")
        if isinstance(oracle_id, str) and oracle_id:
            output.add(oracle_id)
        oracle_ids = value.get("oracle_ids")
        if isinstance(oracle_ids, list):
            output.update(item for item in oracle_ids if isinstance(item, str) and item)
        for child in value.values():
            collect_oracle_ids(child, output)
    elif isinstance(value, list):
        for child in value:
            collect_oracle_ids(child, output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--oracle-index", required=True, type=Path)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--forge-pin", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    manifest = load(args.manifest)
    union_config = manifest.get("oracle_union")
    if not isinstance(union_config, dict) or not isinstance(union_config.get("target_count"), int):
        raise SystemExit("manifest must define oracle_union.target_count")
    target_count = union_config["target_count"]
    source_files = union_config.get("source_files", [])
    if not isinstance(source_files, list):
        raise SystemExit("manifest oracle_union.source_files must be a list")

    source_rows: list[dict[str, Any]] = []
    oracle_ids: set[str] = set()
    missing: list[dict[str, str]] = []
    for relative in source_files:
        if not isinstance(relative, str):
            missing.append({"path": repr(relative), "reason": "source path is not a string"})
            continue
        path = args.manifest.parent / relative
        if not path.exists():
            missing.append({"path": relative, "reason": "source file is absent"})
            continue
        before = set(oracle_ids)
        try:
            collect_oracle_ids(load(path), oracle_ids)
        except Exception as exc:
            missing.append({"path": relative, "reason": f"source is not valid JSON: {exc!r}"})
            continue
        added = sorted(oracle_ids - before)
        source_rows.append({"path": relative, "sha256": sha256(path), "oracle_id_count": len(added)})
        if not added:
            missing.append({"path": relative, "reason": "descriptor contains no materialized oracle_id rows"})

    index = load(args.oracle_index)
    if not isinstance(index, dict):
        raise SystemExit("Scryfall Oracle index must be an object")
    if index.get("source_head") != args.source_head or index.get("source_tree") != args.source_tree:
        raise SystemExit("Scryfall Oracle index provenance does not match qualification input")
    index_rows = index.get("cards", []) if isinstance(index, dict) else []
    if not isinstance(index_rows, list) or index.get("oracle_identity_count") != len(index_rows):
        raise SystemExit("Scryfall Oracle index count is not internally consistent")
    index_by_id = {
        row.get("oracle_id"): row
        for row in index_rows
        if isinstance(row, dict) and isinstance(row.get("oracle_id"), str)
    }
    if len(index_by_id) != len(index_rows):
        raise SystemExit("Scryfall Oracle index contains duplicate or invalid Oracle IDs")
    unknown_ids = sorted(oracle_ids - set(index_by_id))
    cards = []
    for oracle_id in sorted(oracle_ids):
        if oracle_id not in index_by_id:
            # Never manufacture a card record for an identity that the pinned
            # Scryfall index does not contain.  Keep it only in the explicit
            # failure list below so an unknown identity cannot be promoted by
            # a placeholder row.
            continue
        row = dict(index_by_id[oracle_id])
        row.update({
            "oracle_id": oracle_id,
            "source_classes": [],
            "PRESENT": "SOURCE_PRESENT",
            "LOADABLE": "NOT_ASSESSED",
            "EXECUTABLE": "NOT_ASSESSED",
            "DECISION_COMPLETE": "NOT_ASSESSED",
            "HIDDEN_INFO_SAFE": "NOT_ASSESSED",
            "REPLAY_SAFE": "NOT_ASSESSED",
            "behavioral_evidence": "NOT_ASSESSED",
        })
        cards.append(row)

    status = "NOT_RUN" if missing else ("PASS" if len(oracle_ids) == target_count and not unknown_ids else "FAIL")
    result = {
        "schema": "commander-simulator-next.actual-card-requirement-union.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "external_pins": {"forge": args.forge_pin},
        "target_count": target_count,
        "computed_oracle_id_count": len(oracle_ids),
        "status": status,
        "complete": status == "PASS",
        "source_rows": source_rows,
        "missing_sources": missing,
        "unknown_oracle_ids_not_in_scryfall_index": unknown_ids,
        "cards": cards,
        "gate": {
            "target_count_equal": len(oracle_ids) == target_count,
            "all_source_rows_materialized": not missing,
            "all_ids_in_scryfall_index": not unknown_ids,
            "synthetic_promotion": False,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "target_count": target_count, "computed_oracle_id_count": len(oracle_ids)}, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())
