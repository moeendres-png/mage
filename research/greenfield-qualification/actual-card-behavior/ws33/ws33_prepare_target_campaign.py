#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from collections import Counter
from pathlib import Path

SUPPORTED = {
    "Creature": "OPPONENT_CREATURE",
    "Creature.YouCtrl": "OWN_CREATURE",
    "Player": "OPPONENT_PLAYER",
    "Opponent": "OPPONENT_PLAYER",
    "Any": "OPPONENT_PLAYER",
    "Card": "OPPONENT_CREATURE",
    "Creature.OppCtrl": "OPPONENT_CREATURE",
    "Artifact,Enchantment": "OPPONENT_ARTIFACT",
    "Player,Planeswalker": "OPPONENT_PLAYER",
    "Artifact": "OPPONENT_ARTIFACT",
    "Permanent.YouCtrl": "OWN_CREATURE",
    "Creature,Planeswalker": "OPPONENT_CREATURE",
    "Creature.nonBlack": "OPPONENT_CREATURE",
    "Creature.Other+YouCtrl": "OWN_CREATURE",
    "Permanent.nonLand": "OPPONENT_CREATURE",
    "Artifact,Creature": "OPPONENT_ARTIFACT",
    "Creature,Artifact": "OPPONENT_CREATURE",
    "Creature,Enchantment": "OPPONENT_CREATURE",
    "Permanent": "OPPONENT_CREATURE",
    "Card,Emblem": "OPPONENT_CREATURE",
    "Instant,Sorcery": "OPPONENT_INSTANT",
    "Artifact,Creature,Land": "OPPONENT_ARTIFACT",
    "Creature.powerLE2": "OPPONENT_CREATURE",
    "Creature.YouOwn": "OWN_CREATURE",
    "Instant.YouCtrl,Sorcery.YouCtrl": "OWN_INSTANT",
    "Instant.YouOwn,Sorcery.YouOwn": "OWN_INSTANT",
    "Artifact.YouCtrl": "OWN_ARTIFACT",
    "Elemental.YouCtrl": "OWN_ELEMENTAL",
    "Card.nonCreature": "OPPONENT_ARTIFACT",
    "Creature.Other": "OPPONENT_CREATURE",
    "Creature.toughnessGE4": "OPPONENT_ELEMENTAL",
    "Permanent.nonLand+OppCtrl": "OPPONENT_CREATURE",
}
def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_TARGET_PREPARE=FAIL " + message)


