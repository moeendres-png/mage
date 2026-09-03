#!/usr/bin/env python3
"""Adapt the stack-qualified Direct-G harness for the 21 source-proven SVar AF parents.

The SVar campaign must preserve two independent identities that the historical 15-column
ABI did not carry: the source-proven parent and the target SVar. ABILITY parents are bound
to an already materialized root SpellAbility on the actual Card. SVAR parents are built by
name through AbilityFactory with the actual CardState as SVar holder. The target SVar is
never entered directly; an observation-only AbilitySub resolution hook proves that the
production parent actually reaches the modeled target during stack resolution.

Modal Charm parents must traverse Forge's own pre-stack CharmEffect.makeChoices phase;
qualification code never chains a mode itself. The external pilot remains restricted to
the authoritative option set. For the generic ChooseType reachability fixture, the pilot
selects the actor-visible fixture creature type only when Forge actually offers it.
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
        "import forge.game.ability.effects.CharmEffect;\nimport forge.game.spellability.AbilitySub;\nimport forge.game.spellability.SpellAbility;\n",
        "Charm/AbilitySub observation imports",
    )

    old_case = 'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);}'
    new_case = 'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script,parentSVar,targetSVar,targetDispatch,targetScript; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){if(f.length!=19)throw new IllegalArgumentException("WS33 G-SVAR-AF expected 19 case fields, got "+f.length);ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);parentSVar=f[15];targetSVar=f[16];targetDispatch=f[17];targetScript=new String(Base64.getDecoder().decode(f[18]),StandardCharsets.UTF_8);}'
    s = replace_once(s, old_case, new_case, "case parent/target identity ABI")

    s = replace_once(
        s,
        'if(f.length!=15)throw new IllegalArgumentException("bad case TSV fields="+f.length);',
        'if(f.length!=19)throw new IllegalArgumentException("bad case TSV fields="+f.length);',
        "case TSV loader ABI",
    )

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
        'private static int targetModeOrdinal(CaseSpec spec){String choices=AbilityFactory.getMapParams(spec.script).get("Choices");if(choices==null)return -1;String[]names=choices.split(",");int found=-1;for(int i=0;i<names.length;i++)if(spec.targetSVar.equals(names[i].trim())){if(found>=0)throw new IllegalStateException("duplicate target SVar in Choices for "+spec.pathId);found=i;}return found;}\n    '
        'private static void prepareSourceParentChoices(CaseSpec spec,SpellAbility sa){if(!"Charm".equals(spec.dispatch))return;int ordinal=targetModeOrdinal(spec);if(ordinal<0)throw new IllegalStateException("Charm target SVar absent from source-proven Choices for "+spec.pathId);if(!CharmEffect.makeChoices(sa))throw new IllegalStateException("Forge CharmEffect.makeChoices rejected source-proven parent for "+spec.pathId);}\n    '
        'private static boolean matchesTarget(CaseSpec spec,AbilitySub sub){return sub.getApi()!=null&&spec.targetDispatch.equals(sub.getApi().name())&&AbilityFactory.getMapParams(spec.targetScript).equals(sub.getMapParams());}\n    '
    )
    s = replace_once(s, helper_anchor, helper + helper_anchor, "source-parent, choice, and target observer helpers")

    provider_anchor = 'private static void selectByPathPolicy(ExternalDecisionRequest req,String path,List<String>selected,boolean exerciseOptional){List<ExternalDecisionRequest.Option>options=new ArrayList<>(req.getOptions());'
    provider_replacement = (
        'private static void selectByPathPolicy(ExternalDecisionRequest req,String path,List<String>selected,boolean exerciseOptional){List<ExternalDecisionRequest.Option>options=new ArrayList<>(req.getOptions());'
        'CaseEvidence pathEvidence=evidence.get(path);'
        'if(pathEvidence!=null&&"MODE_SELECTION".equals(req.getDecisionKind())&&"Charm".equals(pathEvidence.spec.dispatch)){int ordinal=targetModeOrdinal(pathEvidence.spec);if(ordinal<0||ordinal>=options.size())throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"source-proven target mode is not in authoritative option set for "+path);selected.add(options.get(ordinal).getOptionId());return;}'
        'if(pathEvidence!=null&&"GUI_ONE".equals(req.getDecisionKind())&&"ChooseType".equals(pathEvidence.spec.dispatch)){for(ExternalDecisionRequest.Option o:options)if("Bear".equals(o.getSemanticValue())){selected.add(o.getOptionId());return;}throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"generic fixture creature type Bear is not in authoritative option set for "+path);}'
    )
    s = replace_once(s, provider_anchor, provider_replacement, "authoritative reachability pilot choices")

    s = replace_once(
        s,
        'currentPath.set(spec.pathId);bindTargets(sa);',
        'currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);',
        "production parent choice phase before target setup",
    )

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
        "prepareSourceParentChoices(spec,sa)",
        "CharmEffect.makeChoices(sa)",
        "AbilitySub.setWs33ResolutionObserver",
        "targetExecutions",
    ):
        if required not in s:
            raise SystemExit(f"WS33_G_SVAR_AF_HARNESS=FAIL missing production/evidence route {required}")
    if "AbilityFactory.getAbility(spec.script,source)" in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL detached parent-script reconstruction remains")
    if '"ABILITY".equals(spec.sourceDirective)' not in s or '"SVAR".equals(spec.sourceDirective)' not in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL directive-scoped parent binding missing")
    if '"Bear".equals(o.getSemanticValue())' not in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL authoritative fixture type selection missing")

    args.harness.write_text(s, encoding="utf-8")
    print(
        "WS33_G_SVAR_AF_HARNESS=PASS paths=21 parent_entry=ACTUAL_CARD_OR_NAMED_PARENT_SVAR "
        "parent_pre_stack_choices=FORGE_PRODUCTION target_svar_direct_entry=FALSE "
        "target_runtime_observer=ABILITY_SUB_RESOLUTION"
    )


if __name__ == "__main__":
    main()
