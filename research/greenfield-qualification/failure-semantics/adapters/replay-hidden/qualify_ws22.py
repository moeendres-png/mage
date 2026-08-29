#!/usr/bin/env python3
"""Adjudicate WS22 from actual Q3/Q2 detector traces only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adapter import bind_hidden_info_violation, canonical_hash, load_contract

BASE_SHA = "80743bdbc2950b00e422f3deb38f04111f30a4d4"
WS05_SHA = "554bb06af0dd5e542ff8bbfd5e96054a74642d3a"
WS06_SHA = "e23af2b621f2e318014491b8a84146ed4ad3bed6"
WS90_SHA = "55820618e7243bd5ba8cfa33c3148cea8c166c73"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
WS05_RUN_ID = 33210994482
WS05_ARTIFACT_ID = 9701653278
WS06_RUN_ID = 33209213338
WS06_ARTIFACT_ID = 9701086657


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def all_checks(trace: dict[str, Any]) -> bool:
    checks = trace.get("checks")
    return isinstance(checks, dict) and bool(checks) and all(value is True for value in checks.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--hidden", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--hidden-trace-out", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = load_contract(args.contract)
    replay = load(args.replay)
    hidden_runtime = load(args.hidden)
    hidden = bind_hidden_info_violation(contract, hidden_runtime)
    args.hidden_trace_out.parent.mkdir(parents=True, exist_ok=True)
    args.hidden_trace_out.write_text(json.dumps(hidden, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    replay_outcome = replay.get("outcome", {})
    hidden_outcome = hidden.get("outcome", {})
    replay_baseline = replay.get("qualified_baseline", {})
    replay_detector = replay.get("detector", {})

    hard = {
        "REPLAY_ACTUAL_WS06_DETECTOR_BOUND": (
            replay.get("status") == "PASS"
            and replay.get("category") == "REPLAY_DIVERGENCE"
            and replay.get("production_binding") == "WS06_SEMANTIC_REPLAY_COMPARATOR_E_SEMANTIC_DIVERGENCE"
            and replay_outcome.get("category") == "REPLAY_DIVERGENCE"
            and all_checks(replay)
        ),
        "REPLAY_QUALIFIED_BASELINE_PASSES": (
            replay_baseline.get("status") == "PASS"
            and replay_baseline.get("semantic_state_divergences") == 0
            and replay_baseline.get("rng_event_divergences") == 0
            and replay_baseline.get("decision_event_divergences") == 0
        ),
        "REPLAY_CONTROLLED_DIVERGENCE_REJECTED": (
            replay_detector.get("failure_codes") is not None
            and "E_SEMANTIC_DIVERGENCE" in replay_detector.get("failure_codes", [])
            and replay_detector.get("divergence_counts", {}).get("semantic_state", 0) > 0
            and replay_detector.get("divergence_counts", {}).get("rng_event") == 0
            and replay_detector.get("divergence_counts", {}).get("decision_event") == 0
        ),
        "REPLAY_SEMANTIC_CRITERIA_ONLY": (
            replay_detector.get("stdout_used_as_replay_criterion") is False
            and replay_baseline.get("stdout_used_as_replay_criterion") is False
        ),
        "REPLAY_FAILURE_NO_STATE_COMMIT_OR_FALLBACK": (
            replay_outcome.get("state_committed") is False
            and replay.get("checks", {}).get("no_fallback") is True
        ),
        "HIDDEN_ACTUAL_WS05_DETECTOR_BOUND": (
            hidden.get("status") == "PASS"
            and hidden.get("category") == "HIDDEN_INFO_VIOLATION"
            and hidden.get("production_binding") == "WS05_PRINCIPAL_CARDVIEW_AUTHORIZATION_REDTEAM"
            and hidden_outcome.get("category") == "HIDDEN_INFO_VIOLATION"
            and all_checks(hidden)
        ),
        "HIDDEN_ACTUAL_FORBIDDEN_CARDVIEW_DATUM": (
            hidden_runtime.get("actual_cardview_identity_bearing") is True
            and hidden_runtime.get("authorized_for_target_principal") is False
            and hidden_runtime.get("detected") is True
            and hidden_runtime.get("leaks_before") == 0
            and hidden_runtime.get("leaks_after") == 1
        ),
        "HIDDEN_PUBLIC_ERROR_ENVELOPE_SECRET_SAFE": hidden_runtime.get("public_envelope_secret_safe") is True,
        "HIDDEN_FAILURE_DOES_NOT_MUTATE_STATE": (
            hidden_runtime.get("state_witness_unchanged") is True
            and hidden_outcome.get("state_committed") is False
        ),
        "HIDDEN_FAILS_CLOSED_WITHOUT_FALLBACK": (
            hidden_runtime.get("fail_closed") is True
            and hidden.get("checks", {}).get("no_fallback") is True
        ),
    }
    replay_pass = all(hard[key] for key in hard if key.startswith("REPLAY_"))
    hidden_pass = all(hard[key] for key in hard if key.startswith("HIDDEN_"))
    passed = replay_pass and hidden_pass

    result = {
        "schema": "commander-simulator-next.ws22-failure-replay-hidden-gate.v1",
        "workstream": "WS22",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "base_sha": BASE_SHA,
        "dependencies": {
            "WS05": {"sha": WS05_SHA, "qualified_run_id": WS05_RUN_ID, "artifact_id": WS05_ARTIFACT_ID, "mode": "READ_ONLY"},
            "WS06": {"sha": WS06_SHA, "qualified_run_id": WS06_RUN_ID, "artifact_id": WS06_ARTIFACT_ID, "mode": "READ_ONLY"},
            "WS90_integrated_runtime": {"sha": WS90_SHA, "mode": "READ_ONLY"},
            "Forge": {"sha": FORGE_PIN, "mode": "READ_ONLY"},
        },
        "categories": {
            "REPLAY_DIVERGENCE": {
                "status": "PASS" if replay_pass else "FAIL",
                "evidence_class": "TECHNICALLY_CONFORMANT",
                "production_binding": replay.get("production_binding"),
                "trace_sha256": replay.get("trace_sha256"),
            },
            "HIDDEN_INFO_VIOLATION": {
                "status": "PASS" if hidden_pass else "FAIL",
                "evidence_class": "TECHNICALLY_CONFORMANT",
                "production_binding": hidden.get("production_binding"),
                "trace_sha256": hidden.get("trace_sha256"),
            },
        },
        "hard_gates": hard,
        "regression_implications": {
            "Q2_PRINCIPAL_HIDDEN_INFORMATION": {
                "decision": "NO_RERUN",
                "focused_negative_probe": "PASS" if hidden_pass else "FAIL",
                "reason": (
                    "WS22 does not modify the qualified WS05 source or production visibility overlay. "
                    "It copies exact WS05 code read-only, adds a test-workspace-only injection entry point, "
                    "and exercises the existing CardView/PlayerView authorization detector."
                ),
            },
            "Q3_SEMANTIC_REPLAY": {
                "decision": "NO_RERUN",
                "focused_negative_probe": "PASS" if replay_pass else "FAIL",
                "reason": (
                    "WS22 does not modify the qualified WS06 comparator, tape contract, RNG overlay, or replay runtime. "
                    "It first rechecks the immutable qualified A/B/C evidence as PASS, then mutates only a copied "
                    "semantic-state record and requires the exact WS06 comparator to reject it."
                ),
            },
        },
        "shared_ws12_schema_or_gate_modified": False,
        "FAILURE_SEMANTICS": "DEFERRED_TO_LATER_INTEGRATION",
        "REPLAY_DIVERGENCE": "PASS" if replay_pass else "FAIL",
        "HIDDEN_INFO_VIOLATION": "PASS" if hidden_pass else "FAIL",
        "evidence_classes": ["DIRECTLY_VERIFIED", "CODE_DERIVED", "TECHNICALLY_CONFORMANT"],
        "status": "PASS" if passed else "FAIL",
    }
    result["gate_sha256"] = canonical_hash(result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "REPLAY_DIVERGENCE": result["REPLAY_DIVERGENCE"],
        "HIDDEN_INFO_VIOLATION": result["HIDDEN_INFO_VIOLATION"],
        "FAILURE_SEMANTICS": result["FAILURE_SEMANTICS"],
    }, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