def evidence_profile(path: dict) -> str:
    names = []
    for name, key in (
        ("DECISION", "required_decision_evidence"),
        ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"),
        ("REPLAY", "required_replay_evidence"),
    ):
        if path.get(key):
            names.append(name)
    return "+".join(names) if names else "STATE_ONLY"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out-tsv", type=Path, required=True)
    parser.add_argument("--out-plan", type=Path, required=True)
    args = parser.parse_args()

    manifest = load(args.manifest)
    forge = args.forge_root.resolve()
    rows = []
    skipped = Counter()

    for path in sorted(manifest["paths"], key=lambda item: item["v2_path_id"]):
        if path["owner_family"] != "ACTION_COST_DECISION":
            continue
        if path["implementation_target"] != "forge.game.spellability.TargetRestrictions":
            continue
        if evidence_profile(path) != "DECISION+REPLAY":
            skipped["non_decision_replay_profile"] += 1
            continue
        selector = path.get("semantic_selector_profile", {})
        if selector.get("record") not in {"A", "SVAR"}:
            skipped["unsupported_record"] += 1
            continue
        provenance = [
            item for item in path.get("source_provenance", [])
            if item.get("source_token") == "ValidTgts$" and item.get("source_value") in SUPPORTED
        ]
        if not provenance:
            skipped["unsupported_valid_tgts"] += 1
            continue

        chosen = provenance[0]
        source_path = forge / chosen["forge_source_path"]
        if not source_path.is_file():
            skipped["missing_source"] += 1
            continue
        lines = source_path.read_text(encoding="utf-8").splitlines()
        line_no = int(chosen["source_line"])
        if line_no < 1 or line_no > len(lines):
            skipped["bad_source_line"] += 1
            continue
        source_line = lines[line_no - 1].strip()
        fields = [field.strip() for field in source_line.split("|")]
        if not fields or "$" not in fields[0]:
            skipped["non_ability_line"] += 1
            continue
        ability_field = fields[0]
        svar_name = ""
        if ability_field.startswith("A:"):
            ability_field = ability_field[2:].strip()
        elif ability_field.startswith("SVar:"):
            _, svar_name, ability_field = ability_field.split(":", 2)
            ability_field = ability_field.strip()
        prefix, api = [part.strip() for part in ability_field.split("$", 1)]
        if prefix not in {"SP", "AB", "DB"} or not api:
            skipped["unsupported_ability_record"] += 1
            continue

        name = next((line[5:].strip() for line in lines if line.startswith("Name:")), None)
        require(bool(name), "card source missing Name: " + chosen["forge_source_path"])
        alternate_mode = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("AlternateMode:")), "None")
        alternate_line = next((index + 1 for index, line in enumerate(lines) if line.strip() == "ALTERNATE"), None)
        on_alternate = alternate_line is not None and line_no > alternate_line
        state_by_mode = {
            "Split": ("LeftSplit", "RightSplit"),
            "Prepare": ("Original", "PreparedSpell"),
            "Adventure": ("Original", "Secondary"),
            "Omen": ("Original", "Secondary"),
            "Modal": ("Original", "Backside"),
            "Transform": ("Original", "Backside"),
            "DoubleFaced": ("Original", "Backside"),
        }
        primary_state, alternate_state = state_by_mode.get(alternate_mode, ("Original", "Original"))
        ability_state = alternate_state if on_alternate else primary_state
        parsed_fields = {}
        for field in fields[1:]:
            if "$" in field:
                key, value = [part.strip() for part in field.split("$", 1)]
                parsed_fields[key] = value
        valid_tgts = chosen["source_value"]
        target_type = parsed_fields.get("TargetType", "Card")
        origin = parsed_fields.get("Origin", "Battlefield")
        if any(token in target_type for token in ("Activated", "Triggered")):
            fixture_context = "STACK_TRIGGERED_ABILITY"
        elif api in {"Counter", "CopySpellAbility"} and not target_type.startswith("Spell"):
            target_type = "Spell"
        if target_type.startswith("Spell"):
            if ".singleTarget" in target_type:
                fixture_context = "STACK_SINGLE_TARGET_SPELL"
            elif "Artifact" in valid_tgts:
                fixture_context = "STACK_ARTIFACT_SPELL"
            elif any(token in valid_tgts for token in ("Instant", "Sorcery", "nonCreature", "Card", "Emblem")):
                fixture_context = "STACK_INSTANT_SPELL"
            else:
                fixture_context = "STACK_CREATURE_SPELL"
        elif any(token in target_type for token in ("Activated", "Triggered")):
            pass
        elif origin == "Graveyard":
            fixture_context = "GRAVEYARD"
        else:
            fixture_context = "BATTLEFIELD_OR_PLAYER"
        rows.append({
            "path_id": path["v2_path_id"],
            "oracle_id": chosen["oracle_identity"],
            "card_name": name,
            "valid_tgts": valid_tgts,
            "target_role": SUPPORTED[valid_tgts],
            "ability_kind": prefix,
            "svar_name": svar_name,
            "api": api,
            "ability_state": ability_state,
            "fixture_context": fixture_context,
            "spell_description": parsed_fields.get("SpellDescription", ""),
            "source_path": chosen["forge_source_path"],
            "source_line": line_no,
        })

    require(rows, "no conservative TargetRestrictions cases selected")
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# path_id\toracle_id\tcard_name_b64\tvalid_tgts_b64\ttarget_role\tability_kind\tapi_b64\tsvar_name_b64\tability_state\tfixture_context\tspell_description_b64\tsource_path_b64\tsource_line\n")
        for row in rows:
            handle.write("\t".join([
                row["path_id"], row["oracle_id"], b64(row["card_name"]), b64(row["valid_tgts"]),
                row["target_role"], row["ability_kind"], b64(row["api"]), b64(row["svar_name"]),
                row["ability_state"], row["fixture_context"],
                b64(row["spell_description"]), b64(row["source_path"]),
                str(row["source_line"]),
            ]) + "\n")

    plan = {
        "schema": "commander-simulator-next.ws33-targetrestrictions-campaign-plan.v1",
        "selection_policy": {
            "owner_family": "ACTION_COST_DECISION",
            "implementation_target": "forge.game.spellability.TargetRestrictions",
            "evidence_profile": "DECISION+REPLAY",
            "record": ["A", "SVAR"],
            "actual_single_target_shape_required_at_runtime": True,
            "supported_valid_tgts": SUPPORTED,
            "pilot_policy": "select the fixture-designated target only if Forge emits it; then select DONE only if Forge emits it",
        },
        "case_count": len(rows),
        "valid_tgts_counts": dict(Counter(row["valid_tgts"] for row in rows)),
        "ability_kind_counts": dict(Counter(row["ability_kind"] for row in rows)),
        "skipped_counts": dict(skipped),
        "cases": rows,
    }
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"WS33_TARGET_PREPARE": "PASS", "case_count": len(rows), "valid_tgts": plan["valid_tgts_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
