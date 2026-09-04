#!/usr/bin/env python3
"""Add deterministic, script-semantic library fixtures for WS33 non-AF Decision/RNG obligations.

This is qualification-only. It does not branch on card names or path IDs and does not
alter Forge rules, legal options, RNG, or pilot policy. It only ensures that restrictive
actual-card Valid/ChangeValid/RevealValid predicates have a real pinned-Forge card in the
bounded library window, and that random-rest effects retain at least two pre-match cards.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def fail(msg: str) -> None:
    raise SystemExit("WS33_G_SVAR_OBLIGATION_FIXTURE=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    s = args.harness.read_text(encoding="utf-8")

    call_old = 'actor.setNamedCard("Runeclaw Bear");prepareSourceFixture(spec,game,actor,opponent,source,pe);'
    call_new = 'actor.setNamedCard("Runeclaw Bear");prepareObligationFixture(spec,actor);prepareSourceFixture(spec,game,actor,opponent,source,pe);'
    s = replace_once(s, call_old, call_new, "obligation fixture call")

    anchor = '    private static void prepareSourceFixture(CaseSpec spec,Game game,Player actor,Player opponent,Card source,ParentEvidence pe)'
    helper = r'''    private static void placeLibraryCardAt(String name,Player player,int index){Card c=addCardAtTop(name,player);player.getZone(ZoneType.Library).remove(c);player.getZone(ZoneType.Library).add(c,index);}
    private static void prepareObligationFixture(CaseSpec spec,Player actor){Map<String,String>p=AbilityFactory.getMapParams(spec.targetScript);String valid=p.get("RevealValid");if(valid==null)valid=p.get("ChangeValid");if(valid==null)valid=p.get("Valid");String candidate=null;if(spec.decision){if("Aura".equals(valid))candidate="Pacifism";else if("Hero".equals(valid))candidate="Amateur Hero";else if("Aura,Equipment".equals(valid))candidate="Lightning Greaves";else if("Creature.ChosenType".equals(valid))candidate="Runeclaw Bear";}if(candidate==null&&spec.rng&&valid!=null&&valid.contains("sharesCreatureTypeWith Sacrificed"))candidate="Runeclaw Bear";if(candidate==null)return;boolean randomRest=p.containsKey("RevealRandomOrder")||p.containsKey("RestRandomOrder");int index=spec.rng&&randomRest?2:0;placeLibraryCardAt(candidate,actor,index);}
'''
    s = replace_once(s, anchor, helper + anchor, "obligation fixture helper")

    if 'spec.cardName.equals(' in helper or 'spec.pathId.equals(' in helper:
        fail("card/path-specific branching forbidden")
    for required in (
        'prepareObligationFixture(spec,actor)',
        '"Aura".equals(valid)',
        '"Hero".equals(valid)',
        '"Aura,Equipment".equals(valid)',
        '"Creature.ChosenType".equals(valid)',
        'valid.contains("sharesCreatureTypeWith Sacrificed")',
        'index=spec.rng&&randomRest?2:0',
    ):
        if required not in s:
            fail("missing generated invariant: " + required)

    args.harness.write_text(s, encoding="utf-8")
    print("WS33_G_SVAR_OBLIGATION_FIXTURE=PASS card_name_branches=0 path_id_branches=0 decision_candidates=VALIDITY_DRIVEN rng_rest=NONTRIVIAL")


if __name__ == "__main__":
    main()
