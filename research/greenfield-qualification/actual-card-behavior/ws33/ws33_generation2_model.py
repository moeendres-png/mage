#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
SVAR_DOMAIN = "SVAR_RUNTIME_EXPRESSION"
LEGACY_ERRATA = {
    "forge-behavior-v2:452495ff67d15f9989748411f5ec41067e039c7b",
    "forge-behavior-v2:6dfbc7e6fb17a15e4445462f4383e6ebcf7ffedf",
    "forge-behavior-v2:7caaed2bb9b0c5fe0f5dab44de04175ec1867a16",
    "forge-behavior-v2:beee69a372f7b75417aa7fd9552cdfe6fae1a519",
}


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def load(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    # Generation-1 ABI gate fixtures were serialized relative to the enclosing
    # artifact directory ("ws33/...").  A consumer operating with that ws33
    # directory as its root must resolve the same reference as "..." rather
    # than append the artifact root a second time.  Normalize only this
    # serialized artifact-root convention; all filesystem safety checks remain
    # in the caller.
    if path.name == "WS33_WITNESS_ABI_GATE.json" and isinstance(value, dict):
        for result in value.get("results", []):
            fixture = result.get("fixture")
            if isinstance(fixture, str) and fixture.startswith("ws33/"):
                result["fixture"] = fixture[len("ws33/"):]
    return value


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_GENERATION2_MODEL=FAIL " + message)


def materialize(raw_manifest: dict, consumer_model: dict, source_head: str, source_tree: str, consumer_sha256: str) -> dict:
    raw_paths = raw_manifest["paths"]
    raw_by_id = {row["v2_path_id"]: row for row in raw_paths}
    require(len(raw_paths) == len(raw_by_id), "duplicate WS26 raw IDs")

    raw_svar_ids = {row["v2_path_id"] for row in raw_paths if row.get("dispatch_domain") == SVAR_DOMAIN}
    require(len(raw_svar_ids) == consumer_model.get("raw_svar_path_count"), "consumer/raw SVar count mismatch")
    require(consumer_model.get("forge_pin") == PIN, "consumer Forge pin mismatch")
    require(consumer_model.get("resolved_old_path_count") == len(raw_svar_ids), "not all old SVar paths adjudicated")
    require(consumer_model.get("unresolved_old_path_count") == 0, "unresolved old SVar path")
    require(consumer_model.get("unresolved_occurrence_count") == 0, "unresolved SVar occurrence")

    old_to_new = {key: list(value) for key, value in consumer_model.get("old_to_new", {}).items()}
    non_rules = {row["old_effective_v2_path_id"] for row in consumer_model.get("non_rules_metadata", [])}
    resolved = set(old_to_new) | non_rules
    require(resolved == raw_svar_ids, "consumer adjudication does not exactly cover raw SVar frontier")
    require(set(old_to_new).isdisjoint(non_rules), "production/non-rules overlap")

    new_paths = [dict(row) for row in consumer_model.get("new_paths", [])]
    new_by_id = {row["v2_path_id"]: row for row in new_paths}
    require(len(new_paths) == len(new_by_id) == consumer_model.get("new_consumer_path_count"), "new consumer ID collision")
    require(not (set(new_by_id) & set(raw_by_id)), "new consumer ID collides with historical WS26 ID")
    require(not (LEGACY_ERRATA & set(new_by_id)), "legacy WS29 alias reused as generation2 ID")

    for old_id, mapped in old_to_new.items():
        require(old_id in raw_svar_ids, "consumer migration source is not raw SVar")
        require(bool(mapped), "production-reachable SVar has no generation2 target")
        require(set(mapped) <= set(new_by_id), "consumer migration points outside new path set")
    for row in new_paths:
        historical = set(row.get("historical_ws26_v2_path_ids", []))
        require(bool(historical), "new path lacks historical provenance")
        require(historical <= raw_svar_ids, "new path historical provenance outside raw SVar frontier")
        require(row.get("dispatch_domain") == SVAR_DOMAIN, "new path dispatch domain mismatch")

    unchanged = [dict(row) for row in raw_paths if row["v2_path_id"] not in raw_svar_ids]
    effective_paths = sorted(unchanged + new_paths, key=lambda row: row["v2_path_id"])
    effective_ids = [row["v2_path_id"] for row in effective_paths]
    expected_count = len(raw_paths) - len(raw_svar_ids) + len(new_paths)
    require(len(effective_paths) == expected_count, "derived generation2 path count mismatch")
    require(len(effective_ids) == len(set(effective_ids)), "duplicate generation2 effective ID")
    require(not (raw_svar_ids & set(effective_ids)), "historical SVar ID remains production-required")
    require(not (LEGACY_ERRATA & set(effective_ids)), "legacy WS29 alias remains effective")

    manifest = dict(raw_manifest)
    manifest.update({
        "schema": "commander-simulator-next.behavior-path-manifest.v2.2",
        "model": "WS33_EFFECTIVE_CONSUMER_AWARE_GENERATION_2",
        "ws33_parallel_base_generation": 2,
        "source_head": source_head,
        "source_tree": source_tree,
        "raw_ws26_path_count": len(raw_paths),
        "raw_ws26_svar_path_count": len(raw_svar_ids),
        "consumer_aware_svar_path_count": len(new_paths),
        "non_rules_metadata_old_path_count": len(non_rules),
        "path_count": len(effective_paths),
        "consumer_model_sha256": consumer_sha256,
        "historical_svar_ids_removed_from_effective_model": sorted(raw_svar_ids),
        "legacy_ws29_alias_ids_retained_as_provenance_only": sorted(LEGACY_ERRATA),
        "paths": effective_paths,
    })
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-manifest", type=Path, required=True)
    parser.add_argument("--consumer-model", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = materialize(
        load(args.raw_manifest),
        load(args.consumer_model),
        args.source_head,
        args.source_tree,
        digest(args.consumer_model),
    )
    write(args.out, manifest)
    print(json.dumps({
        "WS33_GENERATION2_MODEL": "PASS",
        "RAW_PATHS": manifest["raw_ws26_path_count"],
        "RAW_SVAR_PATHS": manifest["raw_ws26_svar_path_count"],
        "GENERATION2_SVAR_PATHS": manifest["consumer_aware_svar_path_count"],
        "EFFECTIVE_PATHS": manifest["path_count"],
        "MODEL_SHA256": digest(args.out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
