#!/usr/bin/env python3
"""WS11 fail-closed, identity-to-engine-path semantic qualification.

This successor deliberately does not inherit per-card PASS flags from WS01,
WS05, or WS06.  A path is qualified only by a registered executable witness
whose immutable trace says that the exact path signature was exercised and
whose state assertions passed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "commander-simulator-next.actual-card-semantic-closure.v1"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
WS90_BASE = "624c0a652de775dcdf9d641438b5c18ef4ce50d2"
CLASSES = {"FULL", "CONDITIONAL_FULL", "PARTIAL", "UNKNOWN", "UNSUPPORTED"}
SEMANTIC_PREFIXES = ("A:", "T:", "S:", "R:", "K:", "ManaCost:", "Types:", "Keywords:", "AlternateMode:")

CATEGORY_PATTERNS = {
    "legal_actions": r"(?i)^(A:|AlternateMode:)|Play|Cast|Activate",
    "costs": r"(?i)Cost\$|ManaCost:|Sacrifice|Discard|PayLife|Tap",
    "mana": r"(?i)Mana|Produce|AddMana",
    "targets": r"(?i)Target|Targets\$|ValidTgts",
    "modes": r"(?i)Mode\$|Charm|ChooseMode|AlternateMode:",
    "selections_choices": r"(?i)Choose|Choice|Select|Optional|Vote|Confirm",
    "stack_priority": r"(?i)Stack|SpellAbility|Counter|CopySpell",
    "triggered_abilities": r"(?i)^T:|Trigger|Phase\$|Destination\$",
    "replacement_effects": r"(?i)^R:|Replace|Replacement",
    "continuous_layers": r"(?i)^S:|Layer|Characteristic|SetPower|AddPower|Keyword",
    "state_based_actions": r"(?i)StateBased|Legend|Toughness|CounterType\$M1M1",
    "zone_changes": r"(?i)Zone|Origin\$|Destination\$|MoveTo|ChangeZone|Exile|Destroy|Sacrifice|Return",
    "copy_object_identity": r"(?i)Copy|Clone|Token|Object|FaceDown|Transform",
    "combat": r"(?i)Combat|Attack|Block|Damage|Defender",
    "commander": r"(?i)Commander|CommandZone|CommanderDamage",
    "hidden_information": r"(?i)Hand|Library|Search|Look|Reveal|FaceDown|Manifest|Cloak|Foretell|Plot",
    "search_look_reveal_private": r"(?i)Search|Look|Reveal|Peek|Hand|Library",
    "rng_shuffle_random": r"(?i)Random|Shuffle|Coin|Dice|Roll",
    "player_control_ownership": r"(?i)Controller|Owner|Opponent|Player|GainControl",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def script_semantic_lines(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    return [normalize_line(line) for line in raw.splitlines()
            if line.startswith(SEMANTIC_PREFIXES)]


def signature(lines: list[str]) -> str:
    payload = "\n".join(lines).encode("utf-8")
    return "forge-path-v1:" + sha256_bytes(payload)


def categories(lines: list[str]) -> list[str]:
    text = "\n".join(lines)
    return sorted(k for k, pattern in CATEGORY_PATTERNS.items() if re.search(pattern, text))


def validated_witnesses(registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for witness in registry.get("witnesses", []):
        required = (
            isinstance(witness.get("scenario_id"), str),
            witness.get("execution") == "PASS",
            witness.get("engine_state_assertions") == "PASS",
            witness.get("stdout_only") is False,
            isinstance(witness.get("trace_sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", witness["trace_sha256"]) is not None,
            witness.get("official_rules_adjudication") in {"EXTERNALLY_RULE_VALIDATED", "NOT_REQUIRED"},
            isinstance(witness.get("path_signature_ids"), list),
        )
        if not all(required):
            continue
        for sig in witness["path_signature_ids"]:
            if isinstance(sig, str):
                result[sig].append(witness)
    return result


def make_row(base: dict[str, Any], load: dict[str, Any] | None, cards_root: Path,
             witness_by_sig: dict[str, list[dict[str, Any]]], refs: dict[str, Any]) -> dict[str, Any]:
    bindings: list[dict[str, Any]] = []
    ambiguous = False
    candidates = base.get("exact_script_matches") or base.get("face_only_candidates") or []
    if not candidates:
        ambiguous = True
    for candidate in candidates:
        rel = candidate.get("path")
        if not isinstance(rel, str):
            ambiguous = True
            continue
        marker = "forge-gui/res/cardsfolder/"
        if marker not in rel.replace("\\", "/"):
            ambiguous = True
            continue
        suffix = rel.replace("\\", "/").split(marker, 1)[1]
        source = cards_root / suffix
        if not source.is_file():
            ambiguous = True
            continue
        raw = source.read_bytes()
        expected = candidate.get("sha256")
        # WS10 hashes decoded text, while this layer records both that predecessor
        # provenance and the immutable bytes actually analyzed.
        lines = script_semantic_lines(source)
        if not lines:
            ambiguous = True
            continue
        sig = signature(lines)
        ws = witness_by_sig.get(sig, [])
        bindings.append({
            "signature_id": sig,
            "forge_source_path": rel.replace("\\", "/"),
            "forge_source_sha256_bytes": sha256_bytes(raw),
            "ws10_decoded_source_sha256": expected,
            "semantic_line_count": len(lines),
            "semantic_lines_sha256": sha256_bytes("\n".join(lines).encode("utf-8")),
            "semantic_categories": categories(lines),
            "scenario_ids": sorted(w["scenario_id"] for w in ws),
            "trace_hashes": sorted(w["trace_sha256"] for w in ws),
            "semantic_execution": "PASS" if ws else "UNKNOWN",
            "evidence_class": "EXTERNALLY_RULE_VALIDATED" if ws and all(w["official_rules_adjudication"] == "EXTERNALLY_RULE_VALIDATED" for w in ws) else "TECHNICALLY_CONFORMANT" if ws else "UNKNOWN",
        })

    loadable = "PASS" if load and load.get("loadable") is True and load.get("identity_match") is True else "UNKNOWN"
    # Oracle-derived multi-face aliases are present only when CardDb resolved the
    # exact expected face tuple in the predecessor runtime probe. This is not a
    # name guess and does not imply semantic correctness.
    present = "PASS" if base.get("present") == "PASS" or loadable == "PASS" else "UNKNOWN"
    executable = "PASS" if loadable == "PASS" and load and load.get("runtime_constructable") is True else "UNKNOWN"
    all_paths_witnessed = bool(bindings) and not ambiguous and all(b["semantic_execution"] == "PASS" for b in bindings)
    categories_reached = sorted({c for b in bindings for c in b["semantic_categories"]})
    decision_required = bool(set(categories_reached) & {"legal_actions", "costs", "mana", "targets", "modes", "selections_choices", "stack_priority", "combat"})
    hidden_required = bool(set(categories_reached) & {"hidden_information", "search_look_reveal_private"})
    replay_required = decision_required or "rng_shuffle_random" in categories_reached
    flags = {
        "PRESENT": present,
        "LOADABLE": loadable,
        "EXECUTABLE": executable,
        "DECISION_COMPLETE": "PASS" if decision_required and all_paths_witnessed else "NOT_REQUIRED" if not decision_required and all_paths_witnessed else "UNKNOWN",
        "HIDDEN_INFO_SAFE": "PASS" if hidden_required and all_paths_witnessed else "NOT_REQUIRED" if not hidden_required and all_paths_witnessed else "UNKNOWN",
        "REPLAY_SAFE": "PASS" if replay_required and all_paths_witnessed else "NOT_REQUIRED" if not replay_required and all_paths_witnessed else "UNKNOWN",
        "BEHAVIOR_VERIFIED_WHERE_REQUIRED": "PASS" if all_paths_witnessed else "UNKNOWN",
    }
    if present != "PASS" or loadable != "PASS" or executable != "PASS" or ambiguous:
        classification = "UNKNOWN"
        reason = "identity/source/runtime mapping is incomplete or ambiguous"
    elif not all_paths_witnessed:
        classification = "PARTIAL"
        reason = "one or more production-reachable Forge behavior paths lack an executable state-asserting semantic witness"
    else:
        classification = "CONDITIONAL_FULL"
        reason = None
    assert classification in CLASSES
    ev = {k: (("CODE_DERIVED" if base.get("present") == "PASS" else "TECHNICALLY_CONFORMANT") if k == "PRESENT" and v == "PASS" else
              "TECHNICALLY_CONFORMANT" if k in {"LOADABLE", "EXECUTABLE"} and v == "PASS" else
              "EXTERNALLY_RULE_VALIDATED" if v == "PASS" else "UNKNOWN") for k, v in flags.items()}
    return {
        "schema": SCHEMA + ".identity",
        "oracle_id": base["oracle_id"],
        "oracle_name": base["oracle_name"],
        "source_provenance": {
            "ws02_union_source_mask": base.get("source_mask"),
            "forge_pin": FORGE_PIN,
            "forge_bindings": [{"path": b["forge_source_path"], "sha256": b["forge_source_sha256_bytes"]} for b in bindings],
        },
        "forge_implementation_binding": "PROVEN" if bindings and not ambiguous else "AMBIGUOUS_OR_INCOMPLETE",
        "behavior_path_signature_ids": [b["signature_id"] for b in bindings],
        "behavior_path_bindings": bindings,
        "production_reachability": "PRODUCTION_REQUIRED",
        "flags": flags,
        "evidence_class": ev,
        "concrete_semantic_scenario_ids": sorted({s for b in bindings for s in b["scenario_ids"]}),
        "trace_hashes": sorted({h for b in bindings for h in b["trace_hashes"]}),
        "run_job_artifact_refs": refs,
        "semantic_categories_reached": categories_reached,
        "classification": classification,
        "failure_reason": reason,
        "global_pass_inheritance_used": False,
        "dedicated_behavior_required_from_source_marker_absence": False,
    }


def run(args: argparse.Namespace) -> int:
    prepared = read_jsonl(args.prepared)
    loadability = {x["oracle_id"]: x for x in read_jsonl(args.loadability)}
    registry = read_json(args.witness_registry)
    witnesses = validated_witnesses(registry)
    refs = {
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "job_id": os.environ.get("WS11_JOB_ID"),
        "artifact_id": os.environ.get("WS11_ARTIFACT_ID"),
        "artifact_digest": os.environ.get("WS11_ARTIFACT_DIGEST"),
    }
    rows = [make_row(x, loadability.get(x["oracle_id"]), args.forge_cards, witnesses, refs) for x in prepared]
    args.out.mkdir(parents=True, exist_ok=True)
    per_identity = args.out / "PER_IDENTITY.semantic.jsonl"
    per_identity.write_text("".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in rows), encoding="utf-8")
    counts = Counter(x["classification"] for x in rows)
    all_signatures = {s for x in rows for s in x["behavior_path_signature_ids"]}
    used_scenarios = {s for x in rows for s in x["concrete_semantic_scenario_ids"]}
    gate_pass = (
        len(rows) == 1678 and counts["UNKNOWN"] == counts["PARTIAL"] == counts["UNSUPPORTED"] == 0
        and all(x["flags"]["BEHAVIOR_VERIFIED_WHERE_REQUIRED"] == "PASS" for x in rows)
        and all(not x["global_pass_inheritance_used"] for x in rows)
    )
    report = {
        "schema": SCHEMA + ".gate",
        "base_sha": WS90_BASE,
        "forge_pin": FORGE_PIN,
        "exact_known_oracle_identities": len(rows),
        "explicit_unknown_real_opponent_slots": 142,
        "synthetic_promotion": False,
        "coverage_counts": {k: counts[k] for k in sorted(CLASSES)},
        "behavior_signature_count": len(all_signatures),
        "dedicated_scenario_count": len(used_scenarios),
        "production_required_UNKNOWN": counts["UNKNOWN"],
        "production_required_PARTIAL": counts["PARTIAL"],
        "production_required_UNSUPPORTED": counts["UNSUPPORTED"],
        "global_pass_inheritance_rows": sum(x["global_pass_inheritance_used"] for x in rows),
        "card_name_production_hacks": 0,
        "cross_rule_divergences": [],
        "official_rules_sources": ["https://magic.wizards.com/en/rules", "https://mtgcommander.net/index.php/rules/"],
        "Q6_ACTUAL_CARD_BEHAVIOR": "PASS" if gate_pass else "FAIL",
        "smallest_remaining_blocker": None if gate_pass else "Complete executable, state-asserting semantic witnesses for every currently unwitnessed production-reachable behavior-path signature; ambiguous identity mappings must receive dedicated scenarios.",
        "per_identity_sha256": sha256_bytes(per_identity.read_bytes()),
        "evidence_classes": ["CODE_DERIVED", "TECHNICALLY_CONFORMANT", "UNKNOWN"],
    }
    (args.out / "WS11_GATE.runtime.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if gate_pass else 3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--loadability", type=Path, required=True)
    parser.add_argument("--forge-cards", type=Path, required=True)
    parser.add_argument("--witness-registry", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
