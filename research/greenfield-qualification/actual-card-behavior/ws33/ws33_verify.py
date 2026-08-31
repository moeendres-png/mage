#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ALLOWED_STATUS = {"PASS", "FAIL", "UNSUPPORTED", "UNKNOWN"}
LEGACY_ERRATA_IDS = {
    "forge-behavior-v2:452495ff67d15f9989748411f5ec41067e039c7b",
    "forge-behavior-v2:6dfbc7e6fb17a15e4445462f4383e6ebcf7ffedf",
    "forge-behavior-v2:7caaed2bb9b0c5fe0f5dab44de04175ec1867a16",
    "forge-behavior-v2:beee69a372f7b75417aa7fd9552cdfe6fae1a519",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_VERIFY=FAIL " + message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root

    hashes = root / "WS33_HASHES.sha256"
    require(hashes.is_file(), "missing hash manifest")
    hash_rows = hashes.read_text(encoding="utf-8").splitlines()
    require(bool(hash_rows), "empty hash manifest")
    for line in hash_rows:
        expected, relative = line.split("  ", 1)
        path = root / relative
        require(path.is_file(), "missing hashed file " + relative)
        require(digest(path) == expected, "hash mismatch " + relative)

    manifest = load(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    require(manifest.get("ws33_parallel_base_generation") == 2, "not generation2 manifest")
    paths = manifest["paths"]
    path_ids = [item["v2_path_id"] for item in paths]
    path_set = set(path_ids)
    require(manifest["path_count"] == len(paths), "effective path count mismatch")
    require(len(path_ids) == len(path_set), "duplicate effective path IDs")
    historical_svar = set(manifest.get("historical_svar_ids_removed_from_effective_model", []))
    require(bool(historical_svar), "historical SVar removal set missing")
    require(not (historical_svar & path_set), "historical SVar ID remains effective")
    require(not (LEGACY_ERRATA_IDS & path_set), "legacy WS29 alias remains effective")
    require(manifest["raw_ws26_path_count"] - manifest["raw_ws26_svar_path_count"] + manifest["consumer_aware_svar_path_count"] == len(paths), "generation2 count derivation mismatch")

    coverage = load(root / "WS33_PATH_COVERAGE.json")
    require(coverage.get("ws33_parallel_base_generation") == 2, "coverage not generation2")
    coverage_rows = coverage["paths"]
    require(len(coverage_rows) == len(paths), "coverage ledger incomplete")
    require({row["effective_v2_path_id"] for row in coverage_rows} == path_set, "coverage/path mismatch")
    require(len({row["effective_v2_path_id"] for row in coverage_rows}) == len(paths), "duplicate authoritative coverage")
    require(all(row["status"] in ALLOWED_STATUS for row in coverage_rows), "invalid coverage status")
    actual_counts = Counter(row["status"] for row in coverage_rows)
    require({key: actual_counts.get(key, 0) for key in ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")} == coverage["status_counts"], "coverage status count mismatch")
    for row in coverage_rows:
        if row["status"] == "PASS":
            require(row["state_evidence"] is True, "PASS without state evidence")
            require(row["trace_sha"] is not None, "PASS without immutable trace")
            require(bool(row["rules_refs"]), "PASS without rules authority")

    cases = load_jsonl(root / "WS33_CASE_LEDGER.jsonl")
    executions = load_jsonl(root / "WS33_EXECUTION_LEDGER.jsonl")
    require(len(cases) == len(paths) == len(executions), "case/execution ledger incomplete")
    require({row["effective_v2_path_id"] for row in cases} == path_set, "case ledger mismatch")
    require({row["effective_v2_path_id"] for row in executions} == path_set, "execution ledger mismatch")

    owners = load(root / "WS33_EFFECTIVE_OWNER_PARTITIONS.json")
    owner_ids = [path_id for ids in owners["families"].values() for path_id in ids]
    require(len(owner_ids) == len(paths) and set(owner_ids) == path_set, "owner partition coverage")
    require(len(owner_ids) == len(set(owner_ids)), "owner partitions overlap")
    require(sum(owners["family_counts"].values()) == len(paths), "owner family counts")

    targets = load(root / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json")["targets"]
    target_ids = [path_id for row in targets for path_id in row["path_ids"]]
    require(len(target_ids) == len(paths) and set(target_ids) == path_set, "implementation target coverage")
    require(len(target_ids) == len(set(target_ids)), "implementation target overlap")

    templates = load(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")["templates"]
    template_path_ids = [path_id for row in templates for path_id in row["path_ids"]]
    require(len(template_path_ids) == len(paths) and set(template_path_ids) == path_set, "scenario group coverage")
    require(len(template_path_ids) == len(set(template_path_ids)), "path appears in multiple scenario groups")
    for row in templates:
        admitted = set(row["admitted_path_ids"])
        remaining = set(row["remaining_path_ids"])
        require(admitted.isdisjoint(remaining), "scenario admitted/remaining overlap")
        require(admitted | remaining == set(row["path_ids"]), "scenario partition mismatch")
        expected = "FULLY_EXECUTED" if not remaining else ("PARTIALLY_EXECUTED" if admitted else "MISSING_SCENARIO_TEMPLATE")
        require(row["status"] == expected, "scenario group status mismatch")

    identities = load_jsonl(root / "WS33_PER_IDENTITY.jsonl")
    require(len({row["oracle_identity"] for row in identities}) == len(identities), "duplicate Oracle identity")
    status_by_path = {row["effective_v2_path_id"]: row["status"] for row in coverage_rows}
    for identity in identities:
        effective = set(identity["effective_v2_path_ids"])
        require(effective <= path_set, "identity references non-effective path")
        unresolved = sorted(path_id for path_id in effective if status_by_path[path_id] != "PASS")
        require(unresolved == identity["unresolved_path_ids"], "identity unresolved provenance mismatch")
        require(sorted(path_id for path_id in effective if status_by_path[path_id] == "PASS") == identity["pass_path_ids"], "identity PASS provenance mismatch")
        require((identity["status"] == "FULL") == (not unresolved), "invalid FULL reconstruction")

    model = load(root / "WS33_MODEL_GATE.json")
    require(model.get("ws33_parallel_base_generation") == 2, "model gate not generation2")
    require(model["WS33_MODEL_ERRATA_GATE"] == "PASS", "model gate")
    require(model["WS33_CONSUMER_MODEL_GATE"] == "PASS", "consumer model gate")
    require(model["unresolved_production_reachable_model_bindings"] == 0, "unresolved production model binding")
    require(model["effective_path_count"] == len(paths), "model gate effective count")

    abi = load(root / "abi/WS33_WITNESS_ABI_GATE.json")
    require(abi["WS33_WITNESS_ABI_V2_1_GATE"] == "PASS", "ABI gate")
    require(abi["negative_fixture_count"] == 17, "negative fixture count")
    require(abi["negative_fixtures_rejected_for_intended_reason"] is True, "negative fixtures")
    require(all(result["intended_result"] for result in abi["results"]), "ABI result mismatch")

    witnesses = load_jsonl(root / "WS33_WITNESSES.jsonl")
    witness_paths = []
    model_sha = digest(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    for witness in witnesses:
        require(witness["status"] == "PASS", "authoritative non-PASS witness")
        require(witness["effective_model_sha256"] == model_sha, "witness not rebound to generation2 model")
        witness_paths.extend(witness["v2_path_ids"])
    require(len(witness_paths) == len(set(witness_paths)), "multiple witnesses for a PASS path")
    require(set(witness_paths) == {row["effective_v2_path_id"] for row in coverage_rows if row["status"] == "PASS"}, "PASS witness frontier mismatch")

    merge = load(root / "WS33_CAMPAIGN_MERGE_GATE.json")
    require(merge["status"] == "PASS", "campaign merge gate")
    require(merge.get("generation2_model_revalidated") is True, "merge not generation2-revalidated")
    require(merge.get("generation2_effective_model_sha256") == model_sha, "merge model hash mismatch")
    ws32 = load(root / "WS33_WS32_COMPATIBILITY.json")
    require(ws32["status"] == "PASS", "WS32 compatibility")

    repair = load(root / "WS33_PARALLEL_BASE_REPAIR_DIFF.json")
    require(repair["from_generation"] == 1 and repair["to_generation"] == 2, "repair generation boundary")
    require(repair["generation2_effective_path_count"] == len(paths), "repair diff effective count")
    require(repair["generation2_revalidated_pass_count"] == actual_counts.get("PASS", 0), "repair PASS revalidation count")
    require(repair["pass_revalidation_failures"] == 0, "PASS revalidation failure")
    require(not repair["pass_ids_changed_by_model_repair"], "PASS path changed by SVar repair")

    partition = load(root / "WS33_PARALLEL_REST_PARTITION.json")
    invariants = load(root / "WS33_PARALLEL_PARTITION_INVARIANTS.json")
    unknown = {row["effective_v2_path_id"] for row in coverage_rows if row["status"] == "UNKNOWN"}
    shard_lists = [row["effective_v2_path_ids"] for row in partition["shards"].values()]
    shard_ids = [path_id for ids in shard_lists for path_id in ids]
    require(len(shard_ids) == len(set(shard_ids)), "partition overlap")
    require(set(shard_ids) == unknown, "partition union mismatch")
    require(invariants["PARTITION_DISJOINT"] is True, "partition disjoint gate")
    require(invariants["PARTITION_COMPLETE"] is True, "partition complete gate")
    require(invariants["scenario_group_split_count"] == 0, "scenario group split")
    require(not invariants["pass_overlap"], "PASS appears in child partition")
    require(not invariants["legacy_ws29_alias_overlap"], "legacy WS29 alias appears in child partition")

    gate = load(root / "WS33_Q6_CANDIDATE_GATE.json")
    require(gate["effective_path_count"] == len(paths), "Q6 effective count")
    require(gate["path_status_counts"] == {key: actual_counts.get(key, 0) for key in ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")}, "Q6 gate count mismatch")
    template_counts = Counter(row["status"] for row in templates)
    require(gate["scenario_group_counts"] == {key: template_counts.get(key, 0) for key in ("FULLY_EXECUTED", "PARTIALLY_EXECUTED", "MISSING_SCENARIO_TEMPLATE")}, "Q6 scenario counts")
    require(gate["incomplete_scenario_group_count"] == sum(count for key, count in template_counts.items() if key != "FULLY_EXECUTED"), "Q6 incomplete group count")
    if gate["Q6_CANDIDATE_FOR_CROSS_QUALIFICATION"]:
        require(actual_counts == Counter({"PASS": len(paths)}), "candidate promoted with open path frontier")
        require(gate["WS32_COMPATIBILITY"] == "PASS", "candidate promoted without WS32")

    base_gate = load(root / "WS33_GENERATION2_BASE_GATE.json")
    require(base_gate["PARALLEL_CHILDREN_ELIGIBLE"] is True, "generation2 base gate")
    require(base_gate["PARTITION_DISJOINT"] is True and base_gate["PARTITION_COMPLETE"] is True, "generation2 partition gate")
    require(base_gate["ABI_V2_1"] == "PASS" and base_gate["ABI_NEGATIVE_COUNT"] == 17, "generation2 ABI summary")
    require(base_gate["WS32_COMPATIBILITY"] == "PASS", "generation2 WS32 summary")
    require(base_gate["TARGET_RESTRICTIONS_RECORD_REPLAY"] == "PASS", "generation2 target record/replay")
    require(base_gate["CAMPAIGN_MERGE"] == "PASS" and base_gate["SEMANTIC_REPLAY"] == "PASS", "generation2 merge/replay")
    require(base_gate["GLOBAL_Q6_PASS"] is False, "generation2 base must not assert global Q6")
    require(base_gate["WS34_ELIGIBLE"] is False, "generation2 base must not assert WS34")
    require(base_gate["ARCHITECTURE_FREEZE_ELIGIBLE"] is False, "generation2 base must not assert architecture freeze")

    print("WS33_VERIFY=PASS")


if __name__ == "__main__":
    main()
