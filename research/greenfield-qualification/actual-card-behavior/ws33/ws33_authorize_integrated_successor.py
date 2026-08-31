#!/usr/bin/env python3
"""Authorize a Generation-2 descendant as an integrated WS33 qualification source.

This mutates only the working evidence artifact's successor-provenance document.
It never changes coverage or path status. Authorization is derived from Git ancestry,
source-tree identity, the frozen Generation-2 gate, and strict integrated ownership.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

BASE_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
BASE_TREE = "837f445f78bb26462653c58baf1532e294151b10"
ALLOWED_PREFIXES = (
    ".github/workflows/ws33-",
    "research/greenfield-qualification/actual-card-behavior/ws33/",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_INTEGRATED_SUCCESSOR=FAIL " + msg)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=check)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    args = ap.parse_args()

    root = args.root.resolve()
    repo = args.repo_root.resolve()
    gate = load(root / "WS33_GENERATION2_BASE_GATE.json")
    provenance_path = root / "abi/WS33_SUCCESSOR_PROVENANCE.json"
    provenance = load(provenance_path)

    require(gate.get("PARALLEL_CHILDREN_ELIGIBLE") is True, "Generation-2 input is not qualified")
    gen2_head = gate.get("source_head")
    gen2_tree = gate.get("source_tree")
    require(isinstance(gen2_head, str) and len(gen2_head) == 40, "missing Generation-2 head")
    require(isinstance(gen2_tree, str) and len(gen2_tree) == 40, "missing Generation-2 tree")

    actual_source_tree = git(repo, "rev-parse", f"{args.source_head}^{{tree}}").stdout.strip()
    require(actual_source_tree == args.source_tree, "source tree does not match source head")
    actual_gen2_tree = git(repo, "rev-parse", f"{gen2_head}^{{tree}}").stdout.strip()
    require(actual_gen2_tree == gen2_tree, "Generation-2 tree no longer matches frozen head")

    ancestor = git(repo, "merge-base", "--is-ancestor", gen2_head, args.source_head, check=False)
    require(ancestor.returncode == 0, "qualification source is not a Generation-2 descendant")

    changed = [line for line in git(repo, "diff", "--name-only", gen2_head, args.source_head).stdout.splitlines() if line]
    bad = [path for path in changed if not path.startswith(ALLOWED_PREFIXES)]
    require(not bad, "out-of-scope integrated source changes: " + ",".join(bad))

    key = args.source_head + ":" + args.source_tree
    approvals = provenance.setdefault("approved_qualification_sources", {})
    existing = approvals.get(key)
    derived = {
        "descends_from_model_base": True,
        "model_base_head": BASE_HEAD,
        "model_base_tree": BASE_TREE,
        "generation2_base_head": gen2_head,
        "generation2_base_tree": gen2_tree,
        "generation2_descendant_verified": True,
        "source_tree_verified": True,
        "scoped_integrated_ownership_verified": True,
        "approval_class": "GENERATION2_DESCENDANT_INTEGRATED_QUALIFICATION",
    }
    if existing is None:
        approvals[key] = derived
    else:
        require(existing.get("descends_from_model_base") is True, "existing approval lost model ancestry")
        require(existing.get("model_base_head") == BASE_HEAD, "existing approval has wrong model base head")
        require(existing.get("model_base_tree") == BASE_TREE, "existing approval has wrong model base tree")
        existing.update(derived)

    write(provenance_path, provenance)
    print(json.dumps({
        "WS33_INTEGRATED_SUCCESSOR": "PASS",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "generation2_base_head": gen2_head,
        "generation2_base_tree": gen2_tree,
        "changed_file_count": len(changed),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
