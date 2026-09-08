#!/usr/bin/env python3
"""Filter the full cost campaign to the authoritative WS33B queue subsets.

Verifies the four canonical Cost work-queue items (090/186, 091/8, 092/206,
093/2), binds them against the prepared cases, separates the registered
terminal blockers, and emits the B2 case set and plan.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TERMINAL_BLOCKERS = {
    # Dead Triggered valids in-pin; see WS33B_COST_TERMINAL_BLOCKERS_20260908.md.
    "forge-behavior-v2:83da92d042e1c29d770df07397319afb1a2acb9d": "DEAD_VALID_TriggeredCards",
    "forge-behavior-v2:8671678f79ce684700bee73e1fedcbdd2cc4fa94": "DEAD_VALID_TriggeredNewCard",
    "forge-behavior-v2:f4c7f4744d2aafd7867c487427756616567b0177": "DEAD_VALID_TriggeredNewCard",
    "forge-behavior-v2:e45204fac7594e256cef247c35ef92defba2b797": "DEAD_VALID_TriggeredSource",
    "forge-behavior-v2:fdfdd242632a5ba2208e4acace7b4500bb347efe": "DEAD_VALID_OriginalHost",
}

EXPECTED_ITEMS = {
    ("ws33-g2-template-090", "DECISION+HIDDEN+REPLAY"): 186,
    ("ws33-g2-template-091", "DECISION+RNG+HIDDEN+REPLAY"): 8,
    ("ws33-g2-template-092", "HIDDEN"): 206,
    ("ws33-g2-template-093", "RNG+HIDDEN+REPLAY"): 2,
}


def fail(message: str) -> None:
    raise SystemExit("WS33_ABC_B2_FILTER=FAIL " + message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--input-tsv", type=Path, required=True)
    parser.add_argument("--input-plan", type=Path, required=True)
    parser.add_argument("--out-tsv", type=Path, required=True)
    parser.add_argument("--out-plan", type=Path, required=True)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    queued: list[str] = []
    profile_by_path: dict[str, str] = {}
    for item in queue["items"]:
        if item.get("logical_bucket") != "WS33B":
            continue
        if item.get("runtime_subsystem") != "forge.game.cost.Cost":
            continue
        key = (item.get("scenario_group_id"), item.get("evidence_profile"))
        if key not in EXPECTED_ITEMS:
            fail(f"unexpected B2 queue item {key}")
        if item.get("unresolved_path_count") != EXPECTED_ITEMS[key]:
            fail(f"B2 queue item {key} cardinality changed")
        queued.extend(item["effective_path_ids"])
        for pid in item["effective_path_ids"]:
            profile_by_path[pid] = item["evidence_profile"]
    if len(queued) != 402 or len(set(queued)) != 402:
        fail(f"unexpected B2 queue cardinality {len(queued)} unique={len(set(queued))}")

    terminal = [pid for pid in queued if pid in TERMINAL_BLOCKERS]
    if len(terminal) != 5 or set(terminal) != set(TERMINAL_BLOCKERS):
        fail("terminal blocker registry does not match live queue")
    provable = sorted(set(queued) - set(TERMINAL_BLOCKERS))
    if len(provable) != 397:
        fail(f"unexpected provable cardinality {len(provable)}")

    header, *lines = args.input_tsv.read_text(encoding="utf-8").splitlines()
    by_id = {}
    for line in lines:
        if not line.strip():
            continue
        by_id[line.split("\t", 1)[0]] = line
    missing = [pid for pid in provable if pid not in by_id]
    if missing:
        fail(f"B2 provable paths missing from prepared cases: {len(missing)}")

    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(header + "\n")
        for pid in provable:
            handle.write(by_id[pid] + "\n")

    plan = json.loads(args.input_plan.read_text(encoding="utf-8"))
    if plan.get("case_count") != 402:
        fail("input plan case count is not 402")
    b2_plan = {
        "schema": "commander-simulator-next.ws33-abc-b2-plan.v1",
        "scope": {
            "logical_bucket": "WS33B",
            "runtime_subsystem": "forge.game.cost.Cost",
            "evidence_profiles": ["DECISION+HIDDEN+REPLAY", "DECISION+RNG+HIDDEN+REPLAY",
                                  "HIDDEN", "RNG+HIDDEN+REPLAY"],
        },
        "path_count": 397,
        "paths": provable,
        "profile_by_path": {pid: profile_by_path[pid] for pid in provable},
        "terminal_blockers": TERMINAL_BLOCKERS,
        "terminal_blocker_count": len(TERMINAL_BLOCKERS),
        "recipe_counts": plan.get("recipe_counts", {}),
        "selection_policy": plan.get("selection_policy", {}),
    }
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(b2_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"WS33_ABC_B2_FILTER": "PASS", "path_count": 397,
                      "terminal": len(TERMINAL_BLOCKERS)}, sort_keys=True))


if __name__ == "__main__":
    main()
