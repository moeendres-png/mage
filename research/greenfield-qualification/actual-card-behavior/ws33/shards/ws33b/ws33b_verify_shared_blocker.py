#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

BASE_HEAD = "c69686431c7296cb3e1a2f9e0de8b82886c92c46"
BASE_TREE = "6b885d02e9a0bc8cad2f93af08db99bda75955a5"
BASE_RUN = 33370369458
BASE_JOB = 99419848606
BASE_ARTIFACT_ID = 9750186364
BASE_ARTIFACT_NAME = "ws33-q6-runtime-closure-33370369458"
BASE_ARTIFACT_DIGEST = "sha256:b156241094eb14f8270f07ee7338a30768a20f0ec077d8f68b3c7e097c89dacd"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
OWNER = "ACTION_COST_DECISION"
TARGETS = {
    "forge.game.cost.Cost",
    "forge.game.ability.AbilityUtils#calculateAmount",
}
EXPECTED_COUNTS = {
    "assigned_paths_total": 598,
    "forge.game.cost.Cost": 396,
    "forge.game.ability.AbilityUtils#calculateAmount": 202,
}
EXPECTED_EVIDENCE = {
    "HIDDEN": 206,
    "DECISION+RNG+HIDDEN+REPLAY": 204,
    "DECISION+HIDDEN+REPLAY": 186,
    "RNG+HIDDEN+REPLAY": 2,
}
EXPECTED_TEMPLATE_IDS = {
    "ws33-template-010",
    "ws33-template-089",
    "ws33-template-090",
    "ws33-template-091",
    "ws33-template-092",
}
EXPECTED_MISCLASSIFIED = {
    "forge-behavior-v2:10598c287d160ad9a84a37d73ea796175297dbd9",
    "forge-behavior-v2:85f8e36c876956e07bcad1f3854546ead58d7257",
    "forge-behavior-v2:9573d1b9c2d539b02fbbd5e8ca32f20e13041ad2",
    "forge-behavior-v2:99a9fd94e8802d24880c1274145bb1e29f983b38",
    "forge-behavior-v2:a96a0142f4190398f3cd35ddb3dd65774485d3fa",
    "forge-behavior-v2:df803d033df0233bc03ea7d33a2ac63b3c42a293",
    "forge-behavior-v2:e3a0bf2764c462f5cd8bf0244fafe19bd517b8df",
    "forge-behavior-v2:e6897e594848a944f6f69d2a7364a7579994d3cc",
    "forge-behavior-v2:eec50e1ffeb8fa31a88339678689bdfd70bea2e2",
    "forge-behavior-v2:f262e00ef93b9d8a3acc08a14b36f4c89f2a35dc",
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_profile(row: dict) -> str:
    names = []
    for name, key in (
        ("DECISION", "required_decision_evidence"),
        ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"),
        ("REPLAY", "required_replay_evidence"),
    ):
        if row.get(key):
            names.append(name)
    return "+".join(names) if names else "STATE_ONLY"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def source_reference_lines(lines: list[str], token: str, declaration_line: int) -> list[dict]:
    token_re = re.compile(r"\$\s*" + re.escape(token) + r"(?:\b|$)")
    refs = []
    for idx, line in enumerate(lines, 1):
        if idx == declaration_line:
            continue
        if token_re.search(line):
            refs.append({"line": idx, "text": line})
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-artifact", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    args = parser.parse_args()

    artifact = args.base_artifact.resolve()
    forge = args.forge_root.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest = load(artifact / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    coverage = load(artifact / "WS33_PATH_COVERAGE.json")
    registry = load(artifact / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")
    require(manifest.get("source_head") == BASE_HEAD, "base manifest HEAD mismatch")
    require(manifest.get("source_tree") == BASE_TREE, "base manifest TREE mismatch")
    require(manifest.get("forge_pin") == FORGE_PIN, "base manifest Forge pin mismatch")

    status = {row["effective_v2_path_id"]: row["status"] for row in coverage["paths"]}
    frontier = [
        row for row in manifest["paths"]
        if status.get(row["v2_path_id"]) == "UNKNOWN"
        and row.get("owner_family") == OWNER
        and row.get("implementation_target") in TARGETS
    ]
    require(len(frontier) == EXPECTED_COUNTS["assigned_paths_total"], "WS33B frontier count mismatch")
    target_counts = collections.Counter(row["implementation_target"] for row in frontier)
    for target in TARGETS:
        require(target_counts[target] == EXPECTED_COUNTS[target], f"WS33B target count mismatch for {target}")
    profiles = collections.Counter(evidence_profile(row) for row in frontier)
    require(dict(profiles) == EXPECTED_EVIDENCE, f"WS33B evidence profiles mismatch: {dict(profiles)}")

    frontier_ids = {row["v2_path_id"] for row in frontier}
    templates = [
        row for row in registry["templates"]
        if frontier_ids.intersection(row.get("remaining_path_ids", []))
    ]
    template_ids = {row["template_id"] for row in templates}
    require(template_ids == EXPECTED_TEMPLATE_IDS, f"WS33B template set mismatch: {sorted(template_ids)}")
    covered_by_templates = []
    for row in templates:
        covered_by_templates.extend(pid for pid in row["remaining_path_ids"] if pid in frontier_ids)
    require(len(covered_by_templates) == len(frontier_ids), "WS33B template partition cardinality mismatch")
    require(set(covered_by_templates) == frontier_ids, "WS33B template partition set mismatch")
    require(len(covered_by_templates) == len(set(covered_by_templates)), "WS33B template partition overlaps")

    amount = [row for row in frontier if row["implementation_target"] == "forge.game.ability.AbilityUtils#calculateAmount"]
    event_svar_rows = []
    for row in amount:
        for prov in row.get("source_provenance", []):
            if prov.get("source_directive") == "SVAR" and str(prov.get("source_value", "")).startswith("Event$ "):
                event_svar_rows.append((row, prov))
    event_ids = {row["v2_path_id"] for row, _ in event_svar_rows}
    require(event_ids == EXPECTED_MISCLASSIFIED,
            "replacement-definition misclassification set changed: " + json.dumps(sorted(event_ids)))
    require(len(event_svar_rows) == len(EXPECTED_MISCLASSIFIED),
            "replacement-definition misclassification has duplicate provenance")

    effect_effect = forge / "forge-game/src/main/java/forge/game/ability/effects/EffectEffect.java"
    ability_utils = forge / "forge-game/src/main/java/forge/game/ability/AbilityUtils.java"
    require(effect_effect.is_file(), "pinned Forge EffectEffect.java missing")
    require(ability_utils.is_file(), "pinned Forge AbilityUtils.java missing")
    effect_text = effect_effect.read_text(encoding="utf-8")
    consumer_markers = [
        'if (sa.hasParam("ReplacementEffects"))',
        'effectReplacementEffects = sa.getParam("ReplacementEffects").split(",")',
        'final String actualReplacement = AbilityUtils.getSVar(sa, s);',
        'ReplacementHandler.parseReplacement(actualReplacement, eff, true, eff.getCurrentState())',
    ]
    for marker in consumer_markers:
        require(marker in effect_text, "pinned Forge replacement consumer marker missing: " + marker)

    verified = []
    for row, prov in sorted(event_svar_rows, key=lambda pair: pair[0]["v2_path_id"]):
        rel = prov["forge_source_path"]
        path = forge / rel
        require(path.is_file(), "actual Forge card source missing: " + rel)
        lines = path.read_text(encoding="utf-8").splitlines()
        line_no = int(prov["source_line"])
        require(1 <= line_no <= len(lines), f"source line out of range for {rel}")
        declaration = lines[line_no - 1]
        expected_decl = f"SVar:{prov['source_token']}:{prov['source_value']}"
        require(declaration == expected_decl,
                f"actual source declaration mismatch at {rel}:{line_no}")
        refs = source_reference_lines(lines, prov["source_token"], line_no)
        replacement_refs = [ref for ref in refs if "ReplacementEffects$" in ref["text"]]
        non_replacement_refs = [ref for ref in refs if "ReplacementEffects$" not in ref["text"]]
        require(replacement_refs, f"no actual ReplacementEffects consumer reference for {rel}:{line_no}")
        require(not non_replacement_refs,
                f"SVar {prov['source_token']} has a non-ReplacementEffects script consumer; blocker needs re-adjudication")
        verified.append({
            "v2_path_id": row["v2_path_id"],
            "assigned_implementation_target": row["implementation_target"],
            "owner_family": row["owner_family"],
            "oracle_identity": prov["oracle_identity"],
            "forge_source_path": rel,
            "svar_source_line": line_no,
            "svar_token": prov["source_token"],
            "svar_value_prefix": "Event$",
            "actual_script_consumer_refs": replacement_refs,
            "actual_forge_consumer": {
                "source": "forge-game/src/main/java/forge/game/ability/effects/EffectEffect.java",
                "lookup": "AbilityUtils.getSVar(sa, s)",
                "parser": "ReplacementHandler.parseReplacement(actualReplacement, eff, true, eff.getCurrentState())",
                "calculate_amount_in_consumer_chain": False,
            },
            "adjudication": "MODEL_TARGET_MISMATCH",
            "evidence_class": "CODE_DERIVED",
        })

    frontier_audit = {
        "schema": "commander-simulator-next.ws33b-frontier-audit.v1",
        "qualification_source_head": args.source_head,
        "qualification_source_tree": args.source_tree,
        "ws33_parallel_base": {
            "head": BASE_HEAD,
            "tree": BASE_TREE,
            "run": BASE_RUN,
            "job": BASE_JOB,
            "artifact_id": BASE_ARTIFACT_ID,
            "artifact_name": BASE_ARTIFACT_NAME,
            "artifact_digest": BASE_ARTIFACT_DIGEST,
        },
        "forge_pin": FORGE_PIN,
        "predicate": {
            "status": "UNKNOWN",
            "owner_family": OWNER,
            "implementation_targets": sorted(TARGETS),
        },
        "assigned_paths_total": len(frontier),
        "implementation_target_counts": dict(sorted(target_counts.items())),
        "evidence_profile_counts": dict(sorted(profiles.items())),
        "scenario_template_ids": sorted(template_ids),
        "scenario_template_count": len(template_ids),
        "path_ids_sha256": hashlib.sha256(("\n".join(sorted(frontier_ids)) + "\n").encode("utf-8")).hexdigest(),
        "evidence_class": "DIRECTLY_VERIFIED",
    }
    write_json(out / "WS33B_FRONTIER_AUDIT.json", frontier_audit)

    blocker = {
        "schema": "commander-simulator-next.ws33b-cross-shard-shared-blocker.v1",
        "CROSS_SHARD_SHARED_BLOCKER": True,
        "blocker_id": "WS33B-SHARED-MODEL-CALCULATEAMOUNT-REPLACEMENT-SVAR",
        "classification": "SHARED_EFFECTIVE_PATH_MODEL_TARGET_MISCLASSIFICATION",
        "summary": (
            "The immutable WS33 parallel-base assigns ten actual Replacement-Effect definition SVars "
            "to forge.game.ability.AbilityUtils#calculateAmount. Pinned Forge consumes each through "
            "EffectEffect -> AbilityUtils.getSVar -> ReplacementHandler.parseReplacement, not through "
            "calculateAmount. Calling calculateAmount on these Event$ definitions would be a synthetic "
            "test-side path and is forbidden by the WS33 child contract."
        ),
        "affected_assigned_paths": verified,
        "affected_path_count": len(verified),
        "required_shared_repair": {
            "required": True,
            "reason": (
                "The ten paths are members of the immutable shared WS33 effective behavior-path manifest "
                "and WS33B assignment. Removing/reclassifying them requires rebuilding shared WS33 model/"
                "coverage/scenario artifacts; a child shard is forbidden from mutating those registries."
            ),
            "child_may_patch_around": False,
            "forbidden_workaround": "synthetic AbilityUtils.calculateAmount invocation on Event$ replacement definitions",
            "integrator_action": (
                "Re-adjudicate the shared SVar implementation-target inference, rebuild the authoritative "
                "WS33 effective manifest/coverage/scenario partition from a new qualified common base, then "
                "restart/rebase affected child assignments from that exact common base."
            ),
        },
        "base_provenance": frontier_audit["ws33_parallel_base"],
        "forge_pin": FORGE_PIN,
        "evidence_class": "CODE_DERIVED",
    }
    write_json(out / "WS33B_SHARED_BLOCKER.json", blocker)

    gate = {
        "schema": "commander-simulator-next.ws33b-child-gate.v1",
        "assigned_paths_total": len(frontier),
        "PASS": 0,
        "UNKNOWN": len(frontier),
        "FAIL": 0,
        "UNSUPPORTED": 0,
        "OUT_OF_SCOPE_ADMISSIONS": 0,
        "CROSS_SHARD_SHARED_BLOCKER": True,
        "CHILD_COMPLETE": False,
        "completion_reason": "BLOCKED_BY_SHARED_EFFECTIVE_PATH_MODEL_TARGET_MISCLASSIFICATION",
        "affected_shared_model_paths": len(verified),
        "safe_paths_not_promoted": len(frontier) - len(verified),
        "safe_paths_not_promoted_reason": (
            "Fail-closed stop at the first shared-model blocker. No path is promoted from this child until "
            "the integrator produces a corrected common base, preventing sibling base divergence."
        ),
        "global_q6_claim": False,
        "evidence_class": "TECHNICALLY_CONFORMANT",
    }
    write_json(out / "WS33B_GATE.json", gate)

    shard_manifest = {
        "schema": "commander-simulator-next.ws33b-shard-manifest.v1",
        "shard": "WS33B",
        "branch": "work/ws33b-cost-amount-closure-20260831",
        "qualification_source_head": args.source_head,
        "qualification_source_tree": args.source_tree,
        "ws33_parallel_base": frontier_audit["ws33_parallel_base"],
        "forge_pin": FORGE_PIN,
        "predicate": frontier_audit["predicate"],
        "assigned_paths_total": len(frontier),
        "promoted_path_count": 0,
        "pass_witness_count": 0,
        "cross_shard_shared_blocker": True,
        "child_complete": False,
        "emitted_files": [
            "WS33B_FRONTIER_AUDIT.json",
            "WS33B_SHARED_BLOCKER.json",
            "WS33B_GATE.json",
            "WS33B_HANDOFF.md",
            "WS33B_HASHES.sha256",
        ],
        "global_registry_mutations": 0,
        "foreign_child_path_admissions": 0,
        "evidence_class": "TECHNICALLY_CONFORMANT",
    }
    write_json(out / "WS33B_SHARD_MANIFEST.json", shard_manifest)

    handoff = f"""# WS33B — Shared blocker handoff

## Disposition

```ini
CROSS_SHARD_SHARED_BLOCKER = TRUE
CHILD_COMPLETE = FALSE
assigned_paths_total = {len(frontier)}
PASS = 0
UNKNOWN = {len(frontier)}
FAIL = 0
UNSUPPORTED = 0
OUT_OF_SCOPE_ADMISSIONS = 0
```

WS33B cannot legally reach its child-complete gate from the immutable parallel base because
**{len(verified)} assigned `AbilityUtils#calculateAmount` paths are shared-model target
misclassifications**.

The pinned Forge sources show these are `Event$ ...` replacement-effect definitions. Their
actual runtime consumer is `EffectEffect -> AbilityUtils.getSVar -> ReplacementHandler.parseReplacement`.
They are not amount expressions on the actual parent ability. Invoking `calculateAmount` on those
strings solely to satisfy the assignment would create a synthetic test-side path, prohibited by the
common contract.

No shared WS33 registry/model file was changed. No assigned path was promoted.

## Immutable base

- HEAD: `{BASE_HEAD}`
- TREE: `{BASE_TREE}`
- RUN: `{BASE_RUN}`
- JOB: `{BASE_JOB}`
- ARTIFACT: `{BASE_ARTIFACT_ID}` (`{BASE_ARTIFACT_NAME}`)
- ARTIFACT_DIGEST: `{BASE_ARTIFACT_DIGEST}`
- Forge: `{FORGE_PIN}`

## Required integrator action

Fix the shared SVar implementation-target inference, rebuild and qualify a new common WS33
parallel base, then restart/rebase all affected children from that same exact corrected base.
Do not patch the ten paths only inside WS33B.
"""
    (out / "WS33B_HANDOFF.md").write_text(handoff, encoding="utf-8")

    print("WS33B_FRONTIER=PASS")
    print(f"WS33B_ASSIGNED_PATHS={len(frontier)}")
    print(f"WS33B_COST_PATHS={target_counts['forge.game.cost.Cost']}")
    print(f"WS33B_AMOUNT_PATHS={target_counts['forge.game.ability.AbilityUtils#calculateAmount']}")
    print(f"WS33B_SHARED_MODEL_MISCLASSIFIED_PATHS={len(verified)}")
    print("CROSS_SHARD_SHARED_BLOCKER=TRUE")
    print("WS33B_CHILD_COMPLETE=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
