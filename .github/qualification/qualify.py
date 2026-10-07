#!/usr/bin/env python3
"""Derive the source-bound Mage qualification verdict from the trusted witness.

Trust boundary: this script runs from the trusted default-branch checkout and is
the only writer of the qualification evidence. It reads exactly two inputs, both
produced by trusted code: the source lock and the trusted execution witness.

It also reads the trusted integrity record (``sandbox.py verify``): if any
trusted validator file, sealed evidence file or trusted path was changed or left
writable by the candidate account, or a candidate process survived, the verdict
is FAIL whatever the witness says.

It deliberately has no code path that reads a candidate-authored report. The
earlier design harvested ``candidate/**/target/surefire-reports/TEST-*.xml``,
which was a hole: candidate POM configuration, Maven plugins, lifecycle hooks,
test code and generated files can all create those files, so parsing them from
trusted Python established nothing. That harvesting is gone, not relocated.

Maven/build-result binding, adjudicated explicitly
--------------------------------------------------
A non-zero candidate build exit code is an UNCONDITIONAL FAIL for this workflow.
It is not merely logged. A candidate must not be able to fail its own build and
still reach PASS by supplying evidence, so the verdict is the conjunction of:

  1. the candidate build exited zero;
  2. the trusted driver executed the trusted enumeration of required tests;
  3. every required class was actually entered by the trusted launcher;
  4. tests were found and started, with zero failed, zero aborted, zero failed
     containers, and not every discovered test skipped;
  5. the witness is bound to the locked candidate SHA;
  6. the required corpus satisfies the trusted baseline policy (no unapproved
     removal, a fresh well-formed baseline, an updated candidate baseline);
  7. trusted state integrity held across every candidate execution.

Any missing, unreadable or ambiguous input is UNKNOWN or FAIL. Never PASS.
Mergeability and synthetic-merge state carry no qualification credit here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import corpus_policy  # noqa: E402

SCHEMA = "mage.candidate-qualification.evidence/7"
WITNESS_SCHEMA = "mage.candidate-qualification.witness/7"
EXEC_WITNESS_SCHEMA = "mage.candidate-qualification.trusted-execution-witness/6"
INTEGRITY_SCHEMA = "mage.candidate-qualification.integrity/1"

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"
EXIT_CODES = {PASS: 0, FAIL: 1, UNKNOWN: 2}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def emit(evidence: dict, out: Path, code: int) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(
        "QUALIFICATION = {}{}".format(
            evidence.get("verdict"),
            " ({})".format(json.dumps(evidence.get("reasons"), ensure_ascii=True)) if evidence.get("reasons") else "",
        )
    )
    return code


def base_evidence() -> dict:
    return {
        "schema": SCHEMA,
        "verdict": UNKNOWN,
        "qualification_credit": False,
        "reasons": [],
        "repository": None,
        "pull_request_number": None,
        "trusted_validator": None,
        "candidate": None,
        "comparison_base": None,
        "candidate_build_exit_code": None,
        "candidate_authored_evidence_used": False,
        "candidate_reports_parsed": False,
        "test_evidence": None,
        "guard": {"path": None, "sha256": None},
        "candidate_code_executed_as_validator": False,
        "mergeability_influenced_verdict": False,
        "synthetic_merge_influenced_verdict": False,
    }


def load_json(path: str, label: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise ValueError("{} is missing: {}".format(label, p))
    return json.loads(p.read_text())


def integrity_reasons(integrity) -> tuple[str, list[str]]:
    if not isinstance(integrity, dict) or integrity.get("schema") != INTEGRITY_SCHEMA:
        return UNKNOWN, ["trusted_state_integrity_unverified: integrity record missing or malformed"]
    if integrity.get("status") == "OK" and not integrity.get("violations"):
        return PASS, []
    if integrity.get("status") == "VIOLATION":
        return FAIL, ["trusted_state_integrity_violation: {}".format(v) for v in (integrity.get("violations") or ["unspecified"])[:5]]
    return UNKNOWN, ["trusted_state_integrity_unverified: {}".format(v) for v in (integrity.get("violations") or ["status={}".format(integrity.get("status"))])[:5]]


def decide(lock: dict, witness: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    status = PASS

    def fail(reason: str) -> None:
        nonlocal status
        if status != FAIL:
            status = FAIL
        reasons.append(reason)

    def unknown(reason: str) -> None:
        # A proven FAIL is never softened into UNKNOWN by a later gap.
        nonlocal status
        if status != FAIL:
            status = UNKNOWN
        reasons.append(reason)

    if witness.get("status") != "WITNESSED":
        unknown(
            "trusted_witness_unavailable: {}".format(
                "; ".join(witness.get("notes") or ["status={}".format(witness.get("status"))])
            )
        )
        # What is already proven still decides: a failed candidate build or an
        # altered build definition is a FAIL even when no witness was produced.
        raw = witness.get("candidate_build_exit_code")
        if isinstance(raw, int) and raw != 0:
            fail("candidate_build_failed: maven exit {} is an unconditional qualification failure".format(raw))
        audit = witness.get("build_definition_audit") or {}
        if audit.get("status") == "VIOLATION":
            fail("test_execution_definition_altered: {}".format(", ".join(
                "{}:{}".format(v.get("kind"), v.get("detail")) for v in (audit.get("violations") or [])[:5])))
        return status, reasons

    if witness.get("schema") != WITNESS_SCHEMA:
        unknown("trusted_witness_schema_unexpected: {!r}".format(witness.get("schema")))
        return status, reasons

    if not witness.get("source_binding_ok"):
        fail("source_binding_unproven: witness is not bound to the locked candidate sha")

    if (witness.get("candidate") or {}).get("sha") != (lock.get("candidate") or {}).get("sha"):
        fail("source_binding_mismatch: witness candidate differs from source lock")

    execution = witness.get("trusted_execution_witness") or {}
    if execution.get("schema") != EXEC_WITNESS_SCHEMA:
        unknown("trusted_execution_witness_unusable: unexpected schema")
        return status, reasons

    locked_sha = (lock.get("candidate") or {}).get("sha")
    if execution.get("bound_candidate_sha") != locked_sha or (execution.get("bound_candidate_shas") or [locked_sha]) != [locked_sha]:
        fail("witness_binding_mismatch: execution witness is bound to another candidate")
    if witness.get("test_bytecode_origin") != "trusted_compile_of_trusted_validator_export" or witness.get("candidate_test_classes_used") is not False:
        fail("test_bytecode_not_trusted: authoritative test bytecode did not come from the trusted validator commit")
    if witness.get("candidate_witness_authority") is not False or execution.get("candidate_witness_authority") is not False:
        fail("candidate_witness_authority_present: hostile candidate bytecode shares qualification authority")

    if execution.get("evidence_origin") != "trusted_parent_jdi_observation":
        fail(
            "evidence_origin_not_trusted: {}".format(execution.get("evidence_origin"))
        )
    if execution.get("candidate_authored_evidence_used") is not False:
        fail("candidate_authored_evidence_used: witness does not assert trusted-only evidence")
    if execution.get("execution_mode") != "per_module_external_observer":
        fail(
            "execution_mode_not_per_module: {}".format(execution.get("execution_mode"))
        )
    if execution.get("receipt_authentication") != "trusted_parent_hmac_sha256" \
            or execution.get("all_receipts_hmac_verified") is not True \
            or execution.get("receipt_key_in_candidate_jvm") is not False:
        fail("trusted_parent_receipt_authentication_unproven")

    # Adjudicated rule: a non-zero candidate build exit is an unconditional FAIL.
    raw_exit = witness.get("candidate_build_exit_code")
    if raw_exit in (None, ""):
        unknown("candidate_build_exit_unrecorded: build result binding unproven")
    else:
        try:
            build_exit = int(raw_exit)
        except (TypeError, ValueError):
            unknown("candidate_build_exit_unparseable: {!r}".format(raw_exit))
            build_exit = None
        if build_exit is not None and build_exit != 0:
            fail(
                "candidate_build_failed: maven exit {} is an unconditional qualification failure".format(
                    build_exit
                )
            )

    if not witness.get("required_test_classes"):
        unknown("no_required_tests: trusted enumeration found no required test class")

    audit = witness.get("build_definition_audit")
    if audit is None:
        unknown("build_definition_audit_missing: qualification definition not audited")
    elif audit.get("status") != "CLEAN":
        fail(
            "test_execution_definition_altered: {}".format(
                ", ".join(
                    "{}:{}".format(v.get("kind"), v.get("detail"))
                    for v in (audit.get("violations") or [])[:5]
                )
                or audit.get("status")
            )
        )

    corpus = witness.get("corpus_policy")
    if not isinstance(corpus, dict):
        unknown("corpus_policy_missing: the required corpus was not checked against the trusted baseline")
    else:
        for reason in corpus.get("violations") or []:
            fail(reason)
        for reason in corpus.get("unknowns") or []:
            unknown(reason)
        if corpus.get("status") not in ("OK", "VIOLATION", "UNKNOWN"):
            unknown("corpus_policy_unusable: status={}".format(corpus.get("status")))
        required_methods_bound = corpus.get("trusted_required_methods") or []
        try:
            owning = {corpus_policy.class_of_method(str(m)) for m in required_methods_bound if isinstance(m, str)}
        except corpus_policy.CorpusError as exc:
            fail("required_method_identity_malformed: {}".format(exc))
            owning = set()
        inheriting = corpus.get("trusted_required_inheriting_classes")
        if not isinstance(inheriting, list) or not all(isinstance(c, str) for c in inheriting):
            unknown("required_inheriting_classes_missing: the corpus policy bound no inheriting-class list")
            inheriting = []
        policy_pairs = corpus.get("trusted_required_pairs") or []
        required_from_policy = sorted(policy_pairs)
        if policy_pairs and not (owning or inheriting):
            fail(
                "no_enabled_required_test_methods: the corpus enumerates {} test class(es) "
                "but none has an enabled test method".format(len(policy_pairs))
            )
        # The driver's selection is re-derived here, not trusted from the
        # witness: the required classes that own a required method or only
        # inherit enabled tests.
        expected_selected = sorted(p for p in policy_pairs if p in owning or p in set(inheriting))
        selected_in_witness = witness.get("selected_test_classes")
        if not isinstance(selected_in_witness, list) or sorted(
            "{}::{}".format(e.get("module"), e.get("class_name")) for e in selected_in_witness
            if isinstance(e, dict)
        ) != expected_selected:
            fail("selected_set_not_policy_derived: the witness's selected classes differ from the "
                 "required classes owning or inheriting a required test")
        required_in_witness = sorted(
            "{}::{}".format(e.get("module"), e.get("class_name")) for e in (witness.get("required_test_classes") or [])
        )
        if required_from_policy != required_in_witness:
            fail("required_set_not_policy_derived: witness required set differs from the corpus policy")
        # A class can stay while its methods go. Every method the policy requires
        # (every baseline method still owed) must have been started by the
        # trusted driver; a method the static reading still sees but that never
        # ran is not credit. Candidate-added methods are delta-visible only.
        required_methods = corpus.get("trusted_required_methods")
        observed_methods = execution.get("observed_methods")
        if corpus.get("status") == "OK" and (
            not isinstance(required_methods, list) or not all(isinstance(m, str) for m in required_methods)
        ):
            unknown("required_methods_missing: the corpus policy bound no test methods")
        elif isinstance(required_methods, list):
            if not isinstance(observed_methods, list) or not all(isinstance(m, str) for m in observed_methods):
                fail("observed_methods_missing: the trusted witness reports no started test methods")
            else:
                not_started = sorted(set(required_methods) - set(observed_methods))
                if not_started:
                    fail("required_test_methods_not_started: {} of {}: {}".format(
                        len(not_started), len(required_methods), ",".join(not_started[:10])))
                body_completed = execution.get("body_completed_methods")
                if not isinstance(body_completed, list) or not all(isinstance(m, str) for m in body_completed):
                    fail("required_test_method_body_evidence_missing: parent observer reported no completed method bodies")
                else:
                    body_missing = sorted(set(required_methods) - set(body_completed))
                    if body_missing:
                        fail("required_test_method_bodies_not_completed: {} of {}: {}".format(
                            len(body_missing), len(required_methods), ",".join(body_missing[:10])))

    never_entered = execution.get("classes_never_entered") or []
    if never_entered:
        fail(
            "required_tests_never_entered: {}".format(",".join(never_entered[:10]))
        )

    origin_violations = execution.get("code_origin_violations") or []
    if origin_violations:
        fail(
            "class_origin_mismatch: {}".format("; ".join(origin_violations[:5]))
        )

    control_violations = execution.get("control_violations") or []
    for violation in control_violations[:5]:
        if isinstance(violation, str) and violation.startswith("candidate_junit_control_code:"):
            fail(violation)
        else:
            fail("candidate_execution_control_violation: {}".format(violation))

    # Per-module aggregation integrity. A module that owns required classes but
    # produced no trusted witness is a gap, never a silent skip; and partial
    # execution must not aggregate into PASS.
    completeness = witness.get("module_classpath_completeness") or {}
    if completeness and completeness.get("complete") is not True:
        fail(
            "module_classpath_incomplete: {}".format(
                ",".join(completeness.get("modules_missing_classpath") or [])
            )
        )

    for entry in witness.get("module_execution") or []:
        why = entry.get("reason")
        if why and why not in ("no_required_classes_in_module", "no_trusted_required_classes_in_module"):
            fail("module_witness_rejected: {}: {}".format(entry.get("module"), why))

    modules_without_witness = execution.get("modules_without_witness") or []
    if modules_without_witness:
        fail(
            "module_execution_incomplete: {}".format(",".join(modules_without_witness[:10]))
        )

    required_total = execution.get("trusted_selected_classes") or 0
    entered_total = execution.get("classes_entered_total") or 0
    if required_total > 0 and entered_total < required_total:
        fail(
            "partial_module_execution: {} of {} required module/class pairs entered".format(
                entered_total, required_total
            )
        )

    # The entered set must be exactly the selected set (the required classes
    # that own a required test method): no extra credited class, and no selected
    # (module, class) pair quietly missing. Every required class must still
    # compile from its own module (required_tests_not_compiled below).
    selected = witness.get("selected_test_classes")
    if not isinstance(selected, list):
        selected = witness.get("required_test_classes") or []
    required_pairs = {"{}::{}".format(e.get("module"), e.get("class_name")) for e in selected}
    entered_pairs = set(execution.get("entered_pairs") or [])
    unexpected = sorted(entered_pairs - required_pairs)
    if unexpected:
        fail("unexpected_entered_classes: {}".format(",".join(unexpected[:10])))
    missing_pairs = sorted(required_pairs - entered_pairs)
    if missing_pairs and not modules_without_witness:
        fail("required_pairs_not_entered: {}".format(",".join(missing_pairs[:10])))

    not_compiled = [
        "{}:{}".format(m.get("module"), ",".join(m.get("not_compiled") or [])[:120])
        for m in (witness.get("modules") or [])
        if m.get("not_compiled")
    ]
    if not_compiled:
        fail("required_tests_not_compiled: {}".format("; ".join(not_compiled[:5])))

    counter_keys = (
        "tests_found", "tests_started", "tests_succeeded", "tests_failed",
        "tests_aborted", "tests_skipped", "containers_failed",
    )
    module_totals = {key: 0 for key in counter_keys}
    for entry in witness.get("module_execution") or []:
        record = entry.get("witness")
        if not isinstance(record, dict):
            continue  # required missing witnesses are already rejected above
        if record.get("schema") != EXEC_WITNESS_SCHEMA:
            fail("module_witness_schema_unexpected: {}: {!r}".format(
                entry.get("module"), record.get("schema")))
        if record.get("evidence_origin") != "trusted_parent_jdi_observation":
            fail("module_evidence_origin_untrusted: {}".format(entry.get("module")))
        if record.get("candidate_witness_authority") is not False:
            fail("module_candidate_witness_authority_present: {}".format(entry.get("module")))
        if record.get("receipt_authentication") != "trusted_parent_hmac_sha256" \
                or record.get("receipt_hmac_verified") is not True \
                or record.get("receipt_key_in_candidate_jvm") is not False:
            fail("module_receipt_authentication_unproven: {}".format(entry.get("module")))
        if record.get("observer_status") != "COMPLETE":
            fail("module_observer_incomplete: {}".format(entry.get("module")))
        if record.get("protocol_violations"):
            fail("module_observer_protocol_violation: {}: {}".format(
                entry.get("module"), ",".join(record.get("protocol_violations")[:5])))
        if record.get("control_violations"):
            fail("module_execution_control_violation: {}: {}".format(
                entry.get("module"), ",".join(record.get("control_violations")[:5])))
        if record.get("methods_never_body_completed"):
            fail("module_required_method_bodies_not_completed: {}: {}".format(
                entry.get("module"), ",".join(record.get("methods_never_body_completed")[:5])))
        if record.get("driver_verdict") != "PASS":
            fail("module_observed_execution_failed: {}".format(entry.get("module")))
        if entry.get("observer_exit_code") != 0:
            fail("module_observer_process_failed: {}: {}".format(
                entry.get("module"), entry.get("observer_exit_code")))
        invalid_module = [key for key in counter_keys
                          if type(record.get(key)) is not int or record[key] < 0]
        if invalid_module:
            fail("invalid_module_counter: {}: {}".format(
                entry.get("module"), ",".join(invalid_module)))
            continue
        if record["tests_started"] != (
            record["tests_succeeded"] + record["tests_failed"] + record["tests_aborted"]
        ) or record["tests_found"] < record["tests_started"] + record["tests_skipped"]:
            fail("module_outcomes_mismatch: {}".format(entry.get("module")))
        for key in counter_keys:
            module_totals[key] += record[key]
    if any(module_totals[key] != execution.get(key) for key in counter_keys):
        fail("module_totals_mismatch: aggregated counts differ from raw module records")

    # Authentication proves provenance, not that a buggy trusted producer has
    # emitted meaningful counts. Missing, boolean, negative or non-integer
    # counters must never turn into zero/success through coercion or `or 0`.
    invalid = [key for key in counter_keys
               if type(execution.get(key)) is not int or execution[key] < 0]
    if invalid:
        fail("invalid_execution_counter: {}".format(",".join(invalid)))
        return status, reasons
    totals = execution.get("totals")
    if not isinstance(totals, dict) or any(
        type(totals.get(key)) is not int or totals[key] != execution[key]
        for key in counter_keys
    ):
        fail("execution_totals_mismatch: duplicate totals differ from witnessed counts")
    if execution["tests_started"] != (
        execution["tests_succeeded"] + execution["tests_failed"] + execution["tests_aborted"]
    ):
        fail("execution_outcomes_mismatch: started tests lack matching outcomes")
    if execution["tests_found"] < execution["tests_started"] + execution["tests_skipped"]:
        fail("execution_discovery_mismatch: outcomes exceed discovered tests")

    tests_found = execution.get("tests_found") or 0
    tests_started = execution.get("tests_started") or 0
    tests_failed = execution.get("tests_failed") or 0
    tests_aborted = execution.get("tests_aborted") or 0
    tests_skipped = execution.get("tests_skipped") or 0
    containers_failed = execution.get("containers_failed") or 0

    if tests_found <= 0:
        fail("zero_tests_found: trusted launcher discovered no test")
    if tests_started <= 0:
        fail("zero_tests_executed: trusted launcher started no test")
    if tests_failed > 0:
        fail("test_failures: {} failed".format(tests_failed))
    if tests_aborted > 0:
        fail("tests_aborted: {} aborted".format(tests_aborted))
    if containers_failed > 0:
        fail("container_failures: {} test container(s) failed".format(containers_failed))
    if tests_found > 0 and tests_skipped >= tests_found:
        fail("all_tests_skipped: every discovered test was skipped")

    return status, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--witness", required=True)
    parser.add_argument("--integrity", required=True, help="INTEGRITY.json from sandbox.py verify")
    parser.add_argument("--guard", default=str(Path(__file__).resolve()))
    parser.add_argument("--trusted-root", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    evidence = base_evidence()
    guard_path = Path(args.guard).resolve()
    evidence["guard"]["path"] = str(guard_path)
    evidence["guard"]["sha256"] = sha256_file(guard_path) if guard_path.is_file() else None

    if args.trusted_root:
        trusted_root = Path(args.trusted_root).resolve()
        if trusted_root not in guard_path.parents:
            evidence["verdict"] = FAIL
            evidence["reasons"] = [
                "guard_outside_trusted_root: {} not under {}".format(guard_path, trusted_root)
            ]
            return emit(evidence, out, EXIT_CODES[FAIL])

    try:
        lock = load_json(args.source_lock, "source lock")
        if lock.get("status") != "LOCKED":
            raise ValueError("source lock is not LOCKED")
        for identity in ("trusted_validator", "candidate", "comparison_base"):
            block = lock.get(identity)
            if not isinstance(block, dict) or len(block.get("sha", "")) != 40:
                raise ValueError("source lock identity {!r} is malformed".format(identity))
        witness = load_json(args.witness, "trusted execution witness")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        evidence["reasons"] = ["input_unusable: {}".format(exc)]
        return emit(evidence, out, EXIT_CODES[UNKNOWN])

    evidence["repository"] = lock.get("repository")
    evidence["pull_request_number"] = lock.get("pull_request_number")
    evidence["trusted_validator"] = lock["trusted_validator"]
    evidence["candidate"] = lock["candidate"]
    evidence["comparison_base"] = lock["comparison_base"]
    evidence["candidate_build_exit_code"] = witness.get("candidate_build_exit_code")
    evidence["candidate_authored_evidence_used"] = bool(
        witness.get("candidate_authored_evidence_used")
    )
    evidence["candidate_reports_parsed"] = bool(witness.get("candidate_reports_parsed"))
    evidence["guard"]["witness_driver_sha256"] = (witness.get("driver") or {}).get("sha256")

    verdict, reasons = decide(lock, witness)
    try:
        integrity = json.loads(Path(args.integrity).read_text())
    except (OSError, json.JSONDecodeError):
        integrity = None
    integrity_verdict, integrity_notes = integrity_reasons(integrity)
    evidence["trusted_state_integrity"] = (integrity or {}).get("status")
    if integrity_verdict == FAIL:
        verdict = FAIL
    elif integrity_verdict == UNKNOWN and verdict == PASS:
        verdict = UNKNOWN
    reasons = reasons + integrity_notes
    evidence["verdict"] = verdict
    evidence["qualification_credit"] = verdict == PASS
    evidence["reasons"] = reasons

    execution = witness.get("trusted_execution_witness") or {}
    evidence["test_evidence"] = {
        "origin": execution.get("evidence_origin"),
        "execution_mode": execution.get("execution_mode"),
        "required_test_class_count": len(witness.get("required_test_classes") or []),
        "modules_with_required_tests": execution.get("modules_with_required_tests"),
        "modules_with_witness": execution.get("modules_with_witness"),
        "modules_without_witness": execution.get("modules_without_witness"),
        "module_classpath_completeness": witness.get("module_classpath_completeness"),
        "trusted_selected_classes": execution.get("trusted_selected_classes"),
        "classes_entered_total": execution.get("classes_entered_total"),
        "classes_never_entered": execution.get("classes_never_entered"),
        "code_origin_violations": execution.get("code_origin_violations"),
        "totals": {
            "found": execution.get("tests_found"),
            "started": execution.get("tests_started"),
            "succeeded": execution.get("tests_succeeded"),
            "failed": execution.get("tests_failed"),
            "aborted": execution.get("tests_aborted"),
            "skipped": execution.get("tests_skipped"),
            "containers_failed": execution.get("containers_failed"),
        },
        "failures": execution.get("failures"),
    }
    evidence["notes"] = witness.get("notes") or []

    return emit(evidence, out, EXIT_CODES[verdict])


if __name__ == "__main__":
    sys.exit(main())