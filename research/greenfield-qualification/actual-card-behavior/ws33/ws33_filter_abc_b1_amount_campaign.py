#!/usr/bin/env python3
"""Filter the full amount campaign to the authoritative WS33B queue subset.

Verifies the single canonical work-queue item
(WS33B / calculateAmount / ws33-g2-template-010 / DECISION+RNG+HIDDEN+REPLAY)
binds exactly 273 UNKNOWN paths, then emits the B1 case set and plan.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit("WS33_ABC_B1_FILTER=FAIL " + message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--input-tsv", type=Path, required=True)
    parser.add_argument("--input-plan", type=Path, required=True)
    parser.add_argument("--out-tsv", type=Path, required=True)
    parser.add_argument("--out-plan", type=Path, required=True)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    items = [
        item for item in queue["items"]
        if item.get("logical_bucket") == "WS33B"
        and item.get("runtime_subsystem") == "forge.game.ability.AbilityUtils#calculateAmount"
        and item.get("scenario_group_id") == "ws33-g2-template-010"
        and item.get("evidence_profile") == "DECISION+RNG+HIDDEN+REPLAY"
    ]
    if len(items) != 1:
        fail(f"expected exactly one B1 queue item, found {len(items)}")
    queued = items[0]["effective_path_ids"]
    if len(queued) != 273 or len(set(queued)) != 273:
        fail(f"unexpected B1 queue cardinality {len(queued)} unique={len(set(queued))}")
    if items[0]["unresolved_path_count"] != 273:
        fail("B1 queue item unresolved count is not 273")

    header, *lines = args.input_tsv.read_text(encoding="utf-8").splitlines()
    by_id = {}
    for line in lines:
        if not line.strip():
            continue
        by_id[line.split("\t", 1)[0]] = line
    missing = [pid for pid in queued if pid not in by_id]
    if missing:
        fail(f"B1 queue paths missing from prepared cases: {len(missing)}")
    if set(by_id) != set(queued):
        fail("prepared case set differs from authoritative B1 queue")

    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(header + "\n")
        for pid in sorted(queued):
            handle.write(by_id[pid] + "\n")

    plan = json.loads(args.input_plan.read_text(encoding="utf-8"))
    if plan.get("case_count") != 273:
        fail("input plan case count is not 273")
    b1_plan = {
        "schema": "commander-simulator-next.ws33-abc-b1-plan.v1",
        "scope": {
            "logical_bucket": "WS33B",
            "runtime_subsystem": "forge.game.ability.AbilityUtils#calculateAmount",
            "scenario_group_id": "ws33-g2-template-010",
            "evidence_profile": "DECISION+RNG+HIDDEN+REPLAY",
        },
        "path_count": 273,
        "paths": sorted(queued),
        "recipe_counts": plan.get("recipe_counts", {}),
        "selection_policy": plan.get("selection_policy", {}),
    }
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(b1_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"WS33_ABC_B1_FILTER": "PASS", "path_count": 273}, sort_keys=True))


if __name__ == "__main__":
    main()
