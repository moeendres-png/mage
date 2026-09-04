#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"WS33_G_REQUEST_TRACE_PATCH=FAIL {label}: expected 1 anchor, got {n}")
    return text.replace(old, new, 1)


def replace_one_of(text: str, alternatives: tuple[tuple[str, str], ...], label: str) -> str:
    matches = [(old, new) for old, new in alternatives if text.count(old) == 1]
    if len(matches) != 1:
        counts = {old: text.count(old) for old, _ in alternatives}
        raise SystemExit(f"WS33_G_REQUEST_TRACE_PATCH=FAIL {label}: expected exactly one ABI anchor, got {counts}")
    old, new = matches[0]
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    path = args.harness
    text = path.read_text(encoding="utf-8")
    lineage_event = "writeResolutionLineage(outDir)" in text and "ws33CurrentParentKey" in text

    text = replace_once(
        text,
        '    private static final String SECRET = "Black Lotus";\n',
        '    private static final String SECRET = "Black Lotus";\n'
        '    private static final CopyOnWriteArrayList<String> ws33DecisionRequests = new CopyOnWriteArrayList<>();\n'
        '    private static final CopyOnWriteArrayList<String> ws33StackLifecycle = new CopyOnWriteArrayList<>();\n',
        "request and stack trace storage",
    )

    text = replace_once(
        text,
        'Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);',
        'ws33DecisionRequests.clear();ws33StackLifecycle.clear();Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);',
        "request and stack trace reset",
    )

    anchor = 'Ws05HiddenInfoProbe.observeDecision(player.getName(),player.getId(),request);return decisionSource.decide(player,request,p);});'
    replacement = 'if(p!=null)ws33TraceDecisionRequest(p,request);Ws05HiddenInfoProbe.observeDecision(player.getName(),player.getId(),request);return decisionSource.decide(player,request,p);});'
    text = replace_once(text, anchor, replacement, "request trace provider hook")

    direct_write = 'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);PlayerControllerHuman.setExternalDecisionProviderFactory(null);'
    direct_write_traced = 'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeWs33DecisionRequests(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);'
    event_write = 'writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);'
    event_write_traced = 'writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);writeWs33DecisionRequests(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);'
    lineage_event_write = 'writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);writeResolutionLineage(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);'
    lineage_event_write_traced = 'writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);writeResolutionLineage(outDir);writeWs33DecisionRequests(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);'
    text = replace_one_of(
        text,
        (
            (direct_write, direct_write_traced),
            (event_write, event_write_traced),
            (lineage_event_write, lineage_event_write_traced),
        ),
        "request trace write ABI",
    )

    if lineage_event:
        lifecycle_observer = r'''        MagicStack.setWs33StackLifecycleObserver((stage,ability,flag)->{String k=ws33CurrentParentKey.get();if(k==null)return;ParentEvidence pe=ws33ParentEvidence.get(k);if(pe==null)return;boolean wrapper=ability instanceof WrappedAbility;SpellAbility effective=wrapper?((WrappedAbility)ability).getWrappedAbility():ability;boolean targetMatch=matchesTarget(pe.spec,effective);ws33StackLifecycle.add(String.join("\t",k,stage,Boolean.toString(flag),wrapper?"1":"0",Integer.toString(effective.getId()),Integer.toString(effective.getSourceTrigger()),Integer.toString(effective.getHostCard()==null?-1:effective.getHostCard().getId()),effective.getApi()==null?"":effective.getApi().name(),mapHash(effective.getOriginalMapParams()),mapHash(effective.getMapParams()),targetMatch?"1":"0",Integer.toString(pe.admittedAbilityId),Integer.toString(pe.admittedSourceTrigger),Integer.toString(pe.admittedHostId),pe.admittedApi));});
'''
        text = replace_once(
            text,
            '        Game.setSemanticStateObserver((game,checkpoint)->',
            lifecycle_observer + '        Game.setSemanticStateObserver((game,checkpoint)->',
            "stack lifecycle observer setup",
        )
        text = replace_once(
            text,
            'MagicStack.setWs33ResolutionObserver(null);ws33CurrentParentKey.set(null);',
            'MagicStack.setWs33ResolutionObserver(null);MagicStack.setWs33StackLifecycleObserver(null);ws33CurrentParentKey.set(null);',
            "stack lifecycle observer cleanup",
        )
        text = replace_once(
            text,
            'writeResolutionLineage(outDir);writeWs33DecisionRequests(outDir);',
            'writeResolutionLineage(outDir);writeWs33StackLifecycle(outDir);writeWs33DecisionRequests(outDir);',
            "stack lifecycle evidence write",
        )

    helper = r'''    private static void ws33TraceDecisionRequest(String pathId, ExternalDecisionRequest request){
        StringBuilder options=new StringBuilder();
        for(ExternalDecisionRequest.Option option:request.getOptions()){
            if(options.length()>0)options.append(',');
            options.append(enc(option.getOptionId()));
        }
        ws33DecisionRequests.add(String.join("\t",
                enc(pathId),
                Long.toString(request.getDecisionId()),
                Long.toString(request.getToken()),
                enc(request.getDecisionKind()),
                Integer.toString(request.getActorId()),
                Integer.toString(request.getPrincipalId()),
                enc(request.getVisibilityScope()),
                Integer.toString(request.getMinimumSelection()),
                Integer.toString(request.getMaximumSelection()),
                Boolean.toString(request.isCancelAllowed()),
                enc(request.getResponseSchema()),
                Integer.toString(request.getOptions().size()),
                options.toString()));
    }
    private static void writeWs33DecisionRequests(Path out)throws IOException{
        Files.write(out.resolve("decision-requests-with-path.tsv"),ws33DecisionRequests,StandardCharsets.UTF_8);
    }
    private static void writeWs33StackLifecycle(Path out)throws IOException{
        Files.write(out.resolve("stack-lifecycle.tsv"),ws33StackLifecycle,StandardCharsets.UTF_8);
    }
'''
    text = replace_once(text, '    private static void writeEvidence(', helper + '    private static void writeEvidence(', "request and stack trace helpers")

    forbidden = (
        'getOptions().clear(',
        'getOptions().add(',
        'selected.add("',
        'sa.resolve()',
        'sa.getTargets().add(',
    )
    for token in forbidden:
        if token in text:
            raise SystemExit(f"WS33_G_REQUEST_TRACE_PATCH=FAIL forbidden instrumentation token: {token}")
    if 'decision-requests-with-path.tsv' not in text or 'request.getOptions()' not in text:
        raise SystemExit("WS33_G_REQUEST_TRACE_PATCH=FAIL request trace not materialized")
    if lineage_event:
        for token in (
            'MagicStack.setWs33StackLifecycleObserver',
            'stack-lifecycle.tsv',
            'writeWs33StackLifecycle(outDir)',
            'MagicStack.setWs33StackLifecycleObserver(null)',
        ):
            if token not in text:
                raise SystemExit(f"WS33_G_REQUEST_TRACE_PATCH=FAIL lifecycle instrumentation missing {token}")
    path.write_text(text, encoding="utf-8")
    print("WS33_G_REQUEST_TRACE_PATCH=PASS mode=observer_only payload=opaque_authoritative_option_ids write_abi=DIRECT_OR_EVENT_OR_LINEAGE_EVENT stack_lifecycle=" + ("PARENT_CORRELATED" if lineage_event else "NOT_APPLICABLE"))


if __name__ == "__main__":
    main()
