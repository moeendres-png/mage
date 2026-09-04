#!/usr/bin/env python3
"""Add path-scoped principal-observation evidence to a prepared WS33 G harness.

Qualification instrumentation only. It never alters legal options, targets, stack,
decision policy, RNG, or semantic state. Supported campaign attribution shapes are
Direct-G, SVar AF, and source-parent SVar Event. Missing/mixed anchors fail closed.
"""
from __future__ import annotations
import argparse
from pathlib import Path

def require(c,m):
    if not c: raise SystemExit("WS33_G_PRINCIPAL_OBSERVATION_INSTRUMENT=FAIL "+m)

def replace_once(t,o,n,l):
    c=t.count(o); require(c==1,f"{l}: expected exactly one match, got {c}"); return t.replace(o,n,1)

def bind_path_attribution(t):
    prefix="awaitRemoteTransport(ps);leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks();cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();"
    anchors={
      "DIRECT_G":prefix+"currentPath.set(spec.pathId);bindTargets(sa);",
      "G_SVAR_AF":prefix+"currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);",
      "G_SVAR_EVENT":prefix+"currentPath.set(spec.pathId);ws33CurrentParentKey.set(pk);",
    }
    matches={k:t.count(v) for k,v in anchors.items()}; require(sum(matches.values())==1,f"path attribution anchor ambiguous/missing: {matches}")
    name=next(k for k,v in matches.items() if v==1); old=anchors[name]
    new=old.replace("currentPath.set(spec.pathId);","ExternalObservationTrace.setPath(spec.pathId);currentPath.set(spec.pathId);",1)
    return t.replace(old,new,1),name

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args(); p=a.harness; t=p.read_text()
    t=replace_once(t,"import forge.gamemodes.match.input.ExternalDecisionValidationException;\n","import forge.gamemodes.match.input.ExternalDecisionValidationException;\nimport forge.gamemodes.match.input.ExternalObservationTrace;\n","trace import")
    t=replace_once(t,"Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);","Ws05HiddenInfoProbe.reset();ExternalObservationTrace.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);","trace reset")
    t,mode=bind_path_attribution(t)
    if mode=="G_SVAR_EVENT":
        t=replace_once(t,"ws33CurrentParentKey.set(null);currentPath.set(null);retireSource(game,actor,source);","ws33CurrentParentKey.set(null);ExternalObservationTrace.clearPath();currentPath.set(null);retireSource(game,actor,source);","event path clear")
    else:
        t=replace_once(t,"for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}currentPath.set(null);}}}","for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}ExternalObservationTrace.clearPath();currentPath.set(null);}}}","path clear")
    t=replace_once(t,"writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);","writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);ExternalObservationTrace.write(outDir.resolve(\"PRINCIPAL_OBSERVATIONS.jsonl\"));","trace export") if mode!="G_SVAR_EVENT" else replace_once(t,"writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);writeResolutionLineage(outDir);","writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);writeResolutionLineage(outDir);ExternalObservationTrace.write(outDir.resolve(\"PRINCIPAL_OBSERVATIONS.jsonl\"));","event trace export")
    require(t.count("ExternalObservationTrace.setPath(spec.pathId)")==1,"path binding not unique"); require("ExternalObservationTrace.clearPath()" in t,"path clear missing"); require("PRINCIPAL_OBSERVATIONS.jsonl" in t,"trace export missing"); require("sa.resolve()" not in t,"direct resolve reintroduced"); require("sa.getTargets().add(" not in t,"manual target injection reintroduced"); require("getStack().resolveStack()" in t,"production stack resolution missing")
    p.write_text(t); print("WS33_G_PRINCIPAL_OBSERVATION_INSTRUMENT=PASS"); print(f"WS33_G_PRINCIPAL_OBSERVATION_ATTRIBUTION={mode}"); print("WS33_G_PRINCIPAL_OBSERVATION_PATH_SCOPED=TRUE"); print("WS33_G_PRINCIPAL_OBSERVATION_RULES_MUTATION=0")
if __name__=='__main__': main()
