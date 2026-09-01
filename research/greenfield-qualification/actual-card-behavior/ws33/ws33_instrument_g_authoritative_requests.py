#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"WS33_G_REQUEST_TRACE_PATCH=FAIL {label}: expected 1 anchor, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    path = args.harness
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '    private static final String SECRET = "Black Lotus";\n',
        '    private static final String SECRET = "Black Lotus";\n'
        '    private static final CopyOnWriteArrayList<String> ws33DecisionRequests = new CopyOnWriteArrayList<>();\n',
        "request trace storage",
    )

    text = replace_once(
        text,
        'Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);',
        'ws33DecisionRequests.clear();Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);',
        "request trace reset",
    )

    anchor = 'Ws05HiddenInfoProbe.observeDecision(player.getName(),player.getId(),request);return decisionSource.decide(player,request,p);});'
    replacement = 'if(p!=null)ws33TraceDecisionRequest(p,request);Ws05HiddenInfoProbe.observeDecision(player.getName(),player.getId(),request);return decisionSource.decide(player,request,p);});'
    text = replace_once(text, anchor, replacement, "request trace provider hook")

    text = replace_once(
        text,
        'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);PlayerControllerHuman.setExternalDecisionProviderFactory(null);',
        'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeWs33DecisionRequests(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);',
        "request trace write",
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
'''
    text = replace_once(text, '    private static void writeEvidence(', helper + '    private static void writeEvidence(', "request trace helpers")

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
    path.write_text(text, encoding="utf-8")
    print("WS33_G_REQUEST_TRACE_PATCH=PASS mode=observer_only payload=opaque_authoritative_option_ids")


if __name__ == "__main__":
    main()
