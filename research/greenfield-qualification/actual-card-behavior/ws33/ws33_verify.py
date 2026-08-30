#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ALLOWED_STATUS = {"PASS", "FAIL", "UNSUPPORTED", "UNKNOWN"}
ERRATA_IDS = {
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
    for line in hashes.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = root / relative
        require(path.is_file(), "missing hashed file " + relative)
        require(digest(path) == expected, "hash mismatch " + relative)

    manifest = load(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    paths = manifest["paths"]
    path_ids = [item["v2_path_id"] for item in paths]
    require(manifest["raw_ws26_path_count"] == 4280, "raw path count")
    require(manifest["path_count"] == 4276 == len(paths), "effective path count")
    require(len(path_ids) == len(set(path_ids)), "duplicate effective path IDs")
    require(not (ERRATA_IDS & set(path_ids)), "deprecated aliases remain production-required")

    coverage = load(root / "WS33_PATH_COVERAGE.json")
    coverage_rows = coverage["paths"]
    require(len(coverage_rows) == 4276, "coverage ledger incomplete")
    require({row["effective_v2_path_id"] for row in coverage_rows} == set(path_ids), "coverage/path mismatch")
    require(all(row["status"] in ALLOWED_STATUS for row in coverage_rows), "invalid coverage status")
    require(len({row["effective_v2_path_id"] for row in coverage_rows}) == 4276, "duplicate authoritative coverage")
    actual_counts = Counter(row["status"] for row in coverage_rows)
    require(dict(actual_counts) == coverage["status_counts"], "coverage status count mismatch")
    for row in coverage_rows:
        if row["status"] == "PASS":
            require(row["state_evidence"] is True, "PASS without state evidence")
            require(row["trace_sha"] is not None, "PASS without immutable trace")
            require(bool(row["rules_refs"]), "PASS without rules authority")

    cases = load_jsonl(root / "WS33_CASE_LEDGER.jsonl")
    executions = load_jsonl(root / "WS33_EXECUTION_LEDGER.jsonl")
    require(len(cases) == 4276 == len(executions), "case/execution ledger incomplete")
    require({row["effective_v2_path_id"] for row in cases} == set(path_ids), "case ledger mismatch")
    require({row["effective_v2_path_id"] for row in executions} == set(path_ids), "execution ledger mismatch")

    templates = load(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")["templates"]
    require(len(templates) == 249, "scenario group count")
    template_path_ids = [path_id for row in templates for path_id in row["path_ids"]]
    require(len(template_path_ids) == 4276 and set(template_path_ids) == set(path_ids), "scenario group coverage")
    require(len(template_path_ids) == len(set(template_path_ids)), "path appears in multiple scenario groups")
    for row in templates:
        admitted = set(row["admitted_path_ids"])
        remaining = set(row["remaining_path_ids"])
        require(admitted.isdisjoint(remaining), "scenario group admitted/remaining overlap")
        require(admitted | remaining == set(row["path_ids"]), "scenario group partition mismatch")
        expected = "FULLY_EXECUTED" if not remaining else ("PARTIALLY_EXECUTED" if admitted else "MISSING_SCENARIO_TEMPLATE")
        require(row["status"] == expected, "scenario group status mismatch")

    identities = load_jsonl(root / "WS33_PER_IDENTITY.jsonl")
    require(len(identities) == 1678, "identity reconstruction count")
    status_by_path = {row["effective_v2_path_id"]: row["status"] for row in coverage_rows}
    for identity in identities:
        unresolved = sorted(path_id for path_id in identity["effective_v2_path_ids"] if status_by_path[path_id] != "PASS")
        require(unresolved == identity["unresolved_path_ids"], "identity unresolved provenance mismatch")
        require((identity["status"] == "FULL") == (not unresolved), "invalid FULL reconstruction")

    abi = load(root / "abi/WS33_WITNESS_ABI_GATE.json")
    model = load(root / "WS33_MODEL_GATE.json")
    require(abi["WS33_WITNESS_ABI_V2_1_GATE"] == "PASS", "ABI gate")
    require(abi["negative_fixtures_rejected_for_intended_reason"] is True, "negative fixtures")
    require(model["WS33_MODEL_ERRATA_GATE"] == "PASS", "model gate")
    gate = load(root / "WS33_Q6_CANDIDATE_GATE.json")
    require(gate["path_status_counts"] == {key: actual_counts.get(key, 0) for key in ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")}, "Q6 gate count mismatch")
    template_counts = Counter(row["status"] for row in templates)
    require(gate["scenario_group_counts"] == {key: template_counts.get(key, 0) for key in ("FULLY_EXECUTED", "PARTIALLY_EXECUTED", "MISSING_SCENARIO_TEMPLATE")}, "Q6 scenario group count mismatch")
    require(gate["incomplete_scenario_group_count"] == sum(count for key, count in template_counts.items() if key != "FULLY_EXECUTED"), "Q6 incomplete group count mismatch")
    if gate["Q6_CANDIDATE_FOR_CROSS_QUALIFICATION"]:
        require(actual_counts == Counter({"PASS": 4276}), "candidate promoted with open path frontier")
        require(gate["WS32_COMPATIBILITY"] == "PASS", "candidate promoted without WS32 compatibility")
    print("WS33_VERIFY=PASS")


if __name__ == "__main__":
    main()
