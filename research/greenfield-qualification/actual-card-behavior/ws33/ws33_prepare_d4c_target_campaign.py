#!/usr/bin/env python3
"""WS33-D D4c target campaign preparer (D-local).

Queue item WS33D/template-049/STATE_ONLY/EffectEffect (49 paths): bind each
path to its representative pinned-Forge card script, classify the 4
T1 single-mandatory-target spell-cast paths as provable under the D4c-T1
mechanism (production SP cast from hand, exactly one cast-time
chooseTargetsFor -> TARGET_SELECTION uniquely matched to the
case-designated ENTITY intent, command-zone Effect assertion), retain the
11 D4a/D4b-evidenced paths, and defer the remaining 34 with the exact
D4c survey disposition. Fail-closed on any surprise.

D4c-T1 provable shape (4 paths): production spell-cast entry (D1/D3/D4a
proven), exactly one mandatory target decision on the path to the ledger
Effect line (G-proven TARGET_SELECTION transport via the retained
target-selection overlay), zero other prompts, no hidden/RNG/combat/
turn-passing. Fixture carries two legal candidates per case so the choice
is genuinely discretionary; the provider selects the designated entity
only on a unique authoritative match (zero/multiple fail closed). Any
other decision request at run time fails the case closed.

Keyed per (card, line): gideon_jura L6 (+2 delayed trigger, auto-target
activation -> A-auto) and L11 (0-loyalty animate self-prevention -> D4a
retained) are distinct dispositions, as in D4a/D4b.
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
# (card_file, source_line) -> (disposition, recipe, params, pool, fixture, dA, dO, intent, note)
CARD_TABLE = {
    ("surge_to_victory.txt", 7): (P, "TARGET_SINGLE_GRAVE_SPELL",
        "effect_kind=trigger", "R2C4", "actor_gy=Shock:1,Seismic Rupture:1", 0, 0,
        "ENTITY:Shock:actor:Graveyard",
        "SP cast; 1 TARGET_SELECTION (own-GY instant/sorcery, 2 candidates); PumpAll X automatic; Effect trigger payload"),
    ("heroic_return.txt", 5): (P, "TARGET_SINGLE_GRAVE_CREATURE_RETURN",
        "effect_kind=replacement", "W1C5", "actor_gy=Runeclaw Bear:1,Memnite:1", 0, 0,
        "ENTITY:Runeclaw Bear:actor:Graveyard",
        "SP cast; 1 TARGET_SELECTION (subability DBReturn own-GY creature, 2 candidates); ETBCreat inert for non-Hero; Effect replacement payload"),
    ("makeshift_mannequin.txt", 5): (P, "TARGET_SINGLE_GRAVE_CREATURE_RETURN_COUNTER",
        "effect_kind=static", "B1C3", "actor_gy=Runeclaw Bear:1,Memnite:1", 0, 0,
        "ENTITY:Runeclaw Bear:actor:Graveyard",
        "SP cast; 1 TARGET_SELECTION (own-GY creature, 2 candidates); WithCountersType MANNEQUIN; Effect static payload"),
    ("intimidation_bolt.txt", 5): (P, "TARGET_SINGLE_BATTLEFIELD_DAMAGE",
        "effect_kind=static", "R1W1", "actor_bf=Runeclaw Bear:1;opp_bf=Runeclaw Bear:1", 0, 0,
        "ENTITY:Runeclaw Bear:actor:Battlefield",
        "SP cast; 1 TARGET_SELECTION (BF creature, 2 candidates across owners); fixed 3 damage; Effect ForbidAttack static payload"),
    ("silence.txt", 4): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("unstable_footing.txt", 5): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("ethersworn_shieldmage.txt", 7): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("hildibrand_manderville.txt", 7): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("leitmotif_composer.txt", 9): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("burning_curiosity.txt", 6): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("electric_seaweed.txt", 8): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("gideon_jura.txt", 11): ("RETAINED:D4A_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4a PASS run 34411858516; not re-selected"),
    ("tezzeret_betrayer_of_flesh.txt", 11): ("RETAINED:D4B_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4b PASS run 34419391829; not re-selected"),
    ("elspeth_knight_errant.txt", 7): ("RETAINED:D4B_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4b PASS run 34419391829; not re-selected"),
    ("chandra_torch_of_defiance.txt", 11): ("RETAINED:D4B_EVIDENCED", "-", "", "", "", 0, 0, "-",
        "D4b PASS run 34419391829; not re-selected"),
    ("kang_dynasty.txt", 7): ("DEFERRED:T2_TRIGGER_TARGET", "-", "", "", "", 0, 0, "-",
        "saga chapter-trigger entry + lore phases; T2 subfamily after T1"),
    ("palace_jailer.txt", 9): ("DEFERRED:T2_TRIGGER_TARGET", "-", "", "", "", 0, 0, "-",
        "ETB trigger entry + GUI_ORDER + TARGET_SELECTION; T2 subfamily after T1"),
    ("strongbox_raider.txt", 8): ("DEFERRED:E_CONFIRM_CHOICE", "-", "", "", "", 0, 0, "-",
        "raid + CONFIRM_TRIGGER + ENTITY_CARD_SELECTION; E-confirm subfamily"),
    ("superior_foes_of_spider_man.txt", 12): ("DEFERRED:E_CONFIRM", "-", "", "", "", 0, 0, "-",
        "cast-trigger CONFIRM_TRIGGER + cmc4+ cast setup; E-confirm subfamily"),
    ("containment_construct.txt", 7): ("DEFERRED:E_CONFIRM", "-", "", "", "", 0, 0, "-",
        "discard-trigger CONFIRM_TRIGGER + discard outlet setup; E-confirm subfamily"),
    ("circle_of_protection_blue.txt", 5): ("DEFERRED:E_SINGLE_SOURCE", "-", "", "", "", 0, 0, "-",
        "AB ChooseSource ENTITY_SINGLE_SELECTION + divider re-prompt quirk; entity subfamily"),
    ("expressive_iteration.txt", 7): ("DEFERRED:E_DIG_HIDDEN", "-", "", "", "", 0, 0, "-",
        "2x ENTITY_MULTI_SELECTION dig picks + hidden library look; entity/hidden subfamily"),
    ("atsushi_the_blazing_sky.txt", 10): ("DEFERRED:M_MODAL", "-", "", "", "", 0, 0, "-",
        "dies-trigger Charm MODE_SELECTION + dies setup; modal subfamily"),
    ("solar_array.txt", 5): ("DEFERRED:C_COLOR", "-", "", "", "", 0, 0, "-",
        "mana COLOR_SELECTION on non-stack ability; color-choice subfamily"),
    ("conduit_of_worlds.txt", 6): ("DEFERRED:A_MULTI", "-", "", "", "", 0, 0, "-",
        "AB entry + TARGET_SELECTION + ENTITY_SINGLE_SELECTION + CONFIRM_ACTION; activation subfamily"),
    ("gideon_jura.txt", 6): ("DEFERRED:A_AUTO", "-", "", "", "", 0, 0, "-",
        "+2 loyalty AB, auto-target opponent in 1-opponent games (zero prompts); planeswalker entry; activation subfamily"),
    ("promise_of_loyalty.txt", 7): ("DEFERRED:P_MULTI_ACTOR", "-", "", "", "", 0, 0, "-",
        "per-player ENTITY_CARD_SELECTION incl. opponent principal; multi-actor subfamily"),
    ("quintorius_loremaster.txt", 10): ("DEFERRED:H_HEAVY", "-", "", "", "", 0, 0, "-",
        "end-step turn passage + REJECT-grade sac cost + multi-decision; heavy setup, AUTHORITY_GATE if pursued"),
    ("conspiracy_theorist.txt", 8): ("DEFERRED:H_HEAVY", "-", "", "", "", 0, 0, "-",
        "combat entry + REJECT-grade discard cost; heavy setup, AUTHORITY_GATE if pursued"),
    ("urianger_augurelt.txt", 9): ("DEFERRED:H_HEAVY", "-", "", "", "", 0, 0, "-",
        "face-down exile hidden setup + untap/turn-pass dependency; heavy setup"),
    ("spark_double.txt", 7): ("DEFERRED:X_BLOCKED_REPLACEMENT_ORDER", "-", "", "", "", 0, 0, "-",
        "ETB replacement routing rejects REPLACEMENT_ORDER under strict WS01; SOL adjudication candidate, never blocks siblings"),
    ("progenitors_icon.txt", 7): ("DEFERRED:X_BLOCKED_REPLACEMENT_ORDER", "-", "", "", "", 0, 0, "-",
        "ETB replacement routing rejects REPLACEMENT_ORDER under strict WS01; SOL adjudication candidate, never blocks siblings"),
    ("finale_of_revelation.txt", 7): ("DEFERRED:X_SHUFFLE_D7", "-", "", "", "", 0, 0, "-",
        "X spell + graveyard shuffle (RNG) + conditionals; D7"),
    ("disintegrate.txt", 5): ("DEFERRED:X_AND_TARGET_D7", "-", "", "", "", 0, 0, "-",
        "X spell + any-target; needs tapes"),
    ("furygale_flocking.txt", 7): ("DEFERRED:REPEAT_TOKENS_UNCLEAR", "-", "", "", "", 0, 0, "-",
        "RepeatEach tokenverse + MustAttack effect attachment unclear; needs review"),
    ("aerial_extortionist.txt", 9): ("DEFERRED:TARGETS_COMBAT_D6D8", "-", "", "", "", 0, 0, "-",
        "up-to-one target + combat trigger; D6/D8 (zero-target ETB stretch noted)"),
    ("inkshield.txt", 4): ("DEFERRED:COMBAT_D8", "-", "", "", "", 0, 0, "-",
        "needs combat damage to prevent/convert; combat harness"),
    ("invisible_woman.txt", 10): ("DEFERRED:TARGET_PAYMENT_COMBAT_D6D8", "-", "", "", "", 0, 0, "-",
        "attack-trigger costed targeted Unblockable Effect (not the Wall token); combat/target harness"),
    ("love_on_the_battlefield.txt", 7): ("DEFERRED:COMBAT_D8", "-", "", "", "", 0, 0, "-",
        "exactly-two-attackers + combat damage triggers; combat harness"),
    ("gateway_sneak.txt", 6): ("DEFERRED:GATE_COMBAT_D8", "-", "", "", "", 0, 0, "-",
        "Gate-ETB trigger, unblockable observable via combat; combat harness"),
    ("okoye_mighty_and_adored.txt", 9): ("DEFERRED:COMBAT_TARGET_D8", "-", "", "", "", 0, 0, "-",
        "begin-combat targeted trigger + monarch attacks; combat/target harness"),
    ("winter_soldier_reborn_avenger.txt", 6): ("DEFERRED:COMBAT_TARGET_D8", "-", "", "", "", 0, 0, "-",
        "attack trigger + graveyard target; combat + target harness"),
    ("arbalest_elite.txt", 6): ("DEFERRED:COMBAT_TARGET_D8", "-", "", "", "", 0, 0, "-",
        "damage-AB subability self-untap Effect; target attacking/blocking; combat + target harness"),
    ("klaw_master_of_sound.txt", 11): ("DEFERRED:COMBAT_EXILE_D8", "-", "", "", "", 0, 0, "-",
        "combat damage exile + cast-from-exile triggers; combat harness"),
    ("willie_lumpkin_postman.txt", 8): ("DEFERRED:COMBAT_OPP_CHOICE_D8", "-", "", "", "", 0, 0, "-",
        "combat damage + opponent may-draw choice; combat harness"),
    ("taunt_from_the_rampart.txt", 5): ("DEFERRED:COMBAT_OBS_D8", "-", "", "", "", 0, 0, "-",
        "goad + can't-block observable only via combat; combat harness"),
    ("extract_power.txt", 5): ("DEFERRED:HIDDEN_CHOICE_D8", "-", "", "", "", 0, 0, "-",
        "face-down exile of both libraries + may-play; hidden/choice harness"),
    ("summon_good_king_mog_xii.txt", 7): ("DEFERRED:SAGA_TRIGGER_D8", "-", "", "", "", 0, 0, "-",
        "saga chapter + cast-trigger token copy choice; saga harness"),
    ("human_torch.txt", 8): ("DEFERRED:COMBAT_PAYMENT_D8", "-", "", "", "", 0, 0, "-",
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
        disp, recipe, params, pool, fixture, dA, dO, intent, note = CARD_TABLE[key]
        txt = (a.forge_root / prov["forge_source_path"]).read_text()
        assert "Effect" in txt, f"no Effect line at pin for {key}"
        names = [l[5:] for l in txt.splitlines() if l.startswith("Name:")]
        assert len(names) >= 1 and names[0].strip(), f"no exact Name at pin for {key}"
        if disp == P:
            assert pid not in evidenced, f"D4c case already D-evidenced: {pid}"
            assert intent.startswith("ENTITY:"), f"D4c-T1 case requires ENTITY intent: {key}"
            cases.append((pid, prov["oracle_identity"], names[0].strip(), prov["source_token"],
                          recipe, params, pool, fixture, dA, dO, intent,
                          f"{prov['forge_source_path']}#{prov.get('source_line')}"))
        else:
            deferred.append({"effective_path_id": pid, "card": key[0], "source_line": key[1],
                             "reason": disp, "note": note})
    assert len(cases) == 4 and len(deferred) == 45, "D4c split must be 4 + 45"
    retained = [d for d in deferred if d["reason"].startswith("RETAINED:")]
    assert len(retained) == 11, "exactly the 11 D4a/D4b paths must be retained"
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
        "batch": "D4c", "queue_item": f"{QUEUE_GROUP}/STATE_ONLY/EffectEffect",
        "queue_count": 49, "provable_count": 4, "deferred_count": 45,
        "target_digest": digest, "forge_pin": FORGE_PIN,
        "provable_ids": cids, "intents": intents,
    }, indent=1, sort_keys=True) + "\n")
    print(f"WS33_ABC_D4C_MATERIALIZATION=PASS cases=4 deferred=45 digest={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
