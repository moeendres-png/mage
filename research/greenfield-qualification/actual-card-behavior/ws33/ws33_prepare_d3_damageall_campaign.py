#!/usr/bin/env python3
"""WS33-D D3 DamageAll campaign preparer (D-local).

Queue item WS33D/template-039/STATE_ONLY/DamageAllEffect (17 UNKNOWN paths):
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
QUEUE_GROUP = "ws33-g2-template-039"
QUEUE_SUBSYSTEM = "forge.game.ability.effects.DamageAllEffect"

P = "PROVABLE"
# card_file -> (disposition, ability_kind, recipe, params, pool, fixture, dA, dO, note)
CARD_TABLE = {
    "seismic_rupture.txt": (P, "SP", "SPELL_DAMAGE_ALL", "", "R1C2",
        "actor_bf=Suntail Hawk:1;opp_bf=Runeclaw Bear:1", 0, 0,
        "2 to each nonflyer: bear dies; 1/1 flyer survival proves 0 damage to it"),
    "chain_reaction.txt": (P, "SP", "SPELL_DAMAGE_ALL", "", "R2C2",
        "actor_bf=Runeclaw Bear:2;opp_bf=Runeclaw Bear:1", 0, 0,
        "X=3 creatures on BF; all bears die; no player damage"),
    "volcanic_torrent.txt": (P, "SP", "SPELL_DAMAGE_ALL", "", "R1C4",
        "opp_bf=Elite Vanguard:1", 0, 0,
        "X counts itself so X=1; 2/1 vanguard dies proving the hit"),
    "village_pillagers.txt": (P, "DB", "ETB_DAMAGE_OPP", "", "",
        "opp_bf=Elite Vanguard:1", 0, 0,
        "ETB 1 to each opp creature; 2/1 vanguard dies"),
    "magma_phoenix.txt": (P, "DB", "DIES_TRIGGER_WRATH", "", "W2C2",
        "actor_bf=Runeclaw Bear:1;opp_bf=Runeclaw Bear:1", -3, -3,
        "Wrath kills phoenix+bears; dies trigger 3 to each creature+player"),
    "crystal_inhuman_princess.txt": (P, "DB", "CAST_TRIGGER_SOURCE", "spell=Divination", "U1C2",
        "library_fill=3", 0, -1,
        "cast Divination (mono-U noncreature) -> SpellCast trigger X=1 color"),
    "yshtola_nights_blessed.txt": (P, "DB", "CAST_TRIGGER_SOURCE", "spell=Concentrate", "U2C2",
        "library_fill=4", 2, -2,
        "cast Concentrate (cmc 4) -> trigger 2 to each opp + gain 2"),
    "burn_down_the_house.txt": ("DEFERRED:MODAL_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "Charm modal choice; needs tape"),
    "electric_seaweed.txt": ("DEFERRED:STATE_UNOBSERVABLE", "DB", "-", "", "", "", 0, 0,
        "turn-long dies-watch damage unobservable in final state without damage-mark API"),
    "nova_flame.txt": ("DEFERRED:X_AND_TARGET_D7", "SP", "-", "", "", "", 0, 0,
        "X cost + target own creature + power-derived damage; needs tapes"),
    "cerebral_eruption.txt": ("DEFERRED:TARGET_DECISION_D6", "SP", "-", "", "", "", 0, 0,
        "target opponent + library-top reveal; needs target tape"),
    "kediss_emberclaw_familiar.txt": ("DEFERRED:COMBAT_COMMANDER_D8", "DB", "-", "", "", "", 0, 0,
        "commander combat-damage trigger; needs combat harness"),
    "human_torch.txt": ("DEFERRED:COMBAT_PAYMENT_D8", "DB", "-", "", "", "", 0, 0,
        "combat trigger + mana payment option; needs combat harness"),
    "fateful_tempest.txt": ("DEFERRED:VOTE_D6", "SP", "-", "", "", "", 0, 0,
        "council vote (opponent choice) + mill + MV-derived damage; needs vote machinery"),
    "lady_loki_agent_of_chaos.txt": ("DEFERRED:DIG_AND_CAST_D8", "DB", "-", "", "", "", 0, 0,
        "exile-dig + damage difference + optional free cast; needs dig/choice harness"),
    "chandra_nalaar.txt": ("DEFERRED:TARGETS_DECISION_D6", "AB", "-", "", "", "", 0, 0,
        "all loyalty abilities targeted (+X); needs target tapes"),
    "planetary_annihilation.txt": ("DEFERRED:LAND_CHOICES_D6", "SP", "-", "", "", "", 0, 0,
        "each player chooses 6 lands to keep; needs choice tapes"),
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
    assert len(rows) == 1, "expected exactly one D3 queue item"
    qids = rows[0]["effective_path_ids"]
    assert len(qids) == 17 and len(set(qids)) == 17, "D3 queue item must hold 17 unique ids"

    status, led = {}, {}
    for line in a.ledger.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            status[r["effective_path_id"]] = r.get("current_status")
            led[r["effective_path_id"]] = r
    for pid in qids:
        assert status.get(pid) == "UNKNOWN", f"D3 member not UNKNOWN: {pid}"

    cases, deferred = [], []
    for pid in qids:
        prov = led[pid]["source_provenance"][0]
        card_file = Path(prov["forge_source_path"]).name
        assert card_file in CARD_TABLE, f"card outside frozen table: {card_file}"
        disp, kind, recipe, params, pool, fixture, dA, dO, note = CARD_TABLE[card_file]
        txt = (a.forge_root / prov["forge_source_path"]).read_text()
        assert "DamageAll" in txt, f"no DamageAll line at pin for {card_file}"
        names = [l[5:] for l in txt.splitlines() if l.startswith("Name:")]
        assert len(names) == 1 and names[0].strip(), f"no exact Name at pin for {card_file}"
        if disp == P:
            cases.append((pid, prov["oracle_identity"], names[0].strip(), prov["source_token"],
                          recipe, params, pool, fixture, dA, dO, "NONE",
                          f"{prov['forge_source_path']}#{prov.get('source_line')}"))
        else:
            deferred.append({"effective_path_id": pid, "card": card_file,
                             "reason": disp, "note": note})
    assert len(cases) == 7 and len(deferred) == 10, "D3 split must be 7 + 10"
    cids = sorted(c[0] for c in cases)
    intents = {c[0]: c[10] for c in cases}
    digest = hashlib.sha256(("\n".join(cids) + "\n").encode()).hexdigest()

    a.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out_tsv, "w") as f:
        f.write("#path_id\toracle_id\tcard_b64\tsvar_token_b64\tsvar_expr_b64\trecipe\t"
                "params_b64\tpool_b64\tfixture_b64\tactor_delta\topp_delta\tprovenance_b64\tintent_b64\n")
        for (pid, oracle, name, stok, recipe, params, pool, fixture, dA, dO, intent, provenance) in cases:
            f.write("\t".join([pid, oracle, b64(name), b64(stok), b64("DamageAll"), recipe,
                                b64(params), b64(pool), b64(fixture), str(dA), str(dO),
                                b64(provenance), b64(intent)]) + "\n")
    a.out_deferred.write_text(json.dumps(deferred, indent=1, sort_keys=True) + "\n")
    a.out_plan.write_text(json.dumps({
        "schema": "commander-simulator-next.ws33d-d3-plan.v1",
        "batch": "D3", "queue_item": f"{QUEUE_GROUP}/STATE_ONLY/DamageAllEffect",
        "queue_count": 17, "provable_count": 7, "deferred_count": 10,
        "target_digest": digest, "forge_pin": FORGE_PIN,
        "provable_ids": cids, "intents": intents,
    }, indent=1, sort_keys=True) + "\n")
    print(f"WS33_ABC_D3_MATERIALIZATION=PASS cases=7 deferred=10 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
