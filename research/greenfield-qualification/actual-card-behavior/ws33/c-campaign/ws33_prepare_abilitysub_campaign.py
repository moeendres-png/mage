#!/usr/bin/env python3
"""Prepare the WS33-C AbilitySub pilot case set (deterministic).

Pilot scope: rank-1 cluster (ws33-template-113, STATE_ONLY) pilot card
Cloudblazer -> effective path
forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6
(parent SVar TrigGainLife, SubAbility$ DBDraw pointer).

Writes:
  - abilitysub-cases.tsv  (harness input, 1 pilot row)
  - ABILITYSUB_PILOT_PLAN.json (exact case identity for the certifier)

Full-cluster expansion remains QUEUED in WS33_C_CLUSTER_QUEUE.json.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
PATH_ID = "forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6"
ORACLE_ID = "f84d1291-1f82-4b67-a26e-b79624b4ce1d"
CARD_NAME = "Cloudblazer"
SOURCE_PATH = "forge-gui/res/cardsfolder/c/cloudblazer.txt"
SOURCE_LINE = 7
PARENT_SVAR = "TrigGainLife"
CHILD_SUB = "DBDraw"
PARENT_API = "GainLife"
CHILD_API = "Draw"


def b64(v: str) -> str:
    return base64.b64encode(v.encode("utf-8")).decode("ascii")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-plan", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assert manifest["forge_pin"] == FORGE_PIN
    rows = {r["effective_v2_path_id"]: r for r in manifest["paths"]}
    row = rows.get(PATH_ID)
    assert row is not None, "pilot path missing from owned manifest"
    assert row["scenario_group_id"] == "ws33-template-113"
    assert row["evidence_profile"] == "STATE_ONLY"
    assert row["semantic_selector_profile"]["selectors"] == {"SubAbility": CHILD_SUB}
    assert not (row["requires_decision"] or row["requires_hidden"]
                or row["requires_replay"] or row["requires_rng"])
    prov = [q for q in row["source_provenance"]
            if q["forge_source_path"] == SOURCE_PATH and q["oracle_identity"] == ORACLE_ID]
    assert len(prov) == 1 and prov[0]["source_line"] == SOURCE_LINE, "pilot provenance mismatch"

    header = "#path_id\toracle_id\tcard_name_b64\tparent_svar\tchild_sub\tparent_api\tchild_api\tsource_path_b64\tsource_line\tfixture_kind\tlife_delta\thand_delta_net\n"
    line = "\t".join([
        PATH_ID, ORACLE_ID, b64(CARD_NAME), PARENT_SVAR, CHILD_SUB,
        PARENT_API, CHILD_API, b64(SOURCE_PATH), str(SOURCE_LINE),
        "TRIGGER_ETB_UNTARGETED", "2", "1",
    ]) + "\n"
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    args.out_tsv.write_text(header + line, encoding="utf-8")

    plan = {
        "schema": "commander-simulator-next.ws33-c-abilitysub-pilot-plan.v1",
        "forge_pin": FORGE_PIN,
        "path_count": 1,
        "paths": [PATH_ID],
        "cases": [{
            "path_id": PATH_ID,
            "oracle_identity": ORACLE_ID,
            "card_name": CARD_NAME,
            "parent_svar": PARENT_SVAR,
            "child_sub": CHILD_SUB,
            "parent_api": PARENT_API,
            "child_api": CHILD_API,
            "source_path": SOURCE_PATH,
            "source_line": SOURCE_LINE,
            "fixture_kind": "TRIGGER_ETB_UNTARGETED",
            "life_delta": 2,
            "hand_delta_net": 1,
        }],
    }
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(
        json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256((header + line).encode()).hexdigest()
    print(json.dumps({"WS33_C_PILOT_CASES": 1, "TSV_SHA256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
