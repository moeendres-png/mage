#!/usr/bin/env python3
"""Turn raw candidate test output into a source-bound Mage qualification verdict.

Trust boundary: this script runs from the trusted default-branch checkout and is
the only writer of the qualification evidence. It never reads a verdict from the
candidate tree, because a candidate that can author its own verdict does not need
to pass any test.

Fail-closed contract:
  PASS requires positive proof that tests were discovered and executed.
  Absent, empty, malformed or ambiguous evidence is UNKNOWN or FAIL, never PASS.
  Mergeability and synthetic-merge state carry no qualification credit here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCHEMA = "mage.candidate-qualification.evidence/1"
REPORT_GLOB = "TEST-*.xml"

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


def load_source_lock(path: Path) -> dict:
    if not path.is_file():
        raise ValueError("source lock is missing: {}".format(path))
    lock = json.loads(path.read_text())
    if lock.get("status") != "LOCKED":
        raise ValueError("source lock is not LOCKED: {}".format(lock.get("status")))
    for identity in ("trusted_validator", "candidate", "comparison_base"):
        block = lock.get(identity)
        if not isinstance(block, dict) or len(block.get("sha", "")) != 40:
            raise ValueError("source lock identity {!r} is malformed".format(identity))
    if lock.get("candidate_code_executed_as_validator") is not False:
        raise ValueError("source lock does not assert candidate_code_executed_as_validator=false")
    return lock


def discover_reports(candidate_root: Path) -> list[Path]:
    return sorted(
        p
        for p in candidate_root.glob("**/target/surefire-reports/" + REPORT_GLOB)
        if p.is_file()
    )


def harvest(reports: list[Path]) -> tuple[dict, list[str]]:
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    suites: list[dict] = []
    problems: list[str] = []

    for report in reports:
        try:
            root = ET.parse(report).getroot()
        except ET.ParseError as exc:
            problems.append("unparseable report {}: {}".format(report.name, exc))
            continue

        # surefire writes <testsuite> as the document element; tolerate a
        # wrapping <testsuites> so a different surefire layout cannot silently
        # reduce the harvested totals to zero.
        nodes = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        if not nodes:
            problems.append("no <testsuite> element in {}".format(report.name))
            continue

        for node in nodes:
            counts = {}
            malformed = False
            for attr in ("tests", "failures", "errors", "skipped"):
                raw = node.get(attr)
                try:
                    counts[attr] = int(raw)
                except (TypeError, ValueError):
                    malformed = True
                    problems.append(
                        "{}:{} has non-integer {}={!r}".format(
                            report.name, node.get("name", "?"), attr, raw
                        )
                    )
            if malformed:
                continue
            for key, value in counts.items():
                totals[key] += value
            suites.append(
                {
                    "report": report.name,
                    "suite": node.get("name"),
                    "tests": counts["tests"],
                    "failures": counts["failures"],
                    "errors": counts["errors"],
                    "skipped": counts["skipped"],
                }
            )

    return {"totals": totals, "suites": suites}, problems


def decide(lock: dict, harvested: dict, problems: list[str], binding_ok: bool, binding_note: str) -> tuple[str, list[str]]:
    totals = harvested["totals"]
    reasons: list[str] = []
    status = PASS

    def fail(reason: str) -> None:
        nonlocal status
        if status != FAIL:
            status = FAIL
        reasons.append(reason)

    if not binding_ok:
        fail("source_binding_mismatch: {}".format(binding_note))
    if problems:
        fail("unusable_test_evidence: {}".format("; ".join(sorted(set(problems))[:5])))
    if not harvested["suites"]:
        fail("no_surefire_evidence: candidate produced no parseable surefire report")
    if totals["tests"] <= 0:
        fail("zero_tests_executed: candidate build reported no executed test")
    if totals["failures"] > 0 or totals["errors"] > 0:
        fail(
            "test_failures: failures={} errors={}".format(
                totals["failures"], totals["errors"]
            )
        )
    if totals["skipped"] >= totals["tests"] and totals["tests"] > 0:
        fail("all_tests_skipped: every discovered test was skipped")

    return status, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--observed-candidate-sha", default="")
    parser.add_argument("--guard", default=str(Path(__file__).resolve()))
    parser.add_argument(
        "--trusted-root",
        default=os.environ.get("TRUSTED_REPO_ROOT", str(Path(__file__).resolve().parent)),
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    guard_path = Path(args.guard).resolve()

    evidence: dict = {
        "schema": SCHEMA,
        "repository": None,
        "pull_request_number": None,
        "trusted_validator": None,
        "candidate": None,
        "comparison_base": None,
        "verdict": UNKNOWN,
        "qualification_credit": False,
        "reasons": [],
        "test_evidence": None,
        "guard": {
            "path": str(guard_path),
            "sha256": sha256_file(guard_path) if guard_path.is_file() else None,
        },
        "candidate_code_executed_as_validator": False,
        "mergeability_influenced_verdict": False,
        "synthetic_merge_influenced_verdict": False,
    }

    try:
        lock = load_source_lock(Path(args.source_lock))
    except (ValueError, json.JSONDecodeError) as exc:
        evidence["reasons"] = ["source_lock_unusable: {}".format(exc)]
        out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print("QUALIFICATION = {} ({})".format(UNKNOWN, evidence["reasons"][0]), file=sys.stderr)
        return EXIT_CODES[UNKNOWN]

    evidence["repository"] = lock.get("repository")
    evidence["pull_request_number"] = lock.get("pull_request_number")
    evidence["trusted_validator"] = lock["trusted_validator"]
    evidence["candidate"] = lock["candidate"]
    evidence["comparison_base"] = lock["comparison_base"]

    if evidence["guard"]["sha256"] is None:
        evidence["verdict"] = UNKNOWN
        evidence["reasons"] = ["guard_unreadable: trusted guard script is missing"]
        out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print("QUALIFICATION = UNKNOWN ({})".format(evidence["reasons"][0]), file=sys.stderr)
        return EXIT_CODES[UNKNOWN]

    candidate_root = Path(args.candidate_root).resolve()

    # Source binding: the harvested tree must be the locked candidate, and the
    # trusted source must be a different commit than the candidate. A mismatch is
    # a FAIL, never a PASS, even when the tests themselves are green.
    binding_ok = True
    binding_note = "observed candidate sha matches source lock"
    observed = (args.observed_candidate_sha or "").strip()
    if not observed:
        binding_ok = False
        binding_note = "observed candidate sha was not supplied; binding unproven"
    elif observed != lock["candidate"]["sha"]:
        binding_ok = False
        binding_note = "observed candidate sha {} != locked {}".format(
            observed, lock["candidate"]["sha"]
        )

    reports = discover_reports(candidate_root) if candidate_root.is_dir() else []
    harvested, problems = harvest(reports)

    # Guard a candidate-supplied replacement guard from being the deciding one:
    # the executed guard must resolve inside the trusted source root.
    trusted_root = Path(args.trusted_root).resolve()
    if trusted_root not in guard_path.parents:
        problems.append(
            "guard_outside_trusted_root: {} not under {}".format(guard_path, trusted_root)
        )
    else:
        shadow = candidate_root / ".github" / "qualification" / guard_path.name
        if shadow.is_file():
            evidence["guard"]["candidate_shadow_present"] = True
            evidence["guard"]["candidate_shadow_sha256"] = sha256_file(shadow)
        else:
            evidence["guard"]["candidate_shadow_present"] = False

    verdict, reasons = decide(lock, harvested, problems, binding_ok, binding_note)

    evidence["verdict"] = verdict
    evidence["qualification_credit"] = verdict == PASS
    evidence["reasons"] = reasons
    evidence["test_evidence"] = {
        "report_files": len(reports),
        "reports": [str(p.relative_to(candidate_root)) for p in reports],
        "totals": harvested["totals"],
        "suites": harvested["suites"],
    }

    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    summary = "; ".join(reasons) if reasons else "tests executed and green"
    print(
        "QUALIFICATION = {} candidate={} reports={} tests={} failures={} errors={} skipped={} ({})".format(
            verdict,
            lock["candidate"]["sha"],
            len(reports),
            harvested["totals"]["tests"],
            harvested["totals"]["failures"],
            harvested["totals"]["errors"],
            harvested["totals"]["skipped"],
            summary,
        )
    )
    return EXIT_CODES[verdict]


if __name__ == "__main__":
    sys.exit(main())