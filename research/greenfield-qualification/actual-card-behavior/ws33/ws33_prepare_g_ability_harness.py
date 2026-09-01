#!/usr/bin/env python3
"""Prepare a fail-closed Generation-2 direct-ABILITY G harness.

Historical WS31 contributes scenario/case infrastructure only. The historical direct
SpellAbility.resolve() shortcut and manual target injection are explicitly removed.
The prepared harness uses Forge's own SpellAbility.setupTargets() traversal, admits the
actual parsed ability through MagicStack.addAndUnfreeze(), and resolves through
MagicStack.resolveStack(). Every case records explicit stack-admission and completed-
resolution evidence; a silent MagicStack target rejection therefore cannot become PASS.
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

    # Historical WS31 manually scanned GameObjects and injected a target.  Gen2 must
    # instead use the production SpellAbility target-setup traversal, so GameObject is
    # no longer required by the generated harness.
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

    # The semantic-state observer can fire while Forge is legitimately resolving an
    # unrelated production stack entry.  Starting the campaign there made every case
    # fail the strict pre-admission gate even though the campaign had not touched the
    # stack.  Defer campaign start until Forge itself reaches a quiescent checkpoint;
    # never clear, thaw, or resolve the pre-existing stack from qualification code.
    old_ready = 'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4)return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;return true;}'
    new_ready = 'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4)return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;if(!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving())return false;return true;}'
    s = replace_once(s, old_ready, new_ready, "production-quiescent campaign entry")

    old_evidence = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta;'
    new_evidence = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions;'
    s = replace_once(s, old_evidence, new_evidence, "stack evidence fields")

    old_resolution = 'bindTarget(sa,game,actor,opponent);ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);sa.resolve();game.getAction().checkStateEffects(true);'
    new_resolution = (
        'bindTargets(sa);'
        'if(!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving())'
        'throw new IllegalStateException("non-quiescent stack before exact path");'
        'ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);'
        'game.getStack().addAndUnfreeze(sa);'
        'if(game.getStack().isEmpty())throw new IllegalStateException("MagicStack admission failed for exact path");'
        'ce.stackAdmissions++;int stackSteps=0;'
        'while(!game.getStack().isEmpty()){if(++stackSteps>256)throw new IllegalStateException("stack did not quiesce after exact path");game.getStack().resolveStack();}'
        'if(game.getStack().isFrozen()||game.getStack().isResolving())throw new IllegalStateException("stack remained non-quiescent after exact path");'
        'ce.stackResolutions++;game.getAction().checkStateEffects(true);'
    )
    s = replace_once(s, old_resolution, new_resolution, "production stack resolution")

    old_target = 'private static void bindTarget(SpellAbility sa,Game game,Player actor,Player opponent){if(!sa.usesTargeting())return;List<GameObject>candidates=new ArrayList<>();candidates.add(opponent);candidates.add(actor);for(Player p:game.getPlayers())if(!candidates.contains(p))candidates.add(p);for(Card c:game.getCardsInGame())candidates.add(c);for(GameObject c:candidates){try{if(sa.canTarget(c)){sa.getTargets().add(c);return;}}catch(RuntimeException ignored){}}throw new IllegalStateException("no legal target available for exact path");}'
    new_target = 'private static void bindTargets(SpellAbility sa){for(SpellAbility cur=sa;cur!=null;cur=cur.getSubAbility())if(!cur.getTargets().isEmpty())throw new IllegalStateException("pre-populated targets forbidden");if(!sa.setupTargets())throw new IllegalStateException("Forge SpellAbility.setupTargets rejected exact path");for(SpellAbility cur=sa;cur!=null;cur=cur.getSubAbility())if(cur.usesTargeting()&&!cur.isTargetNumberValid())throw new IllegalStateException("Forge target count invalid after SpellAbility.setupTargets");}'
    s = replace_once(s, old_target, new_target, "authoritative recursive target setup")

    old_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState)))'
    new_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState),Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions)))'
    s = replace_once(s, old_summary, new_summary, "case-summary stack evidence")

    s = s.replace("Ws31HiddenRngReplayQualificationTest", "Ws33GAbilityQualificationTest")
    s = s.replace("WS31 exact-path hidden/RNG/replay qualification campaign.", "WS33 Gen2 direct-ABILITY hidden/RNG/replay diagnostic campaign.")
    s = s.replace("WS31 has no explicit qualification policy", "WS33 G-ABILITY has no explicit qualification policy")
    s = s.replace("WS31 campaign", "WS33 G-ABILITY campaign")

    require("sa.resolve()" not in s, "direct SpellAbility.resolve remains")
    require("getStack().add(sa)" not in s, "raw MagicStack.add remains")
    require("getStack().addAndUnfreeze(sa)" in s and "getStack().resolveStack()" in s, "production MagicStack route missing")
    require("sa.getTargets().add(" not in s, "manual target injection remains")
    require("sa.setupTargets()" in s, "Forge recursive target-setup boundary missing")
    require("chooseTargetsFor(sa)" not in s, "root-only target helper remains")
    require("stackAdmissions" in s and "stackResolutions" in s, "stack admission/resolution evidence missing")
    require("!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving()" in s, "production-quiescent campaign gate missing")
    require("import forge.game.GameObject;" not in s, "obsolete target-search import remains")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(s, encoding="utf-8")
    print("WS33_G_ABILITY_HARNESS_PREP=PASS cases=28 direct_resolution=0 manual_target_injection=0 target_setup=SpellAbility.setupTargets stack_entry=MagicStack.addAndUnfreeze stack_resolution=MagicStack.resolveStack admission_gate=STRICT campaign_entry=PRODUCTION_QUIESCENT")

if __name__ == "__main__":
    main()
