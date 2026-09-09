#!/usr/bin/env python3
"""Emit the WS33-C Effect-static candidate inventory (descriptive only).

Covers owned C UNKNOWN template-113 paths whose semantic profile touches
Effect/static execution (StaticAbilities key, Effect/Static value, or a
SubAbility pointer naming an Effect child), plus the Kappa DBUnblockable
sub-link whose profile carries no Effect keyword. Each row carries the
planning classification decided from pinned Forge script inspection.
Creates NO qualification credit and mutates no canonical input.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"

# path_id suffix -> planning record. `fixture`/`observable`/`lifetime` and
# `blocker` were determined by reading the exact pinned card scripts and
# the referenced Forge effect/static classes. `class` uses the campaign
# planning taxonomy.
PLANNING: dict[str, dict] = {
    # Full effective path IDs -> planning record. Fixture/observable/
    # lifetime/deps decided from pinned Forge script + effect/static class
    # inspection (see Batch-4 selection checkpoint for per-row rationale).
    "forge-behavior-v2:634a4b2d09d12a138afd0544c87c7d2bdb57a05a": {
        "class": "ASSERTABLE_WITH_NARROW_C_VOCABULARY",
        "fixture": "ETB_OTHER_ENTER (Sol Ring enters; Kappa pre-placed via move, setup drain)",
        "observable": "Command effect card + CantBlockBy static + source linkage + P1P1==2; EOT absence",
        "lifetime": "end of turn", "deps": "Sol Ring fixture card",
    },
    "forge-behavior-v2:998516b92a13efe9c0e1c324a8123069ab954815": {
        "class": "ASSERTABLE_WITH_NARROW_C_VOCABULARY",
        "fixture": "ETB_SELF terminal (Kappa self-entry) + ETB_OTHER (Gate enters for Sneak)",
        "observable": "Command effect card + CantBlockBy static + source linkage; EOT absence",
        "lifetime": "end of turn", "deps": "Gate card present for Sneak parent",
    },
    "forge-behavior-v2:2dd428f906c3201282d1e251a9daf937f3413b94": {
        "class": "ASSERTABLE_WITH_NARROW_C_VOCABULARY",
        "fixture": "dies via Thunder DamageAll combo (Hildibrand pre-placed via move)",
        "observable": "Command effect card + MayPlay static + source linkage; Hildibrand in graveyard",
        "lifetime": "UntilTheEndOfYourNextTurn (beyond window; rollback generic machinery)",
        "deps": "Thunder as death outlet (own path already evidenced, not claimed)",
    },
    "forge-behavior-v2:03fca07de5a57a26ce4636fffff8b480174714d0": {"class": "TARGET_DECISION_COLLISION", "fixture": "BeginCombat + cast precondition + targeted Effect", "observable": "-", "lifetime": "-", "deps": "target + precondition"},
    "forge-behavior-v2:074fbe89a9554f00e45a37ca1ed764bc9aabcf2b": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP sorcery cast + choices", "observable": "-", "lifetime": "-", "deps": "cast + choices"},
    "forge-behavior-v2:1013e3dad50a6c87a7df23068c79f581371c925c": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP X-cost cast + target", "observable": "-", "lifetime": "-", "deps": "cast + target"},
    "forge-behavior-v2:21428ed65589dd20efdc4ecc78277921fd2df2e7": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP sorcery cast", "observable": "-", "lifetime": "-", "deps": "cast"},
    "forge-behavior-v2:23fec24a2c5571d37360625c22b1e93b5cd97f36": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP X-cost cast + shuffle", "observable": "-", "lifetime": "-", "deps": "cast + shuffle"},
    "forge-behavior-v2:2d98023e593fac933162baf150bc692673b2cacf": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP cast + graveyard target", "observable": "-", "lifetime": "-", "deps": "cast + target"},
    "forge-behavior-v2:3504ec02fe02c571149dae9916c24e78d51b710d": {"class": "HIDDEN_RNG_SEARCH_REVEAL_BLOCKED", "fixture": "Dig hidden + choice chains", "observable": "-", "lifetime": "-", "deps": "decision + hidden"},
    "forge-behavior-v2:3e516567979775af78d45e8986b3ee7008b569b3": {"class": "TARGET_DECISION_COLLISION", "fixture": "discard outlet + Optional + cast-adjacent", "observable": "-", "lifetime": "-", "deps": "decision"},
    "forge-behavior-v2:423ec0926c3d50196b935ec0b353db9e12c68124": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP sorcery cast", "observable": "-", "lifetime": "-", "deps": "cast"},
    "forge-behavior-v2:5c185a692404396b65077f8c84332085dd1bb4d6": {"class": "COMBAT_BLOCKED", "fixture": "combat damage + UnlessCost choice", "observable": "-", "lifetime": "-", "deps": "combat + decision"},
    "forge-behavior-v2:799608d965d62c4b9a25c53a5fa6c4e7eecee0e1": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP instant cast + graveyard target", "observable": "-", "lifetime": "-", "deps": "cast + target"},
    "forge-behavior-v2:8bc1b77cc21a199a1d7d926d91bea3399307f46d": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "AB cost + graveyard target + Optional", "observable": "-", "lifetime": "-", "deps": "cost + target + decision"},
    "forge-behavior-v2:9dc9af50dece9115f35c4a5a98d94db5438441c1": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP Dig cast + hidden + choice", "observable": "-", "lifetime": "-", "deps": "cast + hidden + decision"},
    "forge-behavior-v2:a52050a95a60545646a286c66180843c684c146a": {"class": "TARGET_DECISION_COLLISION", "fixture": "attack trigger + cost + targeted pump", "observable": "-", "lifetime": "-", "deps": "target + cost"},
    "forge-behavior-v2:cf21ffbb2080b78074898e0cff35a9f6575ea370": {"class": "HIDDEN_RNG_SEARCH_REVEAL_BLOCKED", "fixture": "choice + Dig hidden + Optional", "observable": "-", "lifetime": "-", "deps": "decision + hidden"},
    "forge-behavior-v2:d28300b4ffa7a118713e3a919b453fd8d7299d59": {"class": "TARGET_DECISION_COLLISION", "fixture": "MayPlay chains via targeted/cast parents", "observable": "-", "lifetime": "-", "deps": "target"},
    "forge-behavior-v2:deaf32b75e9aa8fcae718ce88bc55b402412ad7e": {"class": "TARGET_DECISION_COLLISION", "fixture": "discard outlet + OptionalDecider", "observable": "-", "lifetime": "-", "deps": "decision"},
    "forge-behavior-v2:e34ebb80e6834718d33988c679c2167c30ac9d30": {"class": "COMBAT_BLOCKED", "fixture": "SpellCast/LandPlayed/DamageDone triggers", "observable": "-", "lifetime": "-", "deps": "cast + combat (no clean trigger)"},
    "forge-behavior-v2:e8e7d68b867d09d1a4e599c0b4ccb15ab4677c2d": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP instant cast + target", "observable": "-", "lifetime": "-", "deps": "cast + target"},
    "forge-behavior-v2:f9da5d307691cfb356e1c6be638d7a5181a6c2d1": {"class": "COST_OWNERSHIP_BLOCKED", "fixture": "SP Dig cast + hidden library manipulation", "observable": "-", "lifetime": "-", "deps": "cast + hidden"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assert manifest["forge_pin"] == FORGE_PIN
    by_id = {r["effective_v2_path_id"]: r for r in manifest["paths"]}
    rows = []
    for pid, plan in sorted(PLANNING.items()):
        assert pid in by_id, f"path not in manifest: {pid}"
        row = by_id[pid]
        assert row["scenario_group_id"] == "ws33-template-113", pid
        prov = row["source_provenance"][0]
        api = None
        rows.append({
            "effective_path_id": pid,
            "template_id": "ws33-template-113",
            "current_state": "UNKNOWN",
            "representative_card": prov["forge_source_path"].split("/")[-1],
            "forge_source_path": prov["forge_source_path"],
            "source_line": prov["source_line"],
            "oracle_identity": prov["oracle_identity"],
            "semantic_selector_profile": row["semantic_selector_profile"],
            "implementation_target": row["implementation_target"],
            "actual_runtime_class": row["implementation_target"],
            "decision_profile": row["requires_decision"],
            "hidden_profile": row["requires_hidden"],
            "rng_profile": row["requires_rng"],
            "replay_requirement": row["requires_replay"],
            "required_evidence_dimensions": row["required_evidence_dimensions"],
            "planning_class": plan["class"],
            "fixture": plan["fixture"],
            "expected_observable": plan["observable"],
            "expected_lifetime": plan["lifetime"],
            "dependencies": plan["deps"],
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"schema": "commander-simulator-next.ws33-c-effect-static-inventory.v1",
                    "forge_pin": FORGE_PIN, "candidate_count": len(rows),
                    "candidates": rows},
                   sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"EFFECT_STATIC_CANDIDATES": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
