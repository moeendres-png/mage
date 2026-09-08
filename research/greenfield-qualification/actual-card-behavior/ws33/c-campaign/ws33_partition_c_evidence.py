#!/usr/bin/env python3
"""Build the branch-owned WS33-C PASS-evidenced / UNKNOWN-blocked partition.

Inputs: owned manifest, cluster queue, list of adjudicated PASS records
(each with path id + run/job/artifact/digest). Everything else stays
UNKNOWN with an explicit root-cause class. Deterministic output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def canon(o) -> bytes:
    return (json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


DIM_OF = {
    "requires_decision": "DECISION",
    "requires_hidden": "HIDDEN_INFO",
    "requires_rng": "RNG",
    "requires_replay": "SEMANTIC_REPLAY",
}


def blocker_for(row: dict) -> str:
    need = [t for k, t in DIM_OF.items() if row[k]]
    if need:
        return "WITNESS_INFRASTRUCTURE_PENDING:" + "+".join(need)
    return "WITNESS_QUEUED_STATE_ONLY"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--passes", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    manifest = load(args.manifest)
    passes = {p["effective_v2_path_id"]: p for p in load(args.passes)}
    owned = {r["effective_v2_path_id"]: r for r in manifest["paths"]}
    assert set(passes) <= set(owned), "pass outside owned manifest"
    evidenced, blocked = [], []
    for pid in sorted(owned):
        if pid in passes:
            evidenced.append({"effective_v2_path_id": pid, **passes[pid]})
        else:
            blocked.append({
                "effective_v2_path_id": pid,
                "implementation_target": owned[pid]["implementation_target"],
                "scenario_group_id": owned[pid]["scenario_group_id"],
                "evidence_profile": owned[pid]["evidence_profile"],
                "root_cause_class": blocker_for(owned[pid]),
            })
    args.out.write_bytes(canon({
        "schema": "commander-simulator-next.ws33-c-evidence-partition.v1",
        "forge_pin": manifest["forge_pin"],
        "owned_path_count": len(owned),
        "evidenced_path_count": len(evidenced),
        "remaining_unknown_count": len(blocked),
        "evidenced": evidenced,
        "blocked": blocked,
    }))
    print(json.dumps({"EVIDENCED": len(evidenced), "UNKNOWN": len(blocked)}, sort_keys=True))


if __name__ == "__main__":
    main()
