#!/usr/bin/env python3
"""Record pull-request mergeability as data, explicitly without qualification credit.

Separated from the qualification verdict on purpose: GitHub's synthetic merge
result describes whether a PR *could* merge, never whether the candidate is
qualified. Merging is not performed and no merge result is built or executed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

SCHEMA = "mage.candidate-qualification.mergeability/1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    def env(name: str) -> str:
        return (os.environ.get(name) or "").strip() or None

    record = {
        "schema": SCHEMA,
        "constitutes_qualification_credit": False,
        "read_by_qualification_verdict": False,
        "synthetic_merge_built_or_executed": False,
        "mergeable": env("MERGEABLE"),
        "mergeable_state": env("MERGEABLE_STATE"),
        "merge_commit_sha": env("MERGE_COMMIT_SHA"),
        "head_sha": env("HEAD_SHA"),
        "base_sha": env("BASE_SHA"),
        "default_branch": env("DEFAULT_BRANCH_SHA"),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(
        "MERGEABILITY recorded mergeable={} state={} (qualification_credit=false)".format(
            record["mergeable"], record["mergeable_state"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())