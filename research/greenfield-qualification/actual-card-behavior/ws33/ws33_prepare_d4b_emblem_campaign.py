#!/usr/bin/env python3
"""WS33-D D4b emblem campaign preparer (D-local).

Queue item WS33D/template-049/STATE_ONLY/EffectEffect (49 paths): bind each
path to its representative pinned-Forge card script, classify the 3
emblem-ultimate paths as provable under the COMMON_D4B_MECHANISM
(Doubling Season entry-doubling, single actor MAIN1, production casts,
sole ApiType.Effect ultimate, command-zone emblem assertion), and defer the
remaining 46 (8 D4a-retained + 38 standing D4 dispositions). Fail-closed on
any surprise.

D4b provable shape (3 paths): decision-free emblem creation observable as a
command-zone Effect object (+ zones/life/loyalty deltas), with zero targets,
modes, X, affordable optional payments, shuffles, combat, turn passing, or
hidden information on the exercised line. Entry loyalty must read exactly 8
(Doubling Season doubling of printed 4, engine-owned Moved/CounterTable
replacement); any other entry loyalty fails the case closed. Any decision
request at run time fails the case closed and defers the path with exact
evidence.

Keyed per (card, line): the (card, line) pairs are distinct dispositions.
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
QUEUE_GROUP = "ws33-g2-template-049"
QUEUE_SUBSYSTEM = "forge.game.ability.effects.EffectEffect"
RETAINED_PASS_ID = "forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708"

P = "PROVABLE"
# (card_file, source_line) -> (disposition, recipe, params, pool, fixture, dA, dO, note)
CARD_TABLE = {
    ("elspeth_knight_errant.txt", 7): (P, "EMBLEM_STATIC",
        "enabler=Doubling Season;fixture_spell=Wrath of God", "W4G1C8",
        "actor_bf=Runeclaw Bear:1", 0, 0,
        "DS entry-doubling to 8; -8 ultimate; SBA GY; Wrath leaves Bear on BF (indestructible static proof)"),
    ("chandra_torch_of_defiance.txt", 11): (P, "EMBLEM_TRIGGER_PRESENCE",
        "enabler=Doubling Season;final_loyalty=1", "R2G1C6", "", 0, 0,
        "DS entry-doubling to 8; -7 ultimate; loyalty 1; emblem trigger payload presence (damage is sibling line)"),
    ("tezzeret_betrayer_of_flesh.txt", 11): (P, "EMBLEM_TRIGGER_PRESENCE",
        "enabler=Doubling Season;final_loyalty=2", "U2G1C6", "", 0, 0,
        "DS entry-doubling to 8; -6 ultimate; loyalty 2; emblem trigger payload presence (tap-draw is hidden-gated)"),
    ("silence.txt", 4): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("unstable_footing.txt", 5): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("ethersworn_shieldmage.txt", 7): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("hildibrand_manderville.txt", 7): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("leitmotif_composer.txt", 9): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("burning_curiosity.txt", 6): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("electric_seaweed.txt", 8): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("gideon_jura.txt", 11): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0,
        "D4a PASS run 34411858516; not re-selected"),
    ("finale_of_revelation.txt", 7): ("DEFERRED:X_SHUFFLE_D7", "-", "", "", "", 0, 0,
        "X spell + graveyard shuffle (RNG) + conditionals; D7"),
    ("disintegrate.txt", 5): ("DEFERRED:X_AND_TARGET_D7", "-", "", "", "", 0, 0,
        "X spell + any-target; needs tapes"),
    ("furygale_flocking.txt", 7): ("DEFERRED:REPEAT_TOKENS_UNCLEAR", "-", "", "", "", 0, 0,
        "RepeatEach tokenverse + MustAttack effect attachment unclear; needs review"),
    ("strongbox_raider.txt", 8): ("DEFERRED:OPTIONAL_CHOICE_D6", "-", "", "", "", 0, 0,
        "raid + optional + ChooseCard; needs tapes"),
    ("atsushi_the_blazing_sky.txt", 10): ("DEFERRED:MODAL_DIES_D6", "-", "", "", "", 0, 0,
        "dies-trigger Charm modal; needs tapes"),
    ("conduit_of_worlds.txt", 6): ("DEFERRED:TARGET_OPTIONAL_D6", "-", "", "", "", 0, 0,
        "graveyard target + optional + cast conditions; needs tapes"),
    ("surge_to_victory.txt", 7): ("DEFERRED:TARGET_D6", "-", "", "", "", 0, 0,
        "graveyard instant/sorcery target; needs target tape"),
    ("solar_array.txt", 5): ("DEFERRED:MANA_CHOICE_D6", "-", "", "", "", 0, 0,
        "add-any-color mana choice; needs tape"),
    ("promise_of_loyalty.txt", 7): ("DEFERRED:CHOICES_SACRIFICE_D6", "-", "", "", "", 0, 0,
        "each player chooses vow creature + sacrifices rest; needs tapes"),
    ("superior_foes_of_spider_man.txt", 12): ("DEFERRED:OPTIONAL_EXILE_D6", "-", "", "", "", 0, 0,
        "may-exile on cast cmc4+ (OptionalDecider); needs tape"),
    ("gideon_jura.txt", 6): ("DEFERRED:TARGET_TURNS_D6", "-", "", "", "", 0, 0,
        "+2 delayed trigger targets opponent + next-turn machinery; D6 first-target batch"),
    ("spark_double.txt", 7): ("DEFERRED:CLONE_CHOICE_D6", "-", "", "", "", 0, 0,
        "may-enter-as-copy choice among controlled permanents; needs tape"),
    ("quintorius_loremaster.txt", 10): ("DEFERRED:TARGETS_D6", "-", "", "", "", 0, 0,
        "end-step graveyard target + AB target; needs tapes"),
    ("kang_dynasty.txt", 7): ("DEFERRED:SAGA_TARGETS_D6", "-", "", "", "", 0, 0,
        "saga lore progression + targeted goad; needs tapes"),
    ("conspiracy_theorist.txt", 8): ("DEFERRED:ATTACK_DISCARD_CHAIN_D6D8", "-", "", "", "", 0, 0,
        "attack trigger + discard chain + exile-from-grave cost; combat/choice harness"),
    ("heroic_return.txt", 5): ("DEFERRED:TARGET_COSTREDUCTION_D6", "-", "", "", "", 0, 0,
        "graveyard creature target + attacker-presence cost reduction; needs tapes"),
    ("makeshift_mannequin.txt", 5): ("DEFERRED:TARGET_D6", "-", "", "", "", 0, 0,
        "own-graveyard target; needs target tape"),
    ("circle_of_protection_blue.txt", 5): ("DEFERRED:SOURCE_CHOICE_D6", "-", "", "", "", 0, 0,
        "choose blue source + prevention; needs tape + source"),
    ("urianger_augurelt.txt", 9): ("DEFERRED:EXILED_SETUP_D6", "-", "", "", "", 0, 0,
        "Play-Arcanum Effect needs exiled-with-source setup via Draw Arcanum; needs tapes"),
    ("expressive_iteration.txt", 7): ("DEFERRED:SORT_CHOOSE_D6", "-", "", "", "", 0, 0,
        "look-sort-choose 3 (hand/bottom/exile); needs decision tapes"),
    ("progenitors_icon.txt", 7): ("DEFERRED:CHOICES_CHOOSETYPE_D6D7", "-", "", "", "", 0, 0,
        "ETB ChooseType gates flash-grant Effect; needs tapes"),
    ("containment_construct.txt", 7): ("DEFERRED:OPTIONAL_D6", "-", "", "", "", 0, 0,
        "may-exile on discard (OptionalDecider); needs tape"),
    ("intimidation_bolt.txt", 5): ("DEFERRED:TARGET_D6", "-", "", "", "", 0, 0,
        "target creature; needs target tape"),
    ("palace_jailer.txt", 9): ("DEFERRED:TARGET_MONARCH_D6", "-", "", "", "", 0, 0,
        "ETB opponent-creature target + monarch return trigger; needs tapes"),
    ("aerial_extortionist.txt", 9): ("DEFERRED:TARGETS_COMBAT_D6D8", "-", "", "", "", 0, 0,
        "up-to-one target + combat trigger; D6/D8 (zero-target ETB stretch noted)"),
    ("inkshield.txt", 4): ("DEFERRED:COMBAT_D8", "-", "", "", "", 0, 0,
        "needs combat damage to prevent/convert; combat harness"),
    ("invisible_woman.txt", 10): ("DEFERRED:TARGET_PAYMENT_COMBAT_D6D8", "-", "", "", "", 0, 0,
        "attack-trigger costed targeted Unblockable Effect (not the Wall token); combat/target harness"),
    ("love_on_the_battlefield.txt", 7): ("DEFERRED:COMBAT_D8", "-", "", "", "", 0, 0,
        "exactly-two-attackers + combat damage triggers; combat harness"),
    ("gateway_sneak.txt", 6): ("DEFERRED:GATE_COMBAT_D8", "-", "", "", "", 0, 0,
        "Gate-ETB trigger, unblockable observable via combat; combat harness"),
    ("okoye_mighty_and_adored.txt", 9): ("DEFERRED:COMBAT_TARGET_D8", "-", "", "", "", 0, 0,
        "begin-combat targeted trigger + monarch attacks; combat/target harness"),
    ("winter_soldier_reborn_avenger.txt", 6): ("DEFERRED:COMBAT_TARGET_D8", "-", "", "", "", 0, 0,
        "attack trigger + graveyard target; combat + target harness"),
    ("arbalest_elite.txt", 6): ("DEFERRED:COMBAT_TARGET_D8", "-", "", "", "", 0, 0,
        "damage-AB subability self-untap Effect; target attacking/blocking; combat + target harness"),
    ("klaw_master_of_sound.txt", 11): ("DEFERRED:COMBAT_EXILE_D8", "-", "", "", "", 0, 0,
        "combat damage exile + cast-from-exile triggers; combat harness"),
    ("willie_lumpkin_postman.txt", 8): ("DEFERRED:COMBAT_OPP_CHOICE_D8", "-", "", "", "", 0, 0,
        "combat damage + opponent may-draw choice; combat harness"),
    ("taunt_from_the_rampart.txt", 5): ("DEFERRED:COMBAT_OBS_D8", "-", "", "", "", 0, 0,
        "goad + can't-block observable only via combat; combat harness"),
    ("extract_power.txt", 5): ("DEFERRED:HIDDEN_CHOICE_D8", "-", "", "", "", 0, 0,
        "face-down exile of both libraries + may-play; hidden/choice harness"),
    ("summon_good_king_mog_xii.txt", 7): ("DEFERRED:SAGA_TRIGGER_D8", "-", "", "", "", 0, 0,
        "saga chapter + cast-trigger token copy choice; saga harness"),
    ("human_torch.txt", 8): ("DEFERRED:COMBAT_PAYMENT_D8", "-", "", "", "", 0, 0,
        "attack payment + combat-damage redirect; combat harness"),
}


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--partition", type=Path, required=True)
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
    assert len(rows) == 1, "expected exactly one D4 queue item"
    qids = rows[0]["effective_path_ids"]
    assert len(qids) == 49 and len(set(qids)) == 49, "D4 queue item must hold 49 unique ids"

    status, led = {}, {}
    for line in a.ledger.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            status[r["effective_path_id"]] = r.get("current_status")
            led[r["effective_path_id"]] = r
    part = json.loads(a.partition.read_text())
    evidenced = set(part["evidenced"])
    assert RETAINED_PASS_ID not in qids, "retained-PASS id must stay outside the D4 queue"

    cases, deferred = [], []
    for pid in qids:
        assert status.get(pid) == "UNKNOWN", f"D4 member not UNKNOWN in ledger: {pid}"
        prov = led[pid]["source_provenance"][0]
        key = (Path(prov["forge_source_path"]).name, prov.get("source_line"))
        assert key in CARD_TABLE, f"(card, line) outside frozen table: {key}"
        disp, recipe, params, pool, fixture, dA, dO, note = CARD_TABLE[key]
        txt = (a.forge_root / prov["forge_source_path"]).read_text()
        assert "Effect" in txt, f"no Effect line at pin for {key}"
        names = [l[5:] for l in txt.splitlines() if l.startswith("Name:")]
        assert len(names) >= 1 and names[0].strip(), f"no exact Name at pin for {key}"
        if disp == P:
            assert pid not in evidenced, f"D4b case already D-evidenced: {pid}"
            cases.append((pid, prov["oracle_identity"], names[0].strip(), prov["source_token"],
                          recipe, params, pool, fixture, dA, dO, "NONE",
                          f"{prov['forge_source_path']}#{prov.get('source_line')}"))
        else:
            deferred.append({"effective_path_id": pid, "card": key[0], "source_line": key[1],
                             "reason": disp, "note": note})
    assert len(cases) == 3 and len(deferred) == 46, "D4b split must be 3 + 46"
    retained = [d for d in deferred if d["reason"].startswith("RETAINED:")]
    assert len(retained) == 8, "exactly the 8 D4a paths must be retained"
    for d in retained:
        assert d["effective_path_id"] in evidenced, f"retained id not D-evidenced: {d}"
    cids = sorted(c[0] for c in cases)
    intents = {c[0]: c[10] for c in cases}
    digest = hashlib.sha256(("\n".join(cids) + "\n").encode()).hexdigest()

    a.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out_tsv, "w") as f:
        f.write("#path_id\toracle_id\tcard_b64\tsvar_token_b64\tsvar_expr_b64\trecipe\t"
                "params_b64\tpool_b64\tfixture_b64\tactor_delta\topp_delta\tprovenance_b64\tintent_b64\n")
        for (pid, oracle, name, stok, recipe, params, pool, fixture, dA, dO, intent, provenance) in cases:
            f.write("\t".join([pid, oracle, b64(name), b64(stok), b64("Effect"), recipe,
                                b64(params), b64(pool), b64(fixture), str(dA), str(dO),
                                b64(provenance), b64(intent)]) + "\n")
    a.out_deferred.write_text(json.dumps(deferred, indent=1, sort_keys=True) + "\n")
    a.out_plan.write_text(json.dumps({
        "schema": "commander-simulator-next.ws33d-d4-plan.v1",
        "batch": "D4b", "queue_item": f"{QUEUE_GROUP}/STATE_ONLY/EffectEffect",
        "queue_count": 49, "provable_count": 3, "deferred_count": 46,
        "target_digest": digest, "forge_pin": FORGE_PIN,
        "provable_ids": cids, "intents": intents,
    }, indent=1, sort_keys=True) + "\n")
    print(f"WS33_ABC_D4B_MATERIALIZATION=PASS cases=3 deferred=46 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
