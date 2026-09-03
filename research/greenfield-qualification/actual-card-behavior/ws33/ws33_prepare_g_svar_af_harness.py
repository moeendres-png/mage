#!/usr/bin/env python3
"""Adapt the stack-qualified Direct-G harness for the 21 source-proven SVar AF parents.

The SVar campaign preserves two independent identities that the historical 15-column
ABI did not carry: the source-proven parent and the target SVar. ABILITY parents are bound
to an already materialized root SpellAbility on the actual Card. SVAR parents are built by
name through AbilityFactory with the actual CardState as SVar holder. The target SVar is
never entered directly; an observation-only AbilitySub resolution hook proves that the
production parent actually reaches the modeled target during stack resolution.

Modal Charm parents traverse Forge's own pre-stack CharmEffect.makeChoices phase. The
qualification pilot never chains a mode and never derives legality. It identifies the
mode corresponding to the modeled target from the actual parsed parent, then accepts that
mode only when Forge exposes the same opaque AbilitySub identity in the authoritative
MODE_SELECTION request. If Forge filters it out, qualification fails closed.

Forge CharmEffect.chainAbilities clones a chosen mode and, only when absent, adds the
presentation-only map parameter StackDescription=SpellDescription. Runtime target
observation therefore permits exactly that documented clone delta for Charm parents and
keeps exact map equality for every other case. No subset/broad parameter matching is used.
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

    s = replace_once(
        s,
        '    private static final String SECRET = "Black Lotus";\n',
        '    private static final String SECRET = "Black Lotus";\n    private static final Map<String,CaseSpec> ws33CaseSpecs=new ConcurrentHashMap<>();\n    private static final Map<String,String> ws33DesiredModeSemantic=new ConcurrentHashMap<>();\n',
        "path-spec and desired-mode registries",
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

    s = replace_once(
        s,
        'private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath){List<Player>ps=players(game);',
        'private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath){ws33CaseSpecs.clear();for(CaseSpec c:cases)ws33CaseSpecs.put(c.pathId,c);List<Player>ps=players(game);',
        "path-spec registry initialization",
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
        'private static boolean matchesTarget(CaseSpec spec,AbilitySub sub){if(sub.getApi()==null||!spec.targetDispatch.equals(sub.getApi().name()))return false;Map<String,String>expected=AbilityFactory.getMapParams(spec.targetScript);Map<String,String>actual=new LinkedHashMap<>(sub.getMapParams());if(expected.equals(actual))return true;if(!"Charm".equals(spec.dispatch)||expected.containsKey("StackDescription"))return false;if(!"SpellDescription".equals(actual.get("StackDescription")))return false;actual.remove("StackDescription");return expected.equals(actual);}\n    '
        'private static String desiredTargetModeSemantic(CaseSpec spec,SpellAbility sa){AbilitySub match=null;int matches=0;for(AbilitySub candidate:sa.getAdditionalAbilityList("Choices"))if(matchesTarget(spec,candidate)){match=candidate;matches++;}if(matches!=1)throw new IllegalStateException("actual parsed Charm target-mode match count="+matches+" for "+spec.pathId);return "ability_sub:"+match.getId();}\n    '
        'private static void prepareSourceParentChoices(CaseSpec spec,SpellAbility sa){if(!"Charm".equals(spec.dispatch))return;String desired=desiredTargetModeSemantic(spec,sa);ws33DesiredModeSemantic.put(spec.pathId,desired);try{if(!CharmEffect.makeChoices(sa))throw new IllegalStateException("Forge CharmEffect.makeChoices rejected source-proven parent for "+spec.pathId);}finally{ws33DesiredModeSemantic.remove(spec.pathId);}}\n    '
    )
    s = replace_once(s, helper_anchor, helper + helper_anchor, "source-parent, choice, and target observer helpers")

    provider_anchor = 'private static void selectByPathPolicy(ExternalDecisionRequest req,String path,List<String>selected,boolean exerciseOptional){List<ExternalDecisionRequest.Option>options=new ArrayList<>(req.getOptions());'
    provider_replacement = (
        'private static void selectByPathPolicy(ExternalDecisionRequest req,String path,List<String>selected,boolean exerciseOptional){List<ExternalDecisionRequest.Option>options=new ArrayList<>(req.getOptions());'
        'CaseSpec pathSpec=ws33CaseSpecs.get(path);'
        'if(pathSpec!=null&&"MODE_SELECTION".equals(req.getDecisionKind())&&"Charm".equals(pathSpec.dispatch)){String desired=ws33DesiredModeSemantic.get(path);if(desired==null)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"missing source-proven desired mode identity for "+path);ExternalDecisionRequest.Option match=null;int matches=0;for(ExternalDecisionRequest.Option o:options)if(desired.equals(o.getSemanticValue())){match=o;matches++;}if(matches!=1)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"source-proven target mode identity not uniquely present in authoritative option set for "+path);selected.add(match.getOptionId());return;}'
        'if(pathSpec!=null&&"GUI_ONE".equals(req.getDecisionKind())&&"ChooseType".equals(pathSpec.dispatch)){for(ExternalDecisionRequest.Option o:options)if("Bear".equals(o.getSemanticValue())){selected.add(o.getOptionId());return;}throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"generic fixture creature type Bear is not in authoritative option set for "+path);}'
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
        'PlayerControllerHuman.setExternalDecisionProviderFactory(null);ws33CaseSpecs.clear();ws33DesiredModeSemantic.clear();AbilitySub.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);',
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
        "desiredTargetModeSemantic(spec,sa)",
        "ws33DesiredModeSemantic",
        "ws33CaseSpecs",
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
    if "options.get(ordinal)" in s or "targetModeOrdinal" in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL raw Choice ordinal selection remains")
    if 'desired.equals(o.getSemanticValue())' not in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL authoritative desired-mode membership check missing")

    # Fail-closed observer regression: the only tolerated runtime map delta is exactly
    # CharmEffect.chainAbilities' StackDescription=SpellDescription insertion. Any broad
    # subset/contains-all matching would be capable of hiding a different consumer.
    required_observer_contract = (
        'if(expected.equals(actual))return true;',
        'if(!"Charm".equals(spec.dispatch)||expected.containsKey("StackDescription"))return false;',
        'if(!"SpellDescription".equals(actual.get("StackDescription")))return false;',
        'actual.remove("StackDescription");return expected.equals(actual);',
    )
    if not all(token in s for token in required_observer_contract):
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL exact Charm clone observer normalization missing")
    for forbidden in ("containsAll(expected", "containsAll(actual", "entrySet().containsAll", "keySet().containsAll"):
        if forbidden in s:
            raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL broad target observer matching forbidden")

    args.harness.write_text(s, encoding="utf-8")
    print(
        "WS33_G_SVAR_AF_HARNESS=PASS paths=21 parent_entry=ACTUAL_CARD_OR_NAMED_PARENT_SVAR "
        "parent_pre_stack_choices=FORGE_PRODUCTION mode_selection=AUTHORITATIVE_ID_MEMBERSHIP "
        "target_svar_direct_entry=FALSE target_runtime_observer=ABILITY_SUB_RESOLUTION "
        "charm_clone_normalization=STACK_DESCRIPTION_ONLY"
    )


if __name__ == "__main__":
    main()
