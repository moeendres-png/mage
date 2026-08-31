#!/usr/bin/env python3
"""Build the authoritative WS33 integrated path ledger and repair queue."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SHARDS = ("WS33A", "WS33B", "WS33C", "WS33D", "WS33E", "WS33F", "WS33G", "WS33H")
REQUIRED_DIMENSIONS = {
    "required_decision_evidence": "DECISION",
    "required_rng_evidence": "RNG",
    "required_hidden_info_evidence": "HIDDEN_INFO",
    "required_replay_evidence": "SEMANTIC_REPLAY",
}


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_INTEGRATED_FRONTIER=FAIL " + message)


def shard_for(path: dict[str, Any]) -> str:
    owner = path["owner_family"]
    target = path["implementation_target"]
    if owner == "ACTION_COST_DECISION":
        if target == "forge.game.spellability.TargetRestrictions":
            return "WS33A"
        if target in {"forge.game.cost.Cost", "forge.game.ability.AbilityUtils#calculateAmount"}:
            return "WS33B"
        if target in {
            "forge.game.spellability.AbilitySub",
            "forge.game.spellability.SpellApiBased",
            "forge.game.spellability.AbilityApiBased",
        }:
            return "WS33C"
        return "WS33D"
    owners = {
        "TRIGGER_REPLACEMENT_ZONE_SBA": "WS33E",
        "CONTINUOUS_COPY_CONTROL": "WS33F",
        "HIDDEN_RNG_REPLAY": "WS33G",
        "COMBAT_COMMANDER": "WS33H",
    }
    require(owner in owners, f"unassigned owner family {owner}")
    return owners[owner]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--repair-commit", required=True)
    parser.add_argument("--generation2-run-id", required=True)
    parser.add_argument("--generation2-job-id", required=True)
    parser.add_argument("--generation2-artifact-id", required=True)
    parser.add_argument("--generation2-artifact-digest", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output_root = (args.output_root or root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    manifest_path = root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"
    coverage_path = root / "WS33_PATH_COVERAGE.json"
    scenarios_path = root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json"
    errata_path = root / "WS33_MODEL_ERRATA.json"
    witnesses_path = root / "WS33_WITNESSES.jsonl"
    execution_path = root / "WS33_EXECUTION_LEDGER.jsonl"
    generation2_gate_path = root / "WS33_GENERATION2_BASE_GATE.json"

    manifest = load(manifest_path)
    coverage = load(coverage_path)
    scenarios = load(scenarios_path)
    errata = load(errata_path)
    witnesses = load_jsonl(witnesses_path)
    execution = load_jsonl(execution_path)
    generation2_gate = load(generation2_gate_path)
    require(generation2_gate["PARALLEL_CHILDREN_ELIGIBLE"] is True, "input is not an eligible Generation2 base")
    require(generation2_gate["source_head"] == args.repair_commit, "repair commit does not match Generation2 gate")
    require(args.generation2_artifact_digest.startswith("sha256:"), "artifact digest is not SHA-256 qualified")

    paths = manifest["paths"]
    path_by_id = {row["v2_path_id"]: row for row in paths}
    require(len(path_by_id) == len(paths), "duplicate effective path id")
    coverage_by_id = {row["effective_v2_path_id"]: row for row in coverage["paths"]}
    require(set(coverage_by_id) == set(path_by_id), "coverage and effective manifest differ")

    scenario_by_path: dict[str, dict[str, Any]] = {}
    scenario_shards: dict[str, set[str]] = defaultdict(set)
    for scenario in scenarios["templates"]:
        for path_id in scenario["path_ids"]:
            require(path_id in path_by_id, f"scenario contains inactive path {path_id}")
            require(path_id not in scenario_by_path, f"path occurs in multiple scenario groups {path_id}")
            scenario_by_path[path_id] = scenario
            scenario_shards[scenario["template_id"]].add(shard_for(path_by_id[path_id]))
    require(set(scenario_by_path) == set(path_by_id), "scenario registry does not cover effective manifest")

    witness_by_path: dict[str, dict[str, Any]] = {}
    for witness in witnesses:
        for path_id in witness["v2_path_ids"]:
            require(path_id not in witness_by_path, f"multiple witnesses for {path_id}")
            witness_by_path[path_id] = witness
    execution_by_path = {row["effective_v2_path_id"]: row for row in execution}

    if "legacy_ws29_alias_ids" in errata:
        deprecated_aliases = set(errata["legacy_ws29_alias_ids"])
    else:
        deprecated_aliases = {
            row["historical_v2_path_id"]
            for row in errata["errata"]
            if row["disposition"] == "DEPRECATED_MODEL_INVALID_ALIAS"
        }
    alias_overlap = sorted(deprecated_aliases & set(path_by_id))

    rows: list[dict[str, Any]] = []
    shard_sets: dict[str, set[str]] = {name: set() for name in SHARDS}
    for path_id in sorted(path_by_id):
        path = path_by_id[path_id]
        current = coverage_by_id[path_id]
        scenario = scenario_by_path[path_id]
        witness = witness_by_path.get(path_id)
        executed = execution_by_path.get(path_id, {})
        shard = shard_for(path)
        shard_sets[shard].add(path_id)
        required = ["STATE"]
        required.extend(
            title for field, title in REQUIRED_DIMENSIONS.items() if path.get(field) is True
        )
        rows.append({
            "effective_path_id": path_id,
            "source_provenance": path["source_provenance"],
            "representative_actual_oracle_identities": path.get("representative_actual_oracle_identities", []),
            "owner_family": path["owner_family"],
            "logical_bucket": shard,
            "implementation_target": path["implementation_target"],
            "runtime_subsystem": path["implementation_target"],
            "scenario_group_id": scenario["template_id"],
            "scenario_group_status": scenario["status"],
            "evidence_profile": scenario["evidence_profile"],
            "current_status": current["status"],
            "evidence_classification": current["evidence_classification"],
            "required_evidence_dimensions": required,
            "witness_id": witness.get("witness_id") if witness else None,
            "campaign_id": current.get("execution_source") or executed.get("execution_source"),
            "trace_sha256": current.get("trace_sha") or (witness.get("trace_sha256") if witness else None),
            "semantic_replay_evidence_ref": current.get("replay_evidence") or (witness.get("semantic_replay_evidence_ref") if witness else None),
            "decision_tape_ref": current.get("decision_tape") or (witness.get("decision_tape_ref") if witness else None),
            "rng_tape_ref": current.get("rng_tape") or (witness.get("rng_tape_ref") if witness else None),
            "observation_evidence_ref": current.get("observation_evidence") or (witness.get("observation_evidence_ref") if witness else None),
            "repair_commit": args.repair_commit,
            "blocker_classification": None if current["status"] == "PASS" else executed.get("blocker_class", "MISSING_SCENARIO_TEMPLATE"),
        })

    all_ids = set(path_by_id)
    pass_ids = {path_id for path_id, row in coverage_by_id.items() if row["status"] == "PASS"}
    unresolved_ids = all_ids - pass_ids
    partition_union = set().union(*shard_sets.values())
    pairwise_overlap = set()
    for index, left in enumerate(SHARDS):
        for right in SHARDS[index + 1:]:
            pairwise_overlap.update(shard_sets[left] & shard_sets[right])
    split_groups = sorted(group for group, shards in scenario_shards.items() if len(shards) > 1)

    queue_groups: dict[tuple[str, str, str, str, str], list[str]] = defaultdict(list)
    for row in rows:
        if row["current_status"] != "PASS":
            key = (
                row["logical_bucket"], row["owner_family"], row["runtime_subsystem"],
                row["scenario_group_id"], row["evidence_profile"],
            )
            queue_groups[key].append(row["effective_path_id"])
    queue = []
    for key, ids in queue_groups.items():
        bucket, owner, subsystem, scenario_id, profile = key
        queue.append({
            "logical_bucket": bucket,
            "owner_family": owner,
            "runtime_subsystem": subsystem,
            "scenario_group_id": scenario_id,
            "evidence_profile": profile,
            "unresolved_path_count": len(ids),
            "effective_path_ids": sorted(ids),
            "priority_basis": "DESCENDING_UNRESOLVED_PATH_COUNT_THEN_STABLE_KEYS",
        })
    queue.sort(key=lambda row: (-row["unresolved_path_count"], row["logical_bucket"], row["runtime_subsystem"], row["scenario_group_id"]))

    status_counts = Counter(row["current_status"] for row in rows)
    ledger_path = output_root / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"
    queue_path = output_root / "WS33_INTEGRATED_WORK_QUEUE.json"
    gate_path = output_root / "WS33_INTEGRATED_FRONTIER_GATE.json"
    write_jsonl(ledger_path, rows)
    write(queue_path, {
        "schema": "commander-simulator-next.ws33-integrated-work-queue.v1",
        "basis": "effective_path_id",
        "unresolved_path_count": len(unresolved_ids),
        "work_item_count": len(queue),
        "items": queue,
    })

    disjoint = not pairwise_overlap
    complete = partition_union == all_ids
    no_group_split = not split_groups
    no_pass_overlap = not (pass_ids & unresolved_ids)
    no_deprecated_alias = not alias_overlap
    gate_status = "PASS" if all((disjoint, complete, no_group_split, no_pass_overlap, no_deprecated_alias)) else "FAIL"
    gate = {
        "schema": "commander-simulator-next.ws33-integrated-frontier-gate.v1",
        "basis": "effective_path_id",
        "generation2_base_head": generation2_gate["source_head"],
        "generation2_base_tree": generation2_gate["source_tree"],
        "generation2_workflow_run_id": args.generation2_run_id,
        "generation2_workflow_job_id": args.generation2_job_id,
        "generation2_artifact_id": args.generation2_artifact_id,
        "generation2_artifact_digest": args.generation2_artifact_digest,
        "generation2_artifact_gate_sha256": digest(generation2_gate_path),
        "model_source_head": manifest["source_head"],
        "model_source_tree": manifest["source_tree"],
        "effective_path_count": len(all_ids),
        "path_status_counts": {key: status_counts.get(key, 0) for key in ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")},
        "unresolved_path_count": len(unresolved_ids),
        "work_item_count": len(queue),
        "PARTITION_DISJOINT": disjoint,
        "PARTITION_COMPLETE": complete,
        "NO_GROUP_SPLIT": no_group_split,
        "NO_PASS_OVERLAP": no_pass_overlap,
        "NO_DEPRECATED_ALIAS_AS_ACTIVE_PATH": no_deprecated_alias,
        "pairwise_overlap_ids": sorted(pairwise_overlap),
        "missing_partition_ids": sorted(all_ids - partition_union),
        "extra_partition_ids": sorted(partition_union - all_ids),
        "split_scenario_group_ids": split_groups,
        "pass_overlap_ids": sorted(pass_ids & unresolved_ids),
        "deprecated_alias_overlap_ids": alias_overlap,
        "ledger_sha256": digest(ledger_path),
        "queue_sha256": digest(queue_path),
        "status": gate_status,
        "GLOBAL_Q6_PASS": status_counts.get("PASS", 0) == len(all_ids),
        "WS34_ELIGIBLE": False,
        "ARCHITECTURE_FREEZE_ELIGIBLE": False,
    }
    if gate["GLOBAL_Q6_PASS"]:
        gate["WS34_ELIGIBLE"] = True
        gate["ARCHITECTURE_FREEZE_ELIGIBLE"] = True
    write(gate_path, gate)
    require(gate_status == "PASS", "integrated frontier invariants")
    print(f"WS33_INTEGRATED_FRONTIER=PASS paths={len(all_ids)} unresolved={len(unresolved_ids)} work_items={len(queue)}")


if __name__ == "__main__":
    main()
