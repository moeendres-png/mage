#!/usr/bin/env python3
"""Resolve and verify the trusted/candidate source identities for Mage qualification.

Trust boundary: this script runs from the trusted default-branch checkout only.
Candidate Git objects are read strictly as data (``rev-parse`` / ``merge-base``);
no candidate file is executed, imported, sourced or copied into trusted state.

Any identity that cannot be proven is a hard failure. There is no partial or
inferred identity: an unproven identity is never treated as a match.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "mage.candidate-qualification.source-lock/1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class SourceLockError(Exception):
    """A source identity could not be proven. Always fail closed."""


def git(*args: str, cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SourceLockError(
            "git {} failed ({}): {}".format(
                " ".join(args), proc.returncode, proc.stderr.strip()
            )
        )
    return proc.stdout.strip()


def require_sha(value: str, label: str) -> str:
    if not HEX40.match(value or ""):
        raise SourceLockError("{} is not a full 40-hex sha: {!r}".format(label, value))
    return value


def resolve(repo: Path, ref: str, label: str) -> dict:
    sha = require_sha(git("rev-parse", ref, cwd=repo), "{} sha".format(label))
    tree = require_sha(
        git("rev-parse", "{}^{{tree}}".format(ref), cwd=repo), "{} tree".format(label)
    )
    return {"sha": sha, "tree": tree}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--default-branch", required=True)
    parser.add_argument("--trusted-sha", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--pr-number", required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument(
        "--candidate-ref",
        default="",
        help="override the fetched candidate ref; production always uses the PR head ref",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    repo = Path(os.environ.get("TRUSTED_REPO_ROOT", ".")).resolve()
    out = Path(args.out)

    try:
        trusted_sha = require_sha(args.trusted_sha, "trusted")
        candidate_sha = require_sha(args.candidate_sha, "candidate")

        if args.base_ref != args.default_branch:
            raise SourceLockError(
                "base ref {!r} is not the default branch {!r}".format(
                    args.base_ref, args.default_branch
                )
            )
        if not re.match(r"^[1-9][0-9]*$", args.pr_number or ""):
            raise SourceLockError("pr number is not a positive integer")

        # The executing checkout must be the trusted default-branch head.
        head_sha = git("rev-parse", "HEAD", cwd=repo)
        if head_sha != trusted_sha:
            raise SourceLockError(
                "executing checkout HEAD {} is not the trusted sha {}".format(
                    head_sha, trusted_sha
                )
            )
        trusted = resolve(repo, trusted_sha, "trusted_validator")

        # Candidate enters only as fetched Git objects, verified against the
        # event-declared head sha. Nothing from the candidate is checked out here.
        candidate_ref = args.candidate_ref or "refs/pull/{}/head".format(args.pr_number)
        git("fetch", "--no-tags", "origin", candidate_ref, cwd=repo)
        fetched = git("rev-parse", "FETCH_HEAD", cwd=repo)
        if fetched != candidate_sha:
            raise SourceLockError(
                "fetched candidate {} from {} does not match event head sha {}".format(
                    fetched, candidate_ref, candidate_sha
                )
            )
        git("cat-file", "-e", "{}^{{commit}}".format(candidate_sha), cwd=repo)
        candidate = resolve(repo, candidate_sha, "candidate")

        # Comparison base is inspected Git data only; it is never merged, built
        # or executed and it carries no qualification credit of its own.
        merge_base_sha = git("merge-base", trusted_sha, candidate_sha, cwd=repo)
        comparison_base = resolve(repo, merge_base_sha, "comparison_base")

        if trusted["tree"] == candidate["tree"] and trusted["sha"] == candidate["sha"]:
            raise SourceLockError("candidate and trusted validator are the same commit")

    except SourceLockError as exc:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "status": "UNKNOWN",
                    "qualification_credit": False,
                    "error": str(exc),
                    "repository": args.repo,
                    "pull_request_number": args.pr_number,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        print("SOURCE_LOCK = UNKNOWN: {}".format(json.dumps(str(exc), ensure_ascii=True)), file=sys.stderr)
        return 2

    lock = {
        "schema": SCHEMA,
        "status": "LOCKED",
        "repository": args.repo,
        "default_branch": args.default_branch,
        "pull_request_number": args.pr_number,
        "run_id": args.run_id,
        "candidate_fetch_ref": candidate_ref,
        "candidate_fetch_ref_overridden": bool(args.candidate_ref),
        "trusted_validator": trusted,
        "candidate": candidate,
        "comparison_base": comparison_base,
        "candidate_code_executed_as_validator": False,
        "comparison_base_merged_or_executed": False,
        "source_lock_script_sha256": None,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    print(
        "SOURCE_LOCK = LOCKED trusted={} candidate={} comparison_base={}".format(
            trusted["sha"], candidate["sha"], comparison_base["sha"]
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())