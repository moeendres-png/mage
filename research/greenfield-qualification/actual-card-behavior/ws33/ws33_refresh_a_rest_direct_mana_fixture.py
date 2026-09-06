#!/usr/bin/env python3
"""Restore independent real mana-source fixture state between Direct31 cases.

The Direct31 harness intentionally exercises Forge PlaySpellAbility/CostPayment. Earlier
runs seeded basic lands once, so successful prior spells left those real lands tapped and
later independent cases could fail PAY_COST despite valid targets/timing. This fixture
repair invokes Card.untap() only on the actor's battlefield lands at the start of each
case. It never adds mana to a pool, selects payment, bypasses CostPayment, or changes the
ability under qualification.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_REST_DIRECT_MANA_FIXTURE=FAIL " + m)


def replace_once(t: str, old: str, new: str, label: str) -> str:
    n=t.count(old)
    require(n==1, f"{label}: expected exactly one match, got {n}")
    return t.replace(old,new,1)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args()
    p=a.harness; t=p.read_text(encoding='utf-8')

    loop='for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);long leak0=-1,cross0=-1;Card source=null;try{seedCommon(game,actor,opponent);'
    repl='for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);long leak0=-1,cross0=-1;Card source=null;try{refreshPayableResources(actor);seedCommon(game,actor,opponent);'
    t=replace_once(t,loop,repl,'per-case resource refresh')

    anchor='private static void seedPayableResources(Player actor){String[]lands={"Plains","Island","Swamp","Mountain","Forest"};for(String n:lands)for(int i=0;i<10;i++){Card c=addCard(n,actor,ZoneType.Battlefield);c.setTapped(false);}}\n    '
    helper='private static void seedPayableResources(Player actor){String[]lands={"Plains","Island","Swamp","Mountain","Forest"};for(String n:lands)for(int i=0;i<10;i++){Card c=addCard(n,actor,ZoneType.Battlefield);c.setTapped(false);}}\n    private static void refreshPayableResources(Player actor){for(Card c:actor.getCardsIn(ZoneType.Battlefield)){if(c.isLand()&&c.isTapped())c.untap();}}\n    '
    t=replace_once(t,anchor,helper,'refresh helper')

    require(t.count('refreshPayableResources(actor);')==1,'refresh invocation count')
    require(t.count('private static void refreshPayableResources(Player actor)')==1,'refresh helper count')
    require('c.isLand()&&c.isTapped())c.untap()' in t,'Forge Card.untap route missing')
    require('PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa)' in t,'authoritative PlaySpellAbility route missing')
    require('manaPool' not in t and 'getManaPool().add' not in t,'direct mana-pool injection present')
    require('.payCost(' not in t,'direct harness cost payment present')
    require('sa.resolve()' not in t,'direct resolve reintroduced')
    require('sa.getTargets().add(' not in t,'manual target injection reintroduced')
    p.write_text(t,encoding='utf-8')
    print('WS33_A_REST_DIRECT_MANA_FIXTURE=PASS refresh=Card.untap per_case=true mana_pool_injection=0 cost_bypass=0')

if __name__=='__main__': main()
