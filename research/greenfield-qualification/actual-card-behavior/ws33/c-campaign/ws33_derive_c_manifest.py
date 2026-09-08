#!/usr/bin/env python3
"""Derive the deterministic branch-owned WS33-C UNKNOWN manifest and cluster queue.

Reads only canonical inputs (effective manifest, path coverage, scenario
registry, integrated ledger) and writes branch-owned artifacts under
research/greenfield-qualification/actual-card-behavior/ws33/c-campaign/.

No canonical coverage file is mutated.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

C_TARGETS = (
    "forge.game.spellability.AbilitySub",
    "forge.game.spellability.SpellApiBased",
    "forge.game.spellability.AbilityApiBased",
)
# Actual runtime packages at FORGE_PIN 8c7e9afb8e6caee88644b94e25da5852e36f8928.
ACTUAL_RUNTIME = {
    "forge.game.spellability.AbilitySub": "forge.game.spellability.AbilitySub",
    "forge.game.spellability.SpellApiBased": "forge.game.ability.SpellApiBased",
    "forge.game.spellability.AbilityApiBased": "forge.game.ability.AbilityApiBased",
}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def canon(o) -> bytes:
    return (json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    root = args.root
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    manifest = load(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    coverage = load(root / "WS33_PATH_COVERAGE.json")
    scenarios = load(root / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")
    assert manifest["forge_pin"] == "8c7e9afb8e6caee88644b94e25da5852e36f8928"

    cov_by = {r["effective_v2_path_id"]: r for r in coverage["paths"]}
    t_by_path: dict[str, dict] = {}
    for t in scenarios["templates"]:
        for pid in t["path_ids"]:
            assert pid not in t_by_path, f"duplicate scenario membership {pid}"
            t_by_path[pid] = t

    rows = []
    for p in manifest["paths"]:
        if p["implementation_target"] not in C_TARGETS:
            continue
        pid = p["v2_path_id"]
        cb = cov_by[pid]
        assert cb["status"] == "UNKNOWN", f"C path not UNKNOWN: {pid}"
        t = t_by_path[pid]
        rows.append({
            "effective_v2_path_id": pid,
            "implementation_target": p["implementation_target"],
            "actual_runtime_class": ACTUAL_RUNTIME[p["implementation_target"]],
            "target_attribution_defect": (
                p["implementation_target"] != ACTUAL_RUNTIME[p["implementation_target"]]
            ),
            "dispatch_domain": p["dispatch_domain"],
            "dispatch_token": p["dispatch_token"],
            "semantic_selector_profile": p["semantic_selector_profile"],
            "owner_family": p["owner_family"],
            "scenario_group_id": t["template_id"],
            "evidence_profile": t["evidence_profile"],
            "required_evidence_dimensions": ["STATE"]
            + (["DECISION"] if p["required_decision_evidence"] else [])
            + (["HIDDEN_INFO"] if p["required_hidden_info_evidence"] else [])
            + (["RNG"] if p["required_rng_evidence"] else [])
            + (["SEMANTIC_REPLAY"] if p["required_replay_evidence"] else []),
            "requires_decision": bool(p["required_decision_evidence"]),
            "requires_hidden": bool(p["required_hidden_info_evidence"]),
            "requires_replay": bool(p["required_replay_evidence"]),
            "requires_rng": bool(p["required_rng_evidence"]),
            "source_provenance": sorted(
                p["source_provenance"],
                key=lambda q: (q["forge_source_path"], q["source_line"], q["oracle_identity"]),
            ),
            "source_occurrence_count": p["source_occurrence_count"],
            "representative_actual_oracle_identities": sorted(
                p.get("representative_actual_oracle_identities", [])
            ),
            "parent_ws14_primitive_id": p["parent_ws14_primitive_id"],
            "model_origin": p["model_origin"],
        })
    rows.sort(key=lambda r: r["effective_v2_path_id"])
    assert len(rows) == 700, f"expected 700 C UNKNOWN, got {len(rows)}"

    (out / "WS33_C_UNKNOWN_MANIFEST.json").write_bytes(canon({
        "schema": "commander-simulator-next.ws33-c-unknown-manifest.v1",
        "audit_base_sha": "895240f4058076764227a418ad28e84f61d3a7ed",
        "audit_base_tree": "cec73ae51b0168280ea648892f3e9edd46dcd883",
        "forge_pin": "8c7e9afb8e6caee88644b94e25da5852e36f8928",
        "owned_path_count": len(rows),
        "dispatch_time_unknown": 700,
        "discrepancy": 0,
        "paths": rows,
    }))

    clusters: dict[tuple, list] = collections.defaultdict(list)
    for r in rows:
        clusters[(
            r["implementation_target"], r["scenario_group_id"], r["evidence_profile"],
        )].append(r["effective_v2_path_id"])
    items = []
    for (target, group, prof), ids in clusters.items():
        ids = sorted(ids)
        state_only = sum(1 for r in rows if r["effective_v2_path_id"] in set(ids)
                         and not (r["requires_decision"] or r["requires_hidden"]
                                  or r["requires_replay"] or r["requires_rng"]))
        items.append({
            "implementation_target": target,
            "actual_runtime_class": ACTUAL_RUNTIME[target],
            "scenario_group_id": group,
            "evidence_profile": prof,
            "unresolved_path_count": len(ids),
            "state_only_path_count": state_only,
            "effective_path_ids": ids,
        })
    # Rank: STATE_ONLY clusters first (cheapest gates), then by count desc.
    items.sort(key=lambda it: (
        0 if it["evidence_profile"] == "STATE_ONLY" else 1,
        -it["unresolved_path_count"], it["implementation_target"], it["scenario_group_id"],
    ))
    for rank, it in enumerate(items, 1):
        it["rank"] = rank
    (out / "WS33_C_CLUSTER_QUEUE.json").write_bytes(canon({
        "schema": "commander-simulator-next.ws33-c-cluster-queue.v1",
        "owned_path_count": len(rows),
        "cluster_count": len(items),
        "priority_basis": "STATE_ONLY_FIRST_THEN_DESCENDING_COUNT_THEN_STABLE_KEYS",
        "items": items,
    }))
    by_target = collections.Counter(r["implementation_target"] for r in rows)
    by_prof = collections.Counter(r["evidence_profile"] for r in rows)
    print(json.dumps({
        "WS33_C_UNKNOWN": len(rows),
        "DISCREPANCY_VS_DISPATCH_700": len(rows) - 700,
        "BY_TARGET": dict(sorted(by_target.items())),
        "BY_PROFILE": dict(sorted(by_prof.items())),
        "CLUSTERS": len(items),
        "RANK1": {k: items[0][k] for k in (
            "rank", "implementation_target", "scenario_group_id",
            "evidence_profile", "unresolved_path_count")},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
