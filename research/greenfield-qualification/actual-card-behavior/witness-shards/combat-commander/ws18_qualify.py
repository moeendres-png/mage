#!/usr/bin/env python3
"""Fail-closed WS18 witness-shard materializer.

This tool intentionally treats the WS14 implementation map as provenance, not
as semantic evidence.  A COMBAT_COMMANDER primitive moves to PASS only when a
separate witness has exercised the exact primitive in pinned Forge and supplied
state assertions, trace events, and immutable evidence references.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OWNER = "COMBAT_COMMANDER"
SCHEMA = "commander-simulator-next.ws18-combat-commander-shard.v1"


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    primitives = [p for p in manifest["primitives"] if p["owner_family"] == OWNER]
    if len(primitives) != 10:
        raise SystemExit(f"expected exactly 10 {OWNER} primitives, found {len(primitives)}")

    rows = []
    for primitive in sorted(primitives, key=lambda item: item["primitive_id"]):
        rows.append({
            "primitive_id": primitive["primitive_id"],
            "dispatch_domain": primitive["dispatch_domain"],
            "dispatch_token": primitive["dispatch_token"],
            "implementation_target": primitive["implementation_target"],
            "status": "PARTIAL",
            "evidence_class": "UNKNOWN",
            "witness_ids": [],
            "blocker": (
                "No WS18 pinned-Forge semantic witness has exercised this exact "
                "primitive with engine-state assertions. WS14 source binding and "
                "the retained WS07 matrix are prerequisites, not witness evidence."
            ),
        })

    result = {
        "schema": SCHEMA,
        "owner_family": OWNER,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "forge_pin": manifest["forge_pin"],
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "primitive_count": len(rows),
        "counts": {"PASS": 0, "PARTIAL": len(rows), "UNKNOWN": 0, "UNSUPPORTED": 0},
        "witnesses": [],
        "primitive_status": rows,
        "q6_result": "NOT_ADJUDICATED",
        "card_name_production_hacks": 0,
        "stdout_only_pass_witnesses": 0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
