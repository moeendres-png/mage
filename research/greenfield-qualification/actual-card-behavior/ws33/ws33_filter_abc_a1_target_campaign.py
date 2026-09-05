#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_BUCKET = "WS33A"
EXPECTED_SUBSYSTEM = "forge.game.spellability.TargetRestrictions"
EXPECTED_GROUP = "ws33-g2-template-123"
EXPECTED_PROFILE = "DECISION+REPLAY"
EXPECTED_COUNT = 122


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_ABC_A1_FILTER=FAIL " + message)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--queue", type=Path, required=True)
    p.add_argument("--input-tsv", type=Path, required=True)
    p.add_argument("--input-plan", type=Path, required=True)
    p.add_argument("--out-tsv", type=Path, required=True)
    p.add_argument("--out-plan", type=Path, required=True)
    args = p.parse_args()

    queue = load(args.queue)
    matches = [
        item for item in queue["items"]
        if item.get("logical_bucket") == EXPECTED_BUCKET
        and item.get("runtime_subsystem") == EXPECTED_SUBSYSTEM
        and item.get("scenario_group_id") == EXPECTED_GROUP
        and item.get("evidence_profile") == EXPECTED_PROFILE
    ]
    require(len(matches) == 1, f"expected one work item, got {len(matches)}")
    item = matches[0]
    target_ids = list(item["effective_path_ids"])
    require(item.get("unresolved_path_count") == EXPECTED_COUNT, "queue unresolved count drift")
    require(len(target_ids) == EXPECTED_COUNT, "queue path-id count drift")
    require(len(set(target_ids)) == EXPECTED_COUNT, "duplicate queue path ids")

    lines = args.input_tsv.read_text(encoding="utf-8").splitlines()
    require(lines and lines[0].startswith("# path_id\t"), "unexpected TSV header")
    by_id = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        path_id = line.split("\t", 1)[0]
        require(path_id not in by_id, "duplicate prepared path " + path_id)
        by_id[path_id] = line

    missing = sorted(set(target_ids) - set(by_id))
    extra = sorted(set(by_id) - set(target_ids))
    require(not missing, "prepared campaign missing A1 paths: " + ",".join(missing[:5]))

    selected = [by_id[path_id] for path_id in sorted(target_ids)]
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    args.out_tsv.write_text(lines[0] + "\n" + "\n".join(selected) + "\n", encoding="utf-8")

    source_plan = load(args.input_plan)
    source_cases = {case["path_id"]: case for case in source_plan["cases"]}
    require(not (set(target_ids) - set(source_cases)), "input plan missing A1 cases")
    cases = [source_cases[path_id] for path_id in sorted(target_ids)]
    plan = {
        "schema": "commander-simulator-next.ws33-abc-a1-targetrestrictions-plan.v1",
        "source_campaign_schema": source_plan.get("schema"),
        "queue_binding": {
            "logical_bucket": EXPECTED_BUCKET,
            "runtime_subsystem": EXPECTED_SUBSYSTEM,
            "scenario_group_id": EXPECTED_GROUP,
            "evidence_profile": EXPECTED_PROFILE,
            "expected_path_count": EXPECTED_COUNT,
        },
        "selection_policy": source_plan.get("selection_policy"),
        "path_count": len(cases),
        "paths": [case["path_id"] for case in cases],
        "cases": cases,
        "prepared_non_a1_case_count": len(extra),
    }
    require(plan["path_count"] == EXPECTED_COUNT, "filtered plan count drift")
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "WS33_ABC_A1_FILTER": "PASS",
        "path_count": len(cases),
        "prepared_non_a1_case_count": len(extra),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
