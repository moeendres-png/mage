#!/usr/bin/env python3
"""Materialize WS19's fail-closed owner-family coverage shard.

This program deliberately does not turn the completed global WS05/WS06 gates
into primitive witnesses.  A primitive only becomes PASS when a WS19 evidence
record can be validated against the WS14 ABI and is backed by a trace produced
by a pinned-Forge, actual-card scenario.  No such trace is shipped in the
initial WS19 shard, so every assigned primitive is explicitly PARTIAL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

OWNER = "HIDDEN_RNG_REPLAY"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
SCHEMA = "commander-simulator-next.ws19-hidden-rng-replay-coverage.v1"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("forge_pin") != FORGE_PIN:
        raise SystemExit("WS14 manifest Forge pin does not match WS19 pin")
    primitives = [
        item for item in manifest.get("primitives", [])
        if item.get("owner_family") == OWNER
    ]
    if not primitives:
        raise SystemExit("WS14 has no WS19-owned primitives")

    rows = []
    for item in sorted(primitives, key=lambda value: value["primitive_id"]):
        rows.append({
            "primitive_id": item["primitive_id"],
            "dispatch_domain": item["dispatch_domain"],
            "dispatch_token": item["dispatch_token"],
            "implementation_target": item["implementation_target"],
            "implementation_source": item["implementation_source"],
            "status": "PARTIAL",
            "evidence_class": "UNKNOWN",
            "witness_ids": [],
            "failure_reason": "NO_CARD_DRIVEN_PINNED_FORGE_SEMANTIC_WITNESS",
            "exact_blocker": (
                "No actual-card scenario has executed this exact Forge dispatch path with "
                "principal-scoped observations, authoritative state assertions, immutable "
                "trace hash, and decision/RNG tapes where applicable. WS05/WS06 global "
                "qualification is a prerequisite only and is not per-primitive evidence."
            ),
            "required_next_evidence": [
                "pinned_forge_actual_card_execution",
                "trace_event_for_exact_primitive",
                "initial_and_final_semantic_state",
                "principal_scoped_hidden_information_assertion",
                "named_game_rng_tape_when_rng_relevant",
                "semantic_replay_comparison_when_replay_relevant",
                "official_rules_adjudication_when_semantic_rule_is_asserted",
            ],
        })

    doc = {
        "schema": SCHEMA,
        "owner_family": OWNER,
        "forge_pin": FORGE_PIN,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "primitive_manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "primitive_count": len(rows),
        "coverage_counts": {"PASS": 0, "PARTIAL": len(rows), "UNKNOWN": 0, "UNSUPPORTED": 0},
        "pass_witnesses": [],
        "nonqualifying_dependency_evidence": {
            "ws05_q2": "PREREQUISITE_ONLY_NOT_PRIMITIVE_WITNESS",
            "ws06_q3": "PREREQUISITE_ONLY_NOT_PRIMITIVE_WITNESS",
            "reason": "Their global contracts do not establish execution of a WS19-owned actual-card primitive.",
        },
        "primitive_coverage": rows,
        "hard_gate": {
            "all_assigned_primitives_accounted_for": True,
            "pass_requires_ws14_abi_witness": True,
            "pass_requires_pinned_forge_actual_card_execution": True,
            "pass_requires_stdout_only_false": True,
            "global_ws05_ws06_inheritance_used_as_behavior_proof": False,
            "q6_actual_card_behavior": "NOT_ADJUDICATED",
            "result": "FAIL_CLOSED",
        },
    }
    doc["coverage_sha256"] = sha256_json(doc)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
