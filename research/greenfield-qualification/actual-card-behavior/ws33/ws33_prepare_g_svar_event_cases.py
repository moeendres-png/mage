#!/usr/bin/env python3
"""Materialize every non-AbilityFactory SVar production parent entrypoint.

The 32 non-AF effective paths expand to 33 event entrypoints because the real Kang Prime
path has two source-proven trigger parents.  This generator intentionally preserves both;
it never collapses multi-parent reachability to a synthetic primary parent.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from collections import Counter
from pathlib import Path

MODE_RE = re.compile(r"(?:^|\s\|\s)Mode\$\s*([^|]+)")


def fail(msg: str) -> None:
    raise SystemExit("WS33_G_SVAR_EVENT_CASES=FAIL " + msg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topology", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    topology = json.loads(args.topology.read_text(encoding="utf-8"))
    if topology.get("status") != "PASS" or topology.get("remaining_svar_count") != 53:
        fail("input topology is not the frozen green 53-path frontier")

    rows: list[str] = []
    modes: Counter[str] = Counter()
    path_ids: set[str] = set()
    multi: list[str] = []
    ordinal = 0
    for case in sorted(topology["cases"], key=lambda c: c["v2_path_id"]):
        parents = [p for p in case["selected_parents"] if not p["ability_factory_compatible"]]
        if not parents:
            continue
        path_ids.add(case["v2_path_id"])
        if len(parents) > 1:
            multi.append(case["v2_path_id"])
        for entry_index, parent in enumerate(parents, 1):
            ordinal += 1
            script = parent["script"]
            mm = MODE_RE.search(script)
            if not mm:
                fail(f"non-AF parent has no Mode$ for {case['v2_path_id']}")
            mode = mm.group(1).strip()
            modes[mode] += 1
            fields = [
                ordinal,
                case["v2_path_id"],
                entry_index,
                len(parents),
                case["oracle_identity"],
                case["card_name"],
                case["target_svar"],
                case["dispatch_token"],
                case["implementation_target"],
                case["source_path"],
                int(parent["source_line"]),
                parent["directive"],
                parent["consumer_field"],
                mode,
                int(bool(case["required_hidden_info_evidence"])),
                int(bool(case["required_rng_evidence"])),
                int(bool(case["required_replay_evidence"])),
                int(bool(case["required_decision_evidence"])),
                base64.b64encode(case["target_script"].encode("utf-8")).decode("ascii"),
                base64.b64encode(script.encode("utf-8")).decode("ascii"),
            ]
            rows.append("\t".join(map(str, fields)))

    if len(path_ids) != 32 or len(rows) != 33:
        fail(f"expected 32 paths / 33 parent entrypoints, got {len(path_ids)} / {len(rows)}")
    expected_multi = topology.get("multi_parent_paths", [])
    if sorted(multi) != sorted(expected_multi) or len(multi) != 1:
        fail(f"multi-parent identity mismatch generated={multi} topology={expected_multi}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    summary = {
        "schema": "commander-simulator-next.ws33-g-svar-event-cases.v1",
        "status": "PASS",
        "effective_model_sha256": topology["effective_model_sha256"],
        "effective_path_count": len(path_ids),
        "parent_entrypoint_count": len(rows),
        "multi_parent_paths": sorted(multi),
        "modes": dict(sorted(modes.items())),
        "coverage_mutated": False,
        "direct_target_svar_entry": False,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "WS33_G_SVAR_EVENT_CASES=PASS paths=32 entrypoints=33 multi_parent=1 "
        "direct_target_svar=FALSE coverage_mutated=FALSE modes="
        + ",".join(f"{k}:{v}" for k, v in sorted(modes.items()))
    )


if __name__ == "__main__":
    main()
