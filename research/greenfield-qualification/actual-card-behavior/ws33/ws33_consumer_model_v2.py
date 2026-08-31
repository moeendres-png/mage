#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
SVAR_DOMAIN = "SVAR_RUNTIME_EXPRESSION"
OWNER_ACTION = "ACTION_COST_DECISION"
OWNER_TRZ = "TRIGGER_REPLACEMENT_ZONE_SBA"
OWNER_CONT = "CONTINUOUS_COPY_CONTROL"

TEXT_FIELDS = {
    "Description", "SpellDescription", "TriggerDescription", "StackDescription",
    "TgtPrompt", "ValidTgtsDesc", "AILogic", "PrecostDesc", "CostDesc",
}
DESTINATION_NAME_FIELDS = {"SVar"}
REPLACEMENT_FIELDS = {"ReplacementEffects"}
TRIGGER_FIELDS = {"Triggers", "AddTrigger", "TriggersWhenSpent"}
STATIC_FIELDS = {"StaticAbilities", "staticAbilities", "AddStaticAbility", "StaticEffect"}
ABILITY_FIELDS = {
    "Execute", "SubAbility", "RepeatSubAbility", "ReplaceWith", "PreventionSubAbility",
    "WinSubAbility", "OtherwiseSubAbility", "BidSubAbility", "ChooseNumberSubAbility",
    "Lowest", "Highest", "NotLowest", "GuessCorrect", "GuessWrong", "MatchedAbility",
    "UnmatchedAbility", "HeadsSubAbility", "TailsSubAbility", "LoseSubAbility",
    "TrueSubAbility", "FalseSubAbility", "ChosenPile", "UnchosenPile", "FallbackAbility",
    "ChooseSubAbility", "CantChooseSubAbility", "RegenerationAbility", "ReturnAbility",
    "GiftAbility", "VoteSubAbility", "VoteTiedAbility", "Abilities",
}
COST_FIELDS = {"Cost", "UnlessCost"}
AMOUNT_FIELDS = {
    "Amount", "AddPower", "AddToughness", "SetPower", "SetToughness", "Num", "NumAtt",
    "NumDef", "NumDmg", "NumCards", "NumCopies", "CounterNum", "DigNum", "RevealNumber",
    "TokenAmount", "TargetMin", "TargetMax", "DividedAsYouChoose", "ReduceCost", "CheckSVar",
    "ConditionCheckSVar", "RepeatCheckSVar", "LifeAmount", "Announce", "Count", "Number",
    "Max", "Min", "Power", "Toughness", "DamageAmount", "CounterAmount", "RemoveAmount",
    "SacAmount", "DiscardAmount", "ExileAmount", "DrawAmount", "DiscardNum", "PayLifeAmount",
    "ManaAmount", "X", "Y", "Z", "CharmNum",
}
SELECTOR_FIELDS = {
    "Defined", "DefinedCards", "DefinedPlayers", "DefinedObjects", "AffectedDefined", "RememberObjects",
    "RememberLKI", "ValidCard", "ValidCards", "ValidPlayer", "ValidSource", "ValidTarget", "Choices",
}
STATIC_ASSIGN_FIELDS = {"AddSVar"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def path_id(desc: dict) -> str:
    return "forge-behavior-v2:" + hashlib.sha256(canonical(desc)).hexdigest()[:40]


def token_match(value: str, token: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", value) is not None


def parse_fields(body: str) -> dict[str, str]:
    out = {}
    for part in body.split("|"):
        part = part.strip()
        if "$" not in part:
            continue
        key, value = part.split("$", 1)
        out[key.strip()] = value.strip()
    return out


def parse_record(line: str):
    s = line.strip()
    m = re.match(r"^([ASTR]):(.*)$", s)
    if m:
        return {"kind": m.group(1), "fields": parse_fields(m.group(2)), "text": s}
    if s.startswith("K:"):
        return {"kind": "K", "fields": {}, "keyword_parts": s[2:].split(":"), "text": s}
    return None


def svar_decl(line: str):
    s = line.strip()
    if not s.startswith("SVar:"):
        return None
    rest = s[5:]
    if ":" not in rest:
        return None
    name, value = rest.split(":", 1)
    return name.strip(), value.strip()


def index_card(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    svars = {}
    records = []
    for line_no, line in enumerate(lines, 1):
        decl = svar_decl(line)
        if decl:
            name, value = decl
            svars[name] = {"line": line_no, "value": value, "fields": parse_fields(value), "text": line.strip()}
        rec = parse_record(line)
        if rec:
            rec["line"] = line_no
            records.append(rec)
    return {"lines": lines, "svars": svars, "records": records}


def static_modes(forge_root: Path) -> set[str]:
    p = forge_root / "forge-game/src/main/java/forge/game/staticability/StaticAbilityMode.java"
    text = p.read_text(encoding="utf-8", errors="replace")
    modes = set()
    for line in text.splitlines():
        m = re.match(r"\s*([A-Za-z][A-Za-z0-9_]*)\s*(?:\(|,|;)", line)
        if m:
            modes.add(m.group(1))
    return modes


def source_kind(value: str, statics: set[str]) -> str:
    fields = parse_fields(value)
    if value.startswith(("AB$", "SP$", "DB$")):
        return "ABILITY_DEFINITION"
    if value.startswith("ST$"):
        return "STATIC_DEFINITION"
    if value.startswith("Event$"):
        return "REPLACEMENT_DEFINITION"
    if value.startswith("Mode$"):
        mode = fields.get("Mode", "")
        return "STATIC_DEFINITION" if mode in statics else "TRIGGER_DEFINITION"
    if value.startswith("SVar:"):
        return "SVAR_ASSIGNMENT"
    if value in {"TRUE", "FALSE"}:
        return "BOOLEAN_VALUE"
    return "VALUE_EXPRESSION"


def consumer_for(field: str | None, value_kind: str, record_kind: str, statics: set[str], keyword: str | None = None):
    if field in TEXT_FIELDS:
        return None
    if field in REPLACEMENT_FIELDS:
        return ("REPLACEMENT_PARSER", "forge.game.replacement.ReplacementHandler#parseReplacement", OWNER_TRZ)
    if field in TRIGGER_FIELDS:
        return ("TRIGGER_PARSER", "forge.game.trigger.TriggerHandler#parseTrigger", OWNER_TRZ)
    if field in STATIC_FIELDS:
        return ("STATIC_ABILITY_PARSER", "forge.game.staticability.StaticAbility#create", OWNER_CONT)
    if field in STATIC_ASSIGN_FIELDS:
        return ("STATIC_SVAR_ASSIGNMENT", "forge.game.staticability.StaticAbilityContinuous#AddSVar", OWNER_CONT)
    if field in ABILITY_FIELDS:
        return ("ABILITY_FACTORY", "forge.game.ability.AbilityFactory#getAbility", OWNER_ACTION)
    if field in COST_FIELDS:
        return ("COST_PARSER", "forge.game.cost.Cost", OWNER_ACTION)
    if field in AMOUNT_FIELDS:
        return ("AMOUNT_EVALUATION", "forge.game.ability.AbilityUtils#calculateAmount", OWNER_ACTION)
    if field in SELECTOR_FIELDS:
        if value_kind in {"ABILITY_DEFINITION", "TRIGGER_DEFINITION", "REPLACEMENT_DEFINITION", "STATIC_DEFINITION"} and field == "Choices":
            return ("ABILITY_FACTORY", "forge.game.ability.AbilityFactory#getAbility", OWNER_ACTION)
        return ("DEFINED_SELECTOR", "forge.game.ability.AbilityUtils#getDefined", OWNER_ACTION)
    if field in DESTINATION_NAME_FIELDS:
        return None
    if record_kind == "K":
        if value_kind == "REPLACEMENT_DEFINITION":
            return ("KEYWORD_REPLACEMENT_PARSER", "forge.game.replacement.ReplacementHandler#parseReplacement", OWNER_TRZ)
        if value_kind == "TRIGGER_DEFINITION":
            return ("KEYWORD_TRIGGER_PARSER", "forge.game.trigger.TriggerHandler#parseTrigger", OWNER_TRZ)
        if value_kind == "STATIC_DEFINITION":
            return ("KEYWORD_STATIC_PARSER", "forge.game.staticability.StaticAbility#create", OWNER_CONT)
        if value_kind == "ABILITY_DEFINITION":
            return ("KEYWORD_ABILITY_FACTORY", "forge.game.ability.AbilityFactory#getAbility", OWNER_ACTION)
        if value_kind == "SVAR_ASSIGNMENT":
            return ("KEYWORD_SVAR_ASSIGNMENT", "forge.game.staticability.StaticAbilityContinuous#AddSVar", OWNER_CONT)
        return ("KEYWORD_AMOUNT_EVALUATION", "forge.game.ability.AbilityUtils#calculateAmount", OWNER_ACTION)
    return None


def direct_consumers(token: str, own_line: int, card: dict, value_kind: str, statics: set[str]):
    rows = []
    for parent, decl in card["svars"].items():
        if decl["line"] == own_line:
            continue
        for field, value in decl["fields"].items():
            if not token_match(value, token):
                continue
            consumer = consumer_for(field, value_kind, "SVAR", statics)
            if consumer:
                rows.append({
                    "consumer_kind": consumer[0], "implementation_target": consumer[1], "owner_family": consumer[2],
                    "consumer_field": field, "consumer_record_kind": "SVAR", "consumer_line": decl["line"],
                    "consumer_parent_svar": parent, "consumer_keyword": None, "consumer_text": decl["text"],
                })
        if not decl["fields"] and token_match(decl["value"], token):
            rows.append({
                "consumer_kind": "NESTED_VALUE_EXPRESSION", "implementation_target": "forge.game.ability.AbilityUtils#calculateAmount",
                "owner_family": OWNER_ACTION, "consumer_field": "<nested-expression>", "consumer_record_kind": "SVAR",
                "consumer_line": decl["line"], "consumer_parent_svar": parent, "consumer_keyword": None,
                "consumer_text": decl["text"],
            })
    for rec in card["records"]:
        if rec["kind"] == "K":
            if any(token_match(part, token) for part in rec.get("keyword_parts", [])):
                keyword = rec.get("keyword_parts", [None])[0]
                consumer = consumer_for(None, value_kind, "K", statics, keyword)
                if consumer:
                    rows.append({
                        "consumer_kind": consumer[0], "implementation_target": consumer[1], "owner_family": consumer[2],
                        "consumer_field": "<keyword-argument>", "consumer_record_kind": "K", "consumer_line": rec["line"],
                        "consumer_parent_svar": None, "consumer_keyword": keyword, "consumer_text": rec["text"],
                    })
            continue
        for field, value in rec["fields"].items():
            if not token_match(value, token):
                continue
            consumer = consumer_for(field, value_kind, rec["kind"], statics)
            if consumer:
                rows.append({
                    "consumer_kind": consumer[0], "implementation_target": consumer[1], "owner_family": consumer[2],
                    "consumer_field": field, "consumer_record_kind": rec["kind"], "consumer_line": rec["line"],
                    "consumer_parent_svar": None, "consumer_keyword": None, "consumer_text": rec["text"],
                })
    unique = {}
    for row in rows:
        key = (row["implementation_target"], row["owner_family"], row["consumer_kind"], row["consumer_field"],
               row["consumer_record_kind"], row["consumer_parent_svar"], row["consumer_keyword"], row["consumer_line"])
        unique[key] = row
    return [unique[k] for k in sorted(unique)]


def model_descriptor(old: dict, consumer: dict, token: str, value: str) -> dict:
    old_profile = old.get("semantic_selector_profile") or {}
    profile = {
        "consumer_model": "WS33_CONSUMER_AWARE_SVAR_V2",
        "svar_token": token,
        "svar_expression_shape": old_profile.get("svar_expression_shape", value[:180]),
        "first_consumer_kind": consumer["consumer_kind"],
        "first_consumer_field": consumer["consumer_field"],
        "first_consumer_record_kind": consumer["consumer_record_kind"],
        "first_consumer_parent_svar": consumer["consumer_parent_svar"],
        "first_consumer_keyword": consumer["consumer_keyword"],
    }
    return {
        "parent_ws14_primitive_id": old.get("parent_ws14_primitive_id"),
        "dispatch_domain": SVAR_DOMAIN,
        "dispatch_token": token,
        "implementation_target": consumer["implementation_target"],
        "semantic_selector_profile": profile,
        "owner_family": consumer["owner_family"],
        "model_origin": "WS33_SHARED_CONSUMER_REPAIR_V2",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    head = subprocess.check_output(["git", "-C", str(args.forge_root), "rev-parse", "HEAD"], text=True).strip()
    if head != PIN:
        raise SystemExit("Forge pin mismatch: " + head)
    statics = static_modes(args.forge_root)
    manifest = load(args.manifest)
    raw_paths = manifest["paths"]
    svar_paths = [p for p in raw_paths if p.get("dispatch_domain") == SVAR_DOMAIN]
    cache = {}
    new_paths = {}
    migrations = []
    unresolved = []
    old_to_new = collections.defaultdict(set)
    signature_counts = collections.Counter()

    for old in svar_paths:
        old_id = old["v2_path_id"]
        for prov in old.get("source_provenance", []):
            if prov.get("source_directive") != "SVAR":
                continue
            rel = prov["forge_source_path"]
            line_no = int(prov["source_line"])
            token = prov["source_token"]
            value = prov["source_value"]
            path = args.forge_root / rel
            if rel not in cache:
                if not path.is_file():
                    unresolved.append({"old_effective_v2_path_id": old_id, "reason": "CARD_SOURCE_MISSING", "forge_source_path": rel})
                    continue
                cache[rel] = index_card(path)
            card = cache[rel]
            decl = card["svars"].get(token)
            if not decl or decl["line"] != line_no or decl["value"] != value:
                unresolved.append({
                    "old_effective_v2_path_id": old_id, "reason": "SVAR_PROVENANCE_MISMATCH", "forge_source_path": rel,
                    "source_line": line_no, "source_token": token, "manifest_value": value, "actual": decl,
                })
                continue
            value_kind = source_kind(value, statics)
            consumers = direct_consumers(token, line_no, card, value_kind, statics)
            if not consumers:
                unresolved.append({
                    "old_effective_v2_path_id": old_id, "reason": "NO_ACTUAL_FIRST_CONSUMER", "forge_source_path": rel,
                    "source_line": line_no, "source_token": token, "source_value": value, "value_kind": value_kind,
                })
                continue
            for consumer in consumers:
                desc = model_descriptor(old, consumer, token, value)
                new_id = path_id(desc)
                signature_counts[(consumer["consumer_kind"], consumer["implementation_target"], consumer["owner_family"], consumer["consumer_field"])] += 1
                target = new_paths.setdefault(new_id, {
                    "v2_path_id": new_id, **desc,
                    "cross_family_dependencies": list(old.get("cross_family_dependencies", [])),
                    "source_provenance": [], "representative_actual_oracle_identities": [], "source_occurrence_count": 0,
                    "required_decision_evidence": bool(old.get("required_decision_evidence")),
                    "required_rng_evidence": bool(old.get("required_rng_evidence")),
                    "required_hidden_info_evidence": bool(old.get("required_hidden_info_evidence")),
                    "required_replay_evidence": bool(old.get("required_replay_evidence")),
                    "evidence_class": "CODE_DERIVED", "current_witness_status": "UNPROVED",
                    "consumer_evidence": [], "historical_ws26_v2_path_ids": [],
                })
                if prov not in target["source_provenance"]:
                    target["source_provenance"].append(prov)
                target["representative_actual_oracle_identities"] = sorted(set(target["representative_actual_oracle_identities"] + [prov["oracle_identity"]]))[:12]
                target["historical_ws26_v2_path_ids"] = sorted(set(target["historical_ws26_v2_path_ids"] + [old_id]))
                ev = {k: consumer[k] for k in consumer if k != "consumer_text"}
                ev.update({"forge_source_path": rel, "source_line": line_no, "source_token": token, "source_value": value,
                           "consumer_text": consumer["consumer_text"][:500]})
                if ev not in target["consumer_evidence"]:
                    target["consumer_evidence"].append(ev)
                old_to_new[old_id].add(new_id)

    for row in new_paths.values():
        row["source_provenance"].sort(key=lambda p: (p["forge_source_path"], int(p["source_line"]), p["oracle_identity"]))
        row["consumer_evidence"].sort(key=lambda e: (e["forge_source_path"], e["source_line"], e["consumer_line"], e["consumer_field"]))
        row["source_occurrence_count"] = len(row["source_provenance"])

    by_old = {p["v2_path_id"]: p for p in svar_paths}
    for old_id in sorted(by_old):
        old = by_old[old_id]
        ids = sorted(old_to_new.get(old_id, []))
        if not ids:
            continue
        for new_id in ids:
            new = new_paths[new_id]
            migrations.append({
                "old_effective_v2_path_id": old_id,
                "new_effective_v2_path_id": new_id,
                "old_implementation_target": old.get("implementation_target"),
                "new_implementation_target": new["implementation_target"],
                "old_owner_family": old.get("owner_family"),
                "new_owner_family": new["owner_family"],
                "old_scenario_group": None,
                "new_scenario_group": None,
                "migration_reason": "CONSUMER_AWARE_FIRST_RUNTIME_USE",
                "status_before": None,
                "status_after": "UNKNOWN",
            })

    result = {
        "schema": "commander-simulator-next.ws33-consumer-aware-svar-model.v2",
        "forge_pin": PIN,
        "raw_svar_path_count": len(svar_paths),
        "resolved_old_path_count": len(old_to_new),
        "unresolved_old_path_count": len(set(r["old_effective_v2_path_id"] for r in unresolved)),
        "unresolved_occurrence_count": len(unresolved),
        "new_consumer_path_count": len(new_paths),
        "old_to_new": {k: sorted(v) for k, v in sorted(old_to_new.items())},
        "new_paths": [new_paths[k] for k in sorted(new_paths)],
        "migrations": migrations,
        "unresolved": unresolved,
        "consumer_signature_counts": [
            {"consumer_kind": k[0], "implementation_target": k[1], "owner_family": k[2], "consumer_field": k[3], "count": n}
            for k, n in sorted(signature_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
    }
    write_json(args.out, result)
    print(json.dumps({
        "RAW_SVAR_PATHS": len(svar_paths), "RESOLVED_OLD_PATHS": len(old_to_new),
        "UNRESOLVED_OLD_PATHS": result["unresolved_old_path_count"], "UNRESOLVED_OCCURRENCES": len(unresolved),
        "NEW_CONSUMER_PATHS": len(new_paths),
    }, sort_keys=True))
    if unresolved:
        for row in unresolved[:100]:
            print("UNRESOLVED " + json.dumps(row, sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
