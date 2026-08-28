#!/usr/bin/env python3
"""Materialize the exact, provenance-bearing actual-card Oracle union."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "commander-simulator-next.actual-card-requirement-union.v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def materialize(
    manifest_path: Path,
    index_path: Path,
    source_specs: list[tuple[str, Path]],
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    index = _load_json(index_path)
    union_spec = manifest.get("oracle_union")
    if not isinstance(union_spec, dict) or not isinstance(union_spec.get("target_count"), int):
        raise ValueError("manifest oracle_union.target_count must be an integer")
    required_classes = union_spec.get("source_classes")
    if not isinstance(required_classes, list) or not all(isinstance(x, str) for x in required_classes):
        raise ValueError("manifest oracle_union.source_classes must be a string list")

    index_cards = index.get("cards")
    if not isinstance(index_cards, list):
        raise ValueError("Scryfall index must contain a cards list")
    index_ids = {card.get("oracle_id") for card in index_cards}
    if None in index_ids or not all(isinstance(x, str) for x in index_ids):
        raise ValueError("Scryfall index contains an invalid oracle_id")
    index_sha = _sha256(index_path)

    by_oracle_id: dict[str, dict[str, Any]] = {}
    class_ids: dict[str, set[str]] = defaultdict(set)
    source_rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    represented_classes: set[str] = set()
    for source_class, path in source_specs:
        if source_class not in required_classes:
            raise ValueError(f"source class is not declared by manifest: {source_class}")
        represented_classes.add(source_class)
        artifact = _load_json(path)
        if artifact.get("status") != "PASS":
            errors.append({"source_class": source_class, "path": path.name, "error": "RESOLUTION_NOT_PASS"})
        artifact_index_sha = artifact.get("scryfall_index", {}).get("sha256")
        if artifact_index_sha != index_sha:
            errors.append({"source_class": source_class, "path": path.name, "error": "SCRYFALL_INDEX_SHA_MISMATCH"})
        resolved = artifact.get("resolved")
        if not isinstance(resolved, list):
            raise ValueError(f"{path} resolved must be a list")
        for record in resolved:
            oracle_id = record.get("oracle_id")
            oracle_name = record.get("oracle_name")
            if not isinstance(oracle_id, str) or not isinstance(oracle_name, str):
                raise ValueError(f"{path} contains an invalid resolved identity")
            if oracle_id not in index_ids:
                errors.append({"source_class": source_class, "path": path.name, "error": f"ORACLE_ID_NOT_IN_INDEX:{oracle_id}"})
                continue
            existing = by_oracle_id.setdefault(oracle_id, {
                "oracle_id": oracle_id,
                "oracle_name": oracle_name,
                "source_classes": [],
                "source_flags": {},
                "behavior_priority": "REQUIRED_ACTUAL_CARD",
            })
            if existing["oracle_name"] != oracle_name:
                errors.append({"source_class": source_class, "path": path.name, "error": f"ORACLE_NAME_CONFLICT:{oracle_id}"})
            class_ids[source_class].add(oracle_id)
        source_rows.append({
            "source_class": source_class,
            "path": path.name,
            "sha256": _sha256(path),
            "resolution_status": artifact.get("status"),
            "resolved_record_count": len(resolved),
            "distinct_oracle_id_count": len({row.get("oracle_id") for row in resolved}),
        })

    missing_classes = sorted(set(required_classes) - represented_classes)
    for source_class in missing_classes:
        errors.append({"source_class": source_class, "path": "", "error": "REQUIRED_SOURCE_CLASS_MISSING"})

    for oracle_id, card in by_oracle_id.items():
        classes = sorted(source_class for source_class, ids in class_ids.items() if oracle_id in ids)
        card["source_classes"] = classes
        card["source_flags"] = {source_class: source_class in classes for source_class in required_classes}
    cards = sorted(by_oracle_id.values(), key=lambda row: row["oracle_id"])
    target_count = union_spec["target_count"]
    target_count_equal = len(cards) == target_count
    complete = not errors and target_count_equal and not missing_classes
    return {
        "schema": SCHEMA,
        "status": "PASS" if complete else "FAIL",
        "complete": complete,
        "source_head": index.get("source_head"),
        "source_tree": index.get("source_tree"),
        "external_pins": manifest.get("qualification_input", {}),
        "target_count": target_count,
        "computed_oracle_id_count": len(cards),
        "source_classes": required_classes,
        "represented_source_classes": sorted(represented_classes),
        "scryfall_index": {
            "path": index_path.name,
            "sha256": index_sha,
            "payload_sha256": index.get("payload_sha256"),
            "bulk_updated_at": index.get("bulk_updated_at"),
            "oracle_identity_count": index.get("oracle_identity_count"),
        },
        "source_rows": source_rows,
        "gate": {
            "all_resolution_artifacts_pass": all(row["resolution_status"] == "PASS" for row in source_rows),
            "all_ids_in_scryfall_index": not any("ORACLE_ID_NOT_IN_INDEX" in row["error"] for row in errors),
            "all_source_classes_represented": not missing_classes,
            "synthetic_promotion": False,
            "target_count_equal": target_count_equal,
        },
        "errors": errors,
        "cards": cards,
    }


def _source_spec(value: str) -> tuple[str, Path]:
    source_class, separator, path = value.partition("=")
    if not separator or not source_class or not path:
        raise argparse.ArgumentTypeError("source must be SOURCE_CLASS=PATH")
    return source_class, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--source", action="append", type=_source_spec, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(args.manifest, args.index, args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "target_count": result["target_count"],
        "computed_oracle_id_count": result["computed_oracle_id_count"],
        "errors": len(result["errors"]),
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
