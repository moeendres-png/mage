#!/usr/bin/env python3
"""Narrow the proven G3 SVar-event harness mechanism to the exact A-rest Trigger17 cases.

All A Trigger17 cases have exactly one selected source-proven parent entrypoint. This
transform changes only qualification identity/cardinality labels: 33 G parent rows / 32
G effective paths become 17 A parent rows / 17 A effective paths. Trigger legality,
event dispatch, TargetRestrictions, stack resolution, Decision/RNG, and observation stay
Forge-owned and unchanged.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_SVAR_TRIGGER17_ADAPTER=FAIL " + m)


def replace_once(t: str, old: str, new: str, label: str) -> str:
    n=t.count(old); require(n==1, f"{label}: expected one anchor, got {n}"); return t.replace(old,new,1)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args()
    p=a.harness; t=p.read_text(encoding='utf-8')
    t=replace_once(t,
        'if(cases.size()!=33)throw new IllegalStateException("WS33 G-SVAR-EVENT expected 33 parent cases, got "+cases.size());',
        'if(cases.size()!=17)throw new IllegalStateException("WS33 A-SVAR-TRIGGER17 expected 17 parent cases, got "+cases.size());',
        'parent cardinality')
    t=replace_once(t,
        'if(m.size()!=32)throw new IllegalStateException("WS33 G-SVAR-EVENT expected 32 effective paths, got "+m.size());',
        'if(m.size()!=17)throw new IllegalStateException("WS33 A-SVAR-TRIGGER17 expected 17 effective paths, got "+m.size());',
        'effective path cardinality')
    t=t.replace('Ws33GSVarEventQualificationTest','Ws33ARestSVarTriggerQualificationTest')
    t=t.replace('WS33 G-SVAR-EVENT','WS33 A-SVAR-TRIGGER17')

    required=(
        'runTrigger(TriggerType.smartValueOf(spec.mode),rp,false)',
        'addAllTriggeredAbilitiesToStack()',
        'TriggerHandler.setWs33TriggerObserver',
        'MagicStack.setWs33ResolutionObserver',
        'bindExpectedParent(spec,source,pe)',
        'dispatchSourceEvent(spec,game,actor,opponent,source,pe)',
        'targetBindings',
        'targetExecutions',
        'parent-summary.tsv',
    )
    for token in required: require(token in t,'missing inherited production invariant '+token)
    for forbidden in ('AbilityFactory.getAbility(spec.targetScript','sa.resolve()','sa.getTargets().add('):
        require(forbidden not in t,'forbidden target-SVar/rules shortcut '+forbidden)
    require('cases.size()!=17' in t and 'm.size()!=17' in t,'17/17 cardinalities missing')
    require('Ws33ARestSVarTriggerQualificationTest' in t,'A Trigger17 test class missing')
    p.write_text(t,encoding='utf-8')
    print('WS33_A_SVAR_TRIGGER17_ADAPTER=PASS paths=17 parents=17 mechanism=G3_EVENT_PRODUCTION_PARENT')
    print('WS33_A_SVAR_TRIGGER17_RULES_MUTATION=0 target_svar_direct_entry=FALSE')

if __name__=='__main__': main()
