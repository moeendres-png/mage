#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
BASE_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
BASE_TREE = "837f445f78bb26462653c58baf1532e294151b10"
OWNERS = {
    "ACTION_COST_DECISION", "TRIGGER_REPLACEMENT_ZONE_SBA",
    "CONTINUOUS_COPY_CONTROL", "COMBAT_COMMANDER", "HIDDEN_RNG_REPLAY",
}


class WitnessError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def fail(code: str, message: str) -> None:
    raise WitnessError(code, message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def option_ids(options):
    result = []
    for option in options or []:
        if isinstance(option, str):
            result.append(option)
        elif isinstance(option, dict):
            value = option.get("option_id") or option.get("id")
            if value is not None:
                result.append(value)
    return result


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def events(document):
    if isinstance(document, list):
        return document
    return document.get("events", []) if isinstance(document, dict) else []


def validate(witness, manifest, base: Path, schema, provenance) -> bool:
    try:
        jsonschema.Draft202012Validator(schema).validate(witness)
    except jsonschema.ValidationError as exc:
        fail("SCHEMA_INVALID", exc.message)

    if witness["model_base_head"] != BASE_HEAD or witness["model_base_tree"] != BASE_TREE:
        fail("WRONG_WS26_MODEL_HASH", "wrong WS26 model base")
    if witness["forge_pin"] != PIN or manifest.get("forge_pin") != PIN:
        fail("SOURCE_PIN_MISMATCH", "Forge pin mismatch")

    ws26_manifest = base / provenance["ws26_manifest_ref"]
    effective_model = base / provenance["effective_model_ref"]
    overlay_manifest = base / witness["runtime_overlay_manifest"]
    if sha256(ws26_manifest) != witness["ws26_manifest_sha256"]:
        fail("WRONG_WS26_MODEL_HASH", "WS26 manifest digest mismatch")
    if sha256(effective_model) != witness["effective_model_sha256"]:
        fail("UNDECLARED_MODEL_MUTATION", "effective model digest mismatch")
    if not overlay_manifest.is_file():
        fail("UNDECLARED_RUNTIME_OVERLAY", "runtime overlay manifest missing")
    if sha256(overlay_manifest) != witness["runtime_overlay_manifest_sha256"]:
        fail("WRONG_OVERLAY_DIGEST", "runtime overlay manifest digest mismatch")

    source_key = witness["qualification_source_head"] + ":" + witness["qualification_source_tree"]
    approved = provenance.get("approved_qualification_sources", {})
    source = approved.get(source_key)
    if not source or source.get("descends_from_model_base") is not True:
        fail("ARBITRARY_SUCCESSOR_SOURCE", "qualification source is not an approved descendant")
    if source.get("model_base_head") != BASE_HEAD or source.get("model_base_tree") != BASE_TREE:
        fail("WRONG_WS26_MODEL_HASH", "approved source is bound to another model base")

    declared_digest = provenance.get("patched_forge_digests", {}).get(source_key)
    if declared_digest != witness["patched_forge_digest"]:
        fail("UNDECLARED_RUNTIME_OVERLAY", "patched Forge digest is not declared for source")

    allowed_execution_sources = {(manifest["source_head"], manifest["source_tree"])}
    allowed_execution_sources.update(
        (item["head"], item["tree"]) for item in manifest.get("inherited_execution_sources", [])
    )
    allowed_execution_sources.update(
        (item["head"], item["tree"]) for item in provenance.get("approved_execution_sources", [])
    )
    if (witness["source_head"], witness["source_tree"]) not in allowed_execution_sources:
        fail("SOURCE_PIN_MISMATCH", "execution source is not immutable and approved")

    if witness["owner_family"] not in OWNERS:
        fail("OWNER_MISMATCH", "invalid owner family")
    paths = {path["v2_path_id"]: path for path in manifest.get("paths", [])}
    if not witness["v2_path_ids"]:
        fail("MISSING_V2_PATH_COVERAGE", "empty V2 coverage")
    for path_id in witness["v2_path_ids"]:
        if path_id not in paths:
            fail("MISSING_V2_PATH_COVERAGE", "unknown V2 path " + path_id)
        path = paths[path_id]
        if path["owner_family"] != witness["owner_family"]:
            fail("OWNER_MISMATCH", path_id)
        parent = path.get("parent_ws14_primitive_id")
        if parent and parent not in witness["parent_ws14_primitive_ids"]:
            fail("PARENT_PRIMITIVE_MISMATCH", path_id)
        if path.get("required_decision_evidence") and not witness["decision_tape_ref"]:
            fail("DECISION_TAPE_REQUIRED", path_id)
        if path.get("required_rng_evidence") and not witness["rng_tape_ref"]:
            fail("RNG_TAPE_REQUIRED", path_id)
        if path.get("required_hidden_info_evidence") and not witness["observation_evidence_ref"]:
            fail("OBSERVATION_EVIDENCE_REQUIRED", path_id)
        if path.get("required_replay_evidence") and not witness["semantic_replay_evidence_ref"]:
            fail("SEMANTIC_REPLAY_REQUIRED", path_id)

    if witness["stdout_only"] is not False:
        fail("STDOUT_ONLY_FORBIDDEN", "stdout_only=true")
    if not witness["initial_semantic_state"] or not witness["final_semantic_state"] or not witness["state_assertions"]:
        fail("INCOMPLETE_STATE_ASSERTION", "state evidence missing")
    assertion_ids = set()
    for assertion in witness["state_assertions"]:
        if assertion.get("result") != "PASS" or "expected" not in assertion or "actual" not in assertion:
            fail("INCOMPLETE_STATE_ASSERTION", "assertion incomplete")
        assertion_ids.add(assertion["assertion_id"])
    exercised = {}
    for item in witness["path_exercise"]:
        if item.get("exercised") is True and item.get("trace_event_ids") and item.get("assertion_ids"):
            if not set(item["assertion_ids"]) <= assertion_ids:
                fail("INCOMPLETE_STATE_ASSERTION", "path references unknown assertion")
            exercised[item["v2_path_id"]] = item
    if not set(witness["v2_path_ids"]) <= set(exercised):
        fail("MISSING_V2_PATH_COVERAGE", "not every claimed path is exercised")
    for path_id, item in exercised.items():
        if item.get("parent_ws14_primitive_id") != paths[path_id].get("parent_ws14_primitive_id"):
            fail("PARENT_PRIMITIVE_MISMATCH", path_id)
    primitive_exercise = {
        item.get("primitive_id") for item in witness["primitive_exercise"] if item.get("exercised") is True
    }
    if not set(witness["parent_ws14_primitive_ids"]) <= primitive_exercise:
        fail("PARENT_PRIMITIVE_MISMATCH", "parent primitive not exercised")

    execution = witness["execution"]
    if execution.get("engine") != "pinned-forge" or execution.get("actual_rules_core_path") is not True:
        fail("NON_PRODUCTION_EXECUTION", "pinned Rules Core required")
    if execution.get("runtime_overlays_declared") is not True:
        fail("UNDECLARED_RUNTIME_OVERLAY", "execution did not declare overlay set")
    if execution.get("silent_fallbacks") != 0:
        fail("SILENT_FALLBACK", "silent fallback")
    if execution.get("authoritative_decision_boundary") not in {"USED", "NOT_REQUIRED"}:
        fail("DECISION_BOUNDARY_INVALID", "invalid boundary state")

    if witness["decision_tape_ref"]:
        decision_events = events(load(base / witness["decision_tape_ref"]))
        if not decision_events:
            fail("DECISION_TAPE_REQUIRED", "empty decision tape")
        for event in decision_events:
            legal = set(option_ids(event.get("authoritative_legal_options") or event.get("legal_options") or event.get("options")))
            response = as_list(event.get("response_option_ids", event.get("response", event.get("selected_option_ids"))))
            if event.get("validation_result", event.get("response_status")) not in {"PASS", "ACCEPTED"}:
                fail("ILLEGAL_NON_AUTHORITATIVE_RESPONSE", "response not accepted")
            if any(item not in legal for item in response):
                fail("ILLEGAL_NON_AUTHORITATIVE_RESPONSE", "response outside authoritative set")
            if event.get("fallback_used"):
                fail("SILENT_FALLBACK", "decision fallback used")
            for required in ("decision_id", "decision_kind", "game_id", "actor", "principal", "visibility_scope"):
                if required not in event:
                    fail("DECISION_TAPE_REQUIRED", "decision event missing " + required)

    if witness["rng_tape_ref"]:
        rng_events = events(load(base / witness["rng_tape_ref"]))
        if not rng_events:
            fail("RNG_TAPE_REQUIRED", "empty RNG tape")
        for event in rng_events:
            if not (event.get("stream_id") or event.get("stream")):
                fail("RNG_TAPE_REQUIRED", "unnamed RNG stream")
            for required in ("event_index", "operation", "result", "pre_state", "post_state"):
                if required not in event:
                    fail("RNG_TAPE_REQUIRED", "RNG event missing " + required)

    if witness["observation_evidence_ref"]:
        observation = load(base / witness["observation_evidence_ref"])
        leaks = max(
            observation.get("unauthorized_private_exposure_count", 0),
            observation.get("cross_principal_private_exposure_count", 0),
        )
        if leaks != 0:
            fail("HIDDEN_INFO_VIOLATION", "cross-principal private exposure")
        if observation.get("public_private_artifacts_separated") is not True:
            fail("HIDDEN_INFO_VIOLATION", "public/private evidence not separated")

    if witness["semantic_replay_evidence_ref"]:
        replay = load(base / witness["semantic_replay_evidence_ref"])
        if replay.get("semantic_divergence") != 0 or replay.get("comparison_basis") != "CANONICAL_SEMANTIC_STATE":
            fail("SEMANTIC_REPLAY_REQUIRED", "replay is not zero-divergence semantic replay")
        if replay.get("runtime_overlay_manifest_sha256") != witness["runtime_overlay_manifest_sha256"]:
            fail("WRONG_OVERLAY_DIGEST", "replay used another overlay")

    trace = base / witness["trace_ref"]
    if not trace.is_file() or sha256(trace) != witness["trace_sha256"]:
        fail("TRACE_HASH_MISMATCH", "trace hash mismatch")
    if witness["status"] == "PASS" and not witness["rules_authority_refs"]:
        fail("RULES_AUTHORITY_REQUIRED", "PASS lacks official rules authority")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("witness")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--base", default=".")
    args = parser.parse_args()
    base = Path(args.base)
    try:
        validate(
            load(Path(args.witness)), load(Path(args.manifest)), base,
            load(Path(args.schema)), load(Path(args.provenance)),
        )
        print("WS33_WITNESS_VALIDATION=PASS")
    except WitnessError as exc:
        print(f"WS33_WITNESS_VALIDATION=FAIL code={exc.code} message={exc}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
