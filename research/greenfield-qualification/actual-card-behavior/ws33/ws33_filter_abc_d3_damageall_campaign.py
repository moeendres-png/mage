#!/usr/bin/env python3
"""WS33-D D3 filter: bind the prepared case set to the authoritative queue.

Verifies the queue item (WS33D/template-039/STATE_ONLY/DamageAllEffect),
checks every prepared case id is a currently-UNKNOWN queue member, checks no
case id is ledger-PASS (anti-double-credit, D-local), checks the deferred
registry exactly covers the queue remainder, and checks the frozen target
digest over the provable set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--input-tsv", type=Path, required=True)
    ap.add_argument("--input-plan", type=Path, required=True)
    ap.add_argument("--input-deferred", type=Path, required=True)
    ap.add_argument("--target-digest", required=True)
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-plan", type=Path, required=True)
    a = ap.parse_args()

    queue = json.loads(a.queue.read_text())
    rows = [x for x in queue["items"] if x.get("logical_bucket") == "WS33D"
            and x.get("scenario_group_id") == "ws33-g2-template-039"
            and x.get("evidence_profile") == "STATE_ONLY"
            and x.get("runtime_subsystem") == "forge.game.ability.effects.DamageAllEffect"]
    assert len(rows) == 1, f"expected exactly one D1 queue item, found {len(rows)}"
    qids = rows[0]["effective_path_ids"]
    assert len(qids) == 17 and len(set(qids)) == 17, "D3 queue item must hold 17 unique ids"

    status = {}
    for line in a.ledger.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            status[r["effective_path_id"]] = r.get("current_status")
    for pid in qids:
        assert status.get(pid) == "UNKNOWN", f"D3 member not UNKNOWN: {pid}"

    cases = [l for l in a.input_tsv.read_text().splitlines() if l.strip() and not l.startswith("#")]
    case_ids = [l.split("\t")[0] for l in cases]
    assert len(case_ids) == 7 and len(set(case_ids)) == 7
    assert set(case_ids) < set(qids), "case ids must be a strict subset of the queue item"
    assert "forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708" not in case_ids, \
        "retained-PASS id must never be selected"

    deferred = json.loads(a.input_deferred.read_text())
    assert len(deferred) == 10
    assert set(case_ids) | {d["effective_path_id"] for d in deferred} == set(qids), \
        "provable + deferred must exactly cover the queue item"

    digest = hashlib.sha256(("\n".join(sorted(case_ids)) + "\n").encode()).hexdigest()
    assert digest == a.target_digest, f"target digest mismatch {digest} != {a.target_digest}"

    a.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    a.out_tsv.write_text(a.input_tsv.read_text())
    plan = json.loads(a.input_plan.read_text())
    assert plan["target_digest"] == a.target_digest
    a.out_plan.write_text(a.input_plan.read_text())
    print(f"WS33_ABC_D3_FILTER=PASS cases=7 deferred=10 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
