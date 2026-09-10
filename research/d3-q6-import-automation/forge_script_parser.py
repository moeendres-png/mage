#!/usr/bin/env python3
"""D3 Q6 clean-room Forge card-script parser prototype.

Clean-room provenance:
- Implemented from the public Forge wiki format description
  (line-oriented `Key:Value`, A:/T:/S:/R:/SVar:/K: lines, `$`-delimited
  param records) plus direct observation of pinned corpus files.
- No Manabrew/Forge implementation code was copied or embedded.
- The MIT-licensed tree-sitter grammar was used as REFERENCE_ONLY for the
  *pattern* (line classification + byte spans + never-fail diagnostics).
  No grammar source was vendored.
- GPL-3.0-or-later (Forge, forge-card-script) and AGPL-3.0-or-later
  (Manabrew workspace incl. forge-carddb/parity) artifacts were NOT linked,
  vendored, or reimplemented from source. Parity concepts are
  SEPARATE_TOOL_PROCESS only (see report).

PARSE/IMPORT != BEHAVIOR PASS: parser success never promotes a behavior row.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field


PARSER_VERSION = "d3q6-cleanroom-0.1.0"

# Top-level keys observed in Forge wiki + corpus. Anything else -> unsupported.
KNOWN_TOP_KEYS = {
    "Name", "ManaCost", "Colors", "Types", "PT", "Loyalty", "Defense",
    "K", "A", "T", "S", "R", "SVar", "Oracle", "Text",
    "AlternateMode", "ALTERNATE", "SPECIALIZE", "Variant",
    "DeckHints", "DeckHas", "DeckNeeds", "DeckShuffles", "RemAIDeck",
    "RemRandomDeck", "Commander", "MustBlock", "MustAttack",
    "ETB", "Flashback", "Madness", "Bestow", "Cipher",
    "SoundEffect",
}

ABILITY_VERBS = {
    "SP", "AB", "DB",  # spell / activated / delayed-trigger-sub-ability containers
}

# Non-exhaustive verb vocabulary seen in Forge wiki examples (public knowledge).
# Unknown verbs are kept as Raw/unsupported, never guessed.
KNOWN_ABILITY_KINDS = {
    "DealDamage", "Draw", "Destroy", "Exile", "Pump", "Token", "Sacrifice",
    "GainLife", "LoseLife", "Counters", "PutCounter", "RemoveCounter",
    "Discard", "Mulligan", "SearchLibrary", "ChangeZone", "Branch",
    "ChooseCard", "ChoosePlayer", "ChooseType", "ChooseNumber", "ChooseSource",
    "FlipACoin", "RollDice", "Shuffle", "Scry", "Surveil", "Investigate",
    "Airbend", "Play", "Copy", "GainControl", "Attach", "Untap", "Tap",
    "Regenerate", "PreventDamage", "Protection", "Effect", "Animate",
    "Repeat", "RepeatEach", "DelayedTrigger", "TwoPiles", "Clash",
}

KNOWN_TRIGGER_MODES = {
    "ChangesZone", "DamageDone", "DamageDealt", "SpellCast", "AbilityCast",
    "Phase", "Drawn", "Discarded", "Sacrificed", "LifeGained", "LifeLost",
    "CounterAdded", "CounterRemoved", "AttackersDeclared", "BlockersDeclared",
    "TurnFaceUp", "TurnFaceDown", "Taps", "Untaps", "ChangesController",
    "LandPlayed", "Cycled", "Storm", "ETBReplacement",
}

WS33_FAMILIES = (
    "ACTION_COST_DECISION",
    "TRIGGER_REPLACEMENT_ZONE_SBA",
    "CONTINUOUS_COPY_CONTROL",
    "COMBAT_COMMANDER",
    "HIDDEN_RNG_REPLAY",
)

ADVERSARIAL_TAGS = (
    "nested_svar", "targets", "choices_modes", "mana_cost",
    "triggers", "replacements", "hidden_info", "randomness",
    "copy_control", "multiplayer",
)


@dataclass
class Diagnostic:
    code: str
    message: str
    line_no: int
    span: list


@dataclass
class ParamEntry:
    key: str
    raw: str
    semantic: str
    span: list = field(default_factory=list)


@dataclass
class AbilityRecord:
    kind: str  # A/T/S/R/SVar/K/Field/Face
    header: str
    params: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    line_no: int = 0


@dataclass
class ParsedScript:
    path: str
    lines: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)
    ambiguous: bool = False


_PARAM_RE = re.compile(r"\s*\|\s*")
_KEYVAL_RE = re.compile(r"^([^:]*):(.*)$", re.DOTALL)


def _classify_semantic(key: str, value: str) -> str:
    """Heuristic semantic typing by key-name pattern. Raw is always fallback."""
    k = key.lower()
    v = value.strip()
    if not v:
        return "empty"
    if k in ("defined", "defined$") or k.startswith("defined"):
        return "defined_ref"
    if "valid" in k and ("tgt" in k or "card" in k or "player" in k or "target" in k):
        return "selector"
    if k.startswith("num") or k in ("amount", "counternum", "lifegain", "lifeloss"):
        return "amount"
    if k in ("cost", "manacost", "playcost"):
        return "cost"
    if "produced" in k or "combo" in k:
        return "produced_mana"
    if "svarcompare" in k or "checksvar" in k or k.startswith("branchcondition"):
        return "comparison"
    if "zone" in k or k in ("origin", "destination"):
        return "zone_list"
    if k in ("execute", "truesubability", "falsesubability", "subability",
             "remembered", "imprinted"):
        return "svar_ref"
    if k in ("mode", "triggermode"):
        return "trigger_mode"
    if k in ("oracle", "triggerdescription", "spelldescription", "stackdescription"):
        return "rules_text"
    if re.fullmatch(r"[0-9Xx*/+\-. ]+", v):
        return "numeric_expr"
    if v.startswith("Count$") or v.startswith("SVar$") or "Triggered" in v:
        return "computed_expr"
    return "raw"


def parse_script(text: str, path: str = "<memory>") -> ParsedScript:
    ps = ParsedScript(path=path)
    raw_lines = text.splitlines()
    for idx, raw in enumerate(raw_lines, start=1):
        line_start = sum(len(l) + 1 for l in raw_lines[: idx - 1])
        span = [line_start, line_start + len(raw)]
        if raw.strip() == "":
            ps.lines.append({"kind": "Blank", "line_no": idx, "span": span})
            continue
        if raw.lstrip().startswith("#"):
            ps.lines.append({"kind": "Comment", "line_no": idx, "span": span})
            continue
        m = _KEYVAL_RE.match(raw)
        if not m:
            ps.diagnostics.append(Diagnostic("missing_colon",
                                             "line has no ':' separator",
                                             idx, span))
            ps.ambiguous = True
            ps.lines.append({"kind": "Unknown", "line_no": idx, "span": span,
                             "raw": raw})
            continue
        key, value = m.group(1).strip(), m.group(2)
        if key == "":
            ps.diagnostics.append(Diagnostic("empty_key", "empty key before ':'",
                                             idx, span))
            ps.ambiguous = True
        # Face separators
        if key in ("ALTERNATE", "AlternateMode", "SPECIALIZE"):
            ps.lines.append({"kind": "Face", "key": key, "value": value.strip(),
                             "line_no": idx, "span": span})
            continue
        if key not in KNOWN_TOP_KEYS and not key.startswith("Variant"):
            ps.unsupported.append(f"topkey:{key}")
            ps.diagnostics.append(Diagnostic("unknown_topkey",
                                             f"unrecognized top-level key '{key}'",
                                             idx, span))
        if key in ("A", "T", "S", "R"):
            rec = AbilityRecord(kind={"A": "Ability", "T": "Trigger",
                                      "S": "Static", "R": "Replacement"}[key],
                                header=value.strip(), line_no=idx)
            if "$" not in value:
                rec.diagnostics.append(Diagnostic("missing_ability_record",
                                                  f"{key}: line has no '$' record",
                                                  idx, span))
                ps.ambiguous = True
            else:
                for part in _PARAM_RE.split(value.strip()):
                    if "$" not in part:
                        rec.diagnostics.append(
                            Diagnostic("missing_dollar",
                                       f"param segment without '$': {part!r}",
                                       idx, span))
                        ps.ambiguous = True
                        continue
                    pk, pv = part.split("$", 1)
                    pk, pv = pk.strip(), pv.strip()
                    if pk == "":
                        rec.diagnostics.append(Diagnostic("empty_param_key",
                                                          "empty param key", idx, span))
                        ps.ambiguous = True
                    rec.params.append(ParamEntry(pk, pv,
                                                _classify_semantic(pk, pv),
                                                list(span)))
                keys = [p.key for p in rec.params]
                if len(keys) != len(set(keys)):
                    rec.diagnostics.append(Diagnostic("duplicate_param",
                                                      "duplicate param keys", idx, span))
                    ps.ambiguous = True
            ps.lines.append(rec)
        elif key == "SVar":
            # SVar:<Name>:<Value>
            rest = value
            if ":" not in rest:
                ps.diagnostics.append(Diagnostic("svar_missing_name_sep",
                                                 "SVar without name ':' separator",
                                                 idx, span))
                ps.ambiguous = True
                ps.lines.append({"kind": "SVar", "name": rest.strip(),
                                 "value": "", "line_no": idx, "span": span,
                                 "params": []})
                continue
            name, sval = rest.split(":", 1)
            name, sval = name.strip(), sval.strip()
            params: list = []
            if "$" in sval:
                for part in _PARAM_RE.split(sval):
                    if "$" not in part:
                        # bare expression e.g. Count$xPaid fragments
                        params.append(ParamEntry("", part.strip(),
                                                _classify_semantic("", part),
                                                list(span)))
                        continue
                    pk, pv = part.split("$", 1)
                    params.append(ParamEntry(pk.strip(), pv.strip(),
                                            _classify_semantic(pk.strip(), pv.strip()),
                                            list(span)))
            ps.lines.append({"kind": "SVar", "name": name, "value": sval,
                             "line_no": idx, "span": span, "params": params})
        elif key == "K":
            ps.lines.append({"kind": "Keyword", "value": value.strip(),
                             "line_no": idx, "span": span})
        else:
            ps.lines.append({"kind": "Field", "key": key, "value": value.strip(),
                             "line_no": idx, "span": span})
    return ps


def extract_features(ps: ParsedScript, text: str) -> dict:
    feats = {
        "has_trigger": False, "has_replacement": False, "has_static": False,
        "has_ability": False, "has_svar": False, "has_keyword": False,
        "svar_names": [], "svar_edge_count": 0, "max_svar_depth": 0,
        "has_targets": False, "has_choices": False, "has_mana_cost": False,
        "has_hidden": False, "has_random": False, "has_copy_control": False,
        "has_multiplayer": False, "has_modes": False,
        "ability_kinds": [], "trigger_modes": [],
        "unsupported_count": len(ps.unsupported),
        "diagnostic_count": len(ps.diagnostics) + sum(
            len(getattr(l, "diagnostics", [])) if isinstance(l, AbilityRecord) else 0
            for l in ps.lines),
    }
    svar_map: dict = {}
    for l in ps.lines:
        if isinstance(l, AbilityRecord):
            if l.kind == "Ability":
                feats["has_ability"] = True
            elif l.kind == "Trigger":
                feats["has_trigger"] = True
            elif l.kind == "Static":
                feats["has_static"] = True
            elif l.kind == "Replacement":
                feats["has_replacement"] = True
            for p in l.params:
                kl = p.key.lower()
                if "tgt" in kl or "validtgts" in kl or "targetmin" in kl:
                    feats["has_targets"] = True
                if "mode" in kl or "choice" in kl or "choose" in kl or "optional" in kl:
                    feats["has_choices"] = True
                    if "mode" in kl:
                        feats["has_modes"] = True
                if p.key in ("Mode", "Mode$"):
                    feats["trigger_modes"].append(p.raw)
                if kl in ("sp", "ab", "db") or p.key in ("SP", "AB", "DB"):
                    feats["ability_kinds"].append(p.raw)
        elif isinstance(l, dict) and l.get("kind") == "SVar":
            feats["has_svar"] = True
            feats["svar_names"].append(l["name"])
            svar_map[l["name"]] = l["value"]
        elif isinstance(l, dict) and l.get("kind") == "Keyword":
            feats["has_keyword"] = True
        elif isinstance(l, dict) and l.get("kind") == "Field":
            if l.get("key") == "ManaCost" and l.get("value", "").strip() not in ("", "no cost"):
                feats["has_mana_cost"] = True
    t = text
    tl = t.lower()
    if any(s in t for s in ("Hidden", "FaceDown", "Face Down", "Look at", "Reveal")):
        feats["has_hidden"] = True
    if any(s in tl for s in ("flip a coin", "roll", "dice", "random", "shuffle")):
        feats["has_random"] = True
    if any(s in t for s in ("Copy", "GainControl", "Control", "Attach", "Exchange")):
        feats["has_copy_control"] = True
    if any(s in t for s in ("Each player", "Each opponent", "Each other", "multiplayer",
                            "Vote", "Council", "Will of the council", "Monarch")):
        feats["has_multiplayer"] = True
    # SVar chain depth via Execute$/SubAbility refs (bounded, cycle-safe)
    ref_re = re.compile(r"(Execute|TrueSubAbility|FalseSubAbility|SubAbility|Remembered|Imprinted)\$\s*([A-Za-z0-9_]+)")
    edges: dict = {n: ref_re.findall(v) for n, v in svar_map.items()}
    feats["svar_edge_count"] = sum(len(v) for v in edges.values())

    def depth(name: str, seen: set) -> int:
        if name in seen or name not in edges:
            return 0
        seen = seen | {name}
        kids = [k for _, k in edges[name] if k in svar_map]
        if not kids:
            return 1 if edges[name] else 0
        return 1 + max((depth(k, seen) for k in kids), default=0)

    feats["max_svar_depth"] = max((depth(n, set()) for n in svar_map), default=0)
    feats["nested_svar"] = feats["max_svar_depth"] >= 2 or feats["svar_edge_count"] >= 2
    return feats


def map_taxonomy(feats: dict) -> dict:
    fams = set()
    if feats["has_ability"] or feats["has_targets"] or feats["has_choices"] or feats["has_mana_cost"]:
        fams.add("ACTION_COST_DECISION")
    if feats["has_trigger"] or feats["has_replacement"] or feats["has_static"]:
        fams.add("TRIGGER_REPLACEMENT_ZONE_SBA")
    if feats["has_copy_control"]:
        fams.add("CONTINUOUS_COPY_CONTROL")
    if feats["has_hidden"] or feats["has_random"]:
        fams.add("HIDDEN_RNG_REPLAY")
    tags = set()
    if feats.get("nested_svar"):
        tags.add("nested_svar")
    if feats["has_targets"]:
        tags.add("targets")
    if feats["has_choices"] or feats["has_modes"]:
        tags.add("choices_modes")
    if feats["has_mana_cost"]:
        tags.add("mana_cost")
    if feats["has_trigger"]:
        tags.add("triggers")
    if feats["has_replacement"]:
        tags.add("replacements")
    if feats["has_hidden"]:
        tags.add("hidden_info")
    if feats["has_random"]:
        tags.add("randomness")
    if feats["has_copy_control"]:
        tags.add("copy_control")
    if feats["has_multiplayer"]:
        tags.add("multiplayer")
    return {"families": sorted(fams), "adversarial_tags": sorted(tags)}


def scenario_skeleton(path: str, text: str, ps: ParsedScript, feats: dict,
                       provenance: dict) -> dict:
    tax = map_taxonomy(feats)
    diags = [{"code": d.code, "line": d.line_no, "msg": d.message}
             for d in ps.diagnostics]
    for l in ps.lines:
        if isinstance(l, AbilityRecord):
            for d in l.diagnostics:
                diags.append({"code": d.code, "line": d.line_no, "msg": d.message})
    manual_review = bool(diags or ps.unsupported or feats.get("nested_svar")
                         or feats["has_hidden"] or feats["has_random"]
                         or feats["has_copy_control"] or feats["has_multiplayer"])
    generatable = not bool([d for d in diags if d["code"] in (
        "missing_colon", "svar_missing_name_sep")]) and path.endswith(".txt")
    name = ""
    for l in ps.lines:
        if isinstance(l, dict) and l.get("kind") == "Field" and l.get("key") == "Name":
            name = l["value"]
    return {
        "schema": "d3-q6.scenario-skeleton.v1",
        "parser_version": PARSER_VERSION,
        "card_path": path,
        "card_name": name,
        "provenance": provenance,
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "features": feats,
        "taxonomy": tax,
        "diagnostics": diags,
        "unsupported": sorted(set(ps.unsupported)),
        "skeleton_generatable": generatable,
        "manual_review_required": manual_review,
        # Behavior is NEVER passed by the parser:
        "behavior_pass": False,
        "evidence_class": "SYNTHETIC",
        "suggested_setup": {
            "zones": ["Battlefield"] if (feats["has_trigger"] or feats["has_static"]) else ["Hand"],
            "needs_targets": feats["has_targets"],
            "needs_choices": feats["has_choices"],
            "needs_mana": feats["has_mana_cost"],
        },
    }


def analyze_one(path: str, text: str, provenance: dict) -> dict:
    ps = parse_script(text, path)
    feats = extract_features(ps, text)
    skel = scenario_skeleton(path, text, ps, feats, provenance)
    # semantic-field extraction rate per param
    total_params, typed_params = 0, 0
    for l in ps.lines:
        params = []
        if isinstance(l, AbilityRecord):
            params = l.params
        elif isinstance(l, dict) and l.get("kind") == "SVar":
            params = l.get("params", [])
        for p in params:
            if isinstance(p, ParamEntry):
                total_params += 1
                if p.semantic not in ("raw", "empty"):
                    typed_params += 1
    false_positive_probe = bool(feats["has_ability"] and not feats["has_mana_cost"]
                                and not feats["has_targets"] and not feats["has_choices"])
    return {
        "path": path,
        "parsed": True,  # parser never throws; diagnostics carry failure info
        "diagnostics": len(skel["diagnostics"]),
        "unsupported": skel["unsupported"],
        "total_params": total_params,
        "typed_params": typed_params,
        "features": feats,
        "taxonomy": skel["taxonomy"],
        "skeleton_generatable": skel["skeleton_generatable"],
        "manual_review_required": skel["manual_review_required"],
        "ambiguous": ps.ambiguous,
        "false_positive_probe": false_positive_probe,
        "skeleton": skel,
    }
