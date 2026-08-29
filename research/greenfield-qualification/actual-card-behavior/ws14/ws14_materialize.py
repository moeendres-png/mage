#!/usr/bin/env python3
"""WS14 deterministic Forge atomic behavior-path materializer.

Consumes the immutable WS11 per-identity frontier and exact Forge source pin.
It preserves WS11 full-script signatures and adds an engine-dispatch-backed
atomic primitive model. Parsing alone never qualifies behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
BASE_SHA = "6828c7175345d3193d814406428c8ee6b54c1136"
WS11_HEAD = "a604db2f8ebedfa9fad32fe71425ea2bfd031ec4"
WS11_RUN_ID = 33251464459
WS11_JOB_ID = 99097754070
WS11_ARTIFACT_ID = 9714505392
WS11_ARTIFACT_DIGEST = "sha256:74be5debf765e76d3aa8ab8a868795193b8f5dc6b4856d95bf9e94b087a7d581"
WS11_PER_IDENTITY_SHA256 = "1f46fc66d2049d65c7ede91700c0e76e38b3fb7c49c13bb394dd20aa6ea8ced7"
MODEL_SCHEMA = "commander-simulator-next.atomic-behavior-path.v1"
MANIFEST_SCHEMA = MODEL_SCHEMA + ".manifest"
IDENTITY_SCHEMA = MODEL_SCHEMA + ".identity"
OWNER_FAMILIES = (
    "ACTION_COST_DECISION",
    "TRIGGER_REPLACEMENT_ZONE_SBA",
    "CONTINUOUS_COPY_CONTROL",
    "COMBAT_COMMANDER",
    "HIDDEN_RNG_REPLAY",
)
SEMANTIC_PREFIXES = (
    "A:", "T:", "S:", "R:", "K:", "ManaCost:", "Types:",
    "Keywords:", "AlternateMode:",
)

REGISTRY_SPECS = {
    "ABILITY_API": {
        "path": "forge-game/src/main/java/forge/game/ability/ApiType.java",
        "package": "forge.game.ability.effects",
        "entry_re": re.compile(
            r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*\(\s*([A-Za-z][A-Za-z0-9_]*)\.class"
        ),
    },
    "TRIGGER": {
        "path": "forge-game/src/main/java/forge/game/trigger/TriggerType.java",
        "package": "forge.game.trigger",
        "entry_re": re.compile(
            r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*\(\s*([A-Za-z][A-Za-z0-9_]*)\.class"
        ),
    },
    "REPLACEMENT": {
        "path": "forge-game/src/main/java/forge/game/replacement/ReplacementType.java",
        "package": "forge.game.replacement",
        "entry_re": re.compile(
            r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*\(\s*([A-Za-z][A-Za-z0-9_]*)\.class"
        ),
    },
    "STATIC_MODE": {
        "path": "forge-game/src/main/java/forge/game/staticability/StaticAbilityMode.java",
        "package": None,
        "entry_re": None,
    },
}
ABILITY_FACTORY_PATH = "forge-game/src/main/java/forge/game/ability/AbilityFactory.java"

# Explicit systemic owner routing at Forge dispatch-token level. There is no
# card-name logic and no fuzzy/English-similarity matching.
HIDDEN_RNG_APIS = {
    "Clash", "Dig", "DigMultiple", "DigUntil", "Discover", "Draft",
    "FlipCoin", "Heist", "Learn", "LookAt", "Manifest", "ManifestDread",
    "MultiplePiles", "PeekAndReveal", "RearrangeTopOfLibrary", "Reveal",
    "RevealHand", "RollDice", "RollPlanarDice", "Scry", "Seek", "Shuffle",
    "Surveil", "TwoPiles",
}
COMBAT_APIS = {
    "BecomesBlocked", "Block", "Camouflage", "ChangeCombatants", "EachDamage",
    "EndCombatPhase", "Fight", "Fog", "Goad", "MustBlock", "RemoveFromCombat",
    "SwitchBlock",
}
CONTINUOUS_COPY_CONTROL_APIS = {
    "AlterAttribute", "Animate", "AnimateAll", "ChangeText", "Clone",
    "CopyPermanent", "CopySpellAbility", "ControlPlayer", "ControlSpell",
    "ExchangeControl", "ExchangeControlVariant", "ExchangeTextBox", "GainControl",
    "GainControlVariant", "GainOwnership", "Protection", "ProtectionAll", "Pump",
    "PumpAll", "SetState",
}
ZONE_SBA_APIS = {
    "Airbend", "Attach", "ChangeZone", "ChangeZoneAll", "Cloak", "Destroy",
    "DestroyAll", "Earthbend", "Encode", "ExchangeZone", "Manifest",
    "ManifestDread", "Meld", "Mill", "RemoveFromGame", "RemoveFromMatch",
    "Sacrifice", "SacrificeAll", "SetState", "Token", "Unattach",
}
COMBAT_STATIC_MODES = {
    "CantAttackUnless", "CantBlockUnless", "OptionalAttackCost", "CantAttack",
    "CanAttackDefender", "CantBlock", "CantBlockBy", "CanAttackIfHaste",
    "CanBlockIfReach", "MinMaxBlocker", "BlockTapped", "AttackVigilance",
    "MustAttack", "PlayerMustAttack", "MustBlock", "AssignCombatDamageAsUnblocked",
    "CombatDamageToughness", "BlockRestrict", "AttackRestrict",
    "AssignNoCombatDamage", "AttackRequirement",
}
ACTION_STATIC_MODES = {
    "OptionalCost", "AlternativeCost", "CantBeCast", "CantBeActivated",
    "CantPlayLand", "MustTarget", "RaiseCost", "ReduceCost", "SetCost",
    "CantPayLife", "CantTarget", "ActivateAbilityAsIfHaste", "CastWithFlash",
    "Activations", "TapPowerValue", "UnspentMana", "ManaBurn", "ManaConvert",
}
HIDDEN_STATIC_MODES = {"FlipCoinMod", "FlipCoinDoubler", "PlotZone", "SurveilNum"}


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def old_ws11_signature(raw_text: str) -> str:
    lines = [
        normalize_line(line)
        for line in raw_text.splitlines()
        if line.startswith(SEMANTIC_PREFIXES)
    ]
    return "forge-path-v1:" + sha256_bytes("\n".join(lines).encode("utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def read_registry(
    root: Path, domain: str
) -> tuple[dict[str, str], dict[str, Any]]:
    spec = REGISTRY_SPECS[domain]
    path = root / spec["path"]
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    mapping: dict[str, str] = {}
    if domain == "STATIC_MODE":
        in_enum = False
        for line in text.splitlines():
            if "public enum StaticAbilityMode" in line:
                in_enum = True
                continue
            if not in_enum:
                continue
            if line.strip() == ";":
                break
            match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*,?\s*$", line)
            if match:
                token = match.group(1)
                mapping[token.lower()] = (
                    f"forge.game.staticability.StaticAbilityMode#{token}"
                )
    else:
        entry_re = spec["entry_re"]
        assert entry_re is not None
        for line in text.splitlines():
            match = entry_re.match(line)
            if match:
                token, cls = match.groups()
                target = f"{spec['package']}.{cls}"
                key = token.lower()
                if key in mapping and mapping[key] != target:
                    raise ValueError(
                        f"conflicting {domain} registry mapping for {token}"
                    )
                mapping[key] = target
    meta = {
        "path": spec["path"],
        "sha256_bytes": sha256_bytes(raw),
        "entry_count": len(mapping),
    }
    return mapping, meta


def owner_for(domain: str, token: str) -> str:
    if domain in {"TRIGGER", "REPLACEMENT"}:
        return "TRIGGER_REPLACEMENT_ZONE_SBA"
    if domain == "STATIC_MODE":
        if token in COMBAT_STATIC_MODES:
            return "COMBAT_COMMANDER"
        if token in ACTION_STATIC_MODES:
            return "ACTION_COST_DECISION"
        if token in HIDDEN_STATIC_MODES:
            return "HIDDEN_RNG_REPLAY"
        return "CONTINUOUS_COPY_CONTROL"
    if domain == "ABILITY_API":
        if token in HIDDEN_RNG_APIS:
            return "HIDDEN_RNG_REPLAY"
        if token in COMBAT_APIS:
            return "COMBAT_COMMANDER"
        if token in CONTINUOUS_COPY_CONTROL_APIS:
            return "CONTINUOUS_COPY_CONTROL"
        if token in ZONE_SBA_APIS:
            return "TRIGGER_REPLACEMENT_ZONE_SBA"
        return "ACTION_COST_DECISION"
    if domain in {"COST", "TARGETING", "ABILITY_RECORD"}:
        return "ACTION_COST_DECISION"
    raise ValueError(f"unknown primitive domain {domain}")


def primitive_id(domain: str, token: str, target: str) -> str:
    payload = f"{domain}\0{token}\0{target}".encode("utf-8")
    return "forge-primitive-v1:" + sha256_bytes(payload)[:32]


def primitive_descriptor(
    domain: str,
    token: str,
    target: str,
    registry: dict[str, Any],
    *,
    family: str | None = None,
) -> dict[str, Any]:
    return {
        "primitive_id": primitive_id(domain, token, target),
        "primitive_family": family or domain,
        "dispatch_domain": domain,
        "dispatch_token": token,
        "implementation_target": target,
        "implementation_source": registry,
        "owner_family": owner_for(domain, token),
        "cross_family_dependencies": [],
        "evidence_class": "CODE_DERIVED",
    }


def source_record_kind(line: str) -> str | None:
    for prefix, kind in (
        ("A:", "ABILITY"),
        ("T:", "TRIGGER"),
        ("R:", "REPLACEMENT"),
        ("S:", "STATIC"),
        ("K:", "KEYWORD"),
        ("Keywords:", "KEYWORD"),
        ("AlternateMode:", "ALTERNATE_MODE"),
        ("ManaCost:", "MANA_COST"),
        ("SVar:", "SVAR"),
    ):
        if line.startswith(prefix):
            return kind
    return None


def add_primitive(
    catalog: dict[str, dict[str, Any]], desc: dict[str, Any]
) -> None:
    pid = desc["primitive_id"]
    prior = catalog.get(pid)
    if prior is not None and canonical_json(prior) != canonical_json(desc):
        raise ValueError(f"primitive id collision/conflicting semantics: {pid}")
    catalog[pid] = desc


def occurrence(
    desc: dict[str, Any],
    *,
    line_no: int,
    directive: str,
    source_token: str,
    source_value: str,
) -> dict[str, Any]:
    return {
        "primitive_id": desc["primitive_id"],
        "primitive_family": desc["primitive_family"],
        "owner_family": desc["owner_family"],
        "source_line": line_no,
        "source_directive": directive,
        "source_token": source_token,
        "source_value": source_value,
        "implementation_target": desc["implementation_target"],
        "binding_status": "RESOLVED",
        "ambiguity_status": "UNAMBIGUOUS",
    }


def unknown(
    *,
    line_no: int,
    directive: str,
    token: str,
    value: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "primitive_id": None,
        "primitive_family": None,
        "owner_family": None,
        "source_line": line_no,
        "source_directive": directive,
        "source_token": token,
        "source_value": value,
        "implementation_target": None,
        "binding_status": "UNKNOWN",
        "ambiguity_status": "UNKNOWN",
        "reason": reason,
        "evidence_class": "UNKNOWN",
    }


def extract_bindings(
    text: str,
    registries: dict[str, dict[str, str]],
    registry_meta: dict[str, dict[str, Any]],
    ability_factory_meta: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        kind = source_record_kind(line)
        if kind is None:
            continue

        api_match = re.search(
            r"\b(AB|SP|ST|DB)\$\s*([A-Za-z][A-Za-z0-9_]*)", line
        )
        if api_match:
            record_type, api_token = api_match.groups()
            target = registries["ABILITY_API"].get(api_token.lower())
            if target:
                desc = primitive_descriptor(
                    "ABILITY_API", api_token, target, registry_meta["ABILITY_API"]
                )
                add_primitive(catalog, desc)
                resolved.append(
                    occurrence(
                        desc,
                        line_no=line_no,
                        directive=kind,
                        source_token=f"{record_type}$",
                        source_value=api_token,
                    )
                )
            else:
                unresolved.append(
                    unknown(
                        line_no=line_no,
                        directive=kind,
                        token=f"{record_type}$",
                        value=api_token,
                        reason=(
                            "ApiType.smartValueOf dispatch token absent from pinned "
                            "ApiType registry"
                        ),
                    )
                )

            record_targets = {
                "AB": "forge.game.spellability.AbilityApiBased",
                "SP": "forge.game.spellability.SpellApiBased",
                "ST": "forge.game.spellability.StaticAbilityApiBased",
                "DB": "forge.game.spellability.AbilitySub",
            }
            record_target = record_targets[record_type]
            record_desc = primitive_descriptor(
                "ABILITY_RECORD",
                record_type,
                record_target,
                ability_factory_meta,
                family="ABILITY_RECORD",
            )
            add_primitive(catalog, record_desc)
            resolved.append(
                occurrence(
                    record_desc,
                    line_no=line_no,
                    directive=kind,
                    source_token=record_type,
                    source_value=record_type,
                )
            )

            cost_match = re.search(r"(?:^|\|)\s*Cost\$\s*([^|]+)", line)
            if cost_match or record_type == "SP":
                cost_token = "Cost$" if cost_match else "implicit-spell-cost"
                cost_value = (
                    normalize_line(cost_match.group(1)) if cost_match else record_type
                )
                cost_desc = primitive_descriptor(
                    "COST",
                    "AbilityFactory.parseAbilityCost",
                    "forge.game.cost.Cost",
                    ability_factory_meta,
                    family="COST_IMPLEMENTATION",
                )
                add_primitive(catalog, cost_desc)
                resolved.append(
                    occurrence(
                        cost_desc,
                        line_no=line_no,
                        directive=kind,
                        source_token=cost_token,
                        source_value=cost_value,
                    )
                )

            target_match = re.search(
                r"(?:^|\|)\s*ValidTgts\$\s*([^|]+)", line
            )
            if target_match:
                target_desc = primitive_descriptor(
                    "TARGETING",
                    "ValidTgts",
                    "forge.game.spellability.TargetRestrictions",
                    ability_factory_meta,
                    family="TARGETING_IMPLEMENTATION",
                )
                add_primitive(catalog, target_desc)
                resolved.append(
                    occurrence(
                        target_desc,
                        line_no=line_no,
                        directive=kind,
                        source_token="ValidTgts$",
                        source_value=normalize_line(target_match.group(1)),
                    )
                )

        if kind == "TRIGGER":
            match = re.search(r"\bMode\$\s*([A-Za-z][A-Za-z0-9_]*)", line)
            if not match:
                unresolved.append(
                    unknown(
                        line_no=line_no,
                        directive=kind,
                        token="Mode$",
                        value=line,
                        reason="trigger directive has no resolvable Mode$ token",
                    )
                )
            else:
                token = match.group(1)
                target = registries["TRIGGER"].get(token.lower())
                if target:
                    desc = primitive_descriptor(
                        "TRIGGER", token, target, registry_meta["TRIGGER"]
                    )
                    add_primitive(catalog, desc)
                    resolved.append(
                        occurrence(
                            desc,
                            line_no=line_no,
                            directive=kind,
                            source_token="Mode$",
                            source_value=token,
                        )
                    )
                else:
                    unresolved.append(
                        unknown(
                            line_no=line_no,
                            directive=kind,
                            token="Mode$",
                            value=token,
                            reason=(
                                "TriggerType.smartValueOf dispatch token absent from "
                                "pinned TriggerType registry"
                            ),
                        )
                    )
        elif kind == "REPLACEMENT":
            match = re.search(r"\bEvent\$\s*([A-Za-z][A-Za-z0-9_]*)", line)
            if not match:
                unresolved.append(
                    unknown(
                        line_no=line_no,
                        directive=kind,
                        token="Event$",
                        value=line,
                        reason="replacement directive has no resolvable Event$ token",
                    )
                )
            else:
                token = match.group(1)
                target = registries["REPLACEMENT"].get(token.lower())
                if target:
                    desc = primitive_descriptor(
                        "REPLACEMENT", token, target, registry_meta["REPLACEMENT"]
                    )
                    add_primitive(catalog, desc)
                    resolved.append(
                        occurrence(
                            desc,
                            line_no=line_no,
                            directive=kind,
                            source_token="Event$",
                            source_value=token,
                        )
                    )
                else:
                    unresolved.append(
                        unknown(
                            line_no=line_no,
                            directive=kind,
                            token="Event$",
                            value=token,
                            reason=(
                                "ReplacementType.smartValueOf dispatch token absent from "
                                "pinned ReplacementType registry"
                            ),
                        )
                    )
        elif kind == "STATIC":
            match = re.search(r"\bMode\$\s*([A-Za-z][A-Za-z0-9_]*)", line)
            if not match:
                unresolved.append(
                    unknown(
                        line_no=line_no,
                        directive=kind,
                        token="Mode$",
                        value=line,
                        reason="static directive has no resolvable Mode$ token",
                    )
                )
            else:
                token = match.group(1)
                target = registries["STATIC_MODE"].get(token.lower())
                if target:
                    desc = primitive_descriptor(
                        "STATIC_MODE", token, target, registry_meta["STATIC_MODE"]
                    )
                    add_primitive(catalog, desc)
                    resolved.append(
                        occurrence(
                            desc,
                            line_no=line_no,
                            directive=kind,
                            source_token="Mode$",
                            source_value=token,
                        )
                    )
                else:
                    unresolved.append(
                        unknown(
                            line_no=line_no,
                            directive=kind,
                            token="Mode$",
                            value=token,
                            reason=(
                                "StaticAbilityMode.smartValueOf dispatch token absent from "
                                "pinned StaticAbilityMode registry"
                            ),
                        )
                    )
        elif kind == "MANA_COST":
            value = normalize_line(line.split(":", 1)[1])
            desc = primitive_descriptor(
                "COST",
                "CardState.ManaCost",
                "forge.game.cost.Cost",
                ability_factory_meta,
                family="COST_IMPLEMENTATION",
            )
            add_primitive(catalog, desc)
            resolved.append(
                occurrence(
                    desc,
                    line_no=line_no,
                    directive=kind,
                    source_token="ManaCost:",
                    source_value=value,
                )
            )
        elif kind in {"KEYWORD", "ALTERNATE_MODE"}:
            value = normalize_line(line.split(":", 1)[1] if ":" in line else line)
            if value:
                unresolved.append(
                    unknown(
                        line_no=line_no,
                        directive=kind,
                        token=kind,
                        value=value,
                        reason=(
                            "WS14 does not promote keyword/alternate-mode text without "
                            "a direct pinned Java dispatch binding"
                        ),
                    )
                )
        elif kind == "SVAR" and not api_match:
            parts = line.split(":", 2)
            if len(parts) == 3 and parts[2].strip():
                unresolved.append(
                    unknown(
                        line_no=line_no,
                        directive=kind,
                        token=parts[1],
                        value=normalize_line(parts[2]),
                        reason=(
                            "SVar expression is preserved but has no safely resolved "
                            "atomic Java dispatch in WS14"
                        ),
                    )
                )
    return resolved, unresolved


def materialize(ws11_path: Path, forge_root: Path, out_dir: Path) -> dict[str, Any]:
    ws11_raw = ws11_path.read_bytes()
    if sha256_bytes(ws11_raw) != WS11_PER_IDENTITY_SHA256:
        raise ValueError("WS11 PER_IDENTITY.semantic.jsonl SHA-256 mismatch")
    rows = read_jsonl(ws11_path)
    if len(rows) != 1678:
        raise ValueError(f"expected 1678 WS11 identities, got {len(rows)}")

    registries: dict[str, dict[str, str]] = {}
    registry_meta: dict[str, dict[str, Any]] = {}
    for domain in REGISTRY_SPECS:
        registries[domain], registry_meta[domain] = read_registry(forge_root, domain)

    ability_factory = forge_root / ABILITY_FACTORY_PATH
    af_raw = ability_factory.read_bytes()
    af_text = af_raw.decode("utf-8")
    required_evidence = (
        "return ApiType.smartValueOf(abParams.get(getPrefix()))",
        "return new Cost(cost, type == AbilityRecordType.Ability)",
        "return new Cost(state.getManaCost(), false)",
        'mapParams.containsKey("ValidTgts") ? readTarget(mapParams) : null',
    )
    if not all(item in af_text for item in required_evidence):
        raise ValueError(
            "pinned AbilityFactory no longer contains required dispatch/cost/target evidence"
        )
    ability_factory_meta = {
        "path": ABILITY_FACTORY_PATH,
        "sha256_bytes": sha256_bytes(af_raw),
        "evidence": list(required_evidence),
    }

    catalog: dict[str, dict[str, Any]] = {}
    output_rows: list[dict[str, Any]] = []
    unresolved_total = 0
    ambiguous_total = 0
    old_signatures: set[str] = set()

    for base in rows:
        source_bindings = base.get("behavior_path_bindings") or []
        identity_sources: list[dict[str, Any]] = []
        identity_primitives: set[str] = set()
        identity_families: set[str] = set()
        identity_unresolved = 0
        ambiguous = base.get("forge_implementation_binding") != "PROVEN"
        if not source_bindings:
            ambiguous = True
        for binding in source_bindings:
            rel = binding["forge_source_path"].replace("\\", "/")
            source = forge_root / rel
            if not source.is_file():
                raise ValueError(f"missing pinned Forge source: {rel}")
            raw = source.read_bytes()
            actual_sha = sha256_bytes(raw)
            if actual_sha != binding["forge_source_sha256_bytes"]:
                raise ValueError(
                    f"source SHA mismatch for {rel}: {actual_sha} != "
                    f"{binding['forge_source_sha256_bytes']}"
                )
            text = raw.decode("utf-8-sig", errors="strict")
            old_signature = binding["signature_id"]
            recomputed = old_ws11_signature(text)
            if recomputed != old_signature:
                raise ValueError(
                    f"WS11 full-script signature mismatch for {rel}: "
                    f"{recomputed} != {old_signature}"
                )
            old_signatures.add(old_signature)
            resolved, unresolved = extract_bindings(
                text, registries, registry_meta, ability_factory_meta, catalog
            )
            identity_unresolved += len(unresolved)
            primitive_ids = sorted({item["primitive_id"] for item in resolved})
            identity_primitives.update(primitive_ids)
            identity_families.update(
                catalog[pid]["primitive_family"] for pid in primitive_ids
            )
            identity_sources.append(
                {
                    "forge_source_path": rel,
                    "forge_source_sha256_bytes": actual_sha,
                    "ws10_decoded_source_sha256": binding.get(
                        "ws10_decoded_source_sha256"
                    ),
                    "old_ws11_full_script_signature": old_signature,
                    "old_ws11_semantic_lines_sha256": binding.get(
                        "semantic_lines_sha256"
                    ),
                    "atomic_primitive_ids": primitive_ids,
                    "primitive_bindings": sorted(
                        resolved,
                        key=lambda item: (
                            item["source_line"],
                            item["primitive_id"],
                            item["source_token"],
                        ),
                    ),
                    "unresolved_bindings": sorted(
                        unresolved,
                        key=lambda item: (
                            item["source_line"],
                            item["source_token"],
                            item["source_value"],
                        ),
                    ),
                    "ambiguity_status": (
                        "AMBIGUOUS" if ambiguous else "UNAMBIGUOUS"
                    ),
                }
            )
        unresolved_total += identity_unresolved
        ambiguous_total += int(ambiguous)
        output_rows.append(
            {
                "schema": IDENTITY_SCHEMA,
                "oracle_id": base["oracle_id"],
                "oracle_name": base["oracle_name"],
                "forge_pin": FORGE_PIN,
                "ws11_source_provenance": base.get("source_provenance"),
                "forge_sources": identity_sources,
                "old_ws11_full_script_signature_ids": sorted(
                    {
                        source["old_ws11_full_script_signature"]
                        for source in identity_sources
                    }
                ),
                "atomic_primitive_ids": sorted(identity_primitives),
                "primitive_families": sorted(identity_families),
                "unresolved_binding_count": identity_unresolved,
                "ambiguity_status": "AMBIGUOUS" if ambiguous else "UNAMBIGUOUS",
                "behavior_qualification": "NOT_EVALUATED",
                "behavior_pass_issued_from_parsing": False,
                "evidence_class": (
                    "CODE_DERIVED" if identity_primitives else "UNKNOWN"
                ),
            }
        )

    if len(old_signatures) != 1677:
        raise ValueError(
            f"expected 1677 retained WS11 full-script signatures, got "
            f"{len(old_signatures)}"
        )
    for primitive in catalog.values():
        if primitive["owner_family"] not in OWNER_FAMILIES:
            raise ValueError(f"invalid owner family: {primitive}")

    out_dir.mkdir(parents=True, exist_ok=True)
    per_identity_path = out_dir / "PER_IDENTITY.atomic.jsonl"
    per_identity_path.write_bytes(
        b"".join(canonical_json(row) + b"\n" for row in output_rows)
    )

    unresolved_rows: list[dict[str, Any]] = []
    for row in output_rows:
        for source in row["forge_sources"]:
            for item in source["unresolved_bindings"]:
                unresolved_rows.append(
                    {
                        "oracle_id": row["oracle_id"],
                        "oracle_name": row["oracle_name"],
                        "forge_source_path": source["forge_source_path"],
                        **item,
                    }
                )
    unresolved_path = out_dir / "UNRESOLVED_BINDINGS.jsonl"
    unresolved_path.write_bytes(
        b"".join(canonical_json(row) + b"\n" for row in unresolved_rows)
    )

    owner_counts = Counter(item["owner_family"] for item in catalog.values())
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "model": "forge-atomic-path-v1",
        "base_sha": BASE_SHA,
        "forge_pin": FORGE_PIN,
        "ws11_input": {
            "qualified_head": WS11_HEAD,
            "run_id": WS11_RUN_ID,
            "job_id": WS11_JOB_ID,
            "artifact_id": WS11_ARTIFACT_ID,
            "artifact_digest": WS11_ARTIFACT_DIGEST,
            "per_identity_sha256": WS11_PER_IDENTITY_SHA256,
        },
        "identity_count": len(output_rows),
        "old_full_script_signature_count": len(old_signatures),
        "atomic_primitive_count": len(catalog),
        "primitive_count_by_owner_family": {
            family: owner_counts[family] for family in OWNER_FAMILIES
        },
        "unresolved_binding_count": unresolved_total,
        "ambiguous_binding_count": ambiguous_total,
        "deterministic_materialization_contract": (
            "canonical-json/sorted-primitives/sorted-occurrences/no-runtime-time-or-rng"
        ),
        "card_name_production_hacks": 0,
        "synthetic_behavior_promotion": False,
        "behavior_pass_issued_from_parsing": False,
        "registry_sources": {
            **registry_meta,
            "ABILITY_FACTORY": ability_factory_meta,
        },
        "per_identity_sha256": sha256_bytes(per_identity_path.read_bytes()),
        "unresolved_bindings_sha256": sha256_bytes(unresolved_path.read_bytes()),
        "primitives": [catalog[pid] for pid in sorted(catalog)],
        "evidence_classes": ["CODE_DERIVED", "UNKNOWN"],
    }
    manifest_path = out_dir / "WS14_PRIMITIVE_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    gate = {
        "schema": MODEL_SCHEMA + ".gate",
        "WORKSTREAM_COMPLETE": True,
        "Q6_ACTUAL_CARD_BEHAVIOR": "NOT_ADJUDICATED",
        "identity_count": manifest["identity_count"],
        "old_full_script_signature_count": manifest[
            "old_full_script_signature_count"
        ],
        "atomic_primitive_count": manifest["atomic_primitive_count"],
        "primitive_count_by_owner_family": manifest[
            "primitive_count_by_owner_family"
        ],
        "unresolved_binding_count": unresolved_total,
        "ambiguous_binding_count": ambiguous_total,
        "zero_duplicate_primitive_ids_with_conflicting_semantics": True,
        "zero_silent_unresolved_mappings": True,
        "all_unresolved_explicit_unknown": all(
            item["binding_status"] == "UNKNOWN"
            and item["evidence_class"] == "UNKNOWN"
            for item in unresolved_rows
        ),
        "old_full_script_signatures_retained": len(old_signatures) == 1677,
        "card_name_production_hacks": 0,
        "behavior_pass_issued_from_parsing": False,
        "evidence_classes": ["CODE_DERIVED", "UNKNOWN"],
    }
    (out_dir / "WS14_GATE.runtime.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws11-per-identity", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    materialize(args.ws11_per_identity, args.forge_root, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
