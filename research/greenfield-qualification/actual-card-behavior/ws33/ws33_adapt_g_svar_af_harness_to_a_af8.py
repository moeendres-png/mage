#!/usr/bin/env python3
"""Adapt the proven G3 SVar-AF production-parent harness to the exact A-rest AF8 route.

This transform changes qualification cardinality/identity and repairs only two harness
preconditions established by the failed NonTrigger9 run:

1. Forge CharmEffect filters targeted modes against current legal target candidates before
   it emits MODE_SELECTION.  The harness therefore supplies one generic public candidate
   set in public zones before path attribution.  It never decides which candidate is legal.
2. Some real Charm parents require more than one mode.  The pilot always includes the
   source-proven desired mode, then fills only Forge's authoritative minimum cardinality
   from the remaining authoritative option IDs using the existing stable ordering.

No card/path-specific branch, target injection, standalone target-SVar entry, or Rules-Core
mutation is introduced.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_SVAR_AF8_ADAPTER=FAIL " + m)


def replace_once(t: str, old: str, new: str, label: str) -> str:
    n=t.count(old)
    require(n==1, f"{label}: expected one anchor, got {n}")
    return t.replace(old,new,1)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args()
    p=a.harness; t=p.read_text(encoding='utf-8')

    t=replace_once(
        t,
        'if(cases.size()!=21)throw new IllegalStateException("WS33 G-SVAR-AF expected 21 cases, got "+cases.size());',
        'if(cases.size()!=8)throw new IllegalStateException("WS33 A-SVAR-AF8 expected 8 cases, got "+cases.size());',
        'case cardinality')
    t=t.replace('Ws33GSVarAfQualificationTest','Ws33ARestSVarAf8QualificationTest')
    t=t.replace('WS33 G-SVAR-AF','WS33 A-SVAR-AF8')

    # Establish public-zone candidate breadth before evidence attribution.  These fixtures
    # are mechanism-generic: creature, land, instant, sorcery, artifact, and controlled /
    # noncontrolled permanents. Forge TargetRestrictions remains the sole legality judge.
    t=replace_once(
        t,
        'try{seedCommon(game,actor,opponent);',
        'try{seedCommon(game,actor,opponent);prepareAF8PublicCandidates(actor,opponent);',
        'public candidate fixture call')
    helper_anchor='private static void awaitRemoteTransport(List<Player> ps){'
    helper=(
        'private static void prepareAF8PublicCandidates(Player actor,Player opponent){'
        'addCard("Runeclaw Bear",actor,ZoneType.Graveyard);'
        'addCard("Plains",actor,ZoneType.Graveyard);'
        'addCard("Opt",actor,ZoneType.Graveyard);'
        'addCard("Raise Dead",actor,ZoneType.Graveyard);'
        'addCard("Sol Ring",actor,ZoneType.Battlefield);'
        'addCard("Runeclaw Bear",actor,ZoneType.Battlefield);'
        'addCard("Grizzly Bears",opponent,ZoneType.Battlefield);'
        '}\n    '
    )
    t=replace_once(t,helper_anchor,helper+helper_anchor,'public candidate fixture helper')

    old=('if(pathSpec!=null&&"MODE_SELECTION".equals(req.getDecisionKind())&&"Charm".equals(pathSpec.dispatch)){'
         'String desired=ws33DesiredModeSemantic.get(path);if(desired==null)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"missing source-proven desired mode identity for "+path);'
         'ExternalDecisionRequest.Option match=null;int matches=0;for(ExternalDecisionRequest.Option o:options)if(desired.equals(o.getSemanticValue())){match=o;matches++;}'
         'if(matches!=1)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"source-proven target mode identity not uniquely present in authoritative option set for "+path);'
         'selected.add(match.getOptionId());return;}')
    new=('if(pathSpec!=null&&"MODE_SELECTION".equals(req.getDecisionKind())&&"Charm".equals(pathSpec.dispatch)){'
         'String desired=ws33DesiredModeSemantic.get(path);if(desired==null)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"missing source-proven desired mode identity for "+path);'
         'ExternalDecisionRequest.Option match=null;int matches=0;for(ExternalDecisionRequest.Option o:options)if(desired.equals(o.getSemanticValue())){match=o;matches++;}'
         'if(matches!=1)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"source-proven target mode identity not uniquely present in authoritative option set for "+path);'
         'int min=req.getMinimumSelection(),max=req.getMaximumSelection();if(min<0||max<1||min>max||min>options.size())throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"invalid authoritative mode cardinality for "+path+" min="+min+" max="+max+" options="+options.size());'
         'selected.add(match.getOptionId());int need=Math.max(1,min);if(need>max)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"desired mode cannot satisfy authoritative max cardinality for "+path);'
         'List<ExternalDecisionRequest.Option>rest=new ArrayList<>();for(ExternalDecisionRequest.Option o:options)if(!o.getOptionId().equals(match.getOptionId()))rest.add(o);rest.sort(Comparator.comparing(o->stableKey(path,req.getDecisionKind(),o)));'
         'for(int i=0;selected.size()<need&&i<rest.size();i++)selected.add(rest.get(i).getOptionId());if(selected.size()!=need)throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,"authoritative mode minimum not satisfiable for "+path);recordAf8Selection(path,req,selected,"SOURCE_PROVEN_DESIRED_PLUS_MINIMUM");return;}')
    t=replace_once(t,old,new,'authoritative mode minimum cardinality')

    required=(
        'cases.size()!=8',
        'Ws33ARestSVarAf8QualificationTest',
        'prepareAF8PublicCandidates(actor,opponent)',
        'ZoneType.Graveyard',
        'req.getMinimumSelection()',
        'desired.equals(o.getSemanticValue())',
        'rest.sort(Comparator.comparing(o->stableKey(path,req.getDecisionKind(),o)))',
        'recordAf8Selection(path,req,selected,"SOURCE_PROVEN_DESIRED_PLUS_MINIMUM")',
        'resolveSourceParent(spec,source)',
        'prepareSourceParentChoices(spec,sa)',
        'CharmEffect.makeChoices(sa)',
        'AbilitySub.setWs33ResolutionObserver',
        'sa.setupTargets()',
        'getStack().addAndUnfreeze(sa)',
        'getStack().resolveStack()',
        'targetExecutions',
    )
    for token in required: require(token in t,'missing invariant '+token)
    for forbidden in ('sa.resolve()','sa.getTargets().add(','AbilityFactory.getAbility(spec.script,source)','targetModeOrdinal','options.get(ordinal)'):
        require(forbidden not in t,'forbidden shortcut '+forbidden)
    for forbidden in ('Grim Discovery','Fantastic Elasticity','Steel Sabotage','Sublime Epiphany','Profane Command','Aether Tradewinds','forge-behavior-v2:'):
        require(forbidden not in t,'card/path-specific branch forbidden '+forbidden)

    p.write_text(t,encoding='utf-8')
    print('WS33_A_SVAR_AF8_ADAPTER=PASS paths=8 route=ABILITY_ROOT')
    print('WS33_A_SVAR_AF8_MODE_SELECTION=FORGE_AUTHORITATIVE_DESIRED_PLUS_MINIMUM')
    print('WS33_A_SVAR_AF8_FIXTURES=GENERIC_PUBLIC_ZONE_CANDIDATES')
    print('WS33_A_SVAR_AF8_RULES_MUTATION=0 target_svar_direct_entry=FALSE')

if __name__=='__main__': main()
