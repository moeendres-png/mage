#!/usr/bin/env python3
"""Render the source-bound Mage qualification verdict as a job summary.

Reporting only. This script never converts FAIL or UNKNOWN into PASS and never
changes the job's exit status; the enforcing step uses the scorer's own exit
code. Missing or unreadable inputs render as UNKNOWN rather than being omitted,
so a summary can never look cleaner than the evidence.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

VERDICTS = ["PASS", "FAIL", "UNKNOWN"]


def load(path: str) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {"_missing": True}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {"_unreadable": True}


def identity(lock: dict, key: str) -> str:
    block = lock.get(key) or {}
    sha, tree = block.get("sha"), block.get("tree")
    if not sha:
        return "UNAVAILABLE"
    return "{} (tree {})".format(sha, tree or "UNAVAILABLE")


def render(lock, evidence, witness, audit, build_exit, run_id) -> str:
    lines = ["## Mage trusted candidate qualification", ""]
    verdict = evidence.get("verdict")
    lines.append("**QUALIFICATION VERDICT: {}**".format(verdict or "UNKNOWN"))
    lines.append("")
    lines.append("| identity | sha (tree) |")
    lines.append("| --- | --- |")
    lines.append("| trusted_validator | {} |".format(identity(lock, "trusted_validator")))
    lines.append("| candidate | {} |".format(identity(lock, "candidate")))
    lines.append("| comparison_base | {} |".format(identity(lock, "comparison_base")))
    lines.append("")

    totals = ((evidence.get("test_evidence") or {}).get("totals")) or {}
    lines.append("### Trusted execution")
    lines.append("")
    lines.append("- evidence origin: `{}`".format((evidence.get("test_evidence") or {}).get("origin")))
    lines.append("- candidate build exit: `{}` (non-zero is an unconditional FAIL)".format(build_exit or "NOT_RECORDED"))
    lines.append("- required test classes (trusted enumeration): `{}`".format(
        len((evidence.get("test_evidence") or {}).get("required_test_classes") or [])
    ))
    lines.append("- classes the trusted launcher never entered: `{}`".format(
        totals and (evidence.get("test_evidence") or {}).get("classes_never_entered") or []
    ))
    if totals:
        lines.append(
            "- tests found={} started={} succeeded={} failed={} aborted={} skipped={}".format(
                totals.get("found"), totals.get("started"), totals.get("succeeded"),
                totals.get("failed"), totals.get("aborted"), totals.get("skipped"),
            )
        )
    else:
        lines.append("- trusted execution totals: **UNAVAILABLE**")
    lines.append("- candidate-authored evidence used: `{}`".format(
        evidence.get("candidate_authored_evidence_used")
    ))
    lines.append("- candidate reports parsed: `{}`".format(evidence.get("candidate_reports_parsed")))
    lines.append("- witness driver sha256: `{}`".format(
        (evidence.get("guard") or {}).get("witness_driver_sha256")
    ))
    lines.append("- scorer sha256: `{}`".format((evidence.get("guard") or {}).get("sha256")))
    lines.append("- run_id: `{}`".format(run_id))
    lines.append("")

    lines.append("### Build-definition audit")
    lines.append("")
    lines.append("- status: `{}`".format((audit or {}).get("status") or "UNKNOWN"))
    violations = (audit or {}).get("violations") or []
    if violations:
        for violation in violations[:10]:
            lines.append("- {} `{}`: {}".format(violation.get("kind"), violation.get("path"), violation.get("detail")))
    else:
        lines.append("- violations: none")
    lines.append("")

    reasons = evidence.get("reasons") or []
    lines.append("### Reasons")
    lines.append("")
    if reasons:
        for reason in reasons:
            lines.append("- {}".format(reason))
    else:
        lines.append("- none")
    lines.append("")

    lines.append("### Mergeability (informational, no qualification credit)")
    lines.append("")
    lines.append(
        "Mergeability is recorded in a separate job and is never read by this verdict. "
        "A synthetic merge result is Git data about the pull request, not qualification evidence."
    )
    lines.append("")
    lines.append("`PRODUCTION_PROVIDER = NOT_SELECTED` · `ARCHITECTURE_FREEZE = NOT_CLAIMED`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--witness", default="")
    parser.add_argument("--audit", default="")
    parser.add_argument("--build-exit-code", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    lock = load(args.source_lock)
    evidence = load(args.evidence)
    witness = load(args.witness)
    audit = load(args.audit)

    if evidence.get("verdict") not in VERDICTS:
        evidence = dict(evidence)
        evidence["verdict"] = "UNKNOWN"
        evidence["reasons"] = (evidence.get("reasons") or []) + [
            "evidence_unreadable: summary cannot confirm a verdict"
        ]

    text = render(lock, evidence, witness, audit, args.build_exit_code, args.run_id)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print("QUALIFICATION_SUMMARY = " + json.dumps(text, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())