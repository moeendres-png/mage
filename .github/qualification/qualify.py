#!/usr/bin/env python3
"""Derive the source-bound Mage qualification verdict from the trusted witness.

Trust boundary: this script runs from the trusted default-branch checkout and is
the only writer of the qualification evidence. It reads exactly two inputs, both
produced by trusted code: the source lock and the trusted execution witness.

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
  5. the witness is bound to the locked candidate SHA.

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

SCHEMA = "mage.candidate-qualification.evidence/2"
WITNESS_SCHEMA = "mage.candidate-qualification.witness/1"
EXEC_WITNESS_SCHEMA = "mage.candidate-qualification.trusted-execution-witness/1"

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
            " ({})".format("; ".join(evidence.get("reasons") or [])) if evidence.get("reasons") else "",
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


def decide(lock: dict, witness: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    status = PASS

    def fail(reason: str) -> None:
        nonlocal status
        if status != FAIL:
            status = FAIL
        reasons.append(reason)

    def unknown(reason: str) -> None:
        nonlocal status
        status = UNKNOWN
        reasons.append(reason)

    if witness.get("status") != "WITNESSED":
        unknown(
            "trusted_witness_unavailable: {}".format(
                "; ".join(witness.get("notes") or ["status={}".format(witness.get("status"))])
            )
        )
        return status, reasons

    if not witness.get("source_binding_ok"):
        fail("source_binding_unproven: witness is not bound to the locked candidate sha")

    if (witness.get("candidate") or {}).get("sha") != (lock.get("candidate") or {}).get("sha"):
        fail("source_binding_mismatch: witness candidate differs from source lock")

    execution = witness.get("trusted_execution_witness") or {}
    if execution.get("schema") != EXEC_WITNESS_SCHEMA:
        unknown("trusted_execution_witness_unusable: unexpected schema")
        return status, reasons

    if execution.get("bound_candidate_sha") != (lock.get("candidate") or {}).get("sha"):
        fail("witness_binding_mismatch: execution witness is bound to another candidate")

    if execution.get("evidence_origin") != "trusted_side_direct_execution":
        fail(
            "evidence_origin_not_trusted: {}".format(execution.get("evidence_origin"))
        )
    if execution.get("candidate_authored_evidence_used") is not False:
        fail("candidate_authored_evidence_used: witness does not assert trusted-only evidence")

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

    never_entered = execution.get("classes_never_entered") or []
    if never_entered:
        fail(
            "required_tests_never_entered: {}".format(",".join(never_entered[:10]))
        )

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

    if status == PASS and execution.get("driver_verdict") != PASS:
        fail(
            "driver_disagreement: trusted driver verdict {}".format(
                execution.get("driver_verdict")
            )
        )

    return status, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--witness", required=True)
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
    evidence["verdict"] = verdict
    evidence["qualification_credit"] = verdict == PASS
    evidence["reasons"] = reasons

    execution = witness.get("trusted_execution_witness") or {}
    evidence["test_evidence"] = {
        "origin": execution.get("evidence_origin"),
        "required_test_classes": witness.get("required_test_classes"),
        "selected_class_count": execution.get("trusted_selected_classes"),
        "observed_classes": execution.get("observed_classes"),
        "classes_never_entered": execution.get("classes_never_entered"),
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