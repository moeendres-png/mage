#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_properties(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"missing required properties file: {path}")
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            key, value = line, ""
        out[key.strip()] = value.strip()
    return out


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"missing required provenance file: {path}")
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def as_int(props: dict[str, str], key: str, default: int = -1) -> int:
    value = props.get(key)
    if value is None or value == "":
        return default
    return int(value)


def as_bool(props: dict[str, str], key: str) -> bool:
    return props.get(key, "").lower() == "true"


def worker_summary(root: Path, label: str) -> dict[str, str]:
    return load_properties(root / "workers" / label / "summary.properties")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    root = Path(args.evidence_root).resolve()
    result = load_properties(root / "ISOLATION_RESULT.properties")
    provenance = load_env(root / "provenance.env")
    static_path = root / "STATIC_MUTABLE_STATE_AUDIT.json"
    if not static_path.exists():
        raise SystemExit(f"missing required static audit: {static_path}")
    static = json.loads(static_path.read_text(encoding="utf-8"))

    alpha = worker_summary(root, "alpha")
    beta = worker_summary(root, "beta")
    survivor = worker_summary(root, "fault-survivor")

    pids = [as_int(alpha, "pid"), as_int(beta, "pid"), as_int(survivor, "pid")]
    ports = [as_int(alpha, "port"), as_int(beta, "port"), as_int(survivor, "port")]
    ids = [alpha.get("game_id", ""), beta.get("game_id", ""), survivor.get("game_id", "")]

    dependency_runs = {
        "WS01": {
            "head": provenance.get("ws01_head"),
            "run_id": int(provenance["ws01_run_id"]),
            "conclusion": provenance.get("ws01_run_conclusion"),
        },
        "WS05": {
            "head": provenance.get("ws05_head"),
            "run_id": int(provenance["ws05_run_id"]),
            "artifact_id": int(provenance["ws05_artifact_id"]),
            "conclusion": provenance.get("ws05_run_conclusion"),
            "gate": provenance.get("ws05_gate"),
        },
        "WS06": {
            "head": provenance.get("ws06_head"),
            "run_id": int(provenance["ws06_run_id"]),
            "artifact_id": int(provenance["ws06_artifact_id"]),
            "conclusion": provenance.get("ws06_run_conclusion"),
            "gate": provenance.get("ws06_gate"),
        },
    }

    gates = {
        "parallel_4P_games": as_int(result, "parallel_4P_games") >= 2,
        "parallel_worker_pids_distinct": as_bool(result, "parallel_worker_pids_distinct")
            and len(set(pids[:2])) == 2 and min(pids[:2]) > 0,
        "parallel_worker_lifetimes_overlap": as_bool(result, "parallel_worker_lifetimes_overlap"),
        "cross_game_state_leaks": as_int(result, "cross_game_state_leaks", 10**9) == 0,
        "cross_game_rng_leaks": as_int(result, "cross_game_rng_leaks", 10**9) == 0,
        "cross_game_decision_queue_leaks": as_int(result, "cross_game_decision_queue_leaks", 10**9) == 0,
        "cross_game_request_id_collisions": as_int(result, "cross_game_request_id_collisions", 10**9) == 0,
        "cross_game_observation_leaks": as_int(result, "cross_game_observation_leaks", 10**9) == 0,
        "cross_game_controller_state_leaks": as_int(result, "cross_game_controller_state_leaks", 10**9) == 0,
        "distinct_state_identity": as_bool(result, "distinct_state_identity"),
        "distinct_rng_identity": as_bool(result, "distinct_rng_identity"),
        "distinct_decision_identity": as_bool(result, "distinct_decision_identity"),
        "worker_failure_injected_after_game_constructed": as_bool(result, "victim_reached_GAME_CONSTRUCTED")
            and as_int(result, "victim_exit", 0) != 0,
        "single_worker_failure_corrupts_other_game": not as_bool(result, "single_worker_failure_corrupts_other_game"),
        "survivor_state_matches_clean_baseline": as_bool(result, "survivor_state_matches_clean_baseline"),
        "survivor_rng_matches_clean_baseline": as_bool(result, "survivor_rng_matches_clean_baseline"),
        "survivor_decisions_match_clean_baseline": as_bool(result, "survivor_decisions_match_clean_baseline"),
        "parent_failure_count_zero": as_int(result, "failure_count", 10**9) == 0,
        "process_per_game_static_isolation": static.get("status") == "PASS"
            and static.get("architecture") == "PROCESS_PER_GAME"
            and static.get("cross_game_shared_jvm_heap") is False
            and static.get("unisolated_cross_game_mutable_singletons") == 0,
        "worker_process_resources_distinct": len(set(ports[:2])) == 2 and min(ports[:2]) > 0,
        "game_identities_distinct_for_parallel_pair": len(set(ids[:2])) == 2 and all(ids[:2]),
        "ws01_dependency_qualified": dependency_runs["WS01"]["conclusion"] == "success",
        "ws05_dependency_qualified": dependency_runs["WS05"]["conclusion"] == "success"
            and dependency_runs["WS05"]["gate"] == "PASS",
        "ws06_dependency_qualified": dependency_runs["WS06"]["conclusion"] == "success"
            and dependency_runs["WS06"]["gate"] == "PASS",
    }

    passed = all(gates.values())
    failed = sorted(name for name, ok in gates.items() if not ok)
    doc = {
        "schema": "commander-simulator-next.process-isolation-gate.v1",
        "workstream": "WS08",
        "status": "PASS" if passed else "FAIL",
        "Q4_PROCESS_ISOLATION": "PASS" if passed else "FAIL",
        "architecture": "PROCESS_PER_GAME",
        "source_head": provenance.get("source_head"),
        "source_tree": provenance.get("source_tree"),
        "audit_base_sha": provenance.get("audit_base_sha"),
        "forge_pin": provenance.get("forge_pin"),
        "dependencies": dependency_runs,
        "parallel_4P_games": as_int(result, "parallel_4P_games"),
        "cross_game_state_leaks": as_int(result, "cross_game_state_leaks"),
        "cross_game_rng_leaks": as_int(result, "cross_game_rng_leaks"),
        "cross_game_decision_queue_leaks": as_int(result, "cross_game_decision_queue_leaks"),
        "cross_game_request_id_collisions": as_int(result, "cross_game_request_id_collisions"),
        "raw_local_decision_id_overlaps": as_int(result, "raw_local_decision_id_overlaps"),
        "request_id_scope": result.get("request_id_scope"),
        "cross_game_observation_leaks": as_int(result, "cross_game_observation_leaks"),
        "cross_game_controller_state_leaks": as_int(result, "cross_game_controller_state_leaks"),
        "single_worker_failure_corrupts_other_game": as_bool(result, "single_worker_failure_corrupts_other_game"),
        "static_mutable_state_audit": {
            "status": static.get("status"),
            "shared_decision_relevant_mutable_singletons_within_worker": static.get(
                "shared_decision_relevant_mutable_singletons_within_worker"
            ),
            "unisolated_cross_game_mutable_singletons": static.get("unisolated_cross_game_mutable_singletons"),
        },
        "gates": gates,
        "evidence_class": [
            "DIRECTLY_VERIFIED",
            "CODE_DERIVED",
            "TECHNICALLY_CONFORMANT",
            "CI_EXECUTED",
        ],
        "failure": None if passed else {
            "code": "Q4_PROCESS_ISOLATION_FAILED",
            "failed_gates": failed,
            "parent_failures": result.get("failures", ""),
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# WS08 process isolation gate",
        "",
        f"- Q4_PROCESS_ISOLATION: **{doc['Q4_PROCESS_ISOLATION']}**",
        f"- architecture: **{doc['architecture']}**",
        f"- parallel_4P_games: **{doc['parallel_4P_games']}**",
        f"- cross_game_state_leaks: **{doc['cross_game_state_leaks']}**",
        f"- cross_game_rng_leaks: **{doc['cross_game_rng_leaks']}**",
        f"- cross_game_decision_queue_leaks: **{doc['cross_game_decision_queue_leaks']}**",
        f"- cross_game_request_id_collisions: **{doc['cross_game_request_id_collisions']}**",
        f"- cross_game_observation_leaks: **{doc['cross_game_observation_leaks']}**",
        f"- cross_game_controller_state_leaks: **{doc['cross_game_controller_state_leaks']}**",
        "- single_worker_failure_corrupts_other_game: "
        f"**{str(doc['single_worker_failure_corrupts_other_game']).lower()}**",
        f"- failed_gates: **{', '.join(failed) if failed else 'none'}**",
    ]
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"WS08_Q4_PROCESS_ISOLATION={doc['Q4_PROCESS_ISOLATION']}")
    print(f"WS08_FAILED_GATES={','.join(failed)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
