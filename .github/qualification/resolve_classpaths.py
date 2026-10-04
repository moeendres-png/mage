#!/usr/bin/env python3
"""Collect each required module's test classpath from the sandboxed reactor build.

Trusted default-branch source. The candidate build runs, as the sandbox
account, ``mvn test-compile dependency:build-classpath`` in ONE reactor session
with ``-Dmdep.outputFile=target/c12-test-classpath.txt``. Doing both in one
session is what makes sibling modules resolve to the candidate's own reactor
output rather than to a (possibly stale, possibly absent) installed
``org/mage`` jar from the Maven cache.

This script only reads those files back, as data: the module list comes from
the trusted Git enumeration of the locked candidate commit (``corpus_policy``),
never from the working tree, and every file is opened refusing symlinks. A
module whose file is missing is absent from the map, and ``witness.py`` then
fails closed: a module is never dropped for being inconvenient.

The result is candidate-influenced input, never authority (see witness.py).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import corpus_policy  # noqa: E402

SCHEMA = "mage.candidate-qualification.module-classpaths/1"
CLASSPATH_FILE = "target/c12-test-classpath.txt"


def read_candidate_text(path: Path) -> str | None:
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    with os.fdopen(fd, "rb") as handle:
        return handle.read(8 * 1024 * 1024).decode("utf-8", errors="replace")


def collect(git_repo: str, candidate_sha: str, candidate_root: Path) -> tuple[dict, dict]:
    modules = sorted({e["module"] for e in corpus_policy.enumerate_rev(git_repo, candidate_sha)})
    mapping: dict[str, str] = {}
    record = {"schema": SCHEMA, "candidate_sha": candidate_sha, "classpath_file": CLASSPATH_FILE,
              "modules": modules, "unresolved": []}
    for module in modules:
        text = read_candidate_text(candidate_root / module / CLASSPATH_FILE)
        if text is None:
            record["unresolved"].append(module)
            continue
        mapping[module] = "".join(text.splitlines())
    return mapping, record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-repo", required=True)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--out", required=True, help="MODULE_CLASSPATHS.json (module -> classpath)")
    parser.add_argument("--record", required=True)
    args = parser.parse_args()
    mapping, record = collect(args.git_repo, args.candidate_sha, Path(args.candidate_root))
    Path(args.out).write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")
    Path(args.record).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print("MODULE_CLASSPATHS resolved={} unresolved={}".format(len(mapping), json.dumps(record["unresolved"], ensure_ascii=True)))
    return 0 if not record["unresolved"] else 1


if __name__ == "__main__":
    sys.exit(main())
