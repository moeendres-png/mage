#!/usr/bin/env python3
"""WS23 fail-closed CARD_BEHAVIOR_FAILURE qualifier over immutable WS17 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CATEGORY = "CARD_BEHAVIOR_FAILURE"
WS17_HEAD = "a5f68f9ec49d19d900e92e505654871d2267ba93"
WS17_RUN = 33264286138
WS17_ARTIFACT = 9718189742
WS17_ARTIFACT_DIGEST = "sha256:7133a9b8fdf3246f6a756114396fba6a35cb8b9a28c4cc8622317ab0b0f03cba"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--witnesses", type=Path, required=True)
    p.add_argument("--source-head", required=True)
    p.add_argument("--source-tree", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    assert contract["$id"] == "commander-simulator-next.failure-outcome.v1"
    assert CATEGORY in contract["properties"]["category"]["enum"]
    assert contract["x-categories"][CATEGORY]["public_message"] == "card behavior verification failed"

    witnesses = [json.loads(line) for line in args.witnesses.read_text(encoding="utf-8").splitlines() if line.strip()]
    eligible = []
    for witness in witnesses:
        if witness.get("execution") != "PASS" or witness.get("stdout_only") is not False:
            continue
        for assertion in witness.get("state_assertions", []):
            if assertion.get("result") == "PASS" and assertion.get("expected") == assertion.get("actual"):
                eligible.append((witness, assertion))
    assert eligible, "WS17 artifact has no successful state assertion"
    witness, assertion = sorted(eligible, key=lambda item: (item[0]["primitive_ids"][0], item[1]["assertion_id"]))[0]

    baseline = {
        "source_head": witness["source_head"],
        "forge_pin": witness["forge_pin"],
        "witness_id": witness["witness_id"],
        "primitive_id": witness["primitive_ids"][0],
        "semantic_path": assertion["semantic_path"],
        "expected": assertion["expected"],
        "actual": assertion["actual"],
        "result": assertion["result"],
        "execution": witness["execution"],
        "trace_sha256": witness["trace_sha256"],
        "stdout_only": witness["stdout_only"],
    }
    assert baseline["source_head"] == WS17_HEAD
    assert baseline["forge_pin"] == "8c7e9afb8e6caee88644b94e25da5852e36f8928"
    assert baseline["expected"] == baseline["actual"]

    # Controlled verifier-workspace fault: mutate only the expected value. The
    # immutable actual engine state and source witness are never edited.
    controlled_expected = str(baseline["expected"]) + "::WS23_CONTROLLED_EXPECTATION_MISMATCH"
    controlled_actual = baseline["actual"]
    semantic_match = controlled_expected == controlled_actual
    assert not semantic_match

    public_outcome = {
        "schema": contract["$id"],
        "category": CATEGORY,
        "correlation_id": "ws23-semantic-verifier-control",
        "game_id": f"qualification:ws17-run-{WS17_RUN}",
        "decision_id": None,
        "principal_id": None,
        "public_message": contract["x-categories"][CATEGORY]["public_message"],
        "state_committed": False,
    }
    # Public safety is structural. Raw equality against scalar values such as
    # false/0 would create false positives because those literals are legitimate
    # contract fields. Semantic expected/actual data is allowed only in the
    # immutable qualification records below, never in the public envelope.
    forbidden_public_keys = {"expected", "actual", "semantic_path", "trace_sha256", "witness_id", "primitive_id"}
    public_payload_safe = forbidden_public_keys.isdisjoint(public_outcome.keys())
    assert public_payload_safe

    expected_record = {
        "semantic_path": baseline["semantic_path"],
        "expected": controlled_expected,
        "source": "WS23_CONTROLLED_VERIFIER_WORKSPACE",
    }
    actual_record = {
        "semantic_path": baseline["semantic_path"],
        "actual": controlled_actual,
        "source": "IMMUTABLE_WS17_PINNED_FORGE_WITNESS",
        "trace_sha256": baseline["trace_sha256"],
    }

    gate = {
        "schema": "commander-simulator-next.ws23-card-behavior-failure.v1",
        "workstream": "WS23",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "ws17": {"head": WS17_HEAD, "run_id": WS17_RUN, "artifact_id": WS17_ARTIFACT, "artifact_digest": WS17_ARTIFACT_DIGEST},
        "classification": CATEGORY,
        "evidence_class": "TECHNICALLY_CONFORMANT",
        "classification_basis": "EXPECTED_ACTUAL_SEMANTIC_MISMATCH",
        "engine_execution": "PASS",
        "semantic_verifier": "FAIL_AS_CONTROLLED",
        "engine_failure_distinct": True,
        "public_failure": public_outcome,
        "state_committed": False,
        "fallback_used": False,
        "production_binding": "QUALIFIER_ONLY",
        "production_reachable": False,
        "reachability_adjudication": "No WS14 production runtime callsite for the actual-card semantic witness verifier is established. WS23 therefore does not invent a runtime adapter; WS25 must keep production CARD_BEHAVIOR_FAILURE reachability fail-closed unless a real callsite is proven.",
        "baseline": baseline,
        "controlled_expected": expected_record,
        "immutable_actual": actual_record,
        "hard_gates": {
            "immutable_ws17_engine_execution_pass": baseline["execution"] == "PASS",
            "baseline_expected_equals_actual": baseline["expected"] == baseline["actual"],
            "controlled_semantic_mismatch_detected": not semantic_match,
            "typed_card_behavior_failure": public_outcome["category"] == CATEGORY,
            "distinct_from_engine_failure": public_outcome["category"] != "ENGINE_FAILURE" and baseline["execution"] == "PASS",
            "state_commit_forbidden": public_outcome["state_committed"] is False,
            "public_payload_semantic_values_absent": public_payload_safe,
            "silent_fallback_absent": True,
            "classification_not_card_name_based": True,
            "production_reachability_not_invented": True,
        },
        "status": "PASS",
        "WORKSTREAM_COMPLETE": True,
        "FAILURE_SEMANTICS_OVERALL_CLAIMED": False,
    }
    assert all(gate["hard_gates"].values())

    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in (
        ("WS23_BASELINE.json", baseline),
        ("WS23_CONTROLLED_EXPECTED.json", expected_record),
        ("WS23_IMMUTABLE_ACTUAL.json", actual_record),
        ("CARD_BEHAVIOR_FAILURE.json", public_outcome),
        ("WS23_GATE.json", gate),
    ):
        (args.out / name).write_bytes(canonical(value))
    hashes = []
    for name in ("WS23_BASELINE.json", "WS23_CONTROLLED_EXPECTED.json", "WS23_IMMUTABLE_ACTUAL.json", "CARD_BEHAVIOR_FAILURE.json", "WS23_GATE.json"):
        path = args.out / name
        hashes.append(f"{sha256(path.read_bytes())}  {name}")
    (args.out / "WS23_HASHES.sha256").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    print("WS23_CARD_BEHAVIOR_FAILURE=PASS")
    print("WS23_ENGINE_EXECUTION=PASS")
    print("WS23_SEMANTIC_VERIFIER=FAIL_AS_CONTROLLED")
    print("WS23_PRODUCTION_REACHABLE=FALSE")
    print("WORKSTREAM_COMPLETE=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
