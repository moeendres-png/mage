#!/usr/bin/env python3
"""Narrow the proven G3 SVar-AF harness mechanism to the exact A-rest NonTrigger9 case set.

This transform changes only qualification identity/cardinality labels. It does not alter
parent binding, Forge mode selection, TargetRestrictions, stack execution, Decision/RNG,
hidden observation, or any production rules behavior.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_SVAR_NONTRIGGER9_ADAPTER=FAIL " + m)


def replace_once(t: str, old: str, new: str, label: str) -> str:
    n=t.count(old); require(n==1, f"{label}: expected one anchor, got {n}"); return t.replace(old,new,1)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args()
    p=a.harness; t=p.read_text(encoding='utf-8')
    t=replace_once(t,
        'if(cases.size()!=21)throw new IllegalStateException("WS33 G-SVAR-AF expected 21 cases, got "+cases.size());',
        'if(cases.size()!=9)throw new IllegalStateException("WS33 A-SVAR-NONTRIGGER9 expected 9 cases, got "+cases.size());',
        'case cardinality')
    t=t.replace('Ws33GSVarAfQualificationTest','Ws33ARestSVarNonTriggerQualificationTest')
    t=t.replace('WS33 G-SVAR-AF','WS33 A-SVAR-NONTRIGGER9')
    for token in (
        'resolveSourceParent(spec,source)',
        'prepareSourceParentChoices(spec,sa)',
        'CharmEffect.makeChoices(sa)',
        'desired.equals(o.getSemanticValue())',
        'AbilitySub.setWs33ResolutionObserver',
        'sa.setupTargets()',
        'getStack().addAndUnfreeze(sa)',
        'getStack().resolveStack()',
        'targetExecutions',
    ):
        require(token in t, 'missing inherited production invariant '+token)
    for forbidden in ('sa.resolve()','sa.getTargets().add(','AbilityFactory.getAbility(spec.script,source)','targetModeOrdinal','options.get(ordinal)'):
        require(forbidden not in t, 'forbidden shortcut '+forbidden)
    require('cases.size()!=9' in t,'9-case cardinality not installed')
    require('Ws33ARestSVarNonTriggerQualificationTest' in t,'A test class name missing')
    p.write_text(t,encoding='utf-8')
    print('WS33_A_SVAR_NONTRIGGER9_ADAPTER=PASS paths=9 mechanism=G3_AF_PRODUCTION_PARENT')
    print('WS33_A_SVAR_NONTRIGGER9_RULES_MUTATION=0 target_svar_direct_entry=FALSE')

if __name__=='__main__': main()
