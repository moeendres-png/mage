#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import jsonschema

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
BASE_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
BASE_TREE = "837f445f78bb26462653c58baf1532e294151b10"
OWNERS = {
    "ACTION_COST_DECISION",
    "TRIGGER_REPLACEMENT_ZONE_SBA",
    "CONTINUOUS_COPY_CONTROL",
    "COMBAT_COMMANDER",
    "HIDDEN_RNG_REPLAY",
}
STATUS_KEYS = ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")
EVIDENCE_SPECS = (
    ("decision", "required_decision_evidence", "decision_tape_ref", "WS33_DECISION_EVIDENCE_INDEX.json"),
    ("rng", "required_rng_evidence", "rng_tape_ref", "WS33_RNG_EVIDENCE_INDEX.json"),
    ("hidden", "required_hidden_info_evidence", "observation_evidence_ref", "WS33_HIDDEN_INFO_EVIDENCE_INDEX.json"),
    ("replay", "required_replay_evidence", "semantic_replay_evidence_ref", "WS33_REPLAY_EVIDENCE_INDEX.json"),
)


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_CAMPAIGN_MERGE=FAIL " + message)


def under(base: Path, relative: str) -> Path:
    require(bool(relative), "empty campaign file reference")
    base = base.resolve()
    path = (base / relative).resolve()
    require(path == base or base in path.parents, "campaign file escapes campaign root: " + relative)
    require(path.is_file(), "missing campaign file: " + relative)
    return path


