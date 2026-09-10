#!/usr/bin/env python3
"""WS33-D D4c filter: bind the prepared single-target case set to the queue.

Verifies the queue item (WS33D/template-049/STATE_ONLY/EffectEffect),
checks every prepared case id is a currently-UNKNOWN queue member, checks no
case id is ledger-PASS, partition-evidenced, or the retained-PASS id
(anti-double-credit, D-local), checks the deferred registry exactly covers
the queue remainder with exactly 11 D4a/D4b-retained entries, checks every
case carries an ENTITY intent, and checks the frozen target digest over the
provable set.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

RETAINED_PASS_ID = "forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--partition", type=Path, required=True)
    ap.add_argument("--input-tsv", type=Path, required=True)
    ap.add_argument("--input-plan", type=Path, required=True)
    ap.add_argument("--input-deferred", type=Path, required=True)
    ap.add_argument("--target-digest", required=True)
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-plan", type=Path, required=True)
    a = ap.parse_args()

    queue = json.loads(a.queue.read_text())
    rows = [x for x in queue["items"] if x.get("logical_bucket") == "WS33D"
            and x.get("scenario_group_id") == "ws33-g2-template-049"
            and x.get("evidence_profile") == "STATE_ONLY"
            and x.get("runtime_subsystem") == "forge.game.ability.effects.EffectEffect"]
    assert len(rows) == 1, f"expected exactly one D4 queue item, found {len(rows)}"
    qids = rows[0]["effective_path_ids"]
    assert len(qids) == 49 and len(set(qids)) == 49, "D4 queue item must hold 49 unique ids"

    status = {}
    for line in a.ledger.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            status[r["effective_path_id"]] = r.get("current_status")
    for pid in qids:
        assert status.get(pid) == "UNKNOWN", f"D4 member not UNKNOWN: {pid}"
    assert RETAINED_PASS_ID not in qids

    evidenced = set(json.loads(a.partition.read_text())["evidenced"])

    lines = [l for l in a.input_tsv.read_text().splitlines() if l.strip() and not l.startswith("#")]
    assert len(lines) == 4, "D4c input must hold 4 cases"
    case_ids = [l.split("\t")[0] for l in lines]
    assert len(set(case_ids)) == 4
    assert set(case_ids) < set(qids), "case ids must be a strict subset of the queue item"
    assert RETAINED_PASS_ID not in case_ids, "retained-PASS id must never be selected"
    assert not (set(case_ids) & evidenced), "case ids must not intersect D-evidenced"
    for l in lines:
        intent = base64.b64decode(l.split("\t")[12]).decode()
        assert intent.startswith("ENTITY:"), f"D4c-T1 case requires ENTITY intent: {intent}"
        parts = intent.split(":")
        assert len(parts) == 4 and parts[2] in ("actor", "opponent"), f"malformed ENTITY intent: {intent}"
        assert parts[3] in ("Graveyard", "Battlefield", "Hand"), f"malformed ENTITY intent zone: {intent}"

    deferred = json.loads(a.input_deferred.read_text())
    assert len(deferred) == 45
    retained = [d for d in deferred if d["reason"].startswith("RETAINED:")]
    assert len(retained) == 11, "deferred must carry exactly the 11 D4a/D4b-retained paths"
    assert set(case_ids) | {d["effective_path_id"] for d in deferred} == set(qids), \
        "provable + deferred must exactly cover the queue item"

    digest = hashlib.sha256(("\n".join(sorted(case_ids)) + "\n").encode()).hexdigest()
    assert digest == a.target_digest, f"target digest mismatch {digest} != {a.target_digest}"

    a.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    a.out_tsv.write_text(a.input_tsv.read_text())
    plan = json.loads(a.input_plan.read_text())
    assert plan["target_digest"] == a.target_digest
    assert plan["provable_count"] == 4 and plan["deferred_count"] == 45
    assert plan.get("batch") == "D4c"
    a.out_plan.write_text(a.input_plan.read_text())
    print(f"WS33_ABC_D4C_FILTER=PASS cases=4 deferred=45 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
