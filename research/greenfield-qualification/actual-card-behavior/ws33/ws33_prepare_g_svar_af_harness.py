#!/usr/bin/env python3
"""Adapt the stack-qualified Direct-G harness for the 21 source-proven SVar AF parents.

The SVar campaign must preserve two independent identities that the historical 15-column
ABI did not carry: the source-proven parent and the target SVar. ABILITY parents are bound
to an already materialized root SpellAbility on the actual Card. SVAR parents are built by
name through AbilityFactory with the actual CardState as SVar holder. The target SVar is
never entered directly; an observation-only AbilitySub resolution hook proves that the
production parent actually reaches the modeled target during stack resolution.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_G_SVAR_AF_HARNESS=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    s = args.harness.read_text(encoding="utf-8")

    s = replace_once(
        s,
        'if(cases.size()!=28)throw new IllegalStateException("WS33 G-ABILITY expected 28 cases, got "+cases.size());',
        'if(cases.size()!=21)throw new IllegalStateException("WS33 G-SVAR-AF expected 21 cases, got "+cases.size());',
        "case cardinality",
    )
    s = s.replace("Ws33GAbilityQualificationTest", "Ws33GSVarAfQualificationTest")
    s = s.replace("WS33 G-ABILITY", "WS33 G-SVAR-AF")

    s = replace_once(
        s,
        "import forge.game.spellability.SpellAbility;\n",
        "import forge.game.spellability.AbilitySub;\nimport forge.game.spellability.SpellAbility;\n",
        "AbilitySub observation import",
    )

    old_case = 'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);}'
    new_case = 'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script,parentSVar,targetSVar,targetDispatch,targetScript; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){if(f.length!=19)throw new IllegalArgumentException("WS33 G-SVAR-AF expected 19 case fields, got "+f.length);ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);parentSVar=f[15];targetSVar=f[16];targetDispatch=f[17];targetScript=new String(Base64.getDecoder().decode(f[18]),StandardCharsets.UTF_8);}'
    s = replace_once(s, old_case, new_case, "case parent/target identity ABI")

    old_evidence = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions;'
    new_evidence = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions,targetExecutions;'
    s = replace_once(s, old_evidence, new_evidence, "target execution evidence field")

    s = replace_once(
        s,
        'SpellAbility sa=AbilityFactory.getAbility(spec.script,source);',
        'SpellAbility sa=resolveSourceParent(spec,source);',
        "actual source-parent binding",
    )

    helper_anchor = 'private static void awaitRemoteTransport(List<Player> ps){'
    helper = (
        'private static SpellAbility resolveSourceParent(CaseSpec spec,Card source){'
        'if("ABILITY".equals(spec.sourceDirective)){Map<String,String>expected=AbilityFactory.getMapParams(spec.script);SpellAbility match=null;int matches=0;'
        'for(SpellAbility candidate:source.getSpellAbilities())if(expected.equals(candidate.getMapParams())){match=candidate;matches++;}'
        'if(matches!=1)throw new IllegalStateException("actual-card root parent match count="+matches+" for "+spec.pathId);return match;}'
        'if("SVAR".equals(spec.sourceDirective)){if(spec.parentSVar.isEmpty()||!source.getCurrentState().hasSVar(spec.parentSVar))throw new IllegalStateException("actual card missing source-proven parent SVar "+spec.parentSVar+" for "+spec.pathId);'
        'String actual=source.getCurrentState().getSVar(spec.parentSVar);if(!spec.script.equals(actual))throw new IllegalStateException("source-proven parent SVar script mismatch for "+spec.pathId);'
        'return AbilityFactory.getAbility(source,spec.parentSVar,source.getCurrentState());}'
        'throw new IllegalStateException("unsupported source parent directive "+spec.sourceDirective+" for "+spec.pathId);}\n    '
        'private static boolean matchesTarget(CaseSpec spec,AbilitySub sub){return sub.getApi()!=null&&spec.targetDispatch.equals(sub.getApi().name())&&AbilityFactory.getMapParams(spec.targetScript).equals(sub.getMapParams());}\n    '
    )
    s = replace_once(s, helper_anchor, helper + helper_anchor, "source-parent and target observer helpers")

    s = replace_once(
        s,
        'ExternalDecisionTape.setEventObserver(event->{',
        'AbilitySub.setWs33ResolutionObserver(sub->{String p=currentPath.get();if(p!=null){CaseEvidence ce=evidence.get(p);if(ce!=null&&matchesTarget(ce.spec,sub))ce.targetExecutions++;}});ExternalDecisionTape.setEventObserver(event->{',
        "target SVar resolution observer registration",
    )
    s = replace_once(
        s,
        'PlayerControllerHuman.setExternalDecisionProviderFactory(null);ExternalDecisionTape.setEventObserver(null);',
        'PlayerControllerHuman.setExternalDecisionProviderFactory(null);AbilitySub.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);',
        "target SVar resolution observer cleanup",
    )

    old_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState),Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions)))'
    new_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState),Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions),Long.toString(e.targetExecutions)))'
    s = replace_once(s, old_summary, new_summary, "target execution summary evidence")

    if "sa.resolve()" in s or "sa.getTargets().add(" in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL forbidden direct rules shortcut remains")
    for required in (
        "sa.setupTargets()",
        "getStack().addAndUnfreeze(sa)",
        "getStack().resolveStack()",
        "resolveSourceParent(spec,source)",
        "AbilitySub.setWs33ResolutionObserver",
        "targetExecutions",
    ):
        if required not in s:
            raise SystemExit(f"WS33_G_SVAR_AF_HARNESS=FAIL missing production/evidence route {required}")
    if "AbilityFactory.getAbility(spec.script,source)" in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL detached parent-script reconstruction remains")
    if '"ABILITY".equals(spec.sourceDirective)' not in s or '"SVAR".equals(spec.sourceDirective)' not in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL directive-scoped parent binding missing")

    args.harness.write_text(s, encoding="utf-8")
    print(
        "WS33_G_SVAR_AF_HARNESS=PASS paths=21 parent_entry=ACTUAL_CARD_OR_NAMED_PARENT_SVAR "
        "target_svar_direct_entry=FALSE target_runtime_observer=ABILITY_SUB_RESOLUTION"
    )


if __name__ == "__main__":
    main()
