#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ORDER = {"FAIL": 3, "UNSUPPORTED": 2, "NOT_RUN": 1, "PASS": 0}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    root = Path(args.root)
    rows = []
    for path in sorted(root.rglob("*.result.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append(data)
    by_candidate = {}
    for row in rows:
        cand = row["candidate"]
        by_candidate.setdefault(cand, []).append(row)
    summary = {"schema_version": 1, "candidates": {}}
    for cand, items in sorted(by_candidate.items()):
        statuses = {}
        for item in items:
            statuses[item["scenario"]] = item["result"]["status"]
        summary["candidates"][cand] = {
            "commit": items[0]["commit"],
            "scenario_status": statuses,
            "counts": {s: sum(1 for x in items if x["result"]["status"] == s) for s in ["PASS", "FAIL", "UNSUPPORTED", "NOT_RUN"]},
            "worst_status": max((x["result"]["status"] for x in items), key=lambda s: ORDER[s], default="NOT_RUN"),
        }
    Path(args.out).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
