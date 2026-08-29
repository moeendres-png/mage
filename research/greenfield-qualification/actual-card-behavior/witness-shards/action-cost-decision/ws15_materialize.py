#!/usr/bin/env python3
"""Fail-closed WS15 primitive-status materializer.

This is deliberately not a source-presence classifier.  A primitive becomes PASS
only after a WS15 witness JSON validates against the WS14 ABI and its immutable
trace is independently supplied.  The initial shard records every assigned
primitive as PARTIAL, with the exact missing executable proof as its blocker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
FAMILY = "ACTION_COST_DECISION"
SCHEMA = "commander-simulator-next.ws15.action-cost-decision-status.v1"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assigned = sorted(
        (row for row in manifest["primitives"] if row["owner_family"] == FAMILY),
        key=lambda row: row["primitive_id"],
    )
    if len(assigned) != 76:
        raise SystemExit(f"expected exactly 76 WS15 primitives, got {len(assigned)}")
    rows = []
    for primitive in assigned:
        rows.append({
            "primitive_id": primitive["primitive_id"],
            "dispatch_domain": primitive["dispatch_domain"],
            "dispatch_token": primitive["dispatch_token"],
            "implementation_target": primitive["implementation_target"],
            "classification": "PARTIAL",
            "evidence_class": "UNKNOWN",
            "witness_ids": [],
            "stdout_only": None,
            "trace_sha256": None,
            "initial_semantic_state_id": None,
            "final_semantic_state_id": None,
            "decision_tape_ref": None,
            "rng_tape_ref": None,
            "official_rules_adjudication": "UNKNOWN",
            "failure_reason": (
                "No WS15 actual-card, state-asserting pinned-Forge execution has yet "
                "bound this exact primitive through a legal DecisionRequest/authoritative "
                "option path. Dispatch/source provenance is not semantic behavior proof."
            ),
        })
    result = {
        "schema": SCHEMA,
        "owner_family": FAMILY,
        "forge_pin": PIN,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "status": "FAIL_CLOSED_PARTIAL",
        "card_name_production_hacks": 0,
        "assigned_primitive_count": len(rows),
        "pass_count": 0,
        "partial_count": len(rows),
        "unknown_count": 0,
        "unsupported_count": 0,
        "witness_count": 0,
        "rows": rows,
    }
    result["rows_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
