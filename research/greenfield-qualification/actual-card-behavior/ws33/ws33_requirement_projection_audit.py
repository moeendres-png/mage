#!/usr/bin/env python3
"""Audit path-local WS33 evidence requirements against the actual pinned Forge consumer.

This tool is intentionally non-mutating: it never rewrites the frozen Generation-2
manifest or coverage. It identifies evidence requirements that were inherited from
WS26's whole-implementation scan but are not justified by the atomic path's actual
consumer/active parameters.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
REQS = (
    ("decision", "required_decision_evidence"),
    ("rng", "required_rng_evidence"),
    ("hidden", "required_hidden_info_evidence"),
    ("replay", "required_replay_evidence"),
)

DECISION_INTRINSIC = (
    "TargetRestrictions", "CharmEffect", "TwoPilesEffect", "Choose",
)
RNG_INTRINSIC = (
    "ShuffleEffect", "FlipCoinEffect", "RollDiceEffect", "ClashEffect",
)
HIDDEN_INTRINSIC = (
    "DrawEffect", "DiscardEffect", "DigEffect", "DigUntilEffect", "ScryEffect",
    "SurveilEffect", "PeekAndRevealEffect", "RevealEffect", "RevealHandEffect",
    "Search", "ManifestEffect", "RearrangeTopOfLibraryEffect", "TwoPilesEffect",
)

# Parser/classification parameters are not themselves pilot decisions. Random target
# selection is RNG, not discretion. Hidden information is value-sensitive: merely
# having Origin/Destination does not make a public Battlefield zone transition hidden.
DECISION_KEYS = {
    "Optional", "OptionalDecider", "Choices", "Choice", "Chooser",
    "TargetingPlayer", "UnlessPayer",
}
RNG_KEYS = {"Random", "Shuffle", "TargetsAtRandom", "RandomNumTargets", "FlipCoin", "RollDice"}
HIDDEN_OPERATION_KEYS = {"Reveal", "Search", "DigNum", "ScryNum"}
PRIVATE_ZONE_KEYS = {"Origin", "Destination", "ChoiceZone"}
PRIVATE_ZONES = {"Library", "Hand"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_REQUIREMENT_PROJECTION_AUDIT=FAIL " + msg)


def class_source(target: str, root: Path) -> Path | None:
    base = target.split("#", 1)[0]
    if not base.startswith("forge."):
        return None
    rel = Path(*base.split(".")).with_suffix(".java")
    for module in ("forge-game", "forge-core", "forge-gui", "forge-ai"):
        p = root / module / "src/main/java" / rel
        if p.is_file():
            return p
    return None


def impl_params(target: str, root: Path, cache: dict[str, set[str]]) -> set[str]:
    if target in cache:
        return cache[target]
    p = class_source(target, root)
    text = p.read_text(encoding="utf-8", errors="replace") if p else ""
    keys: set[str] = set()
    for pat in (
        r'(?:hasParam|getParam|getParamOrDefault|matchesParam|isParam)[A-Za-z0-9_]*\(\s*"([A-Za-z][A-Za-z0-9_]*)"',
        r'containsKey\(\s*"([A-Za-z][A-Za-z0-9_]*)"',
    ):
        keys.update(re.findall(pat, text))
    cache[target] = keys
    return keys


def path_local_data(path: dict[str, Any], consumed_keys: set[str]) -> tuple[dict[str, str], list[str]]:
    """Return consumed selector values separately from free-form consumer evidence.

    Keeping selector key names out of free-form semantic text prevents false positives
    such as Trigger Mode=ChangesZone becoming a discretionary choice or
    Destination=Battlefield becoming hidden-information evidence.
    """
    profile = path.get("semantic_selector_profile") or {}
    selectors = profile.get("selectors") or {}
    active_selectors: dict[str, str] = {}
    if isinstance(selectors, dict):
        for key, value in selectors.items():
            if key in consumed_keys:
                active_selectors[str(key)] = str(value)

    evidence_strings: list[str] = []
    if profile.get("consumer_model") == "WS33_CONSUMER_AWARE_SVAR_V4":
        for key in ("first_consumer_field", "first_consumer_kind", "svar_expression_shape", "svar_token"):
            value = profile.get(key)
            if value is not None:
                evidence_strings.append(str(value))
    for evidence in path.get("consumer_evidence", []) or []:
        for key in ("consumer_field", "consumer_kind", "consumer_text", "source_value"):
            value = evidence.get(key)
            if value is not None:
                evidence_strings.append(str(value))
    for prov in path.get("source_provenance", []) or []:
        value = prov.get("source_value")
        if value is not None:
            evidence_strings.append(str(value))
    return active_selectors, evidence_strings


def amount_signals(strings: list[str]) -> dict[str, bool]:
    text = "\n".join(strings)
    return {
        "decision": bool(re.search(r"\b(Chosen|Choice|Selected|XPaid|Optional)\b", text, re.I)),
        "rng": bool(re.search(r"\b(Random|FlipCoin|RollDice|Shuffle)\b", text, re.I)),
        "hidden": bool(re.search(r"\b(Library|Hand|CardsInHand|ValidHand|TopCard|Search)\b", text, re.I)),
    }


def truthy_selector(value: str) -> bool:
    return value.strip().lower() not in {"", "false", "no", "none", "0"}


def private_zone_value(value: str) -> bool:
    tokens = {token for token in re.split(r"[^A-Za-z]+", value) if token}
    return bool(tokens & PRIVATE_ZONES)


def project(path: dict[str, Any], forge_root: Path, cache: dict[str, set[str]]) -> tuple[dict[str, bool], dict[str, Any]]:
    target = path["implementation_target"]
    keys = impl_params(target, forge_root, cache)
    selectors, evidence_strings = path_local_data(path, keys)
    values_text = "\n".join(selectors.values())
    evidence_text = "\n".join(evidence_strings)
    semantic_text = "\n".join([values_text, evidence_text])
    simple = target.rsplit(".", 1)[-1]

    if target == "forge.game.ability.AbilityUtils#calculateAmount":
        sig = amount_signals(list(selectors.values()) + evidence_strings)
        decision, rng, hidden = sig["decision"], sig["rng"], sig["hidden"]
        basis = "AMOUNT_EXPRESSION_AND_FIRST_CONSUMER"
    else:
        decision = any(x in simple for x in DECISION_INTRINSIC)
        rng = any(x in simple for x in RNG_INTRINSIC)
        hidden = any(x in simple for x in HIDDEN_INTRINSIC)

        active_keys = set(selectors)
        decision |= bool(active_keys & DECISION_KEYS)
        decision |= bool(re.search(r"\b(Chosen|Selected|Optional)\b", semantic_text, re.I))

        rng |= any(key in RNG_KEYS and truthy_selector(value) for key, value in selectors.items())
        rng |= bool(re.search(r"\b(Random|Shuffle|FlipCoin|RollDice)\b", evidence_text, re.I))

        hidden |= any(key in HIDDEN_OPERATION_KEYS and truthy_selector(value) for key, value in selectors.items())
        hidden |= any(key in PRIVATE_ZONE_KEYS and private_zone_value(value) for key, value in selectors.items())
        hidden |= bool(re.search(r"\b(Library|Hand|CardsInHand|ValidHand|TopCard|Search|Scry|Surveil|Dig)\b", evidence_text, re.I))

        if target == "forge.game.cost.Cost":
            decision = True
        basis = "TARGET_CONSUMED_PARAM_VALUES_AND_INTRINSIC_OPERATION"

    replay = decision or rng
    projected = {"decision": decision, "rng": rng, "hidden": hidden, "replay": replay}
    detail = {
        "basis": basis,
        "implementation_param_keys": sorted(keys),
        "active_consumed_selectors": dict(sorted(selectors.items())),
        "path_local_evidence_strings": evidence_strings[:40],
    }
    return projected, detail


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    head = subprocess.check_output(["git", "-C", str(args.forge_root), "rev-parse", "HEAD"], text=True).strip()
    require(head == PIN, "Forge pin mismatch")

    manifest = load(args.manifest)
    coverage = load(args.coverage)
    paths = manifest["paths"]
    status = {r["effective_v2_path_id"]: r["status"] for r in coverage["paths"]}
    require(set(status) == {p["v2_path_id"] for p in paths}, "manifest/coverage mismatch")

    cache: dict[str, set[str]] = {}
    rows = []
    removals = collections.Counter()
    upgrades = collections.Counter()
    pass_upgrades: list[str] = []
    changed_unknown = 0

    for path in paths:
        pid = path["v2_path_id"]
        projected, detail = project(path, args.forge_root, cache)
        current = {title: bool(path.get(field)) for title, field in REQS}
        removed = sorted(k for k in current if current[k] and not projected[k])
        added = sorted(k for k in current if not current[k] and projected[k])
        for key in removed:
            removals[key] += 1
        for key in added:
            upgrades[key] += 1
        if status[pid] == "PASS" and added:
            pass_upgrades.append(pid)
        if status[pid] == "UNKNOWN" and (removed or added):
            changed_unknown += 1
        if removed or added:
            rows.append({
                "effective_path_id": pid,
                "status": status[pid],
                "owner_family": path["owner_family"],
                "implementation_target": path["implementation_target"],
                "current": current,
                "projected": projected,
                "removal_candidates": removed,
                "upgrade_candidates": added,
                "classification": (
                    "CLASS_WIDE_OVERPROJECTION_CANDIDATE" if removed and not added
                    else "POTENTIAL_UNDERPROJECTION" if added and not removed
                    else "MIXED_REPROJECTION"
                ),
                **detail,
            })

    result = {
        "schema": "commander-simulator-next.ws33-requirement-projection-audit.v2",
        "forge_pin": PIN,
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "effective_path_count": len(paths),
        "unknown_path_count": sum(v == "UNKNOWN" for v in status.values()),
        "changed_unknown_path_count": changed_unknown,
        "candidate_row_count": len(rows),
        "removal_candidate_counts": dict(removals),
        "upgrade_candidate_counts": dict(upgrades),
        "pass_upgrade_candidate_count": len(pass_upgrades),
        "pass_upgrade_candidate_ids": pass_upgrades,
        "status": "PASS" if not pass_upgrades else "FAIL_CLOSED_PASS_REQUIREMENT_UPGRADE",
        "disposition": "AUDIT_ONLY_NO_MANIFEST_MUTATION",
        "candidates": rows,
    }
    write(args.out, result)
    if pass_upgrades:
        first = next(row for row in rows if row["effective_path_id"] == pass_upgrades[0])
        print("FIRST_PASS_UPGRADE_CANDIDATE=" + json.dumps(first, sort_keys=True))
    require(not pass_upgrades, "projection would strengthen existing PASS requirements")
    print(json.dumps({
        "WS33_REQUIREMENT_PROJECTION_AUDIT": "PASS",
        "paths": len(paths),
        "changed_unknown": changed_unknown,
        "candidate_rows": len(rows),
        "removals": dict(removals),
        "upgrades": dict(upgrades),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
