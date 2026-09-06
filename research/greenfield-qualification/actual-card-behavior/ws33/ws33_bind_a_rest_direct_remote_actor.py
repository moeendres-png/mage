#!/usr/bin/env python3
"""Bind A-rest Direct31 discretionary execution to a real remote 4P principal.

The historical 4P qualification harness uses player slot 0 as the local host and slots
1-3 as remote clients. Direct31 previously reused the active host turn player, which made
strict hidden-card decisions correctly fail closed due to absence of RemoteClientGuiGame.
This patch selects slot 1 and moves Forge's real PhaseHandler to MAIN1 for that player.
It does not bypass timing: PlaySpellAbility still evaluates canCastTiming/restrictions.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_REST_DIRECT_REMOTE_ACTOR=FAIL " + m)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument('--harness',type=Path,required=True); a=ap.parse_args()
    p=a.harness; t=p.read_text(encoding='utf-8')
    old='List<Player>ps=players(game);Player actor=game.getPhaseHandler().getPlayerTurn();if(actor==null)throw new IllegalStateException("no active player at MAIN1");Player opponent=null;for(Player p:ps)if(p!=actor){opponent=p;break;}if(opponent==null)throw new IllegalStateException("no opponent");seedPayableResources(actor);'
    new='List<Player>ps=players(game);if(ps.size()!=4)throw new IllegalStateException("Direct31 requires exact 4P harness");Player actor=ps.get(1),opponent=ps.get(2);if(actor==opponent)throw new IllegalStateException("remote actor/opponent alias");restoreMain1(game,actor);if(game.getPhaseHandler().getPlayerTurn()!=actor||!game.getPhaseHandler().is(PhaseType.MAIN1))throw new IllegalStateException("failed to establish remote actor MAIN1");seedPayableResources(actor);'
    n=t.count(old); require(n==1,f'actor binding anchor count={n}')
    t=t.replace(old,new,1)
    require('Player actor=ps.get(1),opponent=ps.get(2)' in t,'remote actor slots missing')
    require('restoreMain1(game,actor)' in t,'real Forge MAIN1 transition missing')
    require('PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa)' in t,'authoritative play path missing')
    require('sa.resolve()' not in t,'direct resolve reintroduced')
    require('sa.getTargets().add(' not in t,'manual target injection reintroduced')
    p.write_text(t,encoding='utf-8')
    print('WS33_A_REST_DIRECT_REMOTE_ACTOR=PASS actor_slot=1 opponent_slot=2 phase=FORGE_MAIN1 legality_bypass=0')

if __name__=='__main__': main()
