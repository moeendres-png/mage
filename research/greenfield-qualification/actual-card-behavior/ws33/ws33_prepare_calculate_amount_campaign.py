#!/usr/bin/env python3
"""Prepare the WS33B AbilityUtils#calculateAmount campaign (273 canonical paths).

Reads the canonical 4188-row integrated closure ledger (never the superseded
4276-world registry), selects exactly the WS33B calculateAmount UNKNOWN set,
classifies each path by amount-expression head, picks a representative
(card, SVar token, SVar expression) with its full card SVar map from pinned
Forge, assigns a fixture recipe, and emits a case TSV plus a plan JSON.

Recipes not yet implemented by the Java campaign test are emitted with an
explicit UNSUPPORTED_* recipe tag so the test fails closed on them.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from collections import Counter
from pathlib import Path

CALCULATE_AMOUNT = "forge.game.ability.AbilityUtils#calculateAmount"


def b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_AMOUNT_PREPARE=FAIL " + message)


def head_of(expr: str) -> str:
    return expr.split("$", 1)[0] if "$" in expr else expr


def read_card_svars(card_path: Path) -> tuple[str, dict[str, str], list[str]]:
    lines = card_path.read_text(encoding="utf-8").splitlines()
    name = next((line[5:].strip() for line in lines if line.startswith("Name:")), "")
    svars: dict[str, str] = {}
    for line in lines:
        text = line.strip()
        if text.startswith("SVar:"):
            parts = text.split(":", 2)
            if len(parts) == 3:
                svars[parts[1].strip()] = parts[2].strip()
    return name, svars, lines


def place_spec(entries: list[tuple[str, str, bool]]) -> str:
    """Semicolon-joined placement list: Name,CTRL,tapped01 entries."""
    return ";".join(f"{name},{ctrl},{1 if tapped else 0}" for name, ctrl, tapped in entries)


def assign_recipe(card_name: str, token: str, expr: str) -> tuple[str, dict]:
    """Return (recipe, params). Params are fixture inputs, never engine outputs."""
    if expr == "Count$xPaid":
        return "COUNT_XPAID", {"paid": 5}
    if expr == "Count$ValidHand Card.YouOwn":
        return "COUNT_HAND_YOUOWN", {"hand_cards": 4}
    if expr.startswith("Count$CardCounters."):
        return "COUNT_HOST_COUNTERS", {"counter": expr.split(".")[1], "counters": 3}
    if expr == "Count$YourLifeTotal":
        return "COUNT_LIFE", {"life": 17}
    if expr == "Count$Valid Land.YouCtrl":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Island", "ACTOR", False)] * 3), "base": 0}
    if expr == "Count$Valid Artifact.YouCtrl":
        # Host Uthros Research Craft is itself an actor artifact: base 1.
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Sol Ring", "ACTOR", False)] * 2), "base": 1}
    if expr == "Count$Valid Artifact.YouCtrl+tapped":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Sol Ring", "ACTOR", True)] * 2), "base": 0}
    if expr == "Count$Valid Plains.YouCtrl":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Plains", "ACTOR", False)] * 3), "base": 0}
    if expr == "Count$Valid Swamp.YouCtrl":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Swamp", "ACTOR", False)] * 2), "base": 0}
    if expr == "Count$Valid Artifact.nonCreature+YouCtrl":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Sol Ring", "ACTOR", False)] * 2), "base": 0}
    if expr == "Count$Valid Creature":
        # Base: decision-fixture Prodigal Sorcerer (actor) + opponent bear.
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Runeclaw Bear", "ACTOR", False)] * 3), "base": 2}
    if expr == "Count$Valid Creature.Other+YouCtrl":
        # Other excludes the host itself; base is Prodigal Sorcerer only.
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Runeclaw Bear", "ACTOR", False)] * 3), "base": 1}
    if expr == "Count$Valid Creature.YouCtrl+withFlying":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Air Elemental", "ACTOR", False)] * 2), "base": 0}
    if expr == "Count$Valid Permanent.YouCtrl$Colors":
        return "COUNT_COLORS", {"expected_colors": 5}
    if expr == "Count$Valid Permanent.YouCtrl+Other":
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Runeclaw Bear", "ACTOR", False)] * 2), "base": 1}
    if expr == "Count$Valid Permanent.nonLand+YouCtrl":
        # Host instant on the battlefield satisfies the Permanent token via
        # isInPlay: base is Prodigal Sorcerer plus the host itself.
        return "COUNT_BATTLEFIELD_VALID", {"place": place_spec([("Runeclaw Bear", "ACTOR", False)] * 2), "base": 2}
    if expr == "Count$Valid Any":
        return "COUNT_VALID_ANY", {}
    if expr == "Count$Valid Gate.YouCtrl$DifferentCardNames":
        # Host Maze's End is itself a Gate watched by YouCtrl: counts.
        return "COUNT_GATE_NAMES", {}
    if expr == "Count$Valid Gate.YouCtrl/Times.2":
        return "COUNT_GATE_TIMES2", {}
    if expr == "Count$Valid Artifact.namedCrown of Empires+YouCtrl":
        return "COUNT_NAMED", {"name": "Crown of Empires", "count": 1}
    if expr == "Count$ValidGraveyard Creature":
        return "COUNT_GRAVE_CREATURE", {"actor_bears": 3, "opponent_bears": 1}
    if expr == "Count$ValidGraveyard Instant.YouOwn,Sorcery.YouOwn":
        return "COUNT_GRAVE_SPELLS", {"actor_shocks": 2, "opponent_shocks": 1}
    if expr == "Count$ValidHand Card.ActivePlayerCtrl":
        return "COUNT_HAND_ACTIVE", {}
    if expr == "Count$ValidBattlefield,Graveyard Card.nonCreature+YouCtrl$GreatestCardManaCost":
        return "COUNT_MAXCMC", {}
    if expr == "Count$AttackersDeclared":
        return "COUNT_ATTACKERS", {"attackers": 2}
    if expr == "Count$CardPower":
        return "COUNT_HOST_POWER", {}
    if expr == "Count$RememberedSize":
        return "COUNT_REMEMBERED_SIZE", {"remembered": 3}
    if expr == "Count$Morbid.1.0":
        return "COUNT_MORBID", {"true_val": 1}
    if expr == "Count$Morbid.5.3":
        return "COUNT_MORBID", {"true_val": 5}
    if expr == "Count$Foretold.1.0":
        return "COUNT_FORETOLD", {"true_val": 1}
    if expr == "Count$Landfall.3.1":
        return "COUNT_LANDFALL", {"true_val": 3}
    if expr == "Count$ThisTurnEntered_Graveyard_from_Battlefield_Creature.modified+YouCtrl":
        return "COUNT_ENTERED_MODIFIED", {}
    if expr == "Number$0":
        return "NUMBER_DEFAULT", {"value": 0}
    if expr == "Number$9/Minus.X":
        return "NUMBER_VRASKA", {"poison": 3}
    if expr == "PlayerCountPlayers$Amount":
        return "PLAYERCOUNT_PLAYERS", {"players": 3}
    if expr == "PlayerCountPlayers$ConditionLEY LifeTotal":
        return "PLAYERCOUNT_CONDITION", {"low_life": 5}
    if expr == "PlayerCountPlayers$HasPropertyLostLifeThisTurn":
        return "PLAYERCOUNT_LOSTLIFE", {"lost": 5}
    if expr == "PlayerCountPlayers$LifeLostThisTurn":
        return "PLAYERCOUNT_LIFELOST_SUM", {"lost": 5}
    if expr == "PlayerCountPropertyYou$CardsDiscardedThisTurn":
        return "PLAYERCOUNT_DISCARDED", {"discarded": 2}
    if expr == "PlayerCountPropertyYou$SacrificedThisTurn Permanent.!token":
        return "PLAYERCOUNT_SACRIFICED", {"sacrificed": 2}
    if expr == "PlayerCount$HasPropertyHasCardsInHand_Card_LE1":
        return "PLAYERCOUNT_HAND_LE1", {}
    if expr == "PlayerCountDefinedRegistered$HighestLifeLostThisTurn":
        return "PLAYERCOUNT_DEFINEDREGISTERED", {"lost": 5}
    if expr == "PlayerCountOpponents$HasPropertyIsRememberedOrController":
        return "PLAYERCOUNT_REMEMBERED", {}
    if expr == "PlayerCountOpponents$HighestCardsInGraveyard":
        return "PLAYERCOUNT_HIGHEST_GRAVE", {"opp1_bears": 2, "opp2_bears": 5}
    if expr == "PlayerCountOpponents$LowestLifeTotal":
        return "PLAYERCOUNT_LOWEST_LIFE", {"low_life": 15}
    if expr == "RememberedLKI$CardToughness":
        return "REMEMBEREDLKI_TOUGHNESS", {"remembered_bears": 2}
    if expr == "ReplaceCount$CounterNum/Plus.1":
        return "REPLACECOUNT_OPS", {"key": "CounterNum", "value": 3, "ops": "Plus.1"}
    if expr == "ReplaceCount$CounterNum/Twice":
        return "REPLACECOUNT_OPS", {"key": "CounterNum", "value": 3, "ops": "Twice"}
    if expr == "ReplaceCount$DamageAmount/Plus.1":
        return "REPLACECOUNT_OPS", {"key": "DamageAmount", "value": 4, "ops": "Plus.1"}
    if expr == "ReplaceCount$DamageAmount/Thrice":
        return "REPLACECOUNT_OPS", {"key": "DamageAmount", "value": 4, "ops": "Thrice"}
    if expr == "ReplaceCount$DamageAmount/Twice":
        return "REPLACECOUNT_OPS", {"key": "DamageAmount", "value": 4, "ops": "Twice"}
    if expr == "ReplaceCount$LifeGained/Plus.1":
        return "REPLACECOUNT_OPS", {"key": "LifeGained", "value": 5, "ops": "Plus.1"}
    if token == "Difference" and expr == "Number$9/Minus.X":
        return "NUMBER_VRASKA", {"poison": 3}
    if expr == "SVar$BManaPaid/LimitMax.Limit":
        return "SVAR_SOULBURN", {"paid": 4, "black": 2}
    if expr == "SVar$Y/Times.2" and token == "X":
        return "SVAR_FANDANIEL", {"actor_shocks": 2, "opponent_shocks": 1}
    if expr == "SVar$Z/Times.Y" and token == "AllM12Empires":
        return "SVAR_SCEPTER", {}
    if expr == "SVar$Y/Abs" and token == "X":
        return "SVAR_LOKI_ABS", {"remembered_bears": 2}
    if expr == "SVar$MaxPlayers/Plus.MaxPermanents":
        return "SVAR_FIREBALL", {}
    if token in {"W", "U", "B", "R", "G", "W2", "U2", "B2", "R2", "G2",
                 "WU", "BR", "WUBR", "X", "WP", "UP", "BP", "RP", "GP",
                 "WS", "US", "BS", "RS", "GS"} and card_name == "First Family":
        return "SVAR_FIRSTFAMILY", {"white": 2, "blue": 2, "black": 2, "red": 2, "green": 2}
    if expr == "TargetedController$LandsInGraveyard":
        return "TARGETEDCONTROLLER_GRAVELANDS", {"actor_lands": 2, "opponent_lands": 1}
    if expr == "TargetedObjects$Amount/Minus.1":
        return "TARGETEDOBJECTS_AMOUNT", {"objects": 3}
    if expr == "TriggeredAttacker$CardPower":
        return "TRIGGEREDATTACKER_POWER", {}
    if expr == "TriggeredObject$Valid Kree":
        return "TRIGGEREDOBJECT_KREE", {}
    if expr == "TriggeredTarget$LifeTotal/HalfUp":
        return "TRIGGEREDTARGET_LIFE", {}
    if expr == "Count$Valid Creature.YouCtrl":
        return (
            "COUNT_BATTLEFIELD_CREATURE_YOUCTRL",
            {"match": ["Runeclaw Bear", "Runeclaw Bear", "Runeclaw Bear"],
             "distractor": [("Runeclaw Bear", "OPPONENT"), ("Island", "ACTOR")]},
        )
    if expr == "Remembered$Amount":
        return "REMEMBERED_AMOUNT", {"remembered_bears": 3}
    if expr == "Remembered$CardPower":
        return "REMEMBERED_CARDPOWER", {"remembered_bears": 3}
    if expr == "Remembered$CardManaCost":
        return "REMEMBERED_CARDMANACOST", {"remembered_bears": 3}
    if expr == "Remembered$Valid Creature":
        return "REMEMBERED_VALID_CREATURE", {"match_bears": 3, "nonmatch_islands": 1}
    if expr == "Remembered$Valid Creature.inZoneGraveyard":
        return "REMEMBERED_VALID_GRAVEYARD", {"match_bears": 3}
    if expr == "Remembered$Valid Card.RememberedPlayerCtrl":
        return "REMEMBERED_VALID_PLAYERCTRL", {"match_bears": 3, "opponent_bears": 1}
    if expr == "Remembered$Valid Card.!token+YouCtrl":
        return "REMEMBERED_VALID_YOUCTRL", {"match_bears": 3, "opponent_bears": 1}
    if expr == "Sacrificed$CardPower":
        return "SACRIFICED_CARDPOWER", {"sacrificed_bears": 3}
    if expr == "Sacrificed$CardToughness":
        return "SACRIFICED_CARDTOUGHNESS", {"sacrificed_bears": 3}
    if expr == "Targeted$CardPower":
        return "TARGETED_CARDPOWER", {"target_bears": 3}
    if expr == "Targeted$CardManaCost":
        return "TARGETED_CARDMANACOST", {"target_bears": 3}
    if expr == "Targeted$CardCounters.LOYALTY":
        return "TARGETED_COUNTERS", {"counter": "LOYALTY", "counters": 4}
    if expr == "Targeted$CardToughness":
        return "TARGETED_CARDTOUGHNESS", {"target_bears": 3}
    if expr == "Targeted$Valid Creature.Human/Plus.1":
        return "TARGETED_VALID_HUMAN_PLUS1", {"human": "Elite Vanguard"}
    if expr == "TargetedPlayer$CardsInHand":
        return "TARGETEDPLAYER_CARDSINHAND", {}
    if expr == "TargetedPlayer$LifeTotal":
        return "TARGETEDPLAYER_LIFETOTAL", {}
    if expr == "TargetedPlayer$Counters.Poison":
        return "TARGETEDPLAYER_POISON", {"poison": 3}
    if expr == "TargetedPlayer$CardsInHand/Minus.X":
        return "TARGETEDPLAYER_HAND_MINUS_X", {"actor_islands": 2, "opponent_islands": 1}
    if expr == "TriggerCount$DamageAmount":
        return "TRIGGERCOUNT_DAMAGE", {"damage": 4}
    if expr == "TriggerCount$Amount":
        return "TRIGGERCOUNT_AMOUNT", {"amount": 4}
    if expr == "PlayerCountOpponents$Amount":
        return "PLAYERCOUNT_OPPONENTS_AMOUNT", {"opponents": 2}
    if expr == "PlayerCountOpponents$HighestValid Land.YouCtrl":
        return "PLAYERCOUNT_OPPONENTS_HIGHEST_LAND", {"opp1_islands": 2, "opp2_islands": 3}
    if expr in ("TriggeredCard$CardCounters.M1M1", "TriggeredCard$CardCounters.P1P1"):
        counter = expr.split(".")[1]
        return "TRIGGEREDCARD_COUNTERS", {"counter": counter, "counters": 3}
    if expr == "TriggeredCard$CardManaCost":
        return "TRIGGEREDCARD_CMC", {}
    if expr == "TriggeredCard$CardPower":
        return "TRIGGEREDCARD_POWER", {}
    if expr == "TriggeredCard$CardNumColors":
        return "TRIGGEREDCARD_COLORS", {}
    if expr == "TriggeredCard$Valid Creature.attacking":
        return "TRIGGEREDCARD_ATTACKING", {}
    if expr == "TriggeredCard$Valid Card.greatestPower":
        return "TRIGGEREDCARD_GREATESTPOWER", {}
    if expr == "TriggeredCard$CardManaCost/Minus.Z":
        return "TRIGGEREDCARD_CMC_MINUS_Z", {"remembered_bears": 2}
    if expr == "TriggeredSpellAbility$CardManaCostLKI":
        return "TRIGGEREDSPELLABILITY_CMC", {}
    if expr == "ReplaceCount$DamageAmount":
        return "REPLACECOUNT_DAMAGE", {"damage": 5}
    if expr == "ParentTargeted$CardPower":
        return "PARENTTARGETED_CARDPOWER", {"target_bears": 2}
    return "UNSUPPORTED_" + head_of(expr).upper(), {"expression": expr}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out-tsv", type=Path, required=True)
    parser.add_argument("--out-plan", type=Path, required=True)
    args = parser.parse_args()

    forge = args.forge_root.resolve()
    rows = [
        json.loads(line)
        for line in args.ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(len(rows) == 4188, f"ledger cardinality {len(rows)} != 4188")

    targets = [
        row for row in rows
        if row.get("logical_bucket") == "WS33B"
        and row.get("implementation_target") == CALCULATE_AMOUNT
        and row.get("current_status") == "UNKNOWN"
    ]
    require(len(targets) == 273, f"target cardinality {len(targets)} != 273")
    digest = hashlib.sha256(
        ("\n".join(sorted(r["effective_path_id"] for r in targets)) + "\n").encode()
    ).hexdigest()
    require(
        digest == "30dd81f733e0c1dfdb2d3020c0b9b1e0a2ed542fcf78123d641839fb24800024",
        "target-list digest mismatch " + digest,
    )

    cases = []
    skipped = Counter()
    for row in sorted(targets, key=lambda r: r["effective_path_id"]):
        provenances = row.get("source_provenance", [])
        require(bool(provenances), "path without provenance " + row["effective_path_id"])
        chosen = None
        for prov in provenances:
            if prov.get("source_directive") != "SVAR":
                continue
            card_file = forge / prov["forge_source_path"]
            if not card_file.is_file():
                continue
            name, svars, lines = read_card_svars(card_file)
            if not name or prov["source_token"] not in svars:
                continue
            chosen = (prov, name, svars, lines)
            break
        if chosen is None:
            skipped["no_resolvable_svar_provenance"] += 1
            continue
        prov, name, svars, lines = chosen
        token = prov["source_token"]
        recorded = svars[token]
        if recorded != prov["source_value"]:
            skipped["svar_value_mismatch"] += 1
            continue
        try:
            line_no = int(prov["source_line"])
        except ValueError:
            skipped["bad_source_line"] += 1
            continue
        recipe, params = assign_recipe(name, token, recorded)
        cases.append({
            "path_id": row["effective_path_id"],
            "oracle_id": prov["oracle_identity"],
            "card_name": name,
            "svar_token": token,
            "svar_expression": recorded,
            "recipe": recipe,
            "recipe_params": params,
            "svar_map": svars,
            "source_path": prov["forge_source_path"],
            "source_line": line_no,
        })

    require(cases, "no amount cases selected")
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "# path_id\toracle_id\tcard_name_b64\tsvar_token_b64\tsvar_expression_b64"
            "\trecipe\trecipe_params_b64\tsvar_map_b64\tsource_path_b64\tsource_line\n"
        )
        for case in cases:
            handle.write("\t".join([
                case["path_id"],
                case["oracle_id"],
                b64(case["card_name"]),
                b64(case["svar_token"]),
                b64(case["svar_expression"]),
                case["recipe"],
                b64(json.dumps(case["recipe_params"], sort_keys=True)),
                b64(json.dumps(case["svar_map"], sort_keys=True)),
                b64(case["source_path"]),
                str(case["source_line"]),
            ]) + "\n")

    plan = {
        "schema": "commander-simulator-next.ws33-calculate-amount-campaign-plan.v1",
        "selection_policy": {
            "ledger": "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl (4188 rows)",
            "logical_bucket": "WS33B",
            "implementation_target": CALCULATE_AMOUNT,
            "current_status": "UNKNOWN",
            "target_digest": digest,
            "representative_policy": "first SVAR provenance resolvable against pinned Forge with exact SVar value match",
            "pilot_policy": "fixture-designated inputs only; engine output asserted against deterministic function of fixture inputs via production calculateAmount/doXMath",
        },
        "case_count": len(cases),
        "recipe_counts": dict(Counter(c["recipe"] for c in cases)),
        "skipped_counts": dict(skipped),
        "cases": cases,
    }
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(
        {"WS33_AMOUNT_PREPARE": "PASS", "case_count": len(cases),
         "recipes": plan["recipe_counts"], "skipped": plan["skipped_counts"]},
        sort_keys=True))


if __name__ == "__main__":
    main()
