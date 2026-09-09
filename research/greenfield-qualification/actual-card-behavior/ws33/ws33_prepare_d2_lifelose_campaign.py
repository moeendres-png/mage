#!/usr/bin/env python3
"""WS33-D D2 LifeLose campaign preparer (D-local, draft).

Queue item WS33D/template-061/STATE_ONLY/LifeLoseEffect (18 UNKNOWN paths):
bind each path to its representative pinned-Forge card script, classify into
a provable recipe or a deferred bucket with exact reason, emit case TSV +
plan + deferred registry. Fail-closed on any surprise.

D2 reuses the D1 harness architecture; new recipes (dies-trigger via Wrath
fixture, ETB-X, draw-lose, converge, planeswalker draw-lose) land in the D2
campaign test. No run is registered by this script.
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
QUEUE_GROUP = "ws33-g2-template-061"
QUEUE_SUBSYSTEM = "forge.game.ability.effects.LifeLoseEffect"

P = "PROVABLE"
# card_file -> (disposition, ability_kind, recipe, params, pool, fixture, dA, dO, note)
CARD_TABLE = {
    "caustic_hound.txt": (P, "DB", "DIES_TRIGGER_WRATH", "", "W2C2",
        "actor_bf=Runeclaw Bear:1;opp_bf=Runeclaw Bear:1", -4, -4,
        "Wrath kills hound+bears; dies trigger each player -4"),
    "grave_venerations.txt": (P, "DB", "DIES_TRIGGER_WRATH", "", "W2C2",
        "actor_bf=Runeclaw Bear:1", 1, -1,
        "Wrath kills the single bear; dies trigger opp -1 you +1"),
    "shimmercreep.txt": (P, "DB", "ETB_TRIGGER_X", "", "", "bf=Plains:1,Island:1", 3, -3,
        "colors among own permanents incl. self (W,U,B) so X=3"),
    "nights_whisper.txt": (P, "SP", "SPELL_DRAW_LOSE", "", "B1C1", "library_fill=3", -2, 0,
        "draw 2 lose 2 from fixed-order filled library"),
    "circle_of_power.txt": (P, "SP", "SPELL_DRAW_LOSE_TOKEN", "", "B1C3", "library_fill=3", -2, 0,
        "draw 2 lose 2 + 0/1 Wizard token + anthem; assert token presence"),
    "urborg_syphon_mage.txt": (P, "AB", "ACTIVATED_DISCARD_TAP", "", "B1C2", "hand=Runeclaw Bear:1", 2, -2,
        "each other player -2, gain = life lost (2); single-card hand forces discard"),
    "painful_truths.txt": (P, "SP", "SPELL_CONVERGE", "", "W1B1C1", "library_fill=4", -2, 0,
        "spend exactly W+B (+C) so converge X=2; draw 2 lose 2"),
    "vraska_betrayals_sting.txt": (P, "AB", "PLANESWALKER_DRAW_LOSE", "", "", "library_fill=2", -1, 0,
        "Draw loyalty ability: draw 1 lose 1; proliferate no-ops without counters"),
    "tomik_wielder_of_law.txt": ("DEFERRED:COMBAT_SETUP_DRAW_D8", "DB", "-", "", "", "", 0, 0,
        "opponent-attackers trigger + combat setup + draw; needs combat harness"),
    "typhoid_mary_fractured.txt": ("DEFERRED:ATTACK_RANDOM_CHOICE_D7", "DB", "-", "", "", "", 0, 0,
        "attacks trigger + random/charm + discard-conditional choice; needs tapes+RNG"),
    "perforating_artist.txt": ("DEFERRED:OPP_UNLESS_CHOICE_D6", "DB", "-", "", "", "", 0, 0,
        "raid end-step + opponent unless-cost choice; needs decision tapes"),
    "exsanguinate.txt": ("DEFERRED:X_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "X spell; X choice is discretionary, needs tape"),
    "fandaniel_telophoroi_ascian.txt": ("DEFERRED:OPP_SAC_CHOICE_D6", "DB", "-", "", "", "", 0, 0,
        "end-step opponent-may-sacrifice + GY-count X; needs tapes"),
    "hoarders_greed.txt": ("DEFERRED:CLASH_D7", "SP", "-", "", "", "", 0, 0,
        "clash procedure with opponent + repeat loop; needs hidden/RNG harness"),
    "bebop_skull_crossbones.txt": ("DEFERRED:COMBAT_OPTIONAL_X_D8", "DB", "-", "", "", "", 0, 0,
        "combat-damage trigger + optional draw-X + X life loss; needs combat harness"),
    "estinien_varlineau.txt": ("DEFERRED:COMBAT_COUNT_X_D8", "DB", "-", "", "", "", 0, 0,
        "second-main-phase draw/lose X from combat-damage count; needs combat harness"),
    "damocles_base_sword_of_kang.txt": ("DEFERRED:COMBAT_VILLAINOUS_D8", "DB", "-", "", "", "", 0, 0,
        "combat-damage villainous choice (opponent); needs combat harness"),
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
            and x.get("scenario_group_id") == QUEUE_GROUP
            and x.get("evidence_profile") == "STATE_ONLY"
            and x.get("runtime_subsystem") == QUEUE_SUBSYSTEM]
    assert len(rows) == 1, "expected exactly one D2 queue item"
    qids = rows[0]["effective_path_ids"]
    assert len(qids) == 18 and len(set(qids)) == 18, "D2 queue item must hold 18 unique ids"

    status, led = {}, {}
    for line in a.ledger.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            status[r["effective_path_id"]] = r.get("current_status")
            led[r["effective_path_id"]] = r
    for pid in qids:
        assert status.get(pid) == "UNKNOWN", f"D2 member not UNKNOWN: {pid}"

    cases, deferred = [], []
    for pid in qids:
        prov = led[pid]["source_provenance"][0]
        card_file = Path(prov["forge_source_path"]).name
        assert card_file in CARD_TABLE, f"card outside frozen table: {card_file}"
        disp, kind, recipe, params, pool, fixture, dA, dO, note = CARD_TABLE[card_file]
        txt = (a.forge_root / prov["forge_source_path"]).read_text()
        assert "LoseLife" in txt, f"no LoseLife line at pin for {card_file}"
        names = [l[5:] for l in txt.splitlines() if l.startswith("Name:")]
        assert len(names) == 1 and names[0].strip(), f"no exact Name at pin for {card_file}"
        if disp == P:
            cases.append((pid, prov["oracle_identity"], names[0].strip(), prov["source_token"],
                          recipe, params, pool, fixture, dA, dO,
                          f"{prov['forge_source_path']}#{prov.get('source_line')}"))
        else:
            deferred.append({"effective_path_id": pid, "card": card_file,
                             "reason": disp, "note": note})
    assert len(cases) == 8 and len(deferred) == 10, "D2 split must be 8 + 10"
    cids = sorted(c[0] for c in cases)
    digest = hashlib.sha256(("\n".join(cids) + "\n").encode()).hexdigest()

    a.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out_tsv, "w") as f:
        f.write("#path_id\toracle_id\tcard_b64\tsvar_token_b64\tsvar_expr_b64\trecipe\t"
                "params_b64\tpool_b64\tfixture_b64\tactor_delta\topp_delta\tprovenance_b64\n")
        for (pid, oracle, name, stok, recipe, params, pool, fixture, dA, dO, provenance) in cases:
            f.write("\t".join([pid, oracle, b64(name), b64(stok), b64("LoseLife"), recipe,
                                b64(params), b64(pool), b64(fixture), str(dA), str(dO),
                                b64(provenance)]) + "\n")
    a.out_deferred.write_text(json.dumps(deferred, indent=1, sort_keys=True) + "\n")
    a.out_plan.write_text(json.dumps({
        "schema": "commander-simulator-next.ws33d-d2-plan.v1",
        "batch": "D2", "queue_item": f"{QUEUE_GROUP}/STATE_ONLY/LifeLoseEffect",
        "queue_count": 18, "provable_count": 8, "deferred_count": 10,
        "target_digest": digest, "forge_pin": FORGE_PIN,
        "provable_ids": cids,
    }, indent=1, sort_keys=True) + "\n")
    print(f"WS33_ABC_D2_MATERIALIZATION=PASS cases=8 deferred=10 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
