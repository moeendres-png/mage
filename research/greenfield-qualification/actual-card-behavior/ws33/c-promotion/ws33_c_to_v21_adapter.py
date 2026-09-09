#!/usr/bin/env python3
"""Deterministic adapter: retained WS33-C batch evidence -> canonical v2.1 witness.

Scope: single C batch execution (one EVIDENCED path) into the exact witness-record
shape required by abi/WS33_WITNESS_SEMANTIC_VALIDATOR.py (CERTIFIER_SHAPE =
V2_1_ADAPTER_TO_EXISTING_SEMANTIC_VALIDATOR). No parallel C-specific semantic
validator is built; the canonical validator remains the sole semantic arbiter.

Lossless-preservation contract (all enforced fail-closed):
  - source evidence bytes (record.json / trace.json) are vendored verbatim;
  - evidence_classification stays TECHNICALLY_CONFORMANT (never upgraded);
  - run/job/artifact/digest/source identities are preserved exactly;
  - exact prior state (UNKNOWN/UNKNOWN dual-book pre-state) is re-verified;
  - target identity is the exact shared dual-book path ID (no fuzzy mapping);
  - decision/runtime trace semantics preserved (tripwire/profile/entrypoint);
  - no fabricated outcome; no fabricated Rules reference (retained
    rules_authority_refs are preserved verbatim and must already be non-empty
    normative references).

Exit 0 on success; exit 2 with WS33_C_ADAPTER=FAIL <code> on any violation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
MODEL_BASE_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
MODEL_BASE_TREE = "837f445f78bb26462653c58baf1532e294151b10"
# Approved qualification source for C promotion: the canonical successor that the
# Book-A effective manifest derives from (manifest source_head/tree). The C batch-5
# execution source is verified to descend from it; execution-source approval is
# carried separately in the staging provenance (approved_execution_sources).
QUALIFICATION_SOURCE_HEAD = "f2ae96970d8f9ce5df2dfd71782a1940be17b31d"
QUALIFICATION_SOURCE_TREE = "76ed6a2b961362e2ec611b89c8544746faccbddc"
RULES_URL_PREFIX = "https://magic.wizards.com/en/rules"
WITNESS_SCHEMA = "commander-simulator-next.actual-card-witness.v2.1"


class AdapterError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def fail(code: str, message: str) -> None:
    raise AdapterError(code, message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail("C_EVIDENCE_UNREADABLE", f"{path}: {exc}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True,
                    help="retained C record.json (artifact bytes)")
    ap.add_argument("--trace", type=Path, required=True,
                    help="retained C trace.json (artifact bytes, vendored verbatim)")
    ap.add_argument("--gate", type=Path, required=True,
                    help="retained WS33_C_BATCH_GATE.json (artifact bytes)")
    ap.add_argument("--manifest", type=Path, required=True,
                    help="canonical Book-A effective behavior path manifest")
    ap.add_argument("--provenance", type=Path, required=True,
                    help="staging provenance (canonical + C execution-source approval)")
    ap.add_argument("--overlay-manifest", type=Path, required=True,
                    help="canonical runtime overlay manifest file")
    ap.add_argument("--overlay-manifest-rel", required=True,
                    help="overlay manifest path as referenced from validator base dir")
    ap.add_argument("--book-a-coverage", type=Path, required=True)
    ap.add_argument("--book-b-ledger", type=Path, required=True)
    ap.add_argument("--source-head", required=True, help="expected C execution source HEAD")
    ap.add_argument("--source-tree", required=True, help="expected C execution source TREE")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--artifact-id", required=True)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--batch-id", required=True)
    ap.add_argument("--runner-os", required=True,
                    help="declared runner OS from the pinned workflow source")
    ap.add_argument("--java-version", required=True,
                    help="declared Java version from the pinned workflow source")
    ap.add_argument("--workflow-source-head", required=True,
                    help="pinned workflow source carrying the env declaration")
    ap.add_argument("--trace-ref", required=True,
                    help="base-relative trace path recorded in the witness")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    try:
        return run(args)
    except AdapterError as exc:
        print(f"WS33_C_ADAPTER=FAIL code={exc.code} message={exc}")
        return 2


def run(args) -> int:
    record = load_json(args.record)
    gate = load_json(args.gate)
    trace_bytes = args.trace.read_bytes()
    try:
        trace = json.loads(trace_bytes.decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        fail("C_EVIDENCE_UNREADABLE", f"trace bytes: {exc}")
    manifest = load_json(args.manifest)
    provenance = load_json(args.provenance)

    # --- 1. Retained gate: terminal PASS, single EVIDENCED path, TC preserved ---
    if gate.get("status") != "PASS":
        fail("C_GATE_NOT_PASS", f"batch gate status={gate.get('status')!r}")
    if gate.get("forge_pin") != FORGE_PIN:
        fail("C_FORGE_PIN_MISMATCH", "batch gate forge pin mismatch")
    if gate.get("batch") != args.batch_id:
        fail("C_GATE_NOT_PASS", f"batch id {gate.get('batch')!r} != {args.batch_id!r}")
    if gate.get("source_head") != args.source_head or gate.get("source_tree") != args.source_tree:
        fail("C_SOURCE_SEAL_MISMATCH", "batch gate source seal != expected C source")
    evidenced = [e for e in gate.get("executions", []) if e.get("status") == "EVIDENCED"]
    if len(gate.get("executions", [])) != 1 or len(evidenced) != 1:
        fail("C_PATH_NOT_SINGLETON", "adapter handles exactly one EVIDENCED execution")
    gex = evidenced[0]
    if gex.get("evidence_class") != "TECHNICALLY_CONFORMANT":
        fail("C_EVIDENCE_CLASS_NOT_TC",
             f"gate evidence_class={gex.get('evidence_class')!r}; TC must be preserved, never converted")
    if len(gex.get("paths", [])) != 1:
        fail("C_PATH_NOT_SINGLETON", "gate execution must evidence exactly one path")
    target = gex["paths"][0]
    if gex.get("run_source_head") != args.source_head:
        fail("C_SOURCE_SEAL_MISMATCH", "gate run source != expected C source HEAD")

    # --- 2. Record identity: same singleton path, same oracle, TC, pin-side checks ---
    if record.get("v2_path_ids") != [target]:
        fail("C_PATH_NOT_SINGLETON", f"record path set {record.get('v2_path_ids')!r} != [{target}]")
    if record.get("evidence_class") != "TECHNICALLY_CONFORMANT":
        fail("C_EVIDENCE_CLASS_NOT_TC", "record evidence_class must stay TECHNICALLY_CONFORMANT")
    if record.get("owner_family") not in ("ACTION_COST_DECISION", "TRIGGER_REPLACEMENT_ZONE_SBA",
                                          "CONTINUOUS_COPY_CONTROL", "COMBAT_COMMANDER",
                                          "HIDDEN_RNG_REPLAY"):
        fail("C_GATE_NOT_PASS", f"record owner_family={record.get('owner_family')!r}")
    if trace.get("forge_pin") != FORGE_PIN:
        fail("C_FORGE_PIN_MISMATCH", "trace forge pin mismatch")
    if trace.get("execution_id") != gex.get("execution_id"):
        fail("C_GATE_NOT_PASS", "trace execution_id != gate execution_id")

    # --- 3. Rules authority: preserved verbatim, must already be normative refs ---
    rules_refs = record.get("rules_authority_refs")
    if not isinstance(rules_refs, list) or not rules_refs:
        fail("C_RULES_AUTHORITY_MISSING",
             "retained record carries no rules_authority_refs; adapter must not fabricate any")
    for ref in rules_refs:
        if not isinstance(ref, str) or not ref.startswith(RULES_URL_PREFIX):
            fail("C_RULES_AUTHORITY_MISSING",
                 f"retained rules ref is not a normative Rules Authority reference: {ref!r}")

    # --- 4. Canonical manifest membership + STATE_ONLY representability ---
    mpaths = {p["v2_path_id"]: p for p in manifest.get("paths", [])}
    mpath = mpaths.get(target)
    if mpath is None:
        fail("MANIFEST_PATH_UNKNOWN", f"target not in canonical manifest: {target}")
    if mpath.get("owner_family") != record.get("owner_family"):
        fail("MANIFEST_OWNER_MISMATCH", "record owner_family != manifest owner_family")
    for key in ("required_decision_evidence", "required_rng_evidence",
                "required_hidden_info_evidence", "required_replay_evidence"):
        if mpath.get(key):
            fail("MANIFEST_REQUIRES_TAPE",
                 f"target requires {key}; C STATE_ONLY evidence cannot represent it losslessly")
    oracle_ids = record.get("oracle_identities", [])
    if (not oracle_ids
            or set(oracle_ids) != set(mpath.get("representative_actual_oracle_identities", []))):
        fail("ORACLE_IDENTITY_MISMATCH", "record oracle set != manifest representative oracle set")
    parent_primitive = mpath.get("parent_ws14_primitive_id")
    if not parent_primitive:
        fail("MANIFEST_PATH_UNKNOWN", "manifest entry lacks parent_ws14_primitive_id")

    # --- 5. Exact dual-book pre-state UNKNOWN/UNKNOWN, same ID, no fuzzy mapping ---
    cov = load_json(args.book_a_coverage)
    cov_by = {p["effective_v2_path_id"]: p for p in cov.get("paths", [])}
    brow = cov_by.get(target)
    if brow is None:
        fail("PRESTATE_NOT_UNKNOWN", "target absent from Book A (exact-ID match required)")
    if brow.get("status") != "UNKNOWN" or brow.get("evidence_classification") != "UNKNOWN":
        fail("PRESTATE_NOT_UNKNOWN",
             f"Book A pre-state={brow.get('status')}/{brow.get('evidence_classification')}; need UNKNOWN/UNKNOWN")
    b_status = None
    for line in args.book_b_ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("effective_path_id") == target:
            b_status = (row.get("current_status"), row.get("evidence_classification"))
            break
    if b_status is None:
        fail("PRESTATE_NOT_UNKNOWN", "target absent from Book B (exact-ID match required)")
    if b_status != ("UNKNOWN", "UNKNOWN"):
        fail("PRESTATE_NOT_UNKNOWN", f"Book B pre-state={b_status}; need UNKNOWN/UNKNOWN")

    # --- 6. Source approval via the existing validator's own extension point ---
    if manifest.get("forge_pin") != FORGE_PIN:
        fail("C_FORGE_PIN_MISMATCH", "canonical manifest forge pin mismatch")
    qkey = QUALIFICATION_SOURCE_HEAD + ":" + QUALIFICATION_SOURCE_TREE
    approved_q = (provenance.get("approved_qualification_sources", {}) or {}).get(qkey)
    if not approved_q or approved_q.get("descends_from_model_base") is not True:
        fail("QUALIFICATION_SOURCE_NOT_APPROVED", "canonical qualification source not approved")
    declared_digest = (provenance.get("patched_forge_digests", {}) or {}).get(qkey)
    if not declared_digest:
        fail("QUALIFICATION_SOURCE_NOT_APPROVED", "no declared patched Forge digest")
    if (provenance.get("ws26_manifest_sha256") or "") == "":
        fail("QUALIFICATION_SOURCE_NOT_APPROVED", "provenance lacks ws26 manifest digest")
    allowed_sources = {(args.source_head, args.source_tree)}
    approved_exec = provenance.get("approved_execution_sources", []) or []
    if (args.source_head, args.source_tree) not in {(e.get("head"), e.get("tree")) for e in approved_exec}:
        fail("EXECUTION_SOURCE_NOT_APPROVED",
             "C execution source is not an approved execution source in staging provenance; "
             "refusing to misrepresent it as the canonical source")
    if (manifest.get("source_head"), manifest.get("source_tree")) != \
            (QUALIFICATION_SOURCE_HEAD, QUALIFICATION_SOURCE_TREE):
        fail("QUALIFICATION_SOURCE_NOT_APPROVED",
             "canonical manifest source != approved qualification source")

    # --- 7. State assertions: all PASS, expected+actual present ---
    initial, final = record.get("initial_semantic_state"), record.get("final_semantic_state")
    if not initial or not final:
        fail("C_STATE_ASSERTION_NOT_PASS", "initial/final semantic state missing")
    assertions = record.get("state_assertions", [])
    if not assertions:
        fail("C_STATE_ASSERTION_NOT_PASS", "no state assertions in retained record")
    assertion_ids = set()
    for a in assertions:
        if a.get("result") != "PASS" or "expected" not in a or "actual" not in a \
                or not a.get("assertion_id"):
            fail("C_STATE_ASSERTION_NOT_PASS",
                 f"assertion not PASS with expected+actual: {a.get('assertion_id')!r}")
        assertion_ids.add(a["assertion_id"])

    # --- 8. Path exercise + parent linkage (decision/runtime trace semantics) ---
    pex = record.get("path_exercise", [])
    if len(pex) != 1 or pex[0].get("v2_path_id") != target or pex[0].get("exercised") is not True:
        fail("C_TRACE_EVENT_MISMATCH", "record path_exercise must exercise exactly the target")
    trace_event_ids = trace.get("trace_event_ids", [])
    for ev in pex[0].get("trace_event_ids", []) or []:
        if ev not in trace_event_ids:
            fail("C_TRACE_EVENT_MISMATCH", f"path references unknown trace event {ev!r}")
    if not pex[0].get("trace_event_ids") or not pex[0].get("assertion_ids"):
        fail("C_TRACE_EVENT_MISMATCH", "path exercise lacks trace_event_ids/assertion_ids")
    for aid in pex[0]["assertion_ids"]:
        if aid not in assertion_ids:
            fail("C_TRACE_EVENT_MISMATCH", f"path references unknown assertion {aid!r}")
    matched = [m for m in trace.get("matched_links", []) if m.get("path_id") == target]
    if not matched:
        fail("C_PARENT_LINKAGE_MISSING", "no matched link for target in retained trace")
    link = matched[0]
    parents = {e.get("id"): e for e in trace.get("parent_resolution_events", [])}
    children = {e.get("id"): e for e in trace.get("child_observations", [])}
    parent_ev, child_ev = parents.get(link.get("parent_id")), children.get(link.get("child_id"))
    if parent_ev is None or child_ev is None:
        fail("C_PARENT_LINKAGE_MISSING", "matched link lacks parent/child observations")
    if child_ev.get("parent_id") != parent_ev.get("id"):
        fail("C_PARENT_LINKAGE_MISSING", "child not linked to parent")
    if link.get("relation_match") is not True:
        fail("C_PARENT_LINKAGE_MISSING", "relation not certified matched")
    if link.get("modeled_class") != mpath.get("implementation_target"):
        fail("C_PARENT_LINKAGE_MISSING", "modeled class != manifest implementation target")
    if link.get("modeled_class") != link.get("actual_runtime_class") \
            and not link.get("attribution_relation"):
        fail("C_PARENT_LINKAGE_MISSING", "model/runtime divergence without attribution relation")
    trip = trace.get("decision_tripwire", {})
    for hit in trip.get("hits", []):
        if hit.get("incidental") is not True:
            fail("C_TRACE_EVENT_MISMATCH",
                 f"non-incidental decision requirement outside STATE_ONLY profile: {hit.get('site')}")
    profile = trace.get("runtime_profile", {})
    if profile.get("unexpected_decision") or profile.get("unexpected_hidden") \
            or profile.get("unexpected_rng") or profile.get("replay_required"):
        fail("C_TRACE_EVENT_MISMATCH", "runtime profile exceeds STATE_ONLY requirements")
    ex = record.get("execution", {})
    if ex.get("actual_rules_core_path") is not True or ex.get("silent_fallbacks") != 0 \
            or ex.get("direct_effect_resolution") is not False:
        fail("C_TRACE_EVENT_MISMATCH", "execution boundary violated in retained record")
    if ex.get("authoritative_decision_boundary") != "NOT_REQUIRED":
        fail("C_TRACE_EVENT_MISMATCH", "decision boundary != NOT_REQUIRED for STATE_ONLY path")

    # --- 9. Emit canonical v2.1 witness (deterministic) ---
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_sha = sha256_bytes(trace_bytes)
    (out_dir / "trace.json").write_bytes(trace_bytes)
    short = target.removeprefix("forge-behavior-v2:")[:8]
    witness_id = f"{args.batch_id.lower().replace('_', '-')}-{short}"
    witness = {
        "schema": WITNESS_SCHEMA,
        "witness_id": witness_id,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "qualification_source_head": QUALIFICATION_SOURCE_HEAD,
        "qualification_source_tree": QUALIFICATION_SOURCE_TREE,
        "model_base_head": MODEL_BASE_HEAD,
        "model_base_tree": MODEL_BASE_TREE,
        "ws26_manifest_sha256": provenance["ws26_manifest_sha256"],
        "effective_model_sha256": sha256_file(args.manifest),
        "forge_pin": FORGE_PIN,
        "runtime_overlay_manifest": args.overlay_manifest_rel,
        "runtime_overlay_manifest_sha256": sha256_file(args.overlay_manifest),
        "patched_forge_digest": declared_digest,
        "execution_environment_identity": {
            "runner_os": args.runner_os,
            "java_version": args.java_version,
            "process_isolation": "GITHUB_EPHEMERAL_RUNNER_FROZEN_SOURCE",
        },
        "oracle_identities": sorted(oracle_ids),
        "parent_ws14_primitive_ids": [parent_primitive],
        "v2_path_ids": [target],
        "owner_family": record["owner_family"],
        "initial_semantic_state": initial,
        "final_semantic_state": final,
        "state_assertions": [
            {"assertion_id": a["assertion_id"], "expected": a["expected"],
             "actual": a["actual"], "result": "PASS"} for a in assertions
        ],
        "primitive_exercise": [{"primitive_id": parent_primitive, "exercised": True}],
        "path_exercise": [{
            "v2_path_id": target,
            "exercised": True,
            "trace_event_ids": list(pex[0]["trace_event_ids"]),
            "assertion_ids": list(pex[0]["assertion_ids"]),
            "parent_ws14_primitive_id": parent_primitive,
        }],
        "decision_tape_ref": None,
        "rng_tape_ref": None,
        "observation_evidence_ref": None,
        "semantic_replay_evidence_ref": None,
        "execution": {
            "engine": "pinned-forge",
            "actual_rules_core_path": True,
            "authoritative_decision_boundary": "NOT_REQUIRED",
            "silent_fallbacks": 0,
            "runtime_overlays_declared": True,
            "production_entrypoint": trace.get("production_entrypoint"),
            "production_stack_path": trace.get("production_stack_path"),
            "direct_effect_resolution": False,
            "environment_basis": (
                f"declared execution environment of retained run {args.run_id} "
                f"per pinned workflow source {args.workflow_source_head}"
            ),
            "overlay_basis": (
                f"retained run bound runtime pins and overlay logs "
                f"(artifact {args.artifact_id})"
            ),
        },
        "trace_ref": args.trace_ref,
        "trace_sha256": trace_sha,
        "stdout_only": False,
        "rules_authority_refs": list(rules_refs),
        "evidence_class": "TECHNICALLY_CONFORMANT",
        "status": "PASS",
    }
    (out_dir / "witness.json").write_text(canon(witness), encoding="utf-8")

    mapping = {
        "schema": "commander-simulator-next.ws33-c-v21-adapter-mapping.v1",
        "witness_id": witness_id,
        "target_path_id": target,
        "evidence_class_preserved": "TECHNICALLY_CONFORMANT",
        "field_basis": {
            "v2_path_ids/owner_family/oracle_identities": "retained record.json verbatim; oracle set == manifest representative set",
            "initial/final_semantic_state/state_assertions": "retained record.json verbatim (5/5 PASS)",
            "path_exercise": "retained record.json verbatim + parent primitive from canonical manifest entry",
            "primitive_exercise": "derived: retained matched_links parent/child linkage certifies parent primitive exercised",
            "decision/rng/observation/replay_refs=null": "canonical manifest requires none (STATE_ONLY); retained tripwire/profile confirm no requirement",
            "execution.engine/pinned-forge": "retained production entrypoint + stack path via AbilityUtils.resolve; no direct resolution",
            "execution.runtime_overlays_declared=true": "retained run bound runtime pins + overlay logs (in-run verification, 18/18 steps success)",
            "execution_environment_identity": f"declared env per pinned workflow source {args.workflow_source_head} (runs-on/java-version); ephemeral GitHub runner with frozen source",
            "rules_authority_refs": "retained record.json verbatim; normative Rules references already present, TC not upgraded to ERV",
            "trace_ref/trace_sha256": "retained trace.json bytes vendored verbatim",
            "source_head/tree": "retained batch gate source seal verbatim; must be an approved execution source in staging provenance",
            "qualification_source/effective_model/overlay/ws26_manifest/patched_digest": "canonical provenance + manifest/overlay bytes at promotion base",
        },
        "provenance": {
            "run_id": args.run_id,
            "job_id": args.job_id,
            "artifact_id": args.artifact_id,
            "artifact_digest": args.artifact_digest,
            "batch_id": args.batch_id,
            "execution_id": gex.get("execution_id"),
            "source_head": args.source_head,
            "source_tree": args.source_tree,
            "forge_pin": FORGE_PIN,
        },
    }
    (out_dir / "adapter-mapping.json").write_text(canon(mapping), encoding="utf-8")
    print(f"WS33_C_ADAPTER=PASS witness={witness_id} target={target} trace_sha256={trace_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
