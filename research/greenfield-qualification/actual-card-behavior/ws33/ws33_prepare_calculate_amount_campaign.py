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


def assign_recipe(token: str, expr: str) -> tuple[str, dict]:
    """Return (recipe, params). Params are fixture inputs, never engine outputs."""
    if expr == "Count$xPaid":
        return "COUNT_XPAID", {"paid": 5}
    if expr == "Count$ValidHand Card.YouOwn":
        return "COUNT_HAND_YOUOWN", {"hand_cards": 4}
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
        recipe, params = assign_recipe(token, recorded)
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
