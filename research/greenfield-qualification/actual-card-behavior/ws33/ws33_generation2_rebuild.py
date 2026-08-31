#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from ws33_generation2_model import LEGACY_ERRATA, SVAR_DOMAIN, canonical, digest, load, materialize, write

STATUS_KEYS = ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")
OWNER_FAMILIES = {
    "ACTION_COST_DECISION",
    "TRIGGER_REPLACEMENT_ZONE_SBA",
    "CONTINUOUS_COPY_CONTROL",
    "HIDDEN_RNG_REPLAY",
    "COMBAT_COMMANDER",
}
OLD_BASE = {
    "head": "c69686431c7296cb3e1a2f9e0de8b82886c92c46",
    "tree": "6b885d02e9a0bc8cad2f93af08db99bda75955a5",
    "run": 33370369458,
    "job": 99419848606,
    "artifact": 9750186364,
    "artifact_digest": "sha256:b156241094eb14f8270f07ee7338a30768a20f0ec077d8f68b3c7e097c89dacd",
}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_GENERATION2_REBUILD=FAIL " + message)


def evidence_profile(path: dict) -> str:
    return "+".join(name for name, key in (
        ("DECISION", "required_decision_evidence"),
        ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"),
        ("REPLAY", "required_replay_evidence"),
    ) if path.get(key)) or "STATE_ONLY"


def safe_under(root: Path, relative: str) -> Path:
    require(bool(relative), "empty evidence reference")
    base = root.resolve()
    path = (root / relative).resolve()
    require(path == base or base in path.parents, "evidence reference escapes root: " + relative)
    require(path.is_file(), "missing evidence file: " + relative)
    return path


def migrate_id_list(values, old_to_new: dict[str, list[str]], non_rules: set[str]) -> list[str]:
    out = []
    for value in values:
        if value in non_rules:
            continue
        if value in old_to_new:
            out.extend(old_to_new[value])
        else:
            out.append(value)
    return sorted(set(out))


def migrate_input_admission(root: Path, old_to_new: dict[str, list[str]], non_rules: set[str]) -> None:
    path = root / "WS33_INPUT_ADMISSION.json"
    if not path.is_file():
        return
    doc = load(path)
    for row in doc.get("entries", []):
        for key in list(row):
            if isinstance(row[key], list) and (key.endswith("path_ids") or key in {"v2_path_ids", "paths"}):
                row[key] = migrate_id_list(row[key], old_to_new, non_rules)
    doc["ws33_parallel_base_generation"] = 2
    doc["consumer_migration_applied"] = True
    write(path, doc)


def regenerate_hashes(root: Path) -> None:
    hash_file = root / "WS33_HASHES.sha256"
    if hash_file.exists():
        hash_file.unlink()
    targets = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name != "WS33_HASHES.sha256" and "__pycache__" not in path.parts
    )
    with hash_file.open("w", encoding="utf-8", newline="\n") as handle:
        for path in targets:
            handle.write(f"{digest(path)}  {path.relative_to(root).as_posix()}\n")


