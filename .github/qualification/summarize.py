#!/usr/bin/env python3
"""Render the source-bound Mage qualification verdict as a job summary.

Reporting only. This script never converts FAIL or UNKNOWN into PASS and never
changes the exit status of the job; the enforcing step is separate and uses the
guard's own exit code. Missing or unreadable inputs render as UNKNOWN rather than
being omitted, so a summary can never look cleaner than the evidence.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

VERDICT_ORDER = ["PASS", "FAIL", "UNKNOWN"]


def load(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        return {"_missing": True}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {"_unreadable": True}


def identity(lock: dict, key: str) -> str:
    block = lock.get(key) or {}
    sha = block.get("sha")
    tree = block.get("tree")
    if not sha:
        return "UNAVAILABLE"
    return "{} (tree {})".format(sha, tree or "UNAVAILABLE")


def render(source_lock: dict, evidence: dict, build_exit: str, run_id: str) -> str:
    lines = ["## Mage trusted candidate qualification", ""]

    lock_status = source_lock.get("status") or ("UNKNOWN" if source_lock.get("_missing") else "UNKNOWN")
    lines.append("**QUALIFICATION VERDICT: {}**".format(evidence.get("verdict") or "UNKNOWN"))
    lines.append("")
    lines.append("| identity | sha (tree) |")
    lines.append("| --- | --- |")
    lines.append("| trusted_validator | {} |".format(identity(source_lock, "trusted_validator")))
    lines.append("| candidate | {} |".format(identity(source_lock, "candidate")))
    lines.append("| comparison_base | {} |".format(identity(source_lock, "comparison_base")))
    lines.append("")

    lines.append("- source_lock: `{}`".format(lock_status))
    lines.append("- candidate_fetch_ref: `{}`".format(source_lock.get("candidate_fetch_ref")))
    lines.append("- maven_exit_code: `{}` (informational, never a pass condition)".format(build_exit or "NOT_RECORDED"))
    lines.append("- candidate_code_executed_as_validator: `{}`".format(
        evidence.get("candidate_code_executed_as_validator")
    ))
    lines.append("- guard_sha256: `{}`".format((evidence.get("guard") or {}).get("sha256")))
    lines.append("- run_id: `{}`".format(run_id))
    lines.append("")

    test_evidence = evidence.get("test_evidence") or {}
    totals = test_evidence.get("totals")
    if totals is None:
        lines.append("- harvested test evidence: **UNAVAILABLE**")
    else:
        lines.append(
            "- harvested surefire evidence: {} report file(s), tests={} failures={} errors={} skipped={}".format(
                test_evidence.get("report_files"),
                totals.get("tests"),
                totals.get("failures"),
                totals.get("errors"),
                totals.get("skipped"),
            )
        )
    lines.append("")

    reasons = evidence.get("reasons") or []
    if reasons:
        lines.append("### Reasons")
        lines.append("")
        for reason in reasons:
            lines.append("- {}".format(reason))
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
    parser.add_argument("--mergeability", default="")
    parser.add_argument("--build-exit-code", default="")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    source_lock = load(args.source_lock)
    evidence = load(args.evidence)
    verdict = evidence.get("verdict")
    if verdict not in VERDICT_ORDER:
        verdict = "UNKNOWN"
        evidence = dict(evidence)
        evidence["verdict"] = "UNKNOWN"
        evidence.setdefault("reasons", []).append("evidence_unreadable: summary cannot confirm a verdict")

    text = render(source_lock, evidence, args.build_exit_code, args.run_id)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())