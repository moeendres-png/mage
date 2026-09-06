#!/usr/bin/env python3
"""Repair the inherited WS31 evidence-only CaseSpec ABI for A-rest Direct31.

The A-rest 19-column topology TSV intentionally omits the historical implementation
column because every A-rest path is already constrained by the immutable integrated
queue to forge.game.spellability.TargetRestrictions. The inherited WS31 evidence
serializer still writes CaseSpec.implementation. Restore that metadata field without
altering any rule, target, cost, decision, RNG, stack, or semantic behavior.
"""
from __future__ import annotations

import argparse
from pathlib import Path

IMPLEMENTATION = "forge.game.spellability.TargetRestrictions"


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_A_REST_DIRECT_CASE_ABI=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    text = args.harness.read_text(encoding="utf-8")

    old_fields = (
        "final int ordinal; final String pathId,oracleId,cardName,scenarioGroup,evidenceProfile,"
        "abilityKind,dispatch,sourcePath,script,validTgts,origin,destination,costShape; "
        "final int sourceLine; final boolean decision,rng,hidden,replay;"
    )
    new_fields = (
        "final int ordinal; final String pathId,oracleId,cardName,scenarioGroup,evidenceProfile,"
        "abilityKind,dispatch,sourcePath,script,validTgts,origin,destination,costShape,implementation; "
        "final int sourceLine; final boolean decision,rng,hidden,replay;"
    )
    text = replace_once(text, old_fields, new_fields, "CaseSpec evidence field")

    old_ctor_tail = (
        'costShape=f[14];decision="1".equals(f[15]);rng="1".equals(f[16]);'
        'hidden="1".equals(f[17]);replay="1".equals(f[18]);}'
    )
    new_ctor_tail = (
        'costShape=f[14];decision="1".equals(f[15]);rng="1".equals(f[16]);'
        'hidden="1".equals(f[17]);replay="1".equals(f[18]);'
        f'implementation="{IMPLEMENTATION}";}}'
    )
    text = replace_once(text, old_ctor_tail, new_ctor_tail, "CaseSpec evidence constructor")

    require(text.count("c.implementation") == 1, "inherited evidence serializer shape changed")
    require(f'implementation="{IMPLEMENTATION}"' in text, "implementation evidence value missing")
    require("PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa)" in text, "production PlaySpellAbility route missing")
    require("MagicStack.setWs33ResolutionObserver" in text, "stack-resolution observer missing")
    require("sa.resolve()" not in text, "direct resolve shortcut present")
    require("sa.getTargets().add(" not in text, "manual target injection present")
    require("AbilityFactory.getAbility(spec.script,source)" not in text, "detached source reconstruction present")

    args.harness.write_text(text, encoding="utf-8")
    print("WS33_A_REST_DIRECT_CASE_ABI=PASS")
    print(f"WS33_A_REST_DIRECT_IMPLEMENTATION={IMPLEMENTATION}")
    print("WS33_A_REST_DIRECT_CASE_ABI_RULES_MUTATION=0")


if __name__ == "__main__":
    main()
