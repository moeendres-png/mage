#!/usr/bin/env python3
"""Add path-scoped principal-observation evidence to a prepared WS33 G harness.

This is qualification instrumentation only. It does not alter legal options, targets,
stack handling, decision policy, RNG, or semantic state. The production-facing adapter
creates principal-scoped temporary Card observations; this script only binds those
transport events to the exact effective path id and exports the payload-free trace.

Exactly one supported campaign attribution anchor must be present:
- Direct-G: currentPath.set(spec.pathId);bindTargets(sa);
- SVar AF: currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);

Missing, duplicated, or mixed attribution anchors fail closed.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_G_PRINCIPAL_OBSERVATION_INSTRUMENT=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def bind_path_attribution(text: str) -> tuple[str, str]:
    prefix = (
        "awaitRemoteTransport(ps);leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks();"
        "cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();"
    )
    anchors = {
        "DIRECT_G": prefix + "currentPath.set(spec.pathId);bindTargets(sa);",
        "G_SVAR_AF": prefix + "currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);",
    }
    matches = {name: text.count(anchor) for name, anchor in anchors.items()}
    total = sum(matches.values())
    require(total == 1, f"path attribution anchor ambiguous/missing: {matches}")
    name = next(name for name, count in matches.items() if count == 1)
    old = anchors[name]
    new = old.replace(
        "currentPath.set(spec.pathId);",
        "ExternalObservationTrace.setPath(spec.pathId);currentPath.set(spec.pathId);",
        1,
    )
    return text.replace(old, new, 1), name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    path = args.harness
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import forge.gamemodes.match.input.ExternalDecisionValidationException;\n",
        "import forge.gamemodes.match.input.ExternalDecisionValidationException;\n"
        "import forge.gamemodes.match.input.ExternalObservationTrace;\n",
        "trace import",
    )
    text = replace_once(
        text,
        "Ws05HiddenInfoProbe.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);",
        "Ws05HiddenInfoProbe.reset();ExternalObservationTrace.reset();Ws05HiddenInfoProbe.registerSecret(SECRET);",
        "trace reset",
    )
    text, attribution_mode = bind_path_attribution(text)
    text = replace_once(
        text,
        "for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}currentPath.set(null);}}}",
        "for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}ExternalObservationTrace.clearPath();currentPath.set(null);}}}",
        "path clear",
    )
    text = replace_once(
        text,
        "writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);PlayerControllerHuman.setExternalDecisionProviderFactory(null);",
        "writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);ExternalObservationTrace.write(outDir.resolve(\"PRINCIPAL_OBSERVATIONS.jsonl\"));PlayerControllerHuman.setExternalDecisionProviderFactory(null);",
        "trace export",
    )

    require("ExternalObservationTrace.setPath(spec.pathId)" in text, "path binding missing")
    require(text.count("ExternalObservationTrace.setPath(spec.pathId)") == 1, "path binding not unique")
    require("ExternalObservationTrace.clearPath()" in text, "path clear missing")
    require("PRINCIPAL_OBSERVATIONS.jsonl" in text, "trace export missing")
    require("sa.resolve()" not in text, "direct SpellAbility.resolve reintroduced")
    require("sa.getTargets().add(" not in text, "manual target injection reintroduced")
    require("getStack().addAndUnfreeze(sa)" in text, "production stack admission missing")
    require("getStack().resolveStack()" in text, "production stack resolution missing")
    if attribution_mode == "G_SVAR_AF":
        require("prepareSourceParentChoices(spec,sa)" in text, "AF source-parent choice phase missing")

    path.write_text(text, encoding="utf-8")
    print("WS33_G_PRINCIPAL_OBSERVATION_INSTRUMENT=PASS")
    print(f"WS33_G_PRINCIPAL_OBSERVATION_ATTRIBUTION={attribution_mode}")
    print("WS33_G_PRINCIPAL_OBSERVATION_PATH_SCOPED=TRUE")
    print("WS33_G_PRINCIPAL_OBSERVATION_RULES_MUTATION=0")


if __name__ == "__main__":
    main()
