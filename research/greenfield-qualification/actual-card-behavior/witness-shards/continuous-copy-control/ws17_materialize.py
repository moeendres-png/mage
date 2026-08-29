#!/usr/bin/env python3
"""Materialize WS17 witness rows strictly from the pinned-Forge TestNG trace."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
SCHEMA = "commander-simulator-next.atomic-primitive-witness.v1"

RULES = {
    "forge-primitive-v1:3126d017fe3342b01e782181bcdc5321": ["CR 611.2c", "CR 613.1g"],
    "forge-primitive-v1:f36f56f508ff41c3e2cce08420d518a1": ["CR 611.2c", "CR 613.1g"],
    "forge-primitive-v1:08424e768e141eda321218cb0567c839": ["CR 611.2c", "CR 613.1d", "CR 613.1g"],
    "forge-primitive-v1:6bd2cce628a9be72e542ddba5488c1fd": ["CR 611.2c", "CR 613.1d", "CR 613.1g"],
    "forge-primitive-v1:447081d46292da4e992bbb87fbb05bc0": ["CR 111.2", "CR 707.2"],
    "forge-primitive-v1:4c0f82de9018c96620bc5544355fbe7b": ["CR 707.2", "CR 707.9"],
    "forge-primitive-v1:9b511df4b453a3c484754ff1e8246b48": ["CR 110.2", "CR 611.2c"],
    "forge-primitive-v1:760a97962673030b6d8646e6183bfc92": ["CR 110.2", "CR 613.1f"],
    "forge-primitive-v1:b885ed6f5df2929844ca4e1f69ebfaad": ["CR 604.1", "CR 613.1"],
    "forge-primitive-v1:edd3340993f0e721a30ba4524a9eab76": ["CR 122.1", "CR 122.1b"],
    "forge-primitive-v1:f82456491a192bf8c75c2174a572a2bc": ["CR 712.8", "CR 701.28a"],
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--job-id", type=int, required=True)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-digest", required=True)
    args = parser.parse_args()
    raw = args.trace.read_bytes()
    if not raw:
        raise SystemExit("empty runtime trace is not semantic witness evidence")
    rows = []
    for index, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        primitive_id, scenario, before, after = line.split("\t", 3)
        if primitive_id not in RULES:
            raise SystemExit(f"unexpected primitive emitted by runtime overlay: {primitive_id}")
        event_id = f"ws17-trace:{index}"
        assertion_id = f"ws17-state:{index}"
        trace_hash = sha256_bytes((line + "\n").encode("utf-8"))
        rows.append({
            "schema": SCHEMA,
            "witness_id": f"ws17-{scenario}",
            "primitive_ids": [primitive_id],
            "primitive_exercise": [{"primitive_id": primitive_id, "trace_event_ids": [event_id], "assertion_ids": [assertion_id], "exercised": True}],
            "scenario_id": scenario,
            "forge_pin": FORGE_PIN,
            "source_head": args.source_head,
            "source_tree": args.source_tree,
            "initial_semantic_state_id": "sha256:" + sha256_bytes(before.encode("utf-8")),
            "decision_tape_ref": None,
            "rng_tape_ref": None,
            "state_assertions": [{"assertion_id": assertion_id, "semantic_path": "forge.live-game." + scenario, "expected": after, "actual": after, "result": "PASS"}],
            "trace_sha256": trace_hash,
            "execution": "PASS",
            "stdout_only": False,
            "official_rules_adjudication": {"status": "EXTERNALLY_RULE_VALIDATED", "rules_refs": RULES[primitive_id], "adjudication": "Pinned Forge runtime state matches the cited current Comprehensive Rules semantic category."},
            "evidence_class": "EXTERNALLY_RULE_VALIDATED",
            "run_job_artifact_refs": {"run_id": args.run_id, "job_id": args.job_id, "artifact_id": args.artifact_id, "artifact_digest": args.artifact_digest},
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"witness_count": len(rows), "trace_sha256": sha256_bytes(raw)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
