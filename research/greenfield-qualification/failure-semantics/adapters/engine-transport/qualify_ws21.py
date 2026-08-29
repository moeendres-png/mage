#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def load_props(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"WS21 FAIL: {message}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-root", required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    root = Path(args.evidence_root)
    result = load_props(root / "WS21_RESULT.properties")
    workers = {
        "engine": root / "workers/engine",
        "transport": root / "workers/transport",
        "malformed": root / "workers/malformed-control",
    }
    expected = {
        "engine": "ENGINE_FAILURE",
        "transport": "TRANSPORT_FAILURE",
        "malformed": "MALFORMED_RESPONSE",
    }
    traces: dict[str, dict] = {}
    outcomes: dict[str, dict] = {}
    for name, path in workers.items():
        outcomes[name] = json.loads((path / "outcome.json").read_text(encoding="utf-8"))
        lines = [line for line in (path / "fault-trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        require(len(lines) == 1, f"{name} must have exactly one deterministic fault trace")
        traces[name] = json.loads(lines[0])
        require(outcomes[name].get("category") == expected[name], f"{name} outcome category mismatch")
        require(traces[name].get("category") == expected[name], f"{name} trace category mismatch")
        require(outcomes[name].get("state_committed") is False, f"{name} outcome committed failed state")
        require(traces[name].get("state_committed") is False, f"{name} trace committed failed state")
        require(traces[name].get("process_alive_while_reporting") is True, f"{name} process was not alive while reporting")

    require(result.get("engine_category") == "ENGINE_FAILURE", "engine exact typed outcome missing")
    require(result.get("engine_worker_exit") == "0", "engine worker termination became process failure")
    require(result.get("engine_process_alive_while_reporting") == "true", "engine worker did not report live")
    require(result.get("engine_state_committed") == "false", "engine failure committed state")
    require(result.get("engine_original_body_after_fault") == "false", "engine continued after injected failure")

    require(result.get("transport_category") == "TRANSPORT_FAILURE", "transport exact typed outcome missing")
    require(result.get("transport_worker_exit") == "0", "transport worker termination became process failure")
    require(result.get("transport_process_alive_while_reporting") == "true", "transport worker did not report live")
    require(result.get("transport_state_committed") == "false", "transport failure committed state")
    require(result.get("transport_decision_applied") == "0", "transport failure substituted a decision")

    require(result.get("malformed_control_category") == "MALFORMED_RESPONSE",
            "malformed pilot response was not distinct from transport failure")
    require(result.get("malformed_transport_propagations") == "0",
            "malformed pilot response crossed transport failure boundary")
    require(result.get("diagnostic_hidden_info_leaks") == "0", "diagnostic hidden-info leak detected")
    require(result.get("distinct_worker_pids") == "3", "fresh process witness incomplete")
    require(result.get("games_per_worker_process") == "1", "same-JVM multi-game topology introduced")

    require(traces["engine"].get("engine_fault_fired") is True, "engine injection not observed")
    require(traces["engine"].get("post_fault_engine_body_reached") is False, "engine original body reached after fault")
    require(traces["transport"].get("engine_fault_fired") is False, "transport fault overlaps engine injection")
    require(traces["transport"].get("transport_requests_written", 0) >= 1, "transport request not delivered")
    require(traces["transport"].get("transport_responses_decoded") == 0, "transport failure decoded a response")
    require(traces["transport"].get("transport_boundary_propagations", 0) >= 1,
            "typed transport exception did not propagate through actual controller boundary")
    require(traces["transport"].get("decision_validated") == 0, "transport failure reached validator")
    require(traces["transport"].get("decision_applied") == 0, "transport failure applied a decision")
    require(traces["malformed"].get("transport_responses_decoded", 0) >= 1,
            "malformed negative control was not a valid transport frame")
    require(traces["malformed"].get("transport_boundary_propagations") == 0,
            "malformed negative control became transport failure")

    gate = {
        "schema": "commander-simulator-next.ws21-engine-transport-gate.v1",
        "status": "PASS",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "forge_pin": FORGE_PIN,
        "ENGINE_FAILURE": "PASS",
        "TRANSPORT_FAILURE": "PASS",
        "FAILURE_SEMANTICS": "NOT_PROMOTED",
        "overall_promotion_performed": False,
        "process_model": "ONE_GAME_PER_OS_PROCESS",
        "hard_gates": {
            "ENGINE_ACTUAL_PATH_TYPED": True,
            "ENGINE_DISTINCT_FROM_PROCESS_AND_CANCEL": True,
            "ENGINE_NO_SILENT_CONTINUATION": True,
            "ENGINE_NO_FAILED_STATE_COMMIT": True,
            "TRANSPORT_ACTUAL_PATH_TYPED": True,
            "TRANSPORT_DISTINCT_FROM_MALFORMED_RESPONSE": True,
            "TRANSPORT_DISTINCT_FROM_ENGINE_AND_PROCESS": True,
            "TRANSPORT_NO_SUBSTITUTED_DECISION": True,
            "TRANSPORT_NO_FAILED_STATE_COMMIT": True,
            "TRANSPORT_DIAGNOSTIC_HIDDEN_INFO_LEAKS_ZERO": True,
            "DETERMINISTIC_MACHINE_READABLE_TRACES": True,
            "PROCESS_PER_GAME_TOPOLOGY_PRESERVED": True,
        },
        "evidence_classification": {
            "engine_fault_site_binding": "CODE_DERIVED",
            "engine_runtime_witness": "TECHNICALLY_CONFORMANT",
            "transport_controller_binding": "CODE_DERIVED",
            "transport_runtime_witness": "TECHNICALLY_CONFORMANT",
            "malformed_response_negative_control": "TECHNICALLY_CONFORMANT",
            "diagnostic_hidden_information_scan": "DIRECTLY_VERIFIED",
        },
        "negative_control": {
            "category": "MALFORMED_RESPONSE",
            "transport_failure_propagations": 0,
        },
    }
    out_json = Path(args.out_json)
    out_json.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# WS21 Engine + Transport Failure Gate\n\n- Status: **PASS**\n- ENGINE_FAILURE: **PASS**\n- TRANSPORT_FAILURE: **PASS**\n- FAILURE_SEMANTICS: **NOT_PROMOTED**\n- Source head: `{args.source_head}`\n- Source tree: `{args.source_tree}`\n- Forge pin: `{FORGE_PIN}`\n- Process model: one game per OS process\n- Malformed-response negative control: **MALFORMED_RESPONSE**, transport propagations 0\n- Structured diagnostic hidden-info leaks: 0\n"""
    Path(args.out_md).write_text(md, encoding="utf-8")
    print("WS21_ENGINE_FAILURE=PASS")
    print("WS21_TRANSPORT_FAILURE=PASS")
    print("WS21_FAILURE_SEMANTICS_PROMOTED=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
