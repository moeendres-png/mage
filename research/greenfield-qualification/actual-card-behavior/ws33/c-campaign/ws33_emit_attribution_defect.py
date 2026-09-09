#!/usr/bin/env python3
"""Emit the WS33-C model-attribution defect artifact (descriptive only).

For every owned C path whose modeled implementation_target names a class
that does not exist at FORGE_PIN, records modeled vs actual runtime class
plus resolution evidence. No canonical input is mutated; no path is
promoted by this artifact.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
ACTUAL_RUNTIME = {
    "forge.game.spellability.SpellApiBased": "forge.game.ability.SpellApiBased",
    "forge.game.spellability.AbilityApiBased": "forge.game.ability.AbilityApiBased",
}
PIN_SOURCE = {
    "forge.game.ability.SpellApiBased":
        "forge-game/src/main/java/forge/game/ability/SpellApiBased.java",
    "forge.game.ability.AbilityApiBased":
        "forge-game/src/main/java/forge/game/ability/AbilityApiBased.java",
}
MISSING_SOURCE = {
    "forge.game.spellability.SpellApiBased":
        "forge-game/src/main/java/forge/game/spellability/SpellApiBased.java",
    "forge.game.spellability.AbilityApiBased":
        "forge-game/src/main/java/forge/game/spellability/AbilityApiBased.java",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--forge-git", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assert manifest["forge_pin"] == FORGE_PIN

    def exists(rel: str) -> bool:
        r = subprocess.run(
            ["git", "-C", str(args.forge_git), "cat-file", "-e", f"{FORGE_PIN}:{rel}"],
            capture_output=True)
        return r.returncode == 0

    rows = []
    for row in manifest["paths"]:
        modeled = row["implementation_target"]
        if modeled not in ACTUAL_RUNTIME:
            continue
        actual = ACTUAL_RUNTIME[modeled]
        rows.append({
            "effective_path_id": row["effective_v2_path_id"],
            "modeled_class": modeled,
            "actual_runtime_class": actual,
            "resolution_evidence": {
                "method": "PIN_SOURCE_LS_TREE",
                "forge_pin": FORGE_PIN,
                "modeled_source_present": exists(MISSING_SOURCE[modeled]),
                "actual_source_present": exists(PIN_SOURCE[actual]),
            },
            "qualification_impact": (
                "Production witness contract for the actual runtime class is "
                "NOT YET DEMONSTRATED. No qualification credit is claimed by "
                "alias or package correction. Model correction requires later "
                "Sol adjudication."),
        })
    rows.sort(key=lambda r: r["effective_path_id"])
    assert all(not r["resolution_evidence"]["modeled_source_present"]
               and r["resolution_evidence"]["actual_source_present"] for r in rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"schema": "commander-simulator-next.ws33-c-attribution-defect.v1",
                    "forge_pin": FORGE_PIN,
                    "defect_count": len(rows), "defects": rows},
                   sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"MODEL_ATTRIBUTION_DEFECT_COUNT": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
