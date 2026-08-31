#!/usr/bin/env python3
"""Bind one immutable WS33 coverage successor as the sole operational frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any


SHARDS = ("WS33A", "WS33B", "WS33C", "WS33D", "WS33E", "WS33F", "WS33G", "WS33H")
STATUS_KEYS = ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_CURRENT_OPERATIONAL_STATE=FAIL " + message)


def verify_internal_hashes(root: Path) -> tuple[int, str]:
    manifest = root / "WS33_HASHES.sha256"
    require(manifest.is_file(), "missing internal hash manifest")
    entries = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, separator, relative = line.partition("  ")
        require(separator == "  " and len(expected) == 64 and bool(relative), "malformed internal hash row")
        target = (root / relative).resolve()
        require(root == target or root in target.parents, "internal hash path escapes artifact root")
        require(target.is_file(), "missing internally hashed file " + relative)
        require(digest(target) == expected, "internal hash mismatch " + relative)
        entries += 1
    require(entries > 0, "empty internal hash manifest")
    return entries, digest(manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--artifact-digest", required=True)
    args = parser.parse_args()

    artifact_root = args.artifact_root.resolve()
    ws33 = artifact_root / "ws33"
    integrated = artifact_root / "integrated"
    require(ws33.is_dir() and integrated.is_dir(), "successor artifact layout is incomplete")
    require(len(args.source_head) == 40 and len(args.source_tree) == 40, "invalid source tuple")
    require(args.artifact_digest.startswith("sha256:") and len(args.artifact_digest) == 71, "invalid artifact digest")

    internal_count, internal_manifest_sha = verify_internal_hashes(ws33)
    coverage = load(ws33 / "WS33_PATH_COVERAGE.json")
    q6 = load(ws33 / "WS33_Q6_CANDIDATE_GATE.json")
    partition = load(ws33 / "WS33_PARALLEL_REST_PARTITION.json")
    frontier = load(integrated / "WS33_INTEGRATED_FRONTIER_GATE.json")
    ledger_path = integrated / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"
    queue_path = integrated / "WS33_INTEGRATED_WORK_QUEUE.json"
    ledger = load_jsonl(ledger_path)

    status_counts = Counter(row["status"] for row in coverage["paths"])
    normalized_counts = {key: status_counts.get(key, 0) for key in STATUS_KEYS}
    require(sum(normalized_counts.values()) == len(coverage["paths"]), "unknown coverage status")
    require(q6["effective_path_count"] == len(coverage["paths"]), "Q6 effective count differs from coverage")
    require(q6["path_status_counts"] == normalized_counts, "Q6 status counts differ from coverage")
    require(frontier["effective_path_count"] == len(coverage["paths"]), "frontier effective count differs from coverage")
    require(frontier["path_status_counts"] == normalized_counts, "frontier status counts differ from coverage")
    require(frontier["ledger_sha256"] == digest(ledger_path), "frontier ledger digest mismatch")
    require(frontier["queue_sha256"] == digest(queue_path), "frontier queue digest mismatch")
    require(len(ledger) == len(coverage["paths"]), "integrated ledger does not cover every path")

    ledger_status = Counter(row["current_status"] for row in ledger)
    require({key: ledger_status.get(key, 0) for key in STATUS_KEYS} == normalized_counts, "ledger status counts differ from coverage")
    unknown_by_shard = Counter(row["logical_bucket"] for row in ledger if row["current_status"] == "UNKNOWN")
    require(set(unknown_by_shard) <= set(SHARDS), "ledger contains an unknown shard")
    shard_counts = {name: unknown_by_shard.get(name, 0) for name in SHARDS}
    require(sum(shard_counts.values()) == normalized_counts["UNKNOWN"], "A-H unknown union differs from coverage")

    partition_ids = {
        path_id
        for shard in partition["shards"].values()
        for path_id in shard["effective_v2_path_ids"]
    }
    coverage_ids = {row["effective_v2_path_id"] for row in coverage["paths"]}
    unresolved_ids = {
        row["effective_v2_path_id"] for row in coverage["paths"] if row["status"] != "PASS"
    }
    require(unresolved_ids <= partition_ids, "historical A-H assignment omits a current unresolved path")
    require(partition_ids <= coverage_ids, "historical A-H assignment contains an inactive path")
    partition_pass_overlap = partition_ids - unresolved_ids

    output_root = args.out.resolve().parent
    output_root.mkdir(parents=True, exist_ok=True)
    for filename in (
        "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl",
        "WS33_INTEGRATED_FRONTIER_GATE.json",
        "WS33_INTEGRATED_WORK_QUEUE.json",
    ):
        shutil.copy2(integrated / filename, output_root / filename)

    descriptor = {
        "schema": "commander-simulator-next.ws33-current-operational-state.v1",
        "classification": "DIRECTLY_VERIFIED_IMMUTABLE_SUCCESSOR",
        "canonical_chain_policy": "ONE_PREDECESSOR_ONE_SERIAL_CAMPAIGN_ONE_SUCCESSOR",
        "predecessor": {
            "source_head": args.source_head,
            "source_tree": args.source_tree,
            "workflow_run_id": args.run_id,
            "workflow_job_id": args.job_id,
            "artifact_id": args.artifact_id,
            "artifact_digest": args.artifact_digest,
            "internal_hash_manifest_sha256": internal_manifest_sha,
            "internal_hash_entry_count": internal_count,
        },
        "forge_pin": load(ws33 / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")["forge_pin"],
        "effective_path_count": len(coverage["paths"]),
        "path_status_counts": normalized_counts,
        "unknown_by_shard": shard_counts,
        "historical_partition_assignment_count": len(partition_ids),
        "historical_partition_promoted_pass_overlap_count": len(partition_pass_overlap),
        "scenario_group_counts": q6["scenario_group_counts"],
        "incomplete_scenario_group_count": q6["incomplete_scenario_group_count"],
        "frontier_gate_sha256": digest(integrated / "WS33_INTEGRATED_FRONTIER_GATE.json"),
        "ledger_sha256": digest(ledger_path),
        "work_queue_sha256": digest(queue_path),
        "WORKSTREAM_COMPLETE": q6["WORKSTREAM_COMPLETE"],
        "Q6_CANDIDATE_FOR_CROSS_QUALIFICATION": q6["Q6_CANDIDATE_FOR_CROSS_QUALIFICATION"],
        "WS34_ELIGIBLE": q6["WS34_ELIGIBLE"],
    }
    write(args.out, descriptor)
    print(json.dumps({
        "WS33_CURRENT_OPERATIONAL_STATE": "PASS",
        "effective": descriptor["effective_path_count"],
        **{key.lower(): value for key, value in normalized_counts.items()},
        "internal_hash_entries": internal_count,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
