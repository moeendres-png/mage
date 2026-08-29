#!/usr/bin/env python3
"""Validate WS19's owner shard against the immutable WS14 manifest."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OWNER = "HIDDEN_RNG_REPLAY"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("ws14_validate_witness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--abi", type=Path, required=True)
    parser.add_argument("--ws14-validator", type=Path, required=True)
    parser.add_argument("--witness-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    abi = json.loads(args.abi.read_text(encoding="utf-8"))
    if manifest["forge_pin"] != FORGE_PIN or coverage["forge_pin"] != FORGE_PIN:
        raise SystemExit("Forge pin mismatch")
    if coverage["primitive_manifest_sha256"] != hashlib.sha256(args.manifest.read_bytes()).hexdigest():
        raise SystemExit("coverage is not bound to the exact manifest bytes")
    expected = {
        item["primitive_id"] for item in manifest["primitives"]
        if item["owner_family"] == OWNER
    }
    rows = coverage["primitive_coverage"]
    actual = {row["primitive_id"] for row in rows}
    if len(rows) != len(actual) or actual != expected:
        raise SystemExit("coverage primitive IDs do not exactly equal WS19 ownership")
    witnesses = coverage["pass_witnesses"]
    witness_ids = {item["witness_id"] for item in witnesses}
    if len(witnesses) != len(witness_ids):
        raise SystemExit("duplicate PASS witness IDs")
    validator = load_module(args.ws14_validator)
    for witness in witnesses:
        if witness.get("execution") != "PASS" or witness.get("stdout_only") is not False:
            raise SystemExit("PASS witness is not an actual non-stdout execution")
        if witness.get("forge_pin") != FORGE_PIN:
            raise SystemExit("PASS witness has a non-pinned Forge")
        validator.validate_witness(abi, witness)
        trace = args.witness_dir / "traces" / f"{witness['trace_sha256']}.json"
        if not trace.is_file() or hashlib.sha256(trace.read_bytes()).hexdigest() != witness["trace_sha256"]:
            raise SystemExit("PASS witness lacks its immutable local trace")
    for row in rows:
        if row["status"] == "PASS":
            if len(row["witness_ids"]) != 1 or row["witness_ids"][0] not in witness_ids:
                raise SystemExit("PASS primitive lacks exactly one registered PASS witness")
        elif row["witness_ids"]:
            raise SystemExit("non-PASS primitive cannot cite a PASS witness")
        if row["status"] not in {"PASS", "PARTIAL", "UNKNOWN", "UNSUPPORTED"}:
            raise SystemExit("invalid primitive status")
        if row["status"] != "PASS" and not row.get("exact_blocker"):
            raise SystemExit("non-PASS primitive lacks an exact blocker")
    counts = {status: sum(1 for row in rows if row["status"] == status)
              for status in ("PASS", "PARTIAL", "UNKNOWN", "UNSUPPORTED")}
    if coverage["coverage_counts"] != counts:
        raise SystemExit("coverage counts do not match primitive rows")
    if coverage["hard_gate"]["global_ws05_ws06_inheritance_used_as_behavior_proof"]:
        raise SystemExit("forbidden global contract inheritance")
    if coverage["hard_gate"]["q6_actual_card_behavior"] != "NOT_ADJUDICATED":
        raise SystemExit("WS19 must not adjudicate Q6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