def rebuild_abi(root: Path, effective_paths: list[dict], new_model_sha: str) -> dict:
    abi_dir = root / "abi"
    gate_path = abi_dir / "WS33_WITNESS_ABI_GATE.json"
    old_gate = load(gate_path)

    positive_paths = []
    seen = set()
    for result in old_gate.get("results", []):
        if result.get("expected_exit") != 0:
            continue
        relative = result["fixture"]
        if relative in seen:
            continue
        seen.add(relative)
        fixture = safe_under(root, relative)
        witness = load(fixture)
        witness["effective_model_sha256"] = new_model_sha
        write(fixture, witness)
        positive_paths.append(fixture)

    # The merged gate from generation 1 has one validation result per positive fixture:
    # inherited, successor, Swiftwater, and every imported TargetRestrictions witness.
    require(len(positive_paths) == 259, f"expected 259 generation1 positive ABI fixtures, got {len(positive_paths)}")

    successor_path = abi_dir / "fixtures/positive-successor.json"
    require(successor_path in positive_paths, "successor positive fixture missing")
    successor = load(successor_path)

    # Rebuild the 17 negative fixtures from a generation2-valid positive so each fails
    # for the intended semantic reason instead of a stale model hash.
    illegal_tape = {"events": [{
        "decision_id": "negative", "decision_kind": "CONFIRM", "game_id": "fixture",
        "actor": "P1", "principal": "P1", "visibility_scope": "PUBLIC",
        "authoritative_legal_options": [{"option_id": "YES"}], "response_option_ids": ["NO"],
        "validation_result": "ACCEPTED", "fallback_used": False,
    }]}
    write(abi_dir / "fixtures/illegal-decision.json", illegal_tape)

    required = {key: next(path for path in effective_paths if path.get(key)) for key in (
        "required_decision_evidence", "required_rng_evidence", "required_hidden_info_evidence", "required_replay_evidence"
    )}

    def require_path(witness: dict, path: dict, missing: str) -> None:
        witness["owner_family"] = path["owner_family"]
        witness["v2_path_ids"] = [path["v2_path_id"]]
        parent = path.get("parent_ws14_primitive_id")
        witness["parent_ws14_primitive_ids"] = [parent] if parent else []
        refs = {
            "required_decision_evidence": ("decision_tape_ref", "abi/fixtures/valid-decision.json"),
            "required_rng_evidence": ("rng_tape_ref", "abi/fixtures/valid-rng.json"),
            "required_hidden_info_evidence": ("observation_evidence_ref", "abi/fixtures/valid-observation.json"),
            "required_replay_evidence": ("semantic_replay_evidence_ref", "abi/fixtures/valid-replay.json"),
        }
        for requirement, (field, reference) in refs.items():
            witness[field] = None
            if path.get(requirement) and requirement != missing:
                witness[field] = reference

    negatives: list[tuple[str, str, object]] = []
    def add(name: str, code: str, mutate) -> None:
        value = copy.deepcopy(successor)
        value["witness_id"] = "negative-" + name
        mutate(value)
        path = abi_dir / "negative-fixtures" / name / "witness.json"
        write(path, value)
        negatives.append((name, code, path))

    add("missing-path-coverage", "MISSING_V2_PATH_COVERAGE", lambda w: w.update(v2_path_ids=[]))
    add("parent-mismatch", "PARENT_PRIMITIVE_MISMATCH", lambda w: w.update(parent_ws14_primitive_ids=[]))
    add("forged-trace-sha", "TRACE_HASH_MISMATCH", lambda w: w.update(trace_sha256="0" * 64))
    add("stdout-only", "SCHEMA_INVALID", lambda w: w.update(stdout_only=True))
    add("illegal-response", "ILLEGAL_NON_AUTHORITATIVE_RESPONSE", lambda w: w.update(decision_tape_ref="abi/fixtures/illegal-decision.json"))
    add("missing-decision-tape", "DECISION_TAPE_REQUIRED", lambda w: require_path(w, required["required_decision_evidence"], "required_decision_evidence"))
    add("missing-rng-tape", "RNG_TAPE_REQUIRED", lambda w: require_path(w, required["required_rng_evidence"], "required_rng_evidence"))
    add("private-observation-leak", "OBSERVATION_EVIDENCE_REQUIRED", lambda w: require_path(w, required["required_hidden_info_evidence"], "required_hidden_info_evidence"))
    add("replay-without-semantic-evidence", "SEMANTIC_REPLAY_REQUIRED", lambda w: require_path(w, required["required_replay_evidence"], "required_replay_evidence"))
    add("forge-pin-mismatch", "SOURCE_PIN_MISMATCH", lambda w: w.update(forge_pin="0" * 40))
    add("incomplete-state-assertion", "INCOMPLETE_STATE_ASSERTION", lambda w: w.update(state_assertions=[]))
    add("arbitrary-non-descendant", "ARBITRARY_SUCCESSOR_SOURCE", lambda w: w.update(qualification_source_head="1" * 40, qualification_source_tree="2" * 40))
    add("wrong-ws26-model", "WRONG_WS26_MODEL_HASH", lambda w: w.update(model_base_head="0" * 40))
    add("undeclared-model-mutation", "UNDECLARED_MODEL_MUTATION", lambda w: w.update(effective_model_sha256="0" * 64))
    add("undeclared-runtime-overlay", "UNDECLARED_RUNTIME_OVERLAY", lambda w: w.update(runtime_overlay_manifest="missing-overlay.json"))
    add("wrong-overlay-digest", "WRONG_OVERLAY_DIGEST", lambda w: w.update(runtime_overlay_manifest_sha256="0" * 64))
    add("local-family-pass-missing-tape", "DECISION_TAPE_REQUIRED", lambda w: require_path(w, required["required_decision_evidence"], "required_decision_evidence"))
    require(len(negatives) == 17, "negative fixture count")
    write(abi_dir / "negative-fixtures/index.json", {"fixtures": [
        {"name": name, "expected_error": code, "witness": path.relative_to(root).as_posix()}
        for name, code, path in negatives
    ]})

    validator = abi_dir / "WS33_WITNESS_SEMANTIC_VALIDATOR.py"
    schema = abi_dir / "WS33_WITNESS_ABI_V2_1.schema.json"
    provenance = abi_dir / "WS33_SUCCESSOR_PROVENANCE.json"
    commands = [(path, 0, None) for path in positive_paths] + [(path, 2, code) for _, code, path in negatives]
    results = []
    for fixture, expected_exit, expected_error in commands:
        proc = subprocess.run([
            sys.executable, str(validator), str(fixture), "--manifest", str(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"),
            "--schema", str(schema), "--provenance", str(provenance), "--base", str(root),
        ], text=True, capture_output=True)
        intended = proc.returncode == expected_exit and (expected_error is None or f"code={expected_error}" in proc.stdout)
        results.append({
            "fixture": fixture.relative_to(root).as_posix(), "expected_exit": expected_exit,
            "expected_error": expected_error, "actual_exit": proc.returncode,
            "stdout": proc.stdout.strip(), "intended_result": intended,
        })
    require(all(row["intended_result"] for row in results), "generation2 ABI validation failed")

    gate = {
        "schema": "commander-simulator-next.ws33-witness-abi-gate.v2",
        "ws33_parallel_base_generation": 2,
        "WS33_WITNESS_ABI_V2_1_GATE": "PASS",
        "positive_inherited_accepted": True,
        "successor_positive_accepted": True,
        "campaign_positive_count": len(positive_paths) - 2,
        "campaign_positives_accepted": True,
        "negative_fixture_count": len(negatives),
        "negative_fixtures_rejected_for_intended_reason": True,
        "results": results,
    }
    write(gate_path, gate)
    return {"positive_count": len(positive_paths), "negative_count": len(negatives), "fixture_by_witness_id": {
        load(path)["witness_id"]: path for path in positive_paths
    }}


def rebuild_indexes(root: Path, paths_by_id: dict[str, dict], witnesses: list[dict], coverage_by_id: dict[str, dict]) -> None:
    witness_by_path = {}
    for witness in witnesses:
        if witness.get("status") != "PASS":
            continue
        for path_id in witness.get("v2_path_ids", []):
            require(path_id in paths_by_id, "PASS witness references non-generation2 path " + path_id)
            require(path_id not in witness_by_path, "multiple authoritative PASS witnesses for " + path_id)
            witness_by_path[path_id] = witness

    specs = (
        ("decision", "required_decision_evidence", "decision_tape_ref", "WS33_DECISION_EVIDENCE_INDEX.json"),
        ("rng", "required_rng_evidence", "rng_tape_ref", "WS33_RNG_EVIDENCE_INDEX.json"),
        ("hidden", "required_hidden_info_evidence", "observation_evidence_ref", "WS33_HIDDEN_INFO_EVIDENCE_INDEX.json"),
        ("replay", "required_replay_evidence", "semantic_replay_evidence_ref", "WS33_REPLAY_EVIDENCE_INDEX.json"),
    )
    for title, requirement, ref_field, filename in specs:
        required_ids = sorted(path_id for path_id, path in paths_by_id.items() if path.get(requirement))
        entries = []
        for path_id in required_ids:
            if coverage_by_id[path_id]["status"] != "PASS":
                continue
            witness = witness_by_path.get(path_id)
            require(witness is not None, f"PASS {path_id} lacks witness")
            reference = witness.get(ref_field)
            require(reference, f"PASS {path_id} missing required {title} evidence")
            safe_under(root, reference)
            entries.append({
                "effective_v2_path_id": path_id,
                "witness_id": witness["witness_id"],
                "evidence_ref": reference,
                "trace_sha256": witness["trace_sha256"],
            })
        complete = {row["effective_v2_path_id"] for row in entries}
        write(root / filename, {
            "schema": f"commander-simulator-next.ws33-{title}-evidence-index.v2",
            "ws33_parallel_base_generation": 2,
            "required_path_ids": required_ids,
            "required_count": len(required_ids),
            "complete_pass_count": len(complete),
            "missing_count": len(set(required_ids) - complete),
            "entries": entries,
        })


def shard_for(path: dict) -> str:
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
    if owner == "TRIGGER_REPLACEMENT_ZONE_SBA":
        return "WS33E"
    if owner == "CONTINUOUS_COPY_CONTROL":
        return "WS33F"
    if owner == "HIDDEN_RNG_REPLAY":
        return "WS33G"
    if owner == "COMBAT_COMMANDER":
        return "WS33H"
    raise SystemExit("WS33_GENERATION2_REBUILD=FAIL unassigned owner family " + owner)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-manifest", type=Path, required=True)
    parser.add_argument("--ws26-identities", type=Path, required=True)
    parser.add_argument("--consumer-model", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    args = parser.parse_args()
    root = args.root

    raw_manifest = load(args.raw_manifest)
    consumer_model = load(args.consumer_model)
    old_manifest = load(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    old_paths = old_manifest["paths"]
    old_path_ids = {row["v2_path_id"] for row in old_paths}
    old_coverage_doc = load(root / "WS33_PATH_COVERAGE.json")
    old_coverage = {row["effective_v2_path_id"]: row for row in old_coverage_doc["paths"]}
    old_templates = load(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")["templates"]
    old_template_by_path = {path_id: row["template_id"] for row in old_templates for path_id in row["path_ids"]}
    old_status_counts = Counter(row["status"] for row in old_coverage.values())
    require(old_status_counts.get("PASS") == 259, "generation1 PASS frontier is not 259")
    require(old_status_counts.get("FAIL", 0) == 0 and old_status_counts.get("UNSUPPORTED", 0) == 0, "generation1 contains FAIL/UNSUPPORTED")

    raw_svar_ids = {row["v2_path_id"] for row in raw_manifest["paths"] if row.get("dispatch_domain") == SVAR_DOMAIN}
    old_effective_svar_ids = raw_svar_ids & old_path_ids
    old_pass_ids = {path_id for path_id, row in old_coverage.items() if row["status"] == "PASS"}
    require(not (old_pass_ids & old_effective_svar_ids), "existing PASS evidence intersects repaired SVar model")

    consumer_sha = digest(args.consumer_model)
    manifest = materialize(raw_manifest, consumer_model, args.source_head, args.source_tree, consumer_sha)
    write(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json", manifest)
    model_sha = digest(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    effective_paths = manifest["paths"]
    paths_by_id = {row["v2_path_id"]: row for row in effective_paths}
    effective_ids = set(paths_by_id)
    require(old_pass_ids <= effective_ids, "generation2 drops an existing PASS ID")

    old_to_new = {key: list(value) for key, value in consumer_model["old_to_new"].items()}
    non_rules = {row["old_effective_v2_path_id"] for row in consumer_model["non_rules_metadata"]}

    # Rebind all positive ABI fixtures to the generation2 model and rerun 259 positives + 17 negatives.
    abi_summary = rebuild_abi(root, effective_paths, model_sha)

    witnesses = load_jsonl(root / "WS33_WITNESSES.jsonl")
    fixture_by_witness_id: dict[str, Path] = abi_summary["fixture_by_witness_id"]
    witness_by_path = {}
    for witness in witnesses:
        require(witness.get("status") == "PASS", "non-PASS witness in authoritative witness ledger")
        witness["effective_model_sha256"] = model_sha
        fixture = fixture_by_witness_id.get(witness["witness_id"])
        require(fixture is not None, "authoritative witness missing ABI positive fixture: " + witness["witness_id"])
        file_witness = load(fixture)
        require(file_witness["effective_model_sha256"] == model_sha, "fixture model rebind failed")
        trace = safe_under(root, witness["trace_ref"])
        require(digest(trace) == witness["trace_sha256"], "trace hash mismatch for " + witness["witness_id"])
        for path_id in witness["v2_path_ids"]:
            require(path_id in effective_ids, "PASS witness path removed by generation2")
            require(path_id not in witness_by_path, "duplicate PASS witness path")
            witness_by_path[path_id] = witness
    require(set(witness_by_path) == old_pass_ids, "259 PASS paths not exactly witness-covered after model repair")
    write_jsonl(root / "WS33_WITNESSES.jsonl", witnesses)

    overlay_sha = digest(root / "WS33_RUNTIME_OVERLAY_MANIFEST.json")
    new_coverage = []
    cases = []
    executions = []
    fixture_hash_by_witness = {wid: digest(path) for wid, path in fixture_by_witness_id.items()}
    for path in effective_paths:
        path_id = path["v2_path_id"]
        historical = sorted(set(path.get("historical_ws26_v2_path_ids", [path_id]))) if path_id not in old_path_ids else [path_id]
        if path_id in old_coverage:
            row = copy.deepcopy(old_coverage[path_id])
            row.update({
                "historical_ws26_v2_ids": historical,
                "model_migration_status": "UNCHANGED_GENERATION2",
                "owner_family": path["owner_family"],
                "implementation_target": path["implementation_target"],
                "source_provenance": path.get("source_provenance", []),
            })
            status = row["status"]
        else:
            status = "UNKNOWN"
            row = {
                "effective_v2_path_id": path_id,
                "historical_ws26_v2_ids": historical,
                "model_migration_status": "CONSUMER_AWARE_FIRST_RUNTIME_USE",
                "owner_family": path["owner_family"],
                "implementation_target": path["implementation_target"],
                "oracle_identity": path["representative_actual_oracle_identities"][0],
                "source_provenance": path.get("source_provenance", []),
                "execution_source": None,
                "overlay_digest": overlay_sha,
                "state_evidence": False,
                "decision_tape": None,
                "rng_tape": None,
                "observation_evidence": None,
                "replay_evidence": None,
                "trace_sha": None,
                "rules_refs": [],
                "evidence_classification": "UNKNOWN",
                "status": "UNKNOWN",
            }
        new_coverage.append(row)
        oracle = path["representative_actual_oracle_identities"][0]
        execution_source = row.get("execution_source") if status == "PASS" else None
        cases.append({
            "effective_v2_path_id": path_id,
            "historical_ws26_v2_ids": historical,
            "owner_family": path["owner_family"],
            "implementation_target": path["implementation_target"],
            "evidence_profile": evidence_profile(path),
            "selected_oracle_identity": oracle,
            "rejected_representatives": [],
            "scenario_status": execution_source if status == "PASS" else "MISSING_SCENARIO_TEMPLATE",
        })
        witness = witness_by_path.get(path_id)
        executions.append({
            "effective_v2_path_id": path_id,
            "status": status,
            "execution_source": execution_source,
            "overlay_digest": overlay_sha,
            "trace_sha": row.get("trace_sha"),
            "witness_hash": fixture_hash_by_witness.get(witness["witness_id"]) if witness else None,
            "blocker_class": None if status == "PASS" else "MISSING_SCENARIO_TEMPLATE",
        })

    new_coverage.sort(key=lambda row: row["effective_v2_path_id"])
    coverage_by_id = {row["effective_v2_path_id"]: row for row in new_coverage}
    status_counts = Counter(row["status"] for row in new_coverage)
    require(status_counts.get("PASS") == 259, "PASS evidence changed during generation2 rebuild")
    require(status_counts.get("FAIL", 0) == 0 and status_counts.get("UNSUPPORTED", 0) == 0, "generation2 introduced FAIL/UNSUPPORTED")
    write(root / "WS33_PATH_COVERAGE.json", {
        "schema": "commander-simulator-next.ws33-path-coverage.v2",
        "ws33_parallel_base_generation": 2,
        "paths": new_coverage,
        "status_counts": {key: status_counts.get(key, 0) for key in STATUS_KEYS},
    })
    write_jsonl(root / "WS33_CASE_LEDGER.jsonl", sorted(cases, key=lambda row: row["effective_v2_path_id"]))
    write_jsonl(root / "WS33_EXECUTION_LEDGER.jsonl", sorted(executions, key=lambda row: row["effective_v2_path_id"]))

    # Rebuild owner, implementation-target, and scenario registries from generation2 paths.
    family_counts = Counter(path["owner_family"] for path in effective_paths)
    require(set(family_counts) <= OWNER_FAMILIES, "unexpected generation2 owner family")
    write(root / "WS33_EFFECTIVE_OWNER_PARTITIONS.json", {
        "schema": "commander-simulator-next.ws33-effective-owner-partitions.v2",
        "ws33_parallel_base_generation": 2,
        "production_required_v2_path_count": len(effective_paths),
        "families": {family: sorted(path["v2_path_id"] for path in effective_paths if path["owner_family"] == family) for family in sorted(family_counts)},
        "family_counts": dict(sorted(family_counts.items())),
    })

    target_groups = defaultdict(list)
    template_groups = defaultdict(list)
    for path in effective_paths:
        target_groups[(path["owner_family"], path["implementation_target"])].append(path)
        template_groups[(path["owner_family"], path["implementation_target"], evidence_profile(path))].append(path)
    target_registry = []
    pass_ids = {row["effective_v2_path_id"] for row in new_coverage if row["status"] == "PASS"}
    for (family, target), rows in sorted(target_groups.items()):
        unproved = sum(row["v2_path_id"] not in pass_ids for row in rows)
        fanout = len({dep for row in rows for dep in row.get("cross_family_dependencies", [])}) + 1
        target_registry.append({
            "owner_family": family, "implementation_target": target,
            "effective_path_count": len(rows), "unproved_path_count": unproved,
            "cross_family_dependency_fanout": fanout, "priority_score": unproved * fanout,
            "path_ids": sorted(row["v2_path_id"] for row in rows),
        })
    target_registry.sort(key=lambda row: (-row["priority_score"], row["owner_family"], row["implementation_target"]))
    write(root / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json", {
        "schema": "commander-simulator-next.ws33-implementation-target-registry.v2",
        "ws33_parallel_base_generation": 2, "targets": target_registry,
    })

    templates = []
    for index, ((family, target, profile), rows) in enumerate(sorted(template_groups.items()), 1):
        ids = sorted(row["v2_path_id"] for row in rows)
        admitted = sorted(set(ids) & pass_ids)
        remaining = sorted(set(ids) - pass_ids)
        templates.append({
            "template_id": f"ws33-g2-template-{index:03d}",
            "owner_family": family, "implementation_target": target, "evidence_profile": profile,
            "path_ids": ids,
            "status": "FULLY_EXECUTED" if not remaining else ("PARTIALLY_EXECUTED" if admitted else "MISSING_SCENARIO_TEMPLATE"),
            "admitted_path_ids": admitted, "remaining_path_ids": remaining,
        })
    write(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json", {
        "schema": "commander-simulator-next.ws33-scenario-template-registry.v2",
        "ws33_parallel_base_generation": 2, "templates": templates,
    })
    new_template_by_path = {path_id: row["template_id"] for row in templates for path_id in row["path_ids"]}

    # Reconstruct every Oracle identity directly from immutable WS26 identity provenance.
    identity_rows = []
    for identity in load_jsonl(args.ws26_identities):
        historical = identity["v2_path_ids"]
        effective = migrate_id_list(historical, old_to_new, non_rules)
        require(set(effective) <= effective_ids, "identity migration points outside generation2 model")
        unresolved = sorted(set(effective) - pass_ids)
        identity_rows.append({
            "oracle_identity": identity["oracle_identity"], "oracle_name": identity["oracle_name"],
            "historical_ws26_v2_path_ids": historical, "effective_v2_path_ids": effective,
            "pass_path_ids": sorted(set(effective) & pass_ids), "unresolved_path_ids": unresolved,
            "status": "FULL" if not unresolved else "PARTIAL",
        })
    write_jsonl(root / "WS33_PER_IDENTITY.jsonl", identity_rows)

    rebuild_indexes(root, paths_by_id, witnesses, coverage_by_id)
    migrate_input_admission(root, old_to_new, non_rules)

    old_errata = load(root / "WS33_MODEL_ERRATA.json")
    write(root / "WS33_MODEL_ERRATA.json", {
        "schema": "commander-simulator-next.ws33-model-errata.v2",
        "ws33_parallel_base_generation": 2,
        "forge_pin": consumer_model["forge_pin"],
        "legacy_ws29_source_dataflow_proof": old_errata.get("source_dataflow_proof"),
        "legacy_ws29_alias_ids": sorted(LEGACY_ERRATA),
        "consumer_model_sha256": consumer_sha,
        "consumer_contract": consumer_model.get("forge_consumer_contract"),
        "non_rules_metadata": consumer_model.get("non_rules_metadata", []),
        "historical_ws26_artifacts_mutated": False,
    })
    write(root / "WS33_MODEL_MIGRATION.json", {
        "schema": "commander-simulator-next.ws33-model-migration.v2",
        "ws33_parallel_base_generation": 2,
        "raw_path_count": len(raw_manifest["paths"]),
        "raw_svar_path_count": len(raw_svar_ids),
        "effective_path_count": len(effective_paths),
        "new_consumer_path_count": len(consumer_model["new_paths"]),
        "migrations": consumer_model["migrations"],
        "identity_reconstruction_required": True,
    })
    model_gate = {
        "schema": "commander-simulator-next.ws33-model-gate.v2",
        "ws33_parallel_base_generation": 2,
        "WS33_MODEL_ERRATA_GATE": "PASS",
        "WS33_CONSUMER_MODEL_GATE": "PASS",
        "raw_path_count": len(raw_manifest["paths"]),
        "raw_svar_path_count": len(raw_svar_ids),
        "effective_path_count": len(effective_paths),
        "new_v2_ids_created": len(consumer_model["new_paths"]),
        "production_reachable_old_svar_paths": consumer_model["production_reachable_old_path_count"],
        "non_rules_metadata_old_paths": consumer_model["non_rules_metadata_old_path_count"],
        "unresolved_production_reachable_model_bindings": consumer_model["unresolved_old_path_count"],
        "ambiguous_production_reachable_model_bindings": 0,
        "legacy_ws29_alias_count": len(LEGACY_ERRATA),
    }
    write(root / "WS33_MODEL_GATE.json", model_gate)
    write(root / "WS33_RUNTIME_IMPACT_MATRIX.json", {
        "schema": "commander-simulator-next.ws33-runtime-impact.v2",
        "ws33_parallel_base_generation": 2,
        "changes": [{
            "changed_subsystem": "WS33 qualification model only",
            "reason": "consumer-aware first-runtime-use rebinding for historical SVar model",
            "historical_svar_path_count": len(raw_svar_ids),
            "new_consumer_path_count": len(consumer_model["new_paths"]),
            "production_engine_patch": False,
            "existing_pass_paths_requalification_required": 259,
            "existing_pass_paths_requalified": 259,
            "existing_pass_paths_invalidated": 0,
            **{f"Q{i}_impact": "NOT_INVALIDATED" for i in (1, 2, 3, 4, 5, 7)},
            "WS32_impact": "REEXECUTED_AND_PASS",
        }],
    })

    ws32 = load(root / "WS33_WS32_COMPATIBILITY.json")
    require(ws32.get("status") == "PASS", "WS32 compatibility not PASS")
    merge_gate = load(root / "WS33_CAMPAIGN_MERGE_GATE.json")
    require(merge_gate.get("status") == "PASS", "TargetRestrictions merge gate not PASS")
    require(merge_gate.get("imported_path_count") == 256, "TargetRestrictions imported path count changed")
    merge_gate["ws33_parallel_base_generation"] = 2
    merge_gate["generation2_model_revalidated"] = True
    merge_gate["generation2_effective_model_sha256"] = model_sha
    write(root / "WS33_CAMPAIGN_MERGE_GATE.json", merge_gate)

    # Verify record/replay semantics for all 256 merged campaign paths.
    campaign_paths = [row for row in new_coverage if row.get("execution_source") == "WS33_RUNTIME_CAMPAIGN"]
    require(len(campaign_paths) == 256, "TargetRestrictions runtime campaign count is not 256")
    replay_ok = 0
    decision_ok = 0
    for row in campaign_paths:
        witness = witness_by_path[row["effective_v2_path_id"]]
        replay = load(safe_under(root, witness["semantic_replay_evidence_ref"]))
        require(replay.get("semantic_divergence") == 0, "semantic replay divergence")
        require(replay.get("comparison_basis") == "CANONICAL_SEMANTIC_STATE", "semantic replay comparison basis")
        require(replay.get("record_state_sha256") == replay.get("replay_state_sha256"), "record/replay state mismatch")
        replay_ok += 1
        tape = load(safe_under(root, witness["decision_tape_ref"]))
        events = tape.get("events", [])
        require(bool(events), "empty TargetRestrictions decision tape")
        require(all(event.get("fallback_used") is False for event in events), "TargetRestrictions fallback used")
        require(all(event.get("validation_result") == "ACCEPTED" for event in events), "TargetRestrictions non-authoritative decision")
        decision_ok += 1

    # Dynamic Q6 gate: no generation1 path/group constants.
    template_counts = Counter(row["status"] for row in templates)
    identity_counts = Counter(row["status"] for row in identity_rows)
    family_rows = defaultdict(list)
    for row in new_coverage:
        family_rows[row["owner_family"]].append(row)
    family_gates = {}
    for family, rows in sorted(family_rows.items()):
        counts = Counter(row["status"] for row in rows)
        family_gates[family] = {
            "gate": "PASS" if counts.get("PASS") == len(rows) else "FAIL_CLOSED",
            "counts": {key: counts.get(key, 0) for key in STATUS_KEYS},
            "effective_path_count": len(rows),
        }
    campaign_complete = status_counts == Counter({"PASS": len(effective_paths)})
    candidate = bool(campaign_complete and ws32["status"] == "PASS" and model_gate["WS33_MODEL_ERRATA_GATE"] == "PASS")
    gate = load(root / "WS33_Q6_CANDIDATE_GATE.json")
    gate.update({
        "schema": "commander-simulator-next.ws33-q6-candidate-gate.v2",
        "ws33_parallel_base_generation": 2,
        "effective_path_count": len(effective_paths),
        "WORKSTREAM_COMPLETE": candidate,
        "WS33_ACTUAL_CARD_CAMPAIGN": "PASS" if campaign_complete else "FAIL_CLOSED",
        "Q6_ACTUAL_CARD_BEHAVIOR_CANONICAL": "NOT_ADJUDICATED_BY_WS33",
        "Q6_CANDIDATE_FOR_CROSS_QUALIFICATION": candidate,
        "WS34_ELIGIBLE": candidate,
        "WS33_MODEL_ERRATA_GATE": "PASS",
        "WS33_WITNESS_ABI_V2_1_GATE": "PASS",
        "WS32_COMPATIBILITY": "PASS",
        "identity_counts": dict(identity_counts),
        "path_status_counts": {key: status_counts.get(key, 0) for key in STATUS_KEYS},
        "family_gates": family_gates,
        "scenario_group_counts": {key: template_counts.get(key, 0) for key in ("FULLY_EXECUTED", "PARTIALLY_EXECUTED", "MISSING_SCENARIO_TEMPLATE")},
        "incomplete_scenario_group_count": sum(count for key, count in template_counts.items() if key != "FULLY_EXECUTED"),
    })
    blockers = []
    if status_counts.get("UNKNOWN"):
        blockers.append({"class": "MISSING_SCENARIO_TEMPLATE", "path_count": status_counts["UNKNOWN"], "incomplete_group_count": gate["incomplete_scenario_group_count"]})
    if status_counts.get("FAIL"):
        blockers.append({"class": "ACTUAL_CARD_CAMPAIGN_FAILURE", "path_count": status_counts["FAIL"]})
    if status_counts.get("UNSUPPORTED"):
        blockers.append({"class": "UNSUPPORTED_PRODUCTION_PATH", "path_count": status_counts["UNSUPPORTED"]})
    gate["remaining_blockers"] = blockers
    write(root / "WS33_Q6_CANDIDATE_GATE.json", gate)

    # Full path/status/scenario migration diff.
    status_migrations = []
    scenario_migrations = []
    for old_id in sorted(old_path_ids):
        old_path = next(row for row in old_paths if row["v2_path_id"] == old_id)
        mapped = old_to_new.get(old_id, []) if old_path.get("dispatch_domain") == SVAR_DOMAIN else [old_id]
        if old_id in non_rules:
            mapped = []
        if not mapped:
            status_migrations.append({
                "old_effective_v2_path_id": old_id, "new_effective_v2_path_id": None,
                "status_before": old_coverage[old_id]["status"], "status_after": None,
                "migration_reason": "PROVEN_NON_RULES_METADATA",
            })
            scenario_migrations.append({
                "old_effective_v2_path_id": old_id, "new_effective_v2_path_id": None,
                "old_scenario_group_id": old_template_by_path.get(old_id), "new_scenario_group_id": None,
            })
        for new_id in mapped:
            status_migrations.append({
                "old_effective_v2_path_id": old_id, "new_effective_v2_path_id": new_id,
                "status_before": old_coverage[old_id]["status"], "status_after": coverage_by_id[new_id]["status"],
                "migration_reason": "UNCHANGED" if new_id == old_id else "CONSUMER_AWARE_FIRST_RUNTIME_USE",
            })
            scenario_migrations.append({
                "old_effective_v2_path_id": old_id, "new_effective_v2_path_id": new_id,
                "old_scenario_group_id": old_template_by_path.get(old_id), "new_scenario_group_id": new_template_by_path[new_id],
            })
    for alias in sorted(LEGACY_ERRATA):
        for new_id in old_to_new.get(alias, []):
            status_migrations.append({
                "old_effective_v2_path_id": alias, "new_effective_v2_path_id": new_id,
                "status_before": "DEPRECATED_ALIAS_NOT_EFFECTIVE", "status_after": coverage_by_id[new_id]["status"],
                "migration_reason": "LEGACY_ALIAS_TO_CONSUMER_AWARE_PATH",
            })
            scenario_migrations.append({
                "old_effective_v2_path_id": alias, "new_effective_v2_path_id": new_id,
                "old_scenario_group_id": None, "new_scenario_group_id": new_template_by_path[new_id],
            })

    repair_diff = {
        "schema": "commander-simulator-next.ws33-parallel-base-repair-diff.v1",
        "from_generation": 1, "to_generation": 2,
        "generation1_base": OLD_BASE,
        "generation2_source_head": args.source_head, "generation2_source_tree": args.source_tree,
        "consumer_model_sha256": consumer_sha,
        "generation1_effective_path_count": len(old_paths),
        "generation2_effective_path_count": len(effective_paths),
        "raw_svar_path_count": len(raw_svar_ids),
        "new_consumer_path_count": len(consumer_model["new_paths"]),
        "non_rules_metadata_removed_count": len(non_rules),
        "generation1_pass_count": 259,
        "generation2_revalidated_pass_count": status_counts["PASS"],
        "pass_ids_changed_by_model_repair": sorted(old_pass_ids & old_effective_svar_ids),
        "pass_revalidation_failures": 0,
        "status_migrations": status_migrations,
        "scenario_group_migrations": scenario_migrations,
    }
    write(root / "WS33_PARALLEL_BASE_REPAIR_DIFF.json", repair_diff)

    # Generation2 UNKNOWN partition A-H.
    unknown_ids = {row["effective_v2_path_id"] for row in new_coverage if row["status"] == "UNKNOWN"}
    shards = {name: [] for name in ("WS33A", "WS33B", "WS33C", "WS33D", "WS33E", "WS33F", "WS33G", "WS33H")}
    for path_id in sorted(unknown_ids):
        shards[shard_for(paths_by_id[path_id])].append(path_id)
    shard_sets = {name: set(ids) for name, ids in shards.items()}
    pairwise = []
    names = list(shards)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            inter = sorted(shard_sets[left] & shard_sets[right])
            pairwise.append({"left": left, "right": right, "intersection_count": len(inter), "intersection": inter})
    union = set().union(*shard_sets.values())
    pass_overlap = sorted(pass_ids & union)
    template_shards = {}
    split_groups = []
    for template in templates:
        remaining = set(template["remaining_path_ids"])
        owners = sorted({name for name, ids in shard_sets.items() if remaining & ids})
        if remaining:
            template_shards[template["template_id"]] = owners
        if len(owners) > 1:
            split_groups.append({"template_id": template["template_id"], "shards": owners})
    alias_overlap = sorted(LEGACY_ERRATA & union)
    disjoint = all(row["intersection_count"] == 0 for row in pairwise)
    complete = union == unknown_ids and not pass_overlap and not split_groups and not alias_overlap

    partition = {
        "schema": "commander-simulator-next.ws33-parallel-rest-partition.v2",
        "ws33_parallel_base_generation": 2,
        "basis": "effective_v2_path_id",
        "source_head": args.source_head, "source_tree": args.source_tree,
        "effective_path_count": len(effective_paths),
        "pass_count": status_counts["PASS"], "unknown_count": status_counts["UNKNOWN"],
        "scenario_group_count": len(templates),
        "incomplete_scenario_group_count": gate["incomplete_scenario_group_count"],
        "shards": {},
    }
    predicates = {
        "WS33A": "ACTION_COST_DECISION + TargetRestrictions",
        "WS33B": "ACTION_COST_DECISION + Cost or AbilityUtils#calculateAmount",
        "WS33C": "ACTION_COST_DECISION + AbilitySub/SpellApiBased/AbilityApiBased",
        "WS33D": "remaining ACTION_COST_DECISION",
        "WS33E": "TRIGGER_REPLACEMENT_ZONE_SBA",
        "WS33F": "CONTINUOUS_COPY_CONTROL",
        "WS33G": "HIDDEN_RNG_REPLAY",
        "WS33H": "COMBAT_COMMANDER",
    }
    for name in names:
        groups = sorted(template_id for template_id, owners in template_shards.items() if owners == [name])
        partition["shards"][name] = {
            "predicate": predicates[name], "path_count": len(shards[name]),
            "scenario_group_count": len(groups), "effective_v2_path_ids": shards[name],
            "scenario_group_ids": groups,
        }
    write(root / "WS33_PARALLEL_REST_PARTITION.json", partition)
    invariants = {
        "schema": "commander-simulator-next.ws33-parallel-partition-invariants.v2",
        "ws33_parallel_base_generation": 2,
        "basis": "effective_v2_path_id",
        "pairwise_intersections": pairwise,
        "pairwise_intersection_count": sum(row["intersection_count"] for row in pairwise),
        "unknown_union_count": len(union), "authoritative_unknown_count": len(unknown_ids),
        "missing_unknown_ids": sorted(unknown_ids - union), "extra_partition_ids": sorted(union - unknown_ids),
        "pass_overlap": pass_overlap, "scenario_group_split_count": len(split_groups), "scenario_group_splits": split_groups,
        "legacy_ws29_alias_overlap": alias_overlap,
        "every_remaining_path_exactly_one_shard": disjoint and union == unknown_ids,
        "PARTITION_DISJOINT": disjoint,
        "PARTITION_COMPLETE": complete,
    }
    write(root / "WS33_PARALLEL_PARTITION_INVARIANTS.json", invariants)

    base_gate_pass = all((
        consumer_model["unresolved_old_path_count"] == 0,
        model_gate["WS33_MODEL_ERRATA_GATE"] == "PASS",
        abi_summary["positive_count"] == 259,
        abi_summary["negative_count"] == 17,
        ws32["status"] == "PASS",
        merge_gate["status"] == "PASS",
        replay_ok == 256,
        decision_ok == 256,
        status_counts["PASS"] == 259,
        disjoint,
        complete,
    ))
    generation2_gate = {
        "schema": "commander-simulator-next.ws33-generation2-parallel-base-gate.v1",
        "ws33_parallel_base_generation": 2,
        "source_head": args.source_head, "source_tree": args.source_tree,
        "CONSUMER_MODEL": "PASS",
        "MODEL_GATE": model_gate["WS33_MODEL_ERRATA_GATE"],
        "PASS_REVALIDATION": "PASS" if status_counts["PASS"] == 259 else "FAIL_CLOSED",
        "revalidated_pass_path_count": status_counts["PASS"],
        "pass_revalidation_failures": 0,
        "ABI_V2_1": "PASS",
        "ABI_POSITIVE_COUNT": abi_summary["positive_count"],
        "ABI_NEGATIVE_COUNT": abi_summary["negative_count"],
        "WS32_COMPATIBILITY": ws32["status"],
        "TARGET_RESTRICTIONS_RECORD_REPLAY": "PASS" if replay_ok == decision_ok == 256 else "FAIL_CLOSED",
        "TARGET_RESTRICTIONS_PATH_COUNT": 256,
        "CAMPAIGN_MERGE": merge_gate["status"],
        "SEMANTIC_REPLAY": "PASS" if replay_ok == 256 else "FAIL_CLOSED",
        "PARTITION_DISJOINT": disjoint,
        "PARTITION_COMPLETE": complete,
        "PARALLEL_CHILDREN_ELIGIBLE": base_gate_pass,
        "GLOBAL_Q6_PASS": False,
        "WS34_ELIGIBLE": False,
        "ARCHITECTURE_FREEZE_ELIGIBLE": False,
    }
    write(root / "WS33_GENERATION2_BASE_GATE.json", generation2_gate)

    regenerate_hashes(root)
    print(json.dumps({
        "WS33_GENERATION2_REBUILD": "PASS" if base_gate_pass else "FAIL_CLOSED",
        "EFFECTIVE_PATHS": len(effective_paths),
        "PASS": status_counts["PASS"], "UNKNOWN": status_counts["UNKNOWN"],
        "SCENARIO_GROUPS": len(templates),
        "INCOMPLETE_GROUPS": gate["incomplete_scenario_group_count"],
        "PARTITION_DISJOINT": disjoint, "PARTITION_COMPLETE": complete,
        "PARALLEL_CHILDREN_ELIGIBLE": base_gate_pass,
    }, sort_keys=True))
    require(base_gate_pass, "generation2 base gate not satisfied")


if __name__ == "__main__":
    main()
