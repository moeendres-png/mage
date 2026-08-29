#!/usr/bin/env python3
"""Fail-closed WS17 primitive matrix: only validated runtime rows can be PASS."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNPROVED = {
    "CantPreventDamage": "no pinned-Forge prevention/replacement state witness yet",
    "Protection": "no target/damage/blocking prohibition witness yet",
    "IgnoreLegendRule": "no simultaneous legend-rule collision and state-based-action witness yet",
    "WitherDamage": "no damage-to-minus-one-minus-one-counter witness yet",
    "UntapOtherPlayer": "no principal-specific multiplayer untap witness yet",
    "CantDraw": "no draw replacement state witness yet",
    "CantGainLife": "no life-gain prevention state witness yet",
    "Panharmonicon": "no ETB trigger multiplicity/order witness yet",
    "ControlPlayer": "no authoritative pilot/control-player decision-path witness yet",
    "ControlGainVariant": "placeholder",
}


def load_validator(path: Path):
    spec = importlib.util.spec_from_file_location("ws14_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--witnesses", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = load_validator(args.validator)
    rows = [json.loads(line) for line in args.witnesses.read_text(encoding="utf-8").splitlines() if line]
    exercised: set[str] = set()
    for row in rows:
        validator.validate_witness(schema, row)
        if row["execution"] != "PASS" or row["stdout_only"]:
            raise SystemExit("nonqualifying runtime witness presented as PASS")
        exercised.update(row["primitive_ids"])
    matrix = []
    for primitive in manifest["primitives"]:
        if primitive["owner_family"] != "CONTINUOUS_COPY_CONTROL":
            continue
        primitive_id = primitive["primitive_id"]
        if primitive_id in exercised:
            status, reason = "PASS", None
        else:
            status = "PARTIAL"
            reason = UNPROVED.get(primitive["dispatch_token"], "no executable state-asserting WS17 witness")
        matrix.append({"primitive_id": primitive_id, "dispatch_token": primitive["dispatch_token"],
                       "implementation_target": primitive["implementation_target"], "status": status,
                       "failure_reason": reason})
    payload = {
        "schema": "commander-simulator-next.ws17-primitive-gate.v1",
        "forge_pin": manifest["forge_pin"], "owner_family": "CONTINUOUS_COPY_CONTROL",
        "primitive_count": len(matrix), "pass_count": sum(x["status"] == "PASS" for x in matrix),
        "partial_count": sum(x["status"] == "PARTIAL" for x in matrix), "unknown_count": 0,
        "unsupported_count": 0, "stdout_only": False,
        "Q6_ACTUAL_CARD_BEHAVIOR": "NOT_ADJUDICATED",
        "WS17_RESULT": "PARTIAL_FAIL_CLOSED" if any(x["status"] != "PASS" for x in matrix) else "PASS_SCOPE_ONLY",
        "witness_registry_sha256": sha256(args.witnesses), "primitive_matrix": matrix,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
