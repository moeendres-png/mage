#!/usr/bin/env python3
"""Inject one controlled semantic-state divergence into qualified WS06 evidence.

The immutable A/B/C evidence must first pass the exact WS06 comparator. A copied
B record is then changed in one canonical state checkpoint only. The same
comparator must reject it with E_SEMANTIC_DIVERGENCE while RNG and decision
streams remain identical.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from adapter import bind_replay_divergence, load_contract


def unique(root: Path, name: str) -> Path:
    matches = sorted(root.rglob(name))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {name} below {root}, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--ws06-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mutated-out", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str((args.ws06_root / "research/greenfield-qualification").resolve()))
    from semantic_replay import compare  # exact checked-out WS06 implementation

    a_path = unique(args.artifact_root, "process-A.json")
    b_path = unique(args.artifact_root, "process-B.json")
    c_path = unique(args.artifact_root, "process-C.json")

    baseline = compare([a_path, b_path, c_path])
    if baseline.get("status") != "PASS":
        raise SystemExit(f"immutable qualified WS06 A/B/C baseline no longer passes: {baseline}")
    if any(baseline.get(key) != 0 for key in (
        "semantic_state_divergences", "rng_event_divergences", "decision_event_divergences"
    )):
        raise SystemExit("qualified WS06 baseline contains a semantic divergence")

    replay_b = json.loads(b_path.read_text(encoding="utf-8"))
    states = replay_b.get("states")
    if not isinstance(states, list) or len(states) < 2 or not isinstance(states[1], dict):
        raise SystemExit("qualified WS06 process-B has no mutable second semantic checkpoint")
    mutated = copy.deepcopy(replay_b)
    mutated["states"][1]["ws22_controlled_semantic_divergence"] = "BOUNDARY_PROBE"
    args.mutated_out.parent.mkdir(parents=True, exist_ok=True)
    args.mutated_out.write_text(json.dumps(mutated, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    divergent = compare([a_path, args.mutated_out, c_path])
    if divergent.get("status") != "FAIL":
        raise SystemExit(f"divergent replay was silently accepted: {divergent}")
    if divergent.get("semantic_state_divergences", 0) < 1:
        raise SystemExit("controlled state divergence was not detected")
    if divergent.get("rng_event_divergences") != 0 or divergent.get("decision_event_divergences") != 0:
        raise SystemExit("controlled state-only injection unexpectedly changed RNG or decision comparison")
    if divergent.get("stdout_used_as_replay_criterion") is not False:
        raise SystemExit("WS06 comparator unexpectedly used stdout as replay criterion")

    trace = bind_replay_divergence(load_contract(args.contract), divergent)
    trace["qualified_baseline"] = {
        "status": baseline.get("status"),
        "semantic_state_divergences": baseline.get("semantic_state_divergences"),
        "rng_event_divergences": baseline.get("rng_event_divergences"),
        "decision_event_divergences": baseline.get("decision_event_divergences"),
        "stdout_used_as_replay_criterion": baseline.get("stdout_used_as_replay_criterion"),
    }
    trace["injection"] = {
        "kind": "CONTROLLED_CANONICAL_SEMANTIC_STATE_FIELD",
        "document": "process-B copy",
        "checkpoint_index": 1,
        "field": "ws22_controlled_semantic_divergence",
        "rng_stream_modified": False,
        "decision_stream_modified": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("WS22_REPLAY_DIVERGENCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
