#!/usr/bin/env python3
"""Prepare a Generation-2-admissible direct-ABILITY subset of the historical WS31 harness.

Historical WS31 contributes scenario/case infrastructure only. The historical direct
SpellAbility.resolve() shortcut and manual target injection are explicitly removed.
The prepared harness routes the actual parsed ability through MagicStack and delegates
target legality/selection to the Forge controller/WS01 external decision boundary.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_G_ABILITY_HARNESS_PREP=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    s = args.source.read_text(encoding="utf-8")

    # The historical target helper used GameObject for test-side target search. Gen2
    # removes that helper entirely and delegates target legality/selection to Forge,
    # so keeping the import makes the generated Java fail the pinned checkstyle gate.
    s = replace_once(s, "import forge.game.GameObject;\n", "", "obsolete GameObject import")
    s = replace_once(
        s,
        'if(cases.size()!=81)throw new IllegalStateException("WS31 expected 81 cases, got "+cases.size());',
        'if(cases.size()!=28)throw new IllegalStateException("WS33 G-ABILITY expected 28 cases, got "+cases.size());',
        "case cardinality",
    )
    s = replace_once(
        s,
        'Card source=addCard(spec.cardName,actor,ZoneType.Battlefield);',
        'Card source=addCard(spec.cardName,actor,"SP$".equals(spec.sourceToken)?ZoneType.Hand:ZoneType.Battlefield);',
        "source zone",
    )
    s = replace_once(
        s,
        'bindTarget(sa,game,actor,opponent);ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);sa.resolve();game.getAction().checkStateEffects(true);',
        'bindTarget(sa,actor);ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);game.getStack().add(sa);while(!game.getStack().isEmpty())game.getStack().resolveStack();game.getAction().checkStateEffects(true);',
        "stack resolution",
    )
    old_target = 'private static void bindTarget(SpellAbility sa,Game game,Player actor,Player opponent){if(!sa.usesTargeting())return;List<GameObject>candidates=new ArrayList<>();candidates.add(opponent);candidates.add(actor);for(Player p:game.getPlayers())if(!candidates.contains(p))candidates.add(p);for(Card c:game.getCardsInGame())candidates.add(c);for(GameObject c:candidates){try{if(sa.canTarget(c)){sa.getTargets().add(c);return;}}catch(RuntimeException ignored){}}throw new IllegalStateException("no legal target available for exact path");}'
    new_target = 'private static void bindTarget(SpellAbility sa,Player actor){if(!sa.usesTargeting())return;if(!sa.getTargets().isEmpty())throw new IllegalStateException("pre-populated targets forbidden");if(!actor.getController().chooseTargetsFor(sa))throw new IllegalStateException("Forge authoritative target selection rejected");if(!sa.isTargetNumberValid())throw new IllegalStateException("Forge target count invalid after authoritative selection");}'
    s = replace_once(s, old_target, new_target, "authoritative target boundary")

    s = s.replace("Ws31HiddenRngReplayQualificationTest", "Ws33GAbilityQualificationTest")
    s = s.replace("WS31 exact-path hidden/RNG/replay qualification campaign.", "WS33 Gen2 direct-ABILITY hidden/RNG/replay diagnostic campaign.")
    s = s.replace("WS31 has no explicit qualification policy", "WS33 G-ABILITY has no explicit qualification policy")
    s = s.replace("WS31 campaign", "WS33 G-ABILITY campaign")

    require("sa.resolve()" not in s, "direct SpellAbility.resolve remains")
    require("getStack().add(sa)" in s and "getStack().resolveStack()" in s, "MagicStack route missing")
    require("sa.getTargets().add(" not in s, "manual target injection remains")
    require("actor.getController().chooseTargetsFor(sa)" in s, "Forge controller target boundary missing")
    require("import forge.game.GameObject;" not in s, "obsolete target-search import remains")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(s, encoding="utf-8")
    print("WS33_G_ABILITY_HARNESS_PREP=PASS cases=28 direct_resolution=0 manual_target_injection=0 target_authority=FORGE_CONTROLLER stack=MagicStack")

if __name__ == "__main__":
    main()
