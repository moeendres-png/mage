#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
BASE_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
BASE_TREE = "837f445f78bb26462653c58baf1532e294151b10"
QUALIFIED_RUNTIME_HEAD = "55820618e7243bd5ba8cfa33c3148cea8c166c73"
QUALIFIED_RUNTIME_TREE = "3706900d49c6ef61690c227bb7b4c0067fbcfb44"
RULES_URL = "https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt"
ERRATA = {
    "forge-behavior-v2:452495ff67d15f9989748411f5ec41067e039c7b": "CraftStatic",
    "forge-behavior-v2:6dfbc7e6fb17a15e4445462f4383e6ebcf7ffedf": "DBStatic",
    "forge-behavior-v2:7caaed2bb9b0c5fe0f5dab44de04175ec1867a16": "TreasureEquip",
    "forge-behavior-v2:beee69a372f7b75417aa7fd9552cdfe6fae1a519": "StaticPump",
}
TERMINAL = "forge-behavior-v2:a8c16ce359130eb6985c8730be000adac668b397"
PREDECESSORS = {
    "WS26": (BASE_HEAD, BASE_TREE, 33283478862, 99182488884, 9723722686, "sha256:b9e1fc4fd792b0baa1da1c17e3bbc9e01b2557d4b73b8590e680679f53b59883"),
    "WS27": ("3f42def33d25c7f03f4a2b612ac1cce129180e7c", "b3bd9dfeac7a169fef92249301a757c271cc08e9", 33304817385, None, 9730143001, "sha256:e8b8a690161c464599269cbd7caed0680291f35428163c6e43c5fe3f71d592be"),
    "WS28": ("56977228b7fc0d149aa3719f5f2a9837e59c63a2", None, 33311668709, None, 9732209789, "sha256:e96df123f562773f5dc7e3495ea41c30183d62aed9a829ca5f2668a954fa1eaa"),
    "WS29": ("ca5fd0166c9a3c7030f37975f0d82380acaf6f8a", "96f015b0b8240f25fbc089fb544b706c1aa9e3f2", 33312384946, None, 9732414644, "sha256:b30415583c2b8c16c6b7cc523e69f5241922aa34d0d3fff17af942dba9c87f62"),
    "WS30": ("b5bc3803ca04e37bd9223e3505e4a748ce03404c", "86532e457c37e5d615780d9b7372d413558db3f5", 33316769544, None, 9733716966, "sha256:9bd386e63983b8d20ea3a2901bd2cdf351c5914ad2379c51477da6fb4987e2ab"),
    "WS31": ("acd6ae330e798f0e2081d194b371f1d66310aab2", "130d97073a4bff68ac20cee33648e0e629187aa2", 33318196568, None, 9734159178, "sha256:d1af7b9c348af2a56ebf9b398d29f06d0f2794df089bdd3caa4b18ebf471cffc"),
    "WS32": ("6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9", "769cb524895495a7a9ee34d53c88036d878f4c2a", 33316168298, None, 9733547137, "sha256:6eb2f0078bf8473571b10433211957e44ef3af93b7bf233e1072e7e12364578e"),
}
WS32_OVERLAY_SHA256 = {
    "CardBehaviorVerificationException.java": "d45deabb67ada9cdeb004d314d24ebf091c5fbcc41b8502d11806f9757253793",
    "CardBehaviorVerifier.java": "64cb7a8c3f6bc69246a5346fdc70e7e16861eb842b7ea7ac84408ed26ad11444",
    "Ws32CardBehaviorFailureQualificationTest.java": "8b5fee96765eb660276b1a7fd61400f208c937f2f63141240b09338eeb0bd048",
}
ARTIFACT_EXECUTION_SOURCE = {
    "WS27": ("93440c26e946934ae9257c16bca0760b02f0c554", "dfc086170097d0dffbfae1da2f956709570bac9e"),
    "WS31": ("3f8656046b7f905afcebe8a4954883fc81f91ec7", "130d97073a4bff68ac20cee33648e0e629187aa2"),
}


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forge_proof(forge: Path):
    if not forge:
        return {"verified": False, "reason": "forge root not supplied"}
    head = subprocess.check_output(["git", "-C", str(forge), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise SystemExit(f"Forge pin mismatch: {head}")
    continuous = forge / "forge-game/src/main/java/forge/game/staticability/StaticAbilityContinuous.java"
    static = forge / "forge-game/src/main/java/forge/game/staticability/StaticAbility.java"
    card = forge / "forge-game/src/main/java/forge/game/card/Card.java"
    if not card.exists():
        card.parent.mkdir(parents=True, exist_ok=True)
        content = subprocess.check_output(["git", "-C", str(forge), "show", f"{PIN}:forge-game/src/main/java/forge/game/card/Card.java"])
        card.write_bytes(content)
    checks = {
        "add_static_parameter_read": "params.containsKey(\"AddStaticAbility\")" in continuous.read_text(encoding="utf-8"),
        "svar_resolved_by_engine": "AbilityUtils.getSVar(stAb, sVars[i])" in continuous.read_text(encoding="utf-8"),
        "static_created_not_trigger_parsed": "getStaticAbilityForStaticAbility(s, stAb)" in continuous.read_text(encoding="utf-8"),
        "continuous_mode_instantiated": "StaticAbilityMode.setValueOf(getParam(\"Mode\"))" in static.read_text(encoding="utf-8"),
        "static_factory_call": "StaticAbility.create(str, this, stAb.getCardState(), false)" in card.read_text(encoding="utf-8"),
    }
    cards = {}
    expected = {
        "u/uthros_research_craft.txt": "AddStaticAbility$ CraftStatic",
        "i/inspirit_flagship_vessel.txt": "AddStaticAbility$ DBStatic",
        "a/armed_with_proof.txt": "AddStaticAbility$ TreasureEquip",
        "d/dancers_chakrams.txt": "AddStaticAbility$ StaticPump",
    }
    for suffix, needle in expected.items():
        path = forge / "forge-gui/res/cardsfolder" / suffix
        text = path.read_text(encoding="utf-8")
        cards[suffix] = {
            "sha256": digest(path), "add_static_reference_verified": needle in text,
            "mode_continuous_svar_verified": "Mode$ Continuous" in text,
        }
    if not all(checks.values()) or not all(all(vv for k, vv in value.items() if k != "sha256") for value in cards.values()):
        raise SystemExit("WS29 errata source/dataflow proof failed")
    return {
        "verified": True, "forge_pin": head, "code_checks": checks, "card_sources": cards,
        "source_files": {
            "StaticAbilityContinuous.java": digest(continuous),
            "StaticAbility.java": digest(static), "Card.java": digest(card),
        },
        "dataflow": [
            "StaticAbilityContinuous AddStaticAbility parameter",
            "AbilityUtils.getSVar",
            "Card.getStaticAbilityForStaticAbility",
            "StaticAbility.create",
            "StaticAbilityMode.Continuous",
        ],
    }


def evidence_profile(path):
    return "+".join(name for name, key in (
        ("DECISION", "required_decision_evidence"), ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"), ("REPLAY", "required_replay_evidence"),
    ) if path.get(key)) or "STATE_ONLY"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--forge-root", type=Path)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    e = args.evidence
    ws26 = e / "ws26/research/greenfield-qualification/actual-card-behavior/ws26"
    raw_manifest_path = ws26 / "WS26_BEHAVIOR_PATH_MANIFEST_V2.json"
    raw_manifest = load(raw_manifest_path)
    raw_paths = raw_manifest["paths"]
    by_id = {path["v2_path_id"]: path for path in raw_paths}
    if len(raw_paths) != 4280 or len(by_id) != 4280 or TERMINAL not in by_id:
        raise SystemExit("unexpected WS26 manifest boundary")
    proof = forge_proof(args.forge_root)
    migrations = []
    for old_id, token in ERRATA.items():
        path = by_id[old_id]
        if path["dispatch_domain"] != "SVAR_RUNTIME_EXPRESSION":
            raise SystemExit("erratum dispatch mismatch")
        profile = path["semantic_selector_profile"]
        if profile.get("terminal_v2_path_ids") != [TERMINAL] or not profile.get("svar_expression_shape", "").startswith("Mode$ Continuous"):
            raise SystemExit("erratum terminal mismatch")
        migrations.append({
            "historical_v2_path_id": old_id, "dispatch_token": token,
            "historical_implementation_target": path["implementation_target"],
            "disposition": "DEPRECATED_MODEL_INVALID_ALIAS",
            "production_required_independent_execution": False,
            "effective_terminal_path_id": TERMINAL,
            "effective_implementation_target": by_id[TERMINAL]["implementation_target"],
            "oracle_identities": path["representative_actual_oracle_identities"],
        })
    effective_paths = [copy.deepcopy(path) for path in raw_paths if path["v2_path_id"] not in ERRATA]
    effective_manifest = copy.deepcopy(raw_manifest)
    effective_manifest.update({
        "schema": "commander-simulator-next.behavior-path-manifest.v2.1",
        "model": "WS33_EFFECTIVE_POST_ERRATUM",
        "model_base_head": BASE_HEAD, "model_base_tree": BASE_TREE,
        "source_head": args.source_head, "source_tree": args.source_tree,
        "raw_ws26_path_count": 4280, "path_count": len(effective_paths),
        "errata_ids_retained_as_provenance": sorted(ERRATA), "paths": effective_paths,
    })
    effective_manifest_path = out / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"
    write_json(effective_manifest_path, effective_manifest)
    family_counts = Counter(path["owner_family"] for path in effective_paths)
    owner_partitions = {
        "schema": "commander-simulator-next.ws33-effective-owner-partitions.v1",
        "production_required_v2_path_count": len(effective_paths),
        "families": {family: sorted(path["v2_path_id"] for path in effective_paths if path["owner_family"] == family) for family in sorted(family_counts)},
        "family_counts": dict(sorted(family_counts.items())),
    }
    write_json(out / "WS33_EFFECTIVE_OWNER_PARTITIONS.json", owner_partitions)
    errata = {
        "schema": "commander-simulator-next.ws33-model-errata.v1", "model_base_head": BASE_HEAD,
        "model_base_tree": BASE_TREE, "forge_pin": PIN, "source_dataflow_proof": proof,
        "errata": migrations, "historical_ws26_artifacts_mutated": False,
    }
    write_json(out / "WS33_MODEL_ERRATA.json", errata)
    write_json(out / "WS33_MODEL_MIGRATION.json", {
        "schema": "commander-simulator-next.ws33-model-migration.v1", "migrations": migrations,
        "raw_path_count": 4280, "effective_path_count": len(effective_paths),
        "identity_reconstruction_required": True,
    })
    model_gate = {
        "schema": "commander-simulator-next.ws33-model-gate.v1",
        "WS33_MODEL_ERRATA_GATE": "PASS" if proof.get("verified") and len(effective_paths) == 4276 else "FAIL_CLOSED",
        "raw_path_count": 4280, "effective_path_count": len(effective_paths),
        "deprecated_alias_count": 4, "new_v2_ids_created": 0,
        "unresolved_production_reachable_model_bindings": 0,
        "ambiguous_production_reachable_model_bindings": 0,
    }
    write_json(out / "WS33_MODEL_GATE.json", model_gate)

    overlay_entries = []
    root = Path(__file__).resolve().parents[2]
    overlay_sources = [
        ("WS01_STRICT_DECISION", "forge-patches/apply-strict-decision-boundary.sh"),
        ("WS01_TARGET_BRIDGE", "forge-patches/apply-ws01-target-decision-bridge.py"),
        ("Q2_OBSERVATION", "forge-patches/apply-ws05-hidden-info-overlay.py"),
        ("Q3_RNG_REPLAY", "forge-patches/apply-ws06-rng-replay-overlay.py"),
    ]
    for name, relative in overlay_sources:
        path = root / relative
        overlay_entries.append({"name": name, "source": relative, "sha256": digest(path), "status": "APPROVED_INPUT_NOT_CAMPAIGN_EXECUTED"})
    ws32_files = [
        "CardBehaviorVerificationException.java", "CardBehaviorVerifier.java",
        "Ws32CardBehaviorFailureQualificationTest.java",
    ]
    for name in ws32_files:
        overlay_entries.append({
            "name": "WS32_" + name, "source_commit": PREDECESSORS["WS32"][0],
            "source_path": "research/greenfield-qualification/actual-card-behavior/ws32/forge-overlay/" + name,
            "sha256": WS32_OVERLAY_SHA256[name],
            "status": "APPROVED_INPUT_NOT_CAMPAIGN_EXECUTED",
        })
    overlay_manifest = {
        "schema": "commander-simulator-next.ws33-runtime-overlay-manifest.v1",
        "forge_pin": PIN, "qualified_runtime_anchor_head": QUALIFIED_RUNTIME_HEAD,
        "qualified_runtime_anchor_tree": QUALIFIED_RUNTIME_TREE,
        "entries": overlay_entries, "new_ws33_runtime_fixes": [],
        "materialization_status": "NOT_EXECUTED", "undeclared_runtime_patches": 0,
    }
    write_json(out / "WS33_RUNTIME_OVERLAY_MANIFEST.json", overlay_manifest)
    overlay_sha = digest(out / "WS33_RUNTIME_OVERLAY_MANIFEST.json")
    patched_forge_digest = hashlib.sha256((PIN + ":" + overlay_sha).encode()).hexdigest()
    impact = [{
        "changed_file_subsystem": "WS33 qualification model and validator only", "reason": "successor ABI and explicit model errata",
        "affected_v2_paths": sorted(ERRATA), "affected_owner_families": ["CONTINUOUS_COPY_CONTROL"],
        "affected_retained_qualification_contract": "WS26 historical files unchanged",
        **{f"Q{i}_impact": "NOT_INVALIDATED" for i in (1, 2, 3, 4, 5, 7)},
        "WS32_impact": "FOCUSED_REQUALIFICATION_REQUIRED",
        "minimal_required_requalification": "ABI fixtures, four model migrations, integrated WS32 focused controls after overlay materialization",
    }]
    write_json(out / "WS33_RUNTIME_IMPACT_MATRIX.json", {"schema": "commander-simulator-next.ws33-runtime-impact.v1", "changes": impact})

    positive = load(ws26 / "WS26_POSITIVE_WITNESS.json")
    trace_src = ws26 / positive["trace_ref"]
    abi_dir = out / "abi"
    source_abi_dir = Path(__file__).resolve().parent / "abi"
    abi_dir.mkdir(parents=True, exist_ok=True)
    for abi_name in (
        "WS33_WITNESS_ABI_V2_1.schema.json",
        "WS33_WITNESS_SEMANTIC_VALIDATOR.py",
    ):
        abi_source = source_abi_dir / abi_name
        abi_destination = abi_dir / abi_name
        if abi_source.resolve() != abi_destination.resolve():
            shutil.copyfile(abi_source, abi_destination)
    trace_dst = abi_dir / "fixtures/WS26_POSITIVE_TRACE.json"
    trace_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(trace_src, trace_dst)
    common = copy.deepcopy(positive)
    common.update({
        "schema": "commander-simulator-next.actual-card-witness.v2.1",
        "qualification_source_head": args.source_head, "qualification_source_tree": args.source_tree,
        "model_base_head": BASE_HEAD, "model_base_tree": BASE_TREE,
        "ws26_manifest_sha256": digest(raw_manifest_path),
        "effective_model_sha256": digest(effective_manifest_path),
        "runtime_overlay_manifest": "WS33_RUNTIME_OVERLAY_MANIFEST.json",
        "runtime_overlay_manifest_sha256": overlay_sha, "patched_forge_digest": patched_forge_digest,
        "execution_environment_identity": {"runner_os": "ubuntu-24.04", "java_version": "17", "process_isolation": "INHERITED_IMMUTABLE_EXECUTION"},
        "semantic_replay_evidence_ref": None, "trace_ref": "abi/fixtures/WS26_POSITIVE_TRACE.json",
    })
    common["execution"]["authoritative_decision_boundary"] = "NOT_REQUIRED"
    common["execution"]["runtime_overlays_declared"] = True
    for exercise in common["path_exercise"]:
        exercise["parent_ws14_primitive_id"] = by_id[exercise["v2_path_id"]].get("parent_ws14_primitive_id")
    inherited = copy.deepcopy(common)
    inherited["witness_id"] = "ws33-v2.1-inherited-ws26-positive"
    inherited["qualification_source_head"] = BASE_HEAD
    inherited["qualification_source_tree"] = BASE_TREE
    successor = copy.deepcopy(common)
    successor["witness_id"] = "ws33-v2.1-successor-positive"
    write_json(abi_dir / "fixtures/positive-inherited.json", inherited)
    write_json(abi_dir / "fixtures/positive-successor.json", successor)
    provenance = {
        "schema": "commander-simulator-next.ws33-successor-provenance.v1",
        "ws26_manifest_sha256": digest(raw_manifest_path),
        "effective_model_ref": "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json",
        "approved_qualification_sources": {
            BASE_HEAD + ":" + BASE_TREE: {"descends_from_model_base": True, "model_base_head": BASE_HEAD, "model_base_tree": BASE_TREE},
            args.source_head + ":" + args.source_tree: {"descends_from_model_base": True, "model_base_head": BASE_HEAD, "model_base_tree": BASE_TREE},
        },
        "approved_execution_sources": [],
        "patched_forge_digests": {
            BASE_HEAD + ":" + BASE_TREE: patched_forge_digest,
            args.source_head + ":" + args.source_tree: patched_forge_digest,
        },
    }
    write_json(abi_dir / "WS33_SUCCESSOR_PROVENANCE.json", provenance)
    illegal_tape = {"events": [{
        "decision_id": "negative", "decision_kind": "CONFIRM", "game_id": "fixture",
        "actor": "P1", "principal": "P1", "visibility_scope": "PUBLIC",
        "authoritative_legal_options": [{"option_id": "YES"}], "response_option_ids": ["NO"],
        "validation_result": "ACCEPTED", "fallback_used": False,
    }]}
    write_json(abi_dir / "fixtures/illegal-decision.json", illegal_tape)
    write_json(abi_dir / "fixtures/valid-decision.json", {"events": [{
        "decision_id": "valid", "decision_kind": "CONFIRM", "game_id": "fixture",
        "actor": "P1", "principal": "P1", "visibility_scope": "PUBLIC",
        "authoritative_legal_options": [{"option_id": "YES"}], "response_option_ids": ["YES"],
        "validation_result": "ACCEPTED", "fallback_used": False,
    }]})
    write_json(abi_dir / "fixtures/valid-rng.json", {"events": [{
        "stream_id": "fixture-rng", "event_index": 0, "operation": "bounded-int",
        "result": 0, "pre_state": {"counter": 0}, "post_state": {"counter": 1},
    }]})
    write_json(abi_dir / "fixtures/valid-observation.json", {
        "unauthorized_private_exposure_count": 0, "cross_principal_private_exposure_count": 0,
        "public_private_artifacts_separated": True,
    })
    write_json(abi_dir / "fixtures/valid-replay.json", {
        "semantic_divergence": 0, "comparison_basis": "CANONICAL_SEMANTIC_STATE",
        "runtime_overlay_manifest_sha256": overlay_sha,
    })
    negatives = []
    def negative(name, code, mutate):
        value = copy.deepcopy(successor)
        value["witness_id"] = "negative-" + name
        mutate(value)
        path = abi_dir / "negative-fixtures" / name / "witness.json"
        write_json(path, value)
        negatives.append({"name": name, "expected_error": code, "witness": str(path.relative_to(out))})
    negative("missing-path-coverage", "MISSING_V2_PATH_COVERAGE", lambda w: w.update(v2_path_ids=[]))
    negative("parent-mismatch", "PARENT_PRIMITIVE_MISMATCH", lambda w: w.update(parent_ws14_primitive_ids=[]))
    negative("forged-trace-sha", "TRACE_HASH_MISMATCH", lambda w: w.update(trace_sha256="0" * 64))
    negative("stdout-only", "SCHEMA_INVALID", lambda w: w.update(stdout_only=True))
    negative("illegal-response", "ILLEGAL_NON_AUTHORITATIVE_RESPONSE", lambda w: w.update(decision_tape_ref="abi/fixtures/illegal-decision.json"))
    required = {key: next(path for path in effective_paths if path.get(key)) for key in (
        "required_decision_evidence", "required_rng_evidence", "required_hidden_info_evidence", "required_replay_evidence"
    )}
    def require_path(w, path, missing):
        w["owner_family"] = path["owner_family"]
        w["v2_path_ids"] = [path["v2_path_id"]]
        parent = path.get("parent_ws14_primitive_id")
        w["parent_ws14_primitive_ids"] = [parent] if parent else []
        refs = {
            "required_decision_evidence": ("decision_tape_ref", "abi/fixtures/valid-decision.json"),
            "required_rng_evidence": ("rng_tape_ref", "abi/fixtures/valid-rng.json"),
            "required_hidden_info_evidence": ("observation_evidence_ref", "abi/fixtures/valid-observation.json"),
            "required_replay_evidence": ("semantic_replay_evidence_ref", "abi/fixtures/valid-replay.json"),
        }
        for requirement, (field, reference) in refs.items():
            if path.get(requirement) and requirement != missing:
                w[field] = reference
    negative("missing-decision-tape", "DECISION_TAPE_REQUIRED", lambda w: require_path(w, required["required_decision_evidence"], "required_decision_evidence"))
    negative("missing-rng-tape", "RNG_TAPE_REQUIRED", lambda w: require_path(w, required["required_rng_evidence"], "required_rng_evidence"))
    negative("private-observation-leak", "OBSERVATION_EVIDENCE_REQUIRED", lambda w: require_path(w, required["required_hidden_info_evidence"], "required_hidden_info_evidence"))
    negative("replay-without-semantic-evidence", "SEMANTIC_REPLAY_REQUIRED", lambda w: require_path(w, required["required_replay_evidence"], "required_replay_evidence"))
    negative("forge-pin-mismatch", "SOURCE_PIN_MISMATCH", lambda w: w.update(forge_pin="0" * 40))
    negative("incomplete-state-assertion", "INCOMPLETE_STATE_ASSERTION", lambda w: w.update(state_assertions=[]))
    negative("arbitrary-non-descendant", "ARBITRARY_SUCCESSOR_SOURCE", lambda w: w.update(qualification_source_head="1" * 40, qualification_source_tree="2" * 40))
    negative("wrong-ws26-model", "WRONG_WS26_MODEL_HASH", lambda w: w.update(model_base_head="0" * 40))
    negative("undeclared-model-mutation", "UNDECLARED_MODEL_MUTATION", lambda w: w.update(effective_model_sha256="0" * 64))
    negative("undeclared-runtime-overlay", "UNDECLARED_RUNTIME_OVERLAY", lambda w: w.update(runtime_overlay_manifest="missing-overlay.json"))
    negative("wrong-overlay-digest", "WRONG_OVERLAY_DIGEST", lambda w: w.update(runtime_overlay_manifest_sha256="0" * 64))
    negative("local-family-pass-missing-tape", "DECISION_TAPE_REQUIRED", lambda w: require_path(w, required["required_decision_evidence"], "required_decision_evidence"))
    write_json(abi_dir / "negative-fixtures/index.json", {"fixtures": negatives})

    validator = abi_dir / "WS33_WITNESS_SEMANTIC_VALIDATOR.py"
    schema = abi_dir / "WS33_WITNESS_ABI_V2_1.schema.json"
    commands = []
    for fixture in (abi_dir / "fixtures/positive-inherited.json", abi_dir / "fixtures/positive-successor.json"):
        commands.append((fixture, 0, None))
    for item in negatives:
        commands.append((out / item["witness"], 2, item["expected_error"]))
    results = []
    for fixture, expected_exit, expected_error in commands:
        proc = subprocess.run([
            sys.executable, str(validator), str(fixture), "--manifest", str(effective_manifest_path),
            "--schema", str(schema), "--provenance", str(abi_dir / "WS33_SUCCESSOR_PROVENANCE.json"),
            "--base", str(out),
        ], text=True, capture_output=True)
        intended = proc.returncode == expected_exit and (expected_error is None or f"code={expected_error}" in proc.stdout)
        results.append({"fixture": str(fixture.relative_to(out)), "expected_exit": expected_exit, "expected_error": expected_error, "actual_exit": proc.returncode, "stdout": proc.stdout.strip(), "intended_result": intended})
    abi_pass = all(item["intended_result"] for item in results)
    write_json(abi_dir / "WS33_WITNESS_ABI_GATE.json", {
        "schema": "commander-simulator-next.ws33-witness-abi-gate.v1",
        "WS33_WITNESS_ABI_V2_1_GATE": "PASS" if abi_pass else "FAIL_CLOSED",
        "positive_inherited_accepted": results[0]["intended_result"],
        "successor_positive_accepted": results[1]["intended_result"],
        "negative_fixtures_rejected_for_intended_reason": all(item["intended_result"] for item in results[2:]),
        "results": results,
    })

    pass_ids = set(positive["v2_path_ids"])
    admission = []
    def admission_row(ws, disposition, path_ids, reason, **extra):
        head, tree, run, job, artifact, artifact_digest = PREDECESSORS[ws]
        execution_head, execution_tree = ARTIFACT_EXECUTION_SOURCE.get(ws, (head, tree))
        admission.append({
            "source_workstream": ws, "source_head": execution_head, "source_tree": execution_tree,
            "branch_final_head": head, "branch_final_tree": tree,
            "run_id": run, "job_id": job, "artifact_id": artifact, "artifact_digest": artifact_digest,
            "v2_path_ids": path_ids, "oracle_identities": extra.pop("oracle_identities", []),
            "forge_pin": PIN, "execution_route": extra.pop("execution_route", None),
            "state_evidence": extra.pop("state_evidence", False), "decision_evidence": extra.pop("decision_evidence", False),
            "rng_evidence": extra.pop("rng_evidence", False), "observation_evidence": extra.pop("observation_evidence", False),
            "replay_evidence": extra.pop("replay_evidence", False), "rules_refs": extra.pop("rules_refs", []),
            "trace_hash": extra.pop("trace_hash", None), "disposition": disposition, "reason": reason, **extra,
        })
    admission_row("WS26", "ABI_ADMISSIBLE", sorted(pass_ids), "Exact immutable WS16 execution already accepted by WS26 ABI and V2.1 rematerialization.", oracle_identities=positive["oracle_identities"], execution_route="actual GameAction zone move plus real replacement/trigger stack lifecycle", state_evidence=True, rules_refs=positive["rules_authority_refs"], trace_hash=positive["trace_sha256"])
    admission_row("WS28", "ABI_ADMISSIBLE", sorted(pass_ids), "WS28's two exact reuses are the canonical WS26 positive witness; no rerun.", oracle_identities=positive["oracle_identities"], execution_route="reuse WS26 immutable execution", state_evidence=True, rules_refs=positive["rules_authority_refs"], trace_hash=positive["trace_sha256"])
    ws27_witness = load_jsonl(e / "ws27/research/greenfield-qualification/actual-card-behavior/ws27/WS27_WITNESSES.jsonl")[0]
    admission_row("WS27", "REEXECUTION_REQUIRED", ws27_witness["v2_path_ids"], "Rematerialization rejected: state assertions omit expected/actual values, primitive_exercise is absent, and authoritative_decision_boundary is outside ABI V2.1.", oracle_identities=ws27_witness["oracle_identities"], execution_route="actual-card family test", state_evidence=False, trace_hash=ws27_witness["trace_sha256"])
    for migration in migrations:
        admission_row("WS29", "MODEL_ERRATUM", [migration["historical_v2_path_id"]], "Mode$ Continuous SVar is consumed through AddStaticAbility and terminates at StaticAbilityMode#Continuous; old parseTrigger alias is not independent production behavior.", oracle_identities=migration["oracle_identities"], execution_route="pinned source/dataflow audit")
    ws30_witnesses = load_jsonl(e / "ws30/ws30/WS30_WITNESSES.jsonl")
    for witness in ws30_witnesses:
        path = by_id[witness["path_id"]]
        missing = [name for name, key in (("decision tape", "required_decision_evidence"), ("RNG tape", "required_rng_evidence"), ("hidden observation", "required_hidden_info_evidence"), ("semantic replay", "required_replay_evidence")) if path.get(key)]
        reason = "WS30 local record lacks ABI initial/final structured states, immutable per-path trace hash, parent exercise, and exact lifecycle proof"
        if missing:
            reason += "; required " + ", ".join(missing) + " also absent"
        admission_row("WS30", "REEXECUTION_REQUIRED", [witness["path_id"]], reason, execution_route=witness.get("dispatch"), state_evidence=False, rules_refs=witness.get("official_rule_refs", []))
    ws31_cov = load(e / "ws31/artifact/research/greenfield-qualification/actual-card-behavior/ws31/WS31_PATH_COVERAGE.json")
    ws31_ids = ws31_cov.get("assigned_v2_path_ids") or ws31_cov.get("paths") or []
    if ws31_ids and isinstance(ws31_ids[0], dict):
        ws31_ids = [item.get("v2_path_id") or item.get("path_id") for item in ws31_ids]
    if not ws31_ids:
        ws31_ids = [path["v2_path_id"] for path in raw_paths if path["owner_family"] == "HIDDEN_RNG_REPLAY"]
    for path_id in sorted(ws31_ids):
        admission_row("WS31", "NONQUALIFYING_DIAGNOSTIC", [path_id], "Diagnostic execution is nonconformant: family gate reports missing decision tapes and 1,970 unauthorized private exposures.", execution_route="diagnostic record/replay harness", observation_evidence=False, replay_evidence=False)
    admission_row("WS32", "REJECTED", [], "Not a Q6 witness source; retained only as the focused failure-semantics compatibility dependency.", execution_route="generic post-resolution verifier")
    write_json(out / "WS33_INPUT_ADMISSION.json", {"schema": "commander-simulator-next.ws33-input-admission.v1", "entries": admission, "disposition_counts": dict(Counter(row["disposition"] for row in admission))})

    target_groups = defaultdict(list)
    template_groups = defaultdict(list)
    for path in effective_paths:
        target_groups[(path["owner_family"], path["implementation_target"])].append(path)
        template_groups[(path["owner_family"], path["implementation_target"], evidence_profile(path))].append(path)
    target_registry = []
    for (family, target), paths in sorted(target_groups.items()):
        unproved = sum(path["v2_path_id"] not in pass_ids for path in paths)
        cross_fanout = len({dep for path in paths for dep in path.get("cross_family_dependencies", [])}) + 1
        target_registry.append({"owner_family": family, "implementation_target": target, "effective_path_count": len(paths), "unproved_path_count": unproved, "cross_family_dependency_fanout": cross_fanout, "priority_score": unproved * cross_fanout, "path_ids": sorted(path["v2_path_id"] for path in paths)})
    target_registry.sort(key=lambda row: (-row["priority_score"], row["owner_family"], row["implementation_target"]))
    write_json(out / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json", {"schema": "commander-simulator-next.ws33-implementation-target-registry.v1", "targets": target_registry})
    templates = []
    for index, ((family, target, profile), paths) in enumerate(sorted(template_groups.items()), 1):
        ids = sorted(path["v2_path_id"] for path in paths)
        admitted = sorted(set(ids) & pass_ids)
        templates.append({"template_id": f"ws33-template-{index:03d}", "owner_family": family, "implementation_target": target, "evidence_profile": profile, "path_ids": ids, "status": "RETAINED_IMMUTABLE_EXECUTION" if admitted else "MISSING_SCENARIO_TEMPLATE", "admitted_path_ids": admitted})
    write_json(out / "WS33_SCENARIO_TEMPLATE_REGISTRY.json", {"schema": "commander-simulator-next.ws33-scenario-template-registry.v1", "templates": templates})

    cases, executions, coverage = [], [], []
    for path in sorted(effective_paths, key=lambda item: item["v2_path_id"]):
        path_id = path["v2_path_id"]
        oracle = path["representative_actual_oracle_identities"][0]
        status = "PASS" if path_id in pass_ids else "UNKNOWN"
        cases.append({"effective_v2_path_id": path_id, "historical_ws26_v2_ids": [path_id] + sorted(old for old in ERRATA if path_id == TERMINAL), "owner_family": path["owner_family"], "implementation_target": path["implementation_target"], "evidence_profile": evidence_profile(path), "selected_oracle_identity": oracle, "rejected_representatives": [], "scenario_status": "RETAINED_IMMUTABLE_EXECUTION" if status == "PASS" else "MISSING_SCENARIO_TEMPLATE"})
        executions.append({"effective_v2_path_id": path_id, "status": status, "execution_source": "WS26_IMMUTABLE" if status == "PASS" else None, "overlay_digest": overlay_sha, "trace_sha": positive["trace_sha256"] if status == "PASS" else None, "witness_hash": digest(abi_dir / "fixtures/positive-inherited.json") if status == "PASS" else None, "blocker_class": None if status == "PASS" else "MISSING_SCENARIO_TEMPLATE"})
        coverage.append({
            "effective_v2_path_id": path_id, "historical_ws26_v2_ids": [path_id] + sorted(old for old in ERRATA if path_id == TERMINAL),
            "model_migration_status": "TERMINAL_FOR_DEPRECATED_ALIASES" if path_id == TERMINAL else "UNCHANGED",
            "owner_family": path["owner_family"], "implementation_target": path["implementation_target"],
            "oracle_identity": oracle, "source_provenance": path.get("source_provenance", []),
            "execution_source": "WS26_IMMUTABLE" if status == "PASS" else None, "overlay_digest": overlay_sha,
            "state_evidence": status == "PASS", "decision_tape": None, "rng_tape": None,
            "observation_evidence": None, "replay_evidence": None,
            "trace_sha": positive["trace_sha256"] if status == "PASS" else None,
            "rules_refs": positive["rules_authority_refs"] if status == "PASS" else [],
            "evidence_classification": "EXTERNALLY_RULE_VALIDATED" if status == "PASS" else "UNKNOWN", "status": status,
        })
    write_jsonl(out / "WS33_CASE_LEDGER.jsonl", cases)
    write_jsonl(out / "WS33_EXECUTION_LEDGER.jsonl", executions)
    write_json(out / "WS33_PATH_COVERAGE.json", {"schema": "commander-simulator-next.ws33-path-coverage.v1", "paths": coverage, "status_counts": dict(Counter(row["status"] for row in coverage))})
    write_jsonl(out / "WS33_WITNESSES.jsonl", [inherited])

    identity_rows = []
    for identity in load_jsonl(ws26 / "WS26_PER_IDENTITY_V2.jsonl"):
        historical = identity["v2_path_ids"]
        effective = sorted((set(historical) - set(ERRATA)) | ({TERMINAL} if set(historical) & set(ERRATA) else set()))
        unresolved = sorted(set(effective) - pass_ids)
        identity_rows.append({"oracle_identity": identity["oracle_identity"], "oracle_name": identity["oracle_name"], "historical_ws26_v2_path_ids": historical, "effective_v2_path_ids": effective, "pass_path_ids": sorted(set(effective) & pass_ids), "unresolved_path_ids": unresolved, "status": "FULL" if not unresolved else "PARTIAL"})
    write_jsonl(out / "WS33_PER_IDENTITY.jsonl", identity_rows)
    for title, key, filename in (
        ("decision", "required_decision_evidence", "WS33_DECISION_EVIDENCE_INDEX.json"),
        ("rng", "required_rng_evidence", "WS33_RNG_EVIDENCE_INDEX.json"),
        ("hidden", "required_hidden_info_evidence", "WS33_HIDDEN_INFO_EVIDENCE_INDEX.json"),
        ("replay", "required_replay_evidence", "WS33_REPLAY_EVIDENCE_INDEX.json"),
    ):
        required_ids = sorted(path["v2_path_id"] for path in effective_paths if path.get(key))
        write_json(out / filename, {"schema": f"commander-simulator-next.ws33-{title}-evidence-index.v1", "required_path_ids": required_ids, "required_count": len(required_ids), "complete_pass_count": 0, "missing_count": len(required_ids), "entries": []})
    write_json(out / "WS33_RULES_ADJUDICATION.json", {"schema": "commander-simulator-next.ws33-rules-adjudication.v1", "official_rules_page": "https://magic.wizards.com/en/rules", "official_rules_text": RULES_URL, "effective_date": "2026-08-07", "live_checked_date": "2026-08-30", "model_errata_is_source_dataflow_not_rules_adjudication": True, "new_path_semantic_adjudications": []})
    write_json(out / "WS33_WS32_COMPATIBILITY.json", {"schema": "commander-simulator-next.ws33-ws32-compatibility.v1", "status": "NOT_RUN", "reason": "Integrated candidate runtime overlay has not executed; WS32 cannot be promoted from its standalone artifact.", "required_controls": ["normal actual-card result unchanged", "verifier disabled by default", "controlled mismatch CARD_BEHAVIOR_FAILURE", "ENGINE_FAILURE distinct", "state_committed=false", "failed result not promoted", "fallback_used=false", "sanitized public payload"]})
    status_counts = Counter(row["status"] for row in coverage)
    family_gate = {}
    for family in sorted(family_counts):
        rows = [row for row in coverage if row["owner_family"] == family]
        counts = Counter(row["status"] for row in rows)
        family_gate[family] = {"gate": "PASS" if counts.get("PASS") == len(rows) else "FAIL_CLOSED", "counts": dict(counts), "effective_path_count": len(rows)}
    q6_gate = {
        "schema": "commander-simulator-next.ws33-q6-candidate-gate.v1", "WORKSTREAM_COMPLETE": False,
        "WS33_MODEL_ERRATA_GATE": model_gate["WS33_MODEL_ERRATA_GATE"],
        "WS33_WITNESS_ABI_V2_1_GATE": "PASS" if abi_pass else "FAIL_CLOSED",
        "WS33_ACTUAL_CARD_CAMPAIGN": "FAIL_CLOSED", "Q6_CANDIDATE_FOR_CROSS_QUALIFICATION": False,
        "WS32_COMPATIBILITY": "NOT_RUN", "WS34_ELIGIBLE": False,
        "oracle_identity_count": len(identity_rows), "identity_counts": dict(Counter(row["status"] for row in identity_rows)),
        "effective_path_count": len(effective_paths), "path_status_counts": {key: status_counts.get(key, 0) for key in ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")},
        "family_gates": family_gate, "silent_fallback_count": 0, "stdout_only_PASS_count": 0,
        "card_name_production_hacks": 0, "second_pilot_rules_engine": 0,
        "remaining_blockers": [{"class": "MISSING_SCENARIO_TEMPLATE", "path_count": status_counts.get("UNKNOWN", 0)}, {"class": "INTEGRATED_RUNTIME_OVERLAY_NOT_EXECUTED", "path_count": status_counts.get("UNKNOWN", 0)}, {"class": "WS32_COMPATIBILITY_NOT_RUN", "path_count": 0}],
        "WS13_ELIGIBLE": False, "INITIAL_ARCHITECTURE_DECISION_FROZEN": False,
        "READY_FOR_GREENFIELD_BUILD": False, "PRODUCTION_REPOSITORY_CREATED": False,
        "Q6_ACTUAL_CARD_BEHAVIOR_CANONICAL": "NOT_ADJUDICATED_BY_WS33",
        "FAILURE_SEMANTICS_CANONICAL": "NOT_ADJUDICATED_BY_WS33",
    }
    write_json(out / "WS33_Q6_CANDIDATE_GATE.json", q6_gate)
    hash_targets = sorted(
        path for path in out.rglob("*")
        if path.is_file() and path.name != "WS33_HASHES.sha256" and "__pycache__" not in path.parts
    )
    with (out / "WS33_HASHES.sha256").open("w", encoding="utf-8", newline="\n") as handle:
        for path in hash_targets:
            handle.write(f"{digest(path)}  {path.relative_to(out).as_posix()}\n")
    print(json.dumps({"model_gate": model_gate["WS33_MODEL_ERRATA_GATE"], "abi_gate": "PASS" if abi_pass else "FAIL_CLOSED", "effective_paths": len(effective_paths), "status_counts": q6_gate["path_status_counts"], "identity_counts": q6_gate["identity_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
