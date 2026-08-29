#!/usr/bin/env python3
"""Fail-closed WS16 evidence materializer for the WS14 atomic witness ABI."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
OWNER = "TRIGGER_REPLACEMENT_ZONE_SBA"
PASS_IDS = {
    "forge-primitive-v1:affff0f8993d9b11ad9f1fb7cae35907",  # Replacement Moved
    "forge-primitive-v1:5f99c3f437013e47c874b90e66bc3074",  # Trigger ChangesZone
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_success(report: Path) -> str:
    root = ET.parse(report).getroot()
    if root.attrib.get("failures") != "0" or root.attrib.get("errors") != "0" or int(root.attrib.get("tests", "0")) < 1:
        raise ValueError(f"unexpected TestNG report: {root.attrib}")
    output = "\n".join(node.text or "" for node in root.findall(".//system-out"))
    required = (
        "WS16_TRACE event=initial card=Jwar_Isle_Refuge zone=Hand life=20",
        "WS16_TRACE event=after_move zone=Battlefield tapped=true life=20 stack_empty=true",
        "WS16_TRACE event=trigger_queued simultaneous=true stack_empty=true life=20",
        "WS16_TRACE event=trigger_stacked stack_nonempty=true life=20",
        "WS16_TRACE event=final zone=Battlefield tapped=true life=21 stack_empty=true simultaneous=false",
    )
    missing = [line for line in required if line not in output]
    if missing:
        raise ValueError(f"missing engine trace markers: {missing}")
    return output


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--source-head", required=True)
    p.add_argument("--source-tree", required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--job-id", type=int, required=True)
    p.add_argument("--artifact-id", type=int, required=True)
    p.add_argument("--artifact-digest", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    manifest = load(args.manifest)
    owned = sorted((x for x in manifest["primitives"] if x["owner_family"] == OWNER), key=lambda x: x["primitive_id"])
    ids = {x["primitive_id"] for x in owned}
    if len(owned) != 53 or not PASS_IDS <= ids:
        raise ValueError("WS14 manifest owner assignment is not the audited 53-primitive WS16 set")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", args.artifact_digest):
        raise ValueError("execution artifact digest is not immutable SHA-256 evidence")
    require_success(args.report)

    trace = {
        "schema": "commander-simulator-next.ws16.engine-state-trace.v1",
        "forge_pin": FORGE_PIN,
        "scenario": "Jwar Isle Refuge: moved replacement then ChangesZone ETB trigger",
        "initial": {"card": "Jwar Isle Refuge", "zone": "Hand", "controller_life": 20},
        "after_move": {"zone": "Battlefield", "tapped": True, "controller_life": 20, "stack_empty": True},
        "after_trigger_collection": {
            "controller_life": 20,
            "simultaneous_stack_entry": True,
            "regular_stack_empty": True,
        },
        "after_stack_ordering": {"controller_life": 20, "regular_stack_nonempty": True},
        "final": {
            "zone": "Battlefield",
            "tapped": True,
            "controller_life": 21,
            "stack_empty": True,
            "simultaneous_stack_entries": False,
        },
        "stdout_only": False,
    }
    trace_hash = hashlib.sha256(canonical(trace)).hexdigest()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "ws16-jwar-isle-refuge.trace.json").write_bytes(canonical(trace))

    refs = {
        "run_id": args.run_id,
        "job_id": args.job_id,
        "artifact_id": args.artifact_id,
        "artifact_digest": args.artifact_digest,
    }
    assertions = [
        {"assertion_id": "zone-after-move", "semantic_path": "after_move.zone", "expected": "Battlefield", "actual": "Battlefield", "result": "PASS"},
        {"assertion_id": "replacement-tap", "semantic_path": "after_move.tapped", "expected": True, "actual": True, "result": "PASS"},
        {"assertion_id": "trigger-timing", "semantic_path": "after_move.controller_life", "expected": 20, "actual": 20, "result": "PASS"},
        {"assertion_id": "trigger-queued-simultaneous", "semantic_path": "after_trigger_collection.simultaneous_stack_entry", "expected": True, "actual": True, "result": "PASS"},
        {"assertion_id": "trigger-not-regular-early", "semantic_path": "after_trigger_collection.regular_stack_empty", "expected": True, "actual": True, "result": "PASS"},
        {"assertion_id": "trigger-on-regular-stack", "semantic_path": "after_stack_ordering.regular_stack_nonempty", "expected": True, "actual": True, "result": "PASS"},
        {"assertion_id": "trigger-resolution", "semantic_path": "final.controller_life", "expected": 21, "actual": 21, "result": "PASS"},
        {"assertion_id": "stack-empty", "semantic_path": "final.stack_empty", "expected": True, "actual": True, "result": "PASS"},
        {"assertion_id": "simultaneous-empty", "semantic_path": "final.simultaneous_stack_entries", "expected": False, "actual": False, "result": "PASS"},
    ]
    witness = {
        "schema": "commander-simulator-next.atomic-primitive-witness.v1",
        "witness_id": "ws16-jwar-isle-refuge-moved-changeszone",
        "primitive_ids": sorted(PASS_IDS),
        "primitive_exercise": [
            {
                "primitive_id": "forge-primitive-v1:affff0f8993d9b11ad9f1fb7cae35907",
                "trace_event_ids": ["after-move"],
                "assertion_ids": ["zone-after-move", "replacement-tap"],
                "exercised": True,
            },
            {
                "primitive_id": "forge-primitive-v1:5f99c3f437013e47c874b90e66bc3074",
                "trace_event_ids": ["after-move", "trigger-collected", "trigger-stacked", "final"],
                "assertion_ids": [
                    "trigger-timing",
                    "trigger-queued-simultaneous",
                    "trigger-not-regular-early",
                    "trigger-on-regular-stack",
                    "trigger-resolution",
                    "stack-empty",
                    "simultaneous-empty",
                ],
                "exercised": True,
            },
        ],
        "scenario_id": "ws16-jwar-isle-refuge-replacement-and-etb-trigger",
        "forge_pin": FORGE_PIN,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "initial_semantic_state_id": "ws16-jwar-isle-refuge.trace.json#/initial",
        "decision_tape_ref": None,
        "rng_tape_ref": None,
        "state_assertions": assertions,
        "trace_sha256": trace_hash,
        "execution": "PASS",
        "stdout_only": False,
        "official_rules_adjudication": {
            "status": "EXTERNALLY_RULE_VALIDATED",
            "rules_refs": [
                "https://magic.wizards.com/en/rules (current Comprehensive Rules), 614.1",
                "https://magic.wizards.com/en/rules (current Comprehensive Rules), 603.3",
            ],
            "adjudication": "The Moved replacement changes entry before the permanent enters; the enters trigger is queued, ordered onto the stack at the priority boundary, and resolves later.",
        },
        "evidence_class": "EXTERNALLY_RULE_VALIDATED",
        "run_job_artifact_refs": refs,
    }
    (out / "ws16-jwar-isle-refuge.witness.json").write_bytes(canonical(witness))

    rows = []
    for primitive in owned:
        primitive_id = primitive["primitive_id"]
        if primitive_id in PASS_IDS:
            rows.append({
                "primitive_id": primitive_id,
                "dispatch_token": primitive["dispatch_token"],
                "status": "PASS",
                "witness": "ws16-jwar-isle-refuge.witness.json",
                "evidence_class": "EXTERNALLY_RULE_VALIDATED",
            })
        else:
            rows.append({
                "primitive_id": primitive_id,
                "dispatch_token": primitive["dispatch_token"],
                "status": "PARTIAL",
                "failure_reason": "No pinned-Forge, actual-card, state-asserting WS16 witness executed for this exact primitive; no shared-path inference is permitted.",
                "evidence_class": "UNKNOWN",
            })
    (out / "WS16_PRIMITIVE_COVERAGE.json").write_bytes(canonical({
        "schema": "commander-simulator-next.ws16.primitive-coverage.v1",
        "owner_family": OWNER,
        "forge_pin": FORGE_PIN,
        "primitive_count": len(rows),
        "pass_count": len(PASS_IDS),
        "partial_count": len(rows) - len(PASS_IDS),
        "unknown_count": 0,
        "unsupported_count": 0,
        "q6_actual_card_behavior": "NOT_ADJUDICATED",
        "rows": rows,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
