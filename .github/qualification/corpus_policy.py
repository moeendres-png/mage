#!/usr/bin/env python3
"""Trusted required-test corpus: enumeration, baseline and delta policy.

Trust boundary: trusted default-branch code. Every input is read as Git data
from the trusted object store (``git ls-tree`` / ``git show`` of an exact
commit), never from a working tree that candidate code could have touched.

Why a baseline exists
---------------------
Enumerating the required tests from the candidate tree alone lets the candidate
decide what is required: rename every ``*Test`` class to ``*Check``, move it out
of ``src/test/java`` or delete it, keep one trivially green test, and the
witness faithfully executes the one test that is left. The *required* corpus
must therefore be anchored to something the candidate cannot edit: the baseline
file committed on the default branch, read at the trusted validator commit.

Policy, evaluated in trusted code only
--------------------------------------
* The trusted baseline must be present (else UNKNOWN), well formed (else
  UNKNOWN) and fresh: its entries must equal the trusted enumeration of the
  trusted validator commit, under the same enumeration rule (else UNKNOWN).
  A stale baseline would silently stop protecting tests added since.
* Every baseline entry must still be enumerated in the candidate. A missing
  entry is a FAIL, whatever the reason (deleted, renamed outside the class
  regex, moved outside a test source root, moved to another module), unless the
  trusted baseline lists it under ``approved_removals``. Approvals only count
  when they are on the default branch: an approval the candidate adds to its
  own copy of the baseline grants nothing to that candidate.
* A baseline entry the candidate lacks because it was added to the default
  branch after the candidate's merge base is reported separately
  (``candidate_behind_default_branch``): still a FAIL, but with the honest
  cause, which is fixed by merging the default branch.
* Candidate additions are welcome and are required as well: the required set
  is every pair the candidate enumerates.
* The candidate's own baseline file must describe the candidate exactly, so a
  merge can never leave the default branch with a stale baseline. Adding a test
  therefore means adding its entry; removing one means a prior, separately
  reviewed approval plus dropping both the entry and the approval.

The approved update path for a removal or rename is two reviewed changes:
first land the approval (the tests still exist, so that change qualifies),
then land the removal. Nothing here can approve anything by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import PurePosixPath

# Trusted code never resolves tools from the inherited PATH (see sandbox.TOOL_PATH).
GIT = shutil.which("git", path="/usr/sbin:/usr/bin:/sbin:/bin") or "/usr/bin/git"

BASELINE_SCHEMA = "mage.candidate-qualification.test-corpus-baseline/1"
POLICY_SCHEMA = "mage.candidate-qualification.corpus-policy/1"
BASELINE_PATH = ".github/qualification/test_corpus_baseline.json"

# Selection rule for what must run, never an evidence heuristic: a class that
# matches but is missing makes the witness FAIL rather than shrinking the set.
TEST_CLASS_RE = r"(Test|Tests|TestCase|Spec|IT)$"
SOURCE_DIR_MARKERS = ("src/test/java", "src/test/kotlin", "src/test/groovy")
SOURCE_SUFFIX = ".java"
PAIR_SEPARATOR = "::"

ENUMERATION_RULE = {
    "class_regex": TEST_CLASS_RE,
    "source_markers": list(SOURCE_DIR_MARKERS),
    "source_suffix": SOURCE_SUFFIX,
    "pair_format": "module" + PAIR_SEPARATOR + "fully.qualified.ClassName",
    "module_rule": "nearest ancestor directory of the test source root that holds a pom.xml",
}


class CorpusError(RuntimeError):
    pass


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(
        [GIT, "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise CorpusError("git {} failed: {}".format(" ".join(args), proc.stderr.strip()))
    return proc.stdout


def tree_paths(repo: str, rev: str) -> list[str]:
    out = git(repo, "ls-tree", "-r", "--name-only", "-z", rev)
    return [p for p in out.split("\0") if p]


def read_blob(repo: str, rev: str, path: str) -> bytes | None:
    proc = subprocess.run(
        [GIT, "-C", str(repo), "show", "{}:{}".format(rev, path)],
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def pair(module: str, class_name: str) -> str:
    return "{}{}{}".format(module, PAIR_SEPARATOR, class_name)


def split_pair(value: str) -> tuple[str, str]:
    module, _, class_name = value.partition(PAIR_SEPARATOR)
    return module, class_name


def enumerate_paths(paths: list[str]) -> list[dict]:
    """Enumerate required (module, class) entries from a list of tree paths."""
    pattern = re.compile(TEST_CLASS_RE)
    pom_dirs = {str(PurePosixPath(p).parent) for p in paths if PurePosixPath(p).name == "pom.xml"}
    found: dict[str, set] = {}
    for path in paths:
        if not path.endswith(SOURCE_SUFFIX):
            continue
        for marker in SOURCE_DIR_MARKERS:
            token = marker + "/"
            if path.startswith(token):
                prefix, rest = "", path[len(token):]
            elif "/" + token in path:
                prefix, rest = path.split("/" + token, 1)
            else:
                continue
            module = _module_of(prefix, pom_dirs)
            if module is None:
                break
            stem = PurePosixPath(rest).with_suffix("")
            if pattern.search(stem.name):
                found.setdefault(module, set()).add(".".join(stem.parts))
            break
    return [
        {"module": module, "class_name": name}
        for module in sorted(found)
        for name in sorted(found[module])
    ]


def _module_of(source_parent: str, pom_dirs: set) -> str | None:
    current = PurePosixPath(source_parent) if source_parent else PurePosixPath(".")
    while True:
        key = str(current)
        if key in pom_dirs:
            return key
        if key == ".":
            return None
        current = current.parent


def enumerate_rev(repo: str, rev: str) -> list[dict]:
    return enumerate_paths(tree_paths(repo, rev))


def pairs_of(entries: list[dict]) -> list[str]:
    return sorted({pair(e["module"], e["class_name"]) for e in entries})


def entries_digest(entries: list[str]) -> str:
    return hashlib.sha256(("\n".join(entries) + "\n").encode("utf-8")).hexdigest()


def build_baseline(entries: list[str], approved_removals: list[dict] | None = None) -> dict:
    entries = sorted(set(entries))
    return {
        "schema": BASELINE_SCHEMA,
        "enumeration_rule": ENUMERATION_RULE,
        "entries": entries,
        "entries_count": len(entries),
        "entries_sha256": entries_digest(entries),
        "approved_removals": sorted(approved_removals or [], key=lambda r: r.get("entry", "")),
    }


def validate_baseline(doc) -> list[str]:
    """Structural problems of a baseline document; empty means well formed."""
    problems: list[str] = []
    if not isinstance(doc, dict):
        return ["baseline is not a JSON object"]
    if doc.get("schema") != BASELINE_SCHEMA:
        problems.append("unexpected schema {!r}".format(doc.get("schema")))
    entries = doc.get("entries")
    if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
        problems.append("entries must be a list of strings")
        return problems
    if entries != sorted(set(entries)):
        problems.append("entries must be sorted and unique")
    for entry in entries:
        module, class_name = split_pair(entry)
        if not module or not class_name or PAIR_SEPARATOR in class_name:
            problems.append("malformed entry {!r}".format(entry))
            break
    if doc.get("entries_count") != len(entries):
        problems.append("entries_count does not match entries")
    if doc.get("entries_sha256") != entries_digest(entries):
        problems.append("entries_sha256 does not match entries")
    removals = doc.get("approved_removals")
    if not isinstance(removals, list):
        problems.append("approved_removals must be a list")
        return problems
    seen = set()
    for removal in removals:
        if not isinstance(removal, dict):
            problems.append("approved removal is not an object")
            continue
        entry = removal.get("entry")
        if not isinstance(entry, str) or entry not in entries:
            # An approval for a test the baseline no longer lists is stale: it
            # would otherwise linger as a blanket licence for a future removal.
            problems.append("approved removal {!r} is not a baseline entry".format(entry))
        if not str(removal.get("reason") or "").strip():
            problems.append("approved removal {!r} has no reason".format(entry))
        if not str(removal.get("reference") or "").strip():
            problems.append("approved removal {!r} has no review reference".format(entry))
        if entry in seen:
            problems.append("approved removal {!r} is duplicated".format(entry))
        seen.add(entry)
    return problems


def load_baseline_blob(blob: bytes | None) -> tuple[dict | None, list[str]]:
    if blob is None:
        return None, ["missing"]
    try:
        doc = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, ["unparseable: {}".format(exc)]
    return doc, validate_baseline(doc)


def evaluate(repo: str, trusted_rev: str, base_rev: str, candidate_rev: str) -> dict:
    """Evaluate the candidate corpus against the trusted baseline. Git data only."""
    result = {
        "schema": POLICY_SCHEMA,
        "status": "UNKNOWN",
        "baseline_path": BASELINE_PATH,
        "trusted_rev": trusted_rev,
        "comparison_base_rev": base_rev,
        "candidate_rev": candidate_rev,
        "enumeration_rule": ENUMERATION_RULE,
        "trusted_baseline": None,
        "unknowns": [],
        "violations": [],
        "required_pairs": [],
        "additions": [],
        "removed_without_approval": [],
        "behind_default_branch": [],
        "approved_removals_applied": [],
        "candidate_baseline": None,
    }

    candidate_pairs = pairs_of(enumerate_rev(repo, candidate_rev))
    result["required_pairs"] = candidate_pairs

    doc, problems = load_baseline_blob(read_blob(repo, trusted_rev, BASELINE_PATH))
    trusted_pairs = pairs_of(enumerate_rev(repo, trusted_rev))
    summary = {"present": doc is not None, "problems": problems}
    result["trusted_baseline"] = summary
    if problems == ["missing"]:
        result["unknowns"].append("corpus_baseline_missing: {} absent at trusted {}".format(BASELINE_PATH, trusted_rev))
        return result
    if problems:
        result["unknowns"].append("corpus_baseline_malformed: {}".format("; ".join(problems[:5])))
        return result

    entries = doc["entries"]
    summary["entries_count"] = len(entries)
    summary["entries_sha256"] = doc["entries_sha256"]
    if doc.get("enumeration_rule") != ENUMERATION_RULE:
        result["unknowns"].append("corpus_baseline_stale: enumeration rule differs from the trusted validator")
        return result
    if entries != trusted_pairs:
        missing = sorted(set(trusted_pairs) - set(entries))
        extra = sorted(set(entries) - set(trusted_pairs))
        summary["unlisted_trusted_tests"] = missing[:50]
        summary["listed_but_absent"] = extra[:50]
        result["unknowns"].append(
            "corpus_baseline_stale: baseline differs from the trusted enumeration "
            "({} unlisted, {} absent)".format(len(missing), len(extra))
        )
        return result

    approved = {r["entry"]: r for r in doc["approved_removals"]}
    base_pairs = set(pairs_of(enumerate_rev(repo, base_rev)))
    candidate_set = set(candidate_pairs)
    for entry in entries:
        if entry in candidate_set:
            continue
        if entry in approved:
            result["approved_removals_applied"].append(approved[entry])
        elif entry not in base_pairs:
            result["behind_default_branch"].append(entry)
        else:
            result["removed_without_approval"].append(entry)
    result["additions"] = sorted(candidate_set - set(entries))

    if result["removed_without_approval"]:
        result["violations"].append(
            "baseline_test_removed: {} required test class(es) no longer enumerated without a "
            "default-branch approval: {}".format(
                len(result["removed_without_approval"]),
                ",".join(result["removed_without_approval"][:10]),
            )
        )
    if result["behind_default_branch"]:
        result["violations"].append(
            "candidate_behind_default_branch: {} baseline test class(es) were added after the "
            "merge base; merge the default branch: {}".format(
                len(result["behind_default_branch"]),
                ",".join(result["behind_default_branch"][:10]),
            )
        )

    candidate_doc, candidate_problems = load_baseline_blob(read_blob(repo, candidate_rev, BASELINE_PATH))
    candidate_summary = {"present": candidate_doc is not None, "problems": candidate_problems}
    result["candidate_baseline"] = candidate_summary
    if candidate_problems:
        result["violations"].append(
            "candidate_corpus_baseline_invalid: {}".format("; ".join(candidate_problems[:5]))
        )
    else:
        unlisted = sorted(candidate_set - set(candidate_doc["entries"]))
        listed_absent = sorted(set(candidate_doc["entries"]) - candidate_set)
        candidate_summary["unlisted"] = unlisted[:50]
        candidate_summary["listed_but_absent"] = listed_absent[:50]
        candidate_summary["consistent"] = not unlisted and not listed_absent and (
            candidate_doc.get("enumeration_rule") == ENUMERATION_RULE
        )
        if not candidate_summary["consistent"]:
            result["violations"].append(
                "candidate_corpus_baseline_not_updated: the candidate's {} does not describe the "
                "candidate ({} unlisted, {} listed but absent)".format(
                    BASELINE_PATH, len(unlisted), len(listed_absent)
                )
            )

    result["status"] = "VIOLATION" if result["violations"] else "OK"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write the baseline for an exact commit")
    gen.add_argument("--repo", required=True)
    gen.add_argument("--rev", required=True)
    gen.add_argument("--keep-approvals-from", default="", help="existing baseline whose still-valid approvals are kept")
    gen.add_argument("--out", required=True)

    ev = sub.add_parser("evaluate", help="evaluate a candidate against the trusted baseline")
    ev.add_argument("--repo", required=True)
    ev.add_argument("--trusted", required=True)
    ev.add_argument("--base", required=True)
    ev.add_argument("--candidate", required=True)
    ev.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "generate":
        entries = pairs_of(enumerate_rev(args.repo, args.rev))
        approvals = []
        if args.keep_approvals_from:
            with open(args.keep_approvals_from, "rb") as handle:
                previous, _ = load_baseline_blob(handle.read())
            approvals = [
                r for r in (previous or {}).get("approved_removals") or [] if r.get("entry") in entries
            ]
        doc = build_baseline(entries, approvals)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print("CORPUS_BASELINE entries={} sha256={}".format(len(entries), doc["entries_sha256"]))
        return 0

    try:
        result = evaluate(args.repo, args.trusted, args.base, args.candidate)
    except CorpusError as exc:
        result = {"schema": POLICY_SCHEMA, "status": "UNKNOWN", "unknowns": ["corpus_policy_error: {}".format(exc)]}
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("CORPUS_POLICY = {}".format(result["status"]))
    return {"OK": 0, "VIOLATION": 1}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
