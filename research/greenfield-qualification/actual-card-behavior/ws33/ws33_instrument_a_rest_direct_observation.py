#!/usr/bin/env python3
"""Instrument the generated A-rest Direct31 harness with path-scoped observation evidence.

Qualification instrumentation only. It does not alter legal options, targets, costs,
RNG, stack ordering, or decision policy. It records ExternalObservationTrace and the
observation-only PlaySpellAbility stage callback against the current exact path.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_REST_DIRECT_OBSERVATION=FAIL " + m)


def replace_once(t: str, o: str, n: str, label: str) -> str:
    c=t.count(o)
    require(c==1, f"{label}: expected exactly one match, got {c}")
    return t.replace(o,n,1)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args()
    p=a.harness; t=p.read_text(encoding='utf-8')

    t=replace_once(t,
        'import forge.gamemodes.match.input.ExternalDecisionValidationException;\n',
        'import forge.gamemodes.match.input.ExternalDecisionValidationException;\nimport forge.gamemodes.match.input.ExternalObservationTrace;\n',
        'observation trace import')
    t=replace_once(t,
        'final CopyOnWriteArrayList<ExternalDecisionTape.Event> allDecisions=new CopyOnWriteArrayList<>();final CopyOnWriteArrayList<String> decisionPath=new CopyOnWriteArrayList<>();',
        'final CopyOnWriteArrayList<ExternalDecisionTape.Event> allDecisions=new CopyOnWriteArrayList<>();final CopyOnWriteArrayList<String> decisionPath=new CopyOnWriteArrayList<>();final CopyOnWriteArrayList<String> playStages=new CopyOnWriteArrayList<>();',
        'play stage evidence list')
    t=replace_once(t,
        'Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);',
        'Ws05HiddenInfoProbe.reset();ExternalObservationTrace.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);',
        'trace reset')
    t=replace_once(t,
        'MagicStack.setWs33ResolutionObserver(ability->{String p=currentPath.get();if(p!=null){CaseEvidence ce=evidence.get(p);if(ce!=null&&matchesSourceRoot(ce.spec,ability))ce.sourceRootExecutions++;}});ExternalDecisionTape.setEventObserver(event->{',
        'MagicStack.setWs33ResolutionObserver(ability->{String p=currentPath.get();if(p!=null){CaseEvidence ce=evidence.get(p);if(ce!=null&&matchesSourceRoot(ce.spec,ability))ce.sourceRootExecutions++;}});PlaySpellAbility.setWs33PlayStageObserver((stage,ability,result)->{String p=currentPath.get();if(p!=null)playStages.add(enc(p)+"\\t"+enc(stage)+"\\t"+result+"\\t"+enc(ability==null||ability.getApi()==null?"":ability.getApi().name()));});ExternalDecisionTape.setEventObserver(event->{',
        'play stage observer binding')
    t=replace_once(t,
        'currentPath.set(spec.pathId);ce.beforeState=semanticState(game);',
        'ExternalObservationTrace.setPath(spec.pathId);currentPath.set(spec.pathId);ce.beforeState=semanticState(game);',
        'path-scoped observation binding')
    t=replace_once(t,
        'currentPath.set(null);restoreMain1(game,actor);',
        'ExternalObservationTrace.clearPath();currentPath.set(null);restoreMain1(game,actor);',
        'path-scoped observation clear')
    t=replace_once(t,
        'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);PlayerControllerHuman.setExternalDecisionProviderFactory(null);MagicStack.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);',
        'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);Files.write(outDir.resolve("play-stages.tsv"),playStages,StandardCharsets.UTF_8);ExternalObservationTrace.write(outDir.resolve("PRINCIPAL_OBSERVATIONS.jsonl"));PlayerControllerHuman.setExternalDecisionProviderFactory(null);PlaySpellAbility.setWs33PlayStageObserver(null);MagicStack.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);',
        'observation export and cleanup')

    require(t.count('ExternalObservationTrace.setPath(spec.pathId)')==1,'path binding count')
    require('ExternalObservationTrace.clearPath()' in t,'path clear missing')
    require('PRINCIPAL_OBSERVATIONS.jsonl' in t,'principal observation export missing')
    require('play-stages.tsv' in t,'play stage export missing')
    require('PlaySpellAbility.setWs33PlayStageObserver' in t,'play stage observer missing')
    require('sa.resolve()' not in t,'direct resolve reintroduced')
    require('sa.getTargets().add(' not in t,'manual target injection reintroduced')
    p.write_text(t,encoding='utf-8')
    print('WS33_A_REST_DIRECT_OBSERVATION=PASS path_scoped=true play_stage_observer=true rules_mutation=0')

if __name__=='__main__': main()