def safe_id(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "witness"
    return slug[:80] + "-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def copy_evidence(campaign_root: Path, out_root: Path, witness_dir: Path, relative: str | None, name: str) -> str | None:
    if relative is None:
        return None
    source = under(campaign_root, relative)
    suffix = source.suffix if source.suffix else ".json"
    destination = witness_dir / (name + suffix)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return destination.relative_to(out_root).as_posix()


def path_map(root: Path):
    manifest = load(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    return manifest, {item["v2_path_id"]: item for item in manifest["paths"]}


def regenerate_hashes(root: Path) -> None:
    targets = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name != "WS33_HASHES.sha256" and "__pycache__" not in path.parts
    )
    with (root / "WS33_HASHES.sha256").open("w", encoding="utf-8", newline="\n") as handle:
        for path in targets:
            handle.write(f"{digest(path)}  {path.relative_to(root).as_posix()}\n")


def update_evidence_indexes(root: Path, paths_by_id: dict, witnesses: list[dict], coverage_by_id: dict) -> None:
    witness_by_path = {}
    for witness in witnesses:
        if witness.get("status") != "PASS":
            continue
        for path_id in witness.get("v2_path_ids", []):
            require(path_id not in witness_by_path, "multiple authoritative PASS witnesses for " + path_id)
            witness_by_path[path_id] = witness

    for title, requirement, ref_field, filename in EVIDENCE_SPECS:
        required_ids = sorted(path_id for path_id, path in paths_by_id.items() if path.get(requirement))
        entries = []
        for path_id in required_ids:
            if coverage_by_id[path_id]["status"] != "PASS":
                continue
            witness = witness_by_path.get(path_id)
            require(witness is not None, f"PASS {path_id} has no authoritative witness")
            reference = witness.get(ref_field)
            require(reference, f"PASS {path_id} missing required {title} evidence")
            entries.append({
                "effective_v2_path_id": path_id,
                "witness_id": witness["witness_id"],
                "evidence_ref": reference,
                "trace_sha256": witness["trace_sha256"],
            })
        complete = {row["effective_v2_path_id"] for row in entries}
        write_json(root / filename, {
            "schema": f"commander-simulator-next.ws33-{title}-evidence-index.v1",
            "required_path_ids": required_ids,
            "required_count": len(required_ids),
            "complete_pass_count": len(complete),
            "missing_count": len(set(required_ids) - complete),
            "entries": entries,
        })


def recompute(root: Path, paths_by_id: dict, imported_witnesses: list[dict]) -> None:
    coverage_doc = load(root / "WS33_PATH_COVERAGE.json")
    coverage = coverage_doc["paths"]
    coverage_by_id = {row["effective_v2_path_id"]: row for row in coverage}
    cases = load_jsonl(root / "WS33_CASE_LEDGER.jsonl")
    case_by_id = {row["effective_v2_path_id"]: row for row in cases}
    executions = load_jsonl(root / "WS33_EXECUTION_LEDGER.jsonl")
    execution_by_id = {row["effective_v2_path_id"]: row for row in executions}

    for witness in imported_witnesses:
        witness_path = root / "campaign" / safe_id(witness["witness_id"]) / "witness.json"
        for path_id in witness["v2_path_ids"]:
            row = coverage_by_id[path_id]
            require(row["status"] != "PASS", "campaign attempts to replace existing PASS path " + path_id)
            row.update({
                "execution_source": "WS33_RUNTIME_CAMPAIGN",
                "state_evidence": True,
                "decision_tape": witness.get("decision_tape_ref"),
                "rng_tape": witness.get("rng_tape_ref"),
                "observation_evidence": witness.get("observation_evidence_ref"),
                "replay_evidence": witness.get("semantic_replay_evidence_ref"),
                "trace_sha": witness["trace_sha256"],
                "rules_refs": witness["rules_authority_refs"],
                "evidence_classification": witness["evidence_class"],
                "status": "PASS",
            })
            case_by_id[path_id]["scenario_status"] = "WS33_RUNTIME_CAMPAIGN"
            execution_by_id[path_id].update({
                "status": "PASS",
                "execution_source": "WS33_RUNTIME_CAMPAIGN",
                "trace_sha": witness["trace_sha256"],
                "witness_hash": digest(witness_path),
                "blocker_class": None,
            })

    coverage = [coverage_by_id[path_id] for path_id in sorted(coverage_by_id)]
    coverage_doc["paths"] = coverage
    coverage_doc["status_counts"] = dict(Counter(row["status"] for row in coverage))
    write_json(root / "WS33_PATH_COVERAGE.json", coverage_doc)
    write_jsonl(root / "WS33_CASE_LEDGER.jsonl", [case_by_id[path_id] for path_id in sorted(case_by_id)])
    write_jsonl(root / "WS33_EXECUTION_LEDGER.jsonl", [execution_by_id[path_id] for path_id in sorted(execution_by_id)])

    pass_ids = {row["effective_v2_path_id"] for row in coverage if row["status"] == "PASS"}

    templates_doc = load(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")
    for template in templates_doc["templates"]:
        ids = set(template["path_ids"])
        admitted = sorted(ids & pass_ids)
        remaining = sorted(ids - pass_ids)
        template["admitted_path_ids"] = admitted
        template["remaining_path_ids"] = remaining
        template["status"] = "FULLY_EXECUTED" if not remaining else ("PARTIALLY_EXECUTED" if admitted else "MISSING_SCENARIO_TEMPLATE")
    write_json(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json", templates_doc)

    target_doc = load(root / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json")
    for target in target_doc["targets"]:
        unproved = sum(path_id not in pass_ids for path_id in target["path_ids"])
        target["unproved_path_count"] = unproved
        target["priority_score"] = unproved * target["cross_family_dependency_fanout"]
    target_doc["targets"].sort(key=lambda row: (-row["priority_score"], row["owner_family"], row["implementation_target"]))
    write_json(root / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json", target_doc)

    identities = load_jsonl(root / "WS33_PER_IDENTITY.jsonl")
    for identity in identities:
        effective = set(identity["effective_v2_path_ids"])
        identity["pass_path_ids"] = sorted(effective & pass_ids)
        identity["unresolved_path_ids"] = sorted(effective - pass_ids)
        identity["status"] = "FULL" if not identity["unresolved_path_ids"] else "PARTIAL"
    write_jsonl(root / "WS33_PER_IDENTITY.jsonl", identities)

    all_witnesses = load_jsonl(root / "WS33_WITNESSES.jsonl")
    existing_ids = {row["witness_id"] for row in all_witnesses}
    for witness in imported_witnesses:
        require(witness["witness_id"] not in existing_ids, "duplicate witness id " + witness["witness_id"])
        all_witnesses.append(witness)
        existing_ids.add(witness["witness_id"])
    write_jsonl(root / "WS33_WITNESSES.jsonl", all_witnesses)

    update_evidence_indexes(root, paths_by_id, all_witnesses, coverage_by_id)

    rules = load(root / "WS33_RULES_ADJUDICATION.json")
    adjudications = list(rules.get("new_path_semantic_adjudications", []))
    for witness in imported_witnesses:
        adjudications.append({
            "witness_id": witness["witness_id"],
            "v2_path_ids": witness["v2_path_ids"],
            "oracle_identities": witness["oracle_identities"],
            "rules_authority_refs": witness["rules_authority_refs"],
            "evidence_class": witness["evidence_class"],
        })
    rules["new_path_semantic_adjudications"] = adjudications
    write_json(root / "WS33_RULES_ADJUDICATION.json", rules)

    abi_gate = load(root / "abi/WS33_WITNESS_ABI_GATE.json")
    abi_gate["campaign_positive_count"] = abi_gate.get("campaign_positive_count", 0) + len(imported_witnesses)
    abi_gate["campaign_positives_accepted"] = bool(abi_gate.get("campaign_positives_accepted", True))
    for witness in imported_witnesses:
        abi_gate.setdefault("results", []).append({
            "fixture": (Path("campaign") / safe_id(witness["witness_id"]) / "witness.json").as_posix(),
            "expected_exit": 0,
            "expected_error": None,
            "actual_exit": 0,
            "stdout": "WS33_WITNESS_VALIDATION=PASS",
            "intended_result": True,
        })
    write_json(root / "abi/WS33_WITNESS_ABI_GATE.json", abi_gate)

    status_counts = Counter(row["status"] for row in coverage)
    template_counts = Counter(row["status"] for row in templates_doc["templates"])
    identity_counts = Counter(row["status"] for row in identities)
    family_rows = defaultdict(list)
    for row in coverage:
        family_rows[row["owner_family"]].append(row)
    family_gates = {}
    for family, rows in sorted(family_rows.items()):
        counts = Counter(row["status"] for row in rows)
        family_gates[family] = {
            "gate": "PASS" if counts.get("PASS") == len(rows) else "FAIL_CLOSED",
            "counts": dict(counts),
            "effective_path_count": len(rows),
        }

    gate = load(root / "WS33_Q6_CANDIDATE_GATE.json")
    model_pass = load(root / "WS33_MODEL_GATE.json")["WS33_MODEL_ERRATA_GATE"] == "PASS"
    abi_pass = abi_gate["WS33_WITNESS_ABI_V2_1_GATE"] == "PASS" and abi_gate["campaign_positives_accepted"] is True
    ws32_pass = gate.get("WS32_COMPATIBILITY") == "PASS"
    campaign_complete = status_counts == Counter({"PASS": len(paths_by_id)})
    candidate = bool(model_pass and abi_pass and ws32_pass and campaign_complete)
    gate.update({
        "WORKSTREAM_COMPLETE": candidate,
        "WS33_ACTUAL_CARD_CAMPAIGN": "PASS" if campaign_complete else "FAIL_CLOSED",
        "Q6_CANDIDATE_FOR_CROSS_QUALIFICATION": candidate,
        "WS34_ELIGIBLE": candidate,
        "identity_counts": dict(identity_counts),
        "path_status_counts": {key: status_counts.get(key, 0) for key in STATUS_KEYS},
        "family_gates": family_gates,
        "scenario_group_counts": {
            key: template_counts.get(key, 0)
            for key in ("FULLY_EXECUTED", "PARTIALLY_EXECUTED", "MISSING_SCENARIO_TEMPLATE")
        },
        "incomplete_scenario_group_count": sum(
            count for key, count in template_counts.items() if key != "FULLY_EXECUTED"
        ),
    })
    blockers = []
    if status_counts.get("UNKNOWN"):
        blockers.append({
            "class": "MISSING_SCENARIO_TEMPLATE",
            "path_count": status_counts["UNKNOWN"],
            "incomplete_group_count": gate["incomplete_scenario_group_count"],
        })
    if status_counts.get("FAIL"):
        blockers.append({"class": "ACTUAL_CARD_CAMPAIGN_FAILURE", "path_count": status_counts["FAIL"]})
    if status_counts.get("UNSUPPORTED"):
        blockers.append({"class": "UNSUPPORTED_PRODUCTION_PATH", "path_count": status_counts["UNSUPPORTED"]})
    if not ws32_pass:
        blockers.append({"class": "WS32_COMPATIBILITY_NOT_PASS", "path_count": 0})
    gate["remaining_blockers"] = blockers
    write_json(root / "WS33_Q6_CANDIDATE_GATE.json", gate)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--runner-os", default="ubuntu-24.04")
    parser.add_argument("--java-version", default="17")
    parser.add_argument("--process-isolation", default="FRESH_JVM_TARGETED_TEST")
    args = parser.parse_args()

    root = args.root.resolve()
    campaign_root = args.campaign_root.resolve()
    index_path = campaign_root / "campaign-index.json"
    if not index_path.is_file():
        print("WS33_CAMPAIGN_MERGE=NOOP no campaign-index.json")
        return

    index = load(index_path)
    require(index.get("schema") == "commander-simulator-next.ws33-runtime-campaign-index.v1", "wrong campaign index schema")
    records = index.get("records")
    require(isinstance(records, list) and records, "campaign index has no records")

    source_schema = Path(__file__).resolve().parent / "campaign" / "WS33_RUNTIME_CAMPAIGN_RECORD.schema.json"
    raw_schema = load(source_schema)
    effective_manifest, paths_by_id = path_map(root)
    schema = root / "abi/WS33_WITNESS_ABI_V2_1.schema.json"
    validator = root / "abi/WS33_WITNESS_SEMANTIC_VALIDATOR.py"
    provenance_path = root / "abi/WS33_SUCCESSOR_PROVENANCE.json"
    provenance = load(provenance_path)
    overlay_path = root / "WS33_RUNTIME_OVERLAY_MANIFEST.json"
    overlay = load(overlay_path)
    overlay_sha = digest(overlay_path)
    patched_forge_digest = overlay.get("patched_forge_content_digest")
    require(isinstance(patched_forge_digest, str) and len(patched_forge_digest) == 64, "missing patched Forge content digest")
    ws26_sha = provenance["ws26_manifest_sha256"]
    effective_sha = digest(root / provenance["effective_model_ref"])

    qualification_key = args.source_head + ":" + args.source_tree
    approved = provenance.get("approved_qualification_sources", {}).get(qualification_key)
    require(approved and approved.get("descends_from_model_base") is True, "campaign source is not approved qualification source")
    provenance.setdefault("approved_execution_sources", [])
    execution_pair = {"head": args.source_head, "tree": args.source_tree}
    if execution_pair not in provenance["approved_execution_sources"]:
        provenance["approved_execution_sources"].append(execution_pair)
    provenance.setdefault("patched_forge_digests", {})[qualification_key] = patched_forge_digest
    write_json(provenance_path, provenance)

    existing_coverage = load(root / "WS33_PATH_COVERAGE.json")
    existing_status = {row["effective_v2_path_id"]: row["status"] for row in existing_coverage["paths"]}
    seen_paths = set()
    seen_witness_ids = {row["witness_id"] for row in load_jsonl(root / "WS33_WITNESSES.jsonl")}
    imported = []

    for relative_record in records:
        record_path = under(campaign_root, relative_record)
        record = load(record_path)
        try:
            jsonschema.Draft202012Validator(raw_schema).validate(record)
        except jsonschema.ValidationError as exc:
            raise SystemExit(f"WS33_CAMPAIGN_MERGE=FAIL raw record {relative_record}: {exc.message}") from exc

        witness_id = record["witness_id"]
        require(witness_id not in seen_witness_ids, "duplicate witness id " + witness_id)
        path_ids = record["v2_path_ids"]
        require(not (set(path_ids) & seen_paths), "campaign paths claimed by multiple records")
        seen_paths.update(path_ids)
        require(all(path_id in paths_by_id for path_id in path_ids), "campaign record references unknown V2 path")
        require(all(existing_status[path_id] != "PASS" for path_id in path_ids), "campaign attempts to replace existing PASS path")
        owner = record["owner_family"]
        require(owner in OWNERS, "invalid owner family")
        require(all(paths_by_id[path_id]["owner_family"] == owner for path_id in path_ids), "campaign witness crosses owner families")
        for path_id in path_ids:
            representatives = set(paths_by_id[path_id].get("representative_actual_oracle_identities", []))
            require(bool(representatives & set(record["oracle_identities"])), "actual Oracle identity is not representative for " + path_id)

        assertion_ids = {item["assertion_id"] for item in record["state_assertions"]}
        exercise_by_path = {item["v2_path_id"]: item for item in record["path_exercise"]}
        require(set(exercise_by_path) == set(path_ids), "raw path_exercise does not exactly cover claimed paths")
        parent_ids = sorted({
            paths_by_id[path_id].get("parent_ws14_primitive_id")
            for path_id in path_ids if paths_by_id[path_id].get("parent_ws14_primitive_id")
        })
        path_exercise = []
        for path_id in path_ids:
            item = dict(exercise_by_path[path_id])
            require(set(item["assertion_ids"]) <= assertion_ids, "path exercise references unknown assertion")
            item["parent_ws14_primitive_id"] = paths_by_id[path_id].get("parent_ws14_primitive_id")
            path_exercise.append(item)

        target_dir = root / "campaign" / safe_id(witness_id)
        trace_ref = copy_evidence(campaign_root, root, target_dir, record["trace_file"], "trace")
        decision_ref = copy_evidence(campaign_root, root, target_dir, record.get("decision_tape_file"), "decision-tape")
        rng_ref = copy_evidence(campaign_root, root, target_dir, record.get("rng_tape_file"), "rng-tape")
        observation_ref = copy_evidence(campaign_root, root, target_dir, record.get("observation_evidence_file"), "observation")
        replay_ref = copy_evidence(campaign_root, root, target_dir, record.get("semantic_replay_evidence_file"), "semantic-replay")

        witness = {
            "schema": "commander-simulator-next.actual-card-witness.v2.1",
            "witness_id": witness_id,
            "source_head": args.source_head,
            "source_tree": args.source_tree,
            "qualification_source_head": args.source_head,
            "qualification_source_tree": args.source_tree,
            "model_base_head": BASE_HEAD,
            "model_base_tree": BASE_TREE,
            "ws26_manifest_sha256": ws26_sha,
            "effective_model_sha256": effective_sha,
            "forge_pin": PIN,
            "runtime_overlay_manifest": "WS33_RUNTIME_OVERLAY_MANIFEST.json",
            "runtime_overlay_manifest_sha256": overlay_sha,
            "patched_forge_digest": patched_forge_digest,
            "execution_environment_identity": record.get("execution_environment_identity") or {
                "runner_os": args.runner_os,
                "java_version": args.java_version,
                "process_isolation": args.process_isolation,
            },
            "oracle_identities": record["oracle_identities"],
            "parent_ws14_primitive_ids": parent_ids,
            "v2_path_ids": path_ids,
            "owner_family": owner,
            "initial_semantic_state": record["initial_semantic_state"],
            "final_semantic_state": record["final_semantic_state"],
            "state_assertions": record["state_assertions"],
            "primitive_exercise": [{"primitive_id": parent, "exercised": True} for parent in parent_ids],
            "path_exercise": path_exercise,
            "decision_tape_ref": decision_ref,
            "rng_tape_ref": rng_ref,
            "observation_evidence_ref": observation_ref,
            "semantic_replay_evidence_ref": replay_ref,
            "execution": {
                "engine": "pinned-forge",
                **record["execution"],
                "runtime_overlays_declared": True,
            },
            "trace_ref": trace_ref,
            "trace_sha256": digest(root / trace_ref),
            "stdout_only": False,
            "rules_authority_refs": record["rules_authority_refs"],
            "evidence_class": record["evidence_class"],
            "status": "PASS",
        }
        witness_path = target_dir / "witness.json"
        write_json(witness_path, witness)
        proc = subprocess.run([
            sys.executable, str(validator), str(witness_path),
            "--manifest", str(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"),
            "--schema", str(schema),
            "--provenance", str(provenance_path),
            "--base", str(root),
        ], text=True, capture_output=True)
        require(proc.returncode == 0, "ABI validation failed for " + witness_id + ": " + proc.stdout.strip())
        imported.append(witness)
        seen_witness_ids.add(witness_id)

    recompute(root, paths_by_id, imported)
    write_json(root / "WS33_CAMPAIGN_MERGE_GATE.json", {
        "schema": "commander-simulator-next.ws33-campaign-merge-gate.v1",
        "status": "PASS",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "imported_witness_count": len(imported),
        "imported_path_count": sum(len(witness["v2_path_ids"]) for witness in imported),
        "witness_ids": [witness["witness_id"] for witness in imported],
    })
    regenerate_hashes(root)
    print(json.dumps({
        "WS33_CAMPAIGN_MERGE": "PASS",
        "imported_witnesses": len(imported),
        "imported_paths": sum(len(witness["v2_path_ids"]) for witness in imported),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
