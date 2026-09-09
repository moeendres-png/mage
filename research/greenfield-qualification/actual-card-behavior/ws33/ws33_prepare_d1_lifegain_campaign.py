#!/usr/bin/env python3
"""WS33-D D1 LifeGain campaign preparer (D-local).

Queue item WS33D/template-059/STATE_ONLY/LifeGainEffect (22 UNKNOWN paths):
bind each path to its representative pinned-Forge card script, classify into
a provable recipe or a deferred bucket with exact reason, emit case TSV +
plan + deferred registry. Fail-closed on any surprise.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"

# card_file -> (disposition, ability_kind, recipe, params, pool, fixture, dA, dO, note)
P = "PROVABLE"
CARD_TABLE = {
    "zuran_orb.txt": (P, "AB", "ACTIVATED_SAC_LAND", "", "", "bf=Plains:1", 2, 0,
        "sac-a-land gain 2; exactly one land forces cost"),
    "trading_post.txt": (P, "AB", "ACTIVATED_DISCARD", "", "C1", "bf=Trading Post:1;hand=Runeclaw Bear:1", 4, 0,
        "mode-1 gain 4; single-card hand forces discard"),
    "ayli_eternal_pilgrim.txt": (P, "AB", "ACTIVATED_SAC_CREATURE", "", "C1", "bf=Runeclaw Bear:1", 2, 0,
        "gain=toughness of the single other sacrificed creature"),
    "dimension_x_pizzasaur.txt": (P, "AB", "ACTIVATED_SAC_SELF", "", "C2", "", 3, -3,
        "AB line only: gain 3 + opponent loses 3"),
    "tainted_sigil.txt": (P, "AB", "ACTIVATED_SAC_SELF", "", "", "", 0, 0,
        "no life lost this turn so X=0; exact zero-delta line"),
    "angels_mercy.txt": (P, "SP", "SPELL_BASE", "", "W4", "", 7, 0,
        "instant gain 7; exact pool pays 2WW"),
    "timely_reinforcements.txt": (P, "SP", "SPELL_CONDITIONAL_LIFE", "", "W3", "actor_life=15;opp_life=20", 6, 0,
        "life condition true (+6), token condition false (no tokens)"),
    "avenge.txt": (P, "SP", "SPELL_DESTROY_ALL", "", "W2C4", "actor_bf=Runeclaw Bear:2;opp_bf=Runeclaw Bear:1", 3, 0,
        "destroy all 3, gain 3; no cost reduction without prior attack"),
    "cloudblazer.txt": (P, "DB", "ETB_TRIGGER", "", "", "library_fill=5", 2, 0,
        "ETB gain 2 + draw 2 from fixed-order filled library, no shuffle"),
    "vampiric_rites.txt": (P, "AB", "ACTIVATED_SAC_DRAW", "", "B1C1", "bf=Runeclaw Bear:1;library_fill=5", 1, 0,
        "gain 1 + draw 1 from fixed-order filled library, no shuffle"),
    "perimeter_captain.txt": ("DEFERRED:OPTIONAL_DECISION_D6", "DB", "-", "", "", "", 0, 0,
        "Blocks trigger has OptionalDecider You (may); needs tape"),
    "kimoyo_beads.txt": ("DEFERRED:MODAL_DECISION_D6", "DB", "-", "", "", "", 0, 0,
        "end-step Charm with 3 choices; needs tape"),
    "soul_burn.txt": ("DEFERRED:X_AND_TARGET_D7", "SP", "-", "", "", "", 0, 0,
        "X cost + targeting + damage-derived amount; needs tapes"),
    "exsanguinate.txt": ("DEFERRED:X_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "X spell; X choice is discretionary, needs tape"),
    "tribute_to_hunger.txt": ("DEFERRED:TARGET_AND_OPP_CHOICE_D6", "SP", "-", "", "", "", 0, 0,
        "target opponent + opponent sacrifice choice; needs tapes"),
    "light_of_hope.txt": ("DEFERRED:MODAL_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "Charm modal choice; needs tape"),
    "soul_shackled_zombie.txt": ("DEFERRED:TARGET_AND_CONDITIONAL_D6", "DB", "-", "", "", "", 0, 0,
        "up-to-two graveyard targets + conditional; needs tapes"),
    "divine_offering.txt": ("DEFERRED:TARGET_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "target artifact; needs target tape"),
    "swords_to_plowshares.txt": ("DEFERRED:TARGET_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "target creature; needs target tape"),
    "condemn.txt": ("DEFERRED:TARGET_AND_COMBAT_D6", "SP", "-", "", "", "", 0, 0,
        "target attacking creature; needs combat setup + target tape"),
    "elixir_of_immortality.txt": ("DEFERRED:SHUFFLE_RNG_D7", "AB", "-", "", "", "", 0, 0,
        "graveyard shuffle consumes RNG; needs RNG replay tapes"),
    "lightkeeper_of_emeria.txt": ("DEFERRED:KICKER_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "multikicker choice is discretionary, needs tape"),
}
def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out-tsv", type=Path, required=True)
    ap.add_argument("--out-plan", type=Path, required=True)
    ap.add_argument("--out-deferred", type=Path, required=True)
    a = ap.parse_args()

    head = subprocess.run(["git", "-C", str(a.forge_root), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    assert head.returncode == 0 and head.stdout.strip() == FORGE_PIN, "Forge pin mismatch"

    queue = json.loads(a.queue.read_text())
    rows = [x for x in queue["items"] if x.get("logical_bucket") == "WS33D"
            and x.get("scenario_group_id") == "ws33-g2-template-059"
            and x.get("evidence_profile") == "STATE_ONLY"
            and x.get("runtime_subsystem") == "forge.game.ability.effects.LifeGainEffect"]
    assert len(rows) == 1, "expected exactly one D1 queue item"
    qids = rows[0]["effective_path_ids"]
    assert len(qids) == 22 and len(set(qids)) == 22, "D1 queue item must hold 22 unique ids"

    status, led = {}, {}
    for line in a.ledger.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            status[r["effective_path_id"]] = r.get("current_status")
            led[r["effective_path_id"]] = r
    for pid in qids:
        assert status.get(pid) == "UNKNOWN", f"D1 member not UNKNOWN: {pid}"

    cases, deferred = [], []
    for pid in qids:
        prov = led[pid]["source_provenance"][0]
        card_file = Path(prov["forge_source_path"]).name
        assert card_file in CARD_TABLE, f"card outside frozen table: {card_file}"
        disp, kind, recipe, params, pool, fixture, dA, dO, note = CARD_TABLE[card_file]
        txt = (a.forge_root / prov["forge_source_path"]).read_text()
        assert "GainLife" in txt, f"no GainLife line at pin for {card_file}"
        oracle = prov["oracle_identity"]
        if disp == P:
            cases.append((pid, oracle, card_file, prov["source_token"], recipe,
                          params, pool, fixture, dA, dO,
                          f"{prov['forge_source_path']}#{prov.get('source_line')}"))
        else:
            deferred.append({"effective_path_id": pid, "card": card_file,
                             "reason": disp, "note": note})
    assert len(cases) == 10 and len(deferred) == 12, "D1 split must be 10 + 12"
    cids = sorted(c[0] for c in cases)
    digest = hashlib.sha256(("\n".join(cids) + "\n").encode()).hexdigest()

    a.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out_tsv, "w") as f:
        f.write("#path_id\toracle_id\tcard_b64\tsvar_token_b64\tsvar_expr_b64\trecipe\t"
                "params_b64\tpool_b64\tfixture_b64\tactor_delta\topp_delta\tprovenance_b64\n")
        for (pid, oracle, card, stok, recipe, params, pool, fixture, dA, dO, provenance) in cases:
            card_name = Path(card).stem.replace("_", " ")
            f.write("\t".join([pid, oracle, b64(card_name), b64(stok), b64("GainLife"), recipe,
                                b64(params), b64(pool), b64(fixture), str(dA), str(dO),
                                b64(provenance)]) + "\n")
    a.out_deferred.write_text(json.dumps(deferred, indent=1, sort_keys=True) + "\n")
    a.out_plan.write_text(json.dumps({
        "schema": "commander-simulator-next.ws33d-d1-plan.v1",
        "batch": "D1", "queue_item": "ws33-g2-template-059/STATE_ONLY/LifeGainEffect",
        "queue_count": 22, "provable_count": 10, "deferred_count": 12,
        "target_digest": digest, "forge_pin": FORGE_PIN,
        "provable_ids": cids,
    }, indent=1, sort_keys=True) + "\n")
    print(f"WS33_ABC_D1_MATERIALIZATION=PASS cases=10 deferred=12 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
