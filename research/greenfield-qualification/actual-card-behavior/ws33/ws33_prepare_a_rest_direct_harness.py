#!/usr/bin/env python3
"""Adapt the qualified WS33 direct-ability harness for post-A1 A-rest Direct31.

Each path binds to the actual source-bound SpellAbility on the pinned Forge card.
Fixture code establishes only real game state/resources. PlaySpellAbility remains
sole authority for announcements, target setup, timing, restrictions and costs;
MagicStack observation proves the source root reaches non-fizzled resolution.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_A_REST_DIRECT_HARNESS=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    i = text.find(start)
    require(i >= 0, label + ": start anchor missing")
    j = text.find(end, i)
    require(j >= 0, label + ": end anchor missing")
    return text[:i] + replacement + text[j:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    s = args.harness.read_text(encoding="utf-8")

    s = s.replace("Ws33GAbilityQualificationTest", "Ws33ARestDirectQualificationTest")
    s = s.replace("WS33 G-ABILITY", "WS33 A-REST-DIRECT")
    s = replace_once(s,
        'if(cases.size()!=28)throw new IllegalStateException("WS33 A-REST-DIRECT expected 28 cases, got "+cases.size());',
        'if(cases.size()!=31)throw new IllegalStateException("WS33 A-REST-DIRECT expected 31 cases, got "+cases.size());',
        "case cardinality")
    s = replace_once(s, "import forge.game.player.Player;\n",
        "import forge.game.player.Player;\nimport forge.game.player.PlaySpellAbility;\n", "PlaySpellAbility import")
    s = replace_once(s, "import forge.game.spellability.SpellAbility;\n",
        "import forge.game.combat.Combat;\nimport forge.game.phase.PhaseType;\nimport forge.game.spellability.SpellAbility;\nimport forge.game.zone.MagicStack;\n",
        "combat/phase/stack imports")

    old_case = 'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);}'
    new_case = 'final int ordinal; final String pathId,oracleId,cardName,scenarioGroup,evidenceProfile,abilityKind,dispatch,sourcePath,script,validTgts,origin,destination,costShape; final int sourceLine; final boolean decision,rng,hidden,replay;\n        CaseSpec(String[] f){if(f.length!=19)throw new IllegalArgumentException("WS33 A-REST-DIRECT expected 19 case fields, got "+f.length);ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];scenarioGroup=f[4];evidenceProfile=f[5];abilityKind=f[6];dispatch=f[7];sourcePath=f[8];sourceLine=Integer.parseInt(f[9]);script=new String(Base64.getDecoder().decode(f[10]),StandardCharsets.UTF_8);validTgts=new String(Base64.getDecoder().decode(f[11]),StandardCharsets.UTF_8);origin=new String(Base64.getDecoder().decode(f[12]),StandardCharsets.UTF_8);destination=new String(Base64.getDecoder().decode(f[13]),StandardCharsets.UTF_8);costShape=f[14];decision="1".equals(f[15]);rng="1".equals(f[16]);hidden="1".equals(f[17]);replay="1".equals(f[18]);}'
    s = replace_once(s, old_case, new_case, "Direct31 case ABI")
    s = replace_once(s, 'if(f.length!=15)throw new IllegalArgumentException("bad case TSV fields="+f.length);',
        'if(f.length!=19)throw new IllegalArgumentException("bad case TSV fields="+f.length);', "case TSV width")

    old_ev = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions;'
    new_ev = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions,sourceRootExecutions;'
    s = replace_once(s, old_ev, new_ev, "source root execution evidence")

    ready_old = 'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4)return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;if(!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving())return false;return true;}'
    ready_new = 'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4)return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;if(!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving())return false;return game.getPhaseHandler().is(PhaseType.MAIN1)&&game.getPhaseHandler().getPlayerTurn()!=null;}'
    s = replace_once(s, ready_old, ready_new, "active MAIN1 entry")

    s = replace_once(s, 'ExternalDecisionTape.setEventObserver(event->{',
        'MagicStack.setWs33ResolutionObserver(ability->{String p=currentPath.get();if(p!=null){CaseEvidence ce=evidence.get(p);if(ce!=null&&matchesSourceRoot(ce.spec,ability))ce.sourceRootExecutions++;}});ExternalDecisionTape.setEventObserver(event->{',
        "source root stack observer")
    s = replace_once(s, 'PlayerControllerHuman.setExternalDecisionProviderFactory(null);ExternalDecisionTape.setEventObserver(null);',
        'PlayerControllerHuman.setExternalDecisionProviderFactory(null);MagicStack.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);',
        "stack observer cleanup")

    run_start = 'private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath)'
    run_end = 'private static void awaitRemoteTransport(List<Player> ps)'
    run = r'''private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath){List<Player>ps=players(game);Player actor=game.getPhaseHandler().getPlayerTurn();if(actor==null)throw new IllegalStateException("no active player at MAIN1");Player opponent=null;for(Player p:ps)if(p!=actor){opponent=p;break;}if(opponent==null)throw new IllegalStateException("no opponent");seedPayableResources(actor);for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);long leak0=-1,cross0=-1;Card source=null;try{seedCommon(game,actor,opponent);prepareGenericTargets(game,actor,opponent);Card canary=addCard(SECRET,actor,ZoneType.Library);Ws05HiddenInfoProbe.setPhase(spec.pathId,canary.getId(),Set.of());source=addCard(spec.cardName,actor,"SP".equals(spec.abilityKind)?ZoneType.Hand:ZoneType.Battlefield);source.setSickness(false);source.setTapped(false);source.addRemembered(opponent);source.addRemembered(addCard("Runeclaw Bear",opponent,ZoneType.Battlefield));opponent.setNamedCard("Runeclaw Bear");actor.setNamedCard("Runeclaw Bear");SpellAbility sa=resolveActualSourceAbility(spec,source);sa.setActivatingPlayer(actor);prepareDynamicFixture(spec,game,actor,opponent,source,currentPath);awaitRemoteTransport(ps);leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks();cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();currentPath.set(spec.pathId);ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);if(!PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa))throw new IllegalStateException("Forge PlaySpellAbility rejected exact source path");ce.stackAdmissions++;drainStack(game);if(ce.sourceRootExecutions<1)throw new IllegalStateException("exact source root did not reach MagicStack resolution");ce.stackResolutions++;game.getAction().checkStateEffects(true);awaitRemoteTransport(ps);ce.afterState=semanticState(game);ce.afterDigest=sha256(ce.afterState);ce.status="PASS";}catch(Throwable t){ce.status="FAIL";ce.failureType=t.getClass().getName();ce.failureMessage=sanitize(String.valueOf(t.getMessage()));Ws05HiddenInfoProbe.observeException(t);}finally{ce.leakDelta=leak0<0?0:Ws05HiddenInfoProbe.pilotVisibleLeaks()-leak0;ce.crossPrincipalDelta=cross0<0?0:Ws05HiddenInfoProbe.crossPrincipalLeaks()-cross0;for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}currentPath.set(null);restoreMain1(game,actor);}}}
    '''
    s = replace_between(s, run_start, run_end, run, "Direct31 campaign")

    helper_anchor = 'private static void awaitRemoteTransport(List<Player> ps)'
    helpers = r'''private static boolean matchesSourceRoot(CaseSpec spec,SpellAbility ability){if(ability==null||ability.getApi()==null||!spec.dispatch.equals(ability.getApi().name()))return false;Map<String,String>expected=AbilityFactory.getMapParams(spec.script);return expected.equals(ability.getOriginalMapParams())||expected.equals(ability.getMapParams());}
    private static SpellAbility resolveActualSourceAbility(CaseSpec spec,Card source){Map<String,String>expected=AbilityFactory.getMapParams(spec.script);SpellAbility match=null;int matches=0;for(SpellAbility candidate:source.getCurrentState().getSpellAbilities()){boolean kind="SP".equals(spec.abilityKind)?candidate.isSpell():candidate.isActivatedAbility();if(kind&&(expected.equals(candidate.getOriginalMapParams())||expected.equals(candidate.getMapParams()))){match=candidate;matches++;}}if(matches!=1)throw new IllegalStateException("actual source-bound ability match count="+matches+" for "+spec.pathId);return match;}
    private static void seedPayableResources(Player actor){String[]lands={"Plains","Island","Swamp","Mountain","Forest"};for(String n:lands)for(int i=0;i<10;i++){Card c=addCard(n,actor,ZoneType.Battlefield);c.setTapped(false);}}
    private static void prepareGenericTargets(Game game,Player actor,Player opponent){addCard("Runeclaw Bear",actor,ZoneType.Battlefield);addCard("Runeclaw Bear",opponent,ZoneType.Battlefield);addCard("Sol Ring",actor,ZoneType.Battlefield);addCard("Sol Ring",opponent,ZoneType.Battlefield);addCard("Glorious Anthem",actor,ZoneType.Battlefield);addCard("Glorious Anthem",opponent,ZoneType.Battlefield);addCard("Swiftwater Cliffs",actor,ZoneType.Battlefield);addCard("Swiftwater Cliffs",opponent,ZoneType.Battlefield);addCard("Runeclaw Bear",actor,ZoneType.Graveyard);addCard("Sol Ring",actor,ZoneType.Graveyard);addCard("Shock",actor,ZoneType.Graveyard);addCard("Think Twice",actor,ZoneType.Graveyard);addCard("Plains",actor,ZoneType.Graveyard);addCard("Think Twice",actor,ZoneType.Exile);}
    private static void prepareDynamicFixture(CaseSpec spec,Game game,Player actor,Player opponent,Card source,AtomicReference<String>currentPath){if(spec.script.contains("Sac<1/Creature>"))addCard("Runeclaw Bear",actor,ZoneType.Battlefield);if(spec.script.contains("IsPresent$ Permanent.White+YouCtrl")){addCard("Savannah Lions",actor,ZoneType.Battlefield);addCard("Glorious Anthem",actor,ZoneType.Battlefield);}if(spec.validTgts.contains("withFlashback"))addCard("Think Twice",actor,ZoneType.Exile);if(spec.validTgts.contains("nonBasic+OppCtrl"))addCard("Swiftwater Cliffs",opponent,ZoneType.Battlefield);if(spec.validTgts.contains("attacking")){game.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,actor);Combat combat=new Combat(opponent);Card attacker=addCard("Runeclaw Bear",opponent,ZoneType.Battlefield);combat.addAttacker(attacker,actor);game.getPhaseHandler().setCombat(combat);}if(spec.validTgts.contains("enchanted")){Card permanent=addCard("Runeclaw Bear",opponent,ZoneType.Battlefield);Card aura=addCard("Pacifism",actor,ZoneType.Battlefield);aura.attachToEntity(permanent,null);}if(spec.script.contains("CheckSVar$ X")){currentPath.set(spec.pathId);castFixtureInstant(game,actor);currentPath.set(null);}}
    private static void castFixtureInstant(Game game,Player actor){Card c=addCard("Opt",actor,ZoneType.Hand);SpellAbility sa=c.getFirstSpellAbility();sa.setActivatingPlayer(actor);if(!PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa))throw new IllegalStateException("actual instant-history fixture cast rejected");drainStack(game);}
    private static void restoreMain1(Game game,Player actor){game.getPhaseHandler().devModeSet(PhaseType.MAIN1,actor);game.getPhaseHandler().setCombat(null);}
    private static void drainStack(Game game){int steps=0;while(true){game.getAction().checkStateEffects(true);game.getStack().addAllTriggeredAbilitiesToStack();if(game.getStack().isEmpty())break;if(++steps>512)throw new IllegalStateException("Direct31 stack did not quiesce");game.getStack().resolveStack();}if(game.getStack().isFrozen()||game.getStack().isResolving())throw new IllegalStateException("Direct31 stack remained non-quiescent");}
    '''
    s = replace_once(s, helper_anchor, helpers + helper_anchor, "Direct31 fixture helpers")

    old_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState),Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions)))'
    new_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState),Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions),Long.toString(e.sourceRootExecutions)))'
    s = replace_once(s, old_summary, new_summary, "source root summary evidence")

    require("PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa)" in s, "PlaySpellAbility route missing")
    require("resolveActualSourceAbility(spec,source)" in s, "actual source-bound ability binding missing")
    require("MagicStack.setWs33ResolutionObserver" in s, "stack observer missing")
    require("sa.resolve()" not in s, "direct SpellAbility.resolve shortcut present")
    require("sa.getTargets().add(" not in s, "manual target injection present")
    require("AbilityFactory.getAbility(spec.script,source)" not in s, "detached source ability reconstruction present")
    body=s[s.find(run_start):s.find(run_end,s.find(run_start))]
    require("bindTargets(sa)" not in body and ".setupTargets()" not in body, "qualification code pre-selects targets before PlaySpellAbility")

    args.harness.write_text(s, encoding="utf-8")
    print("WS33_A_REST_DIRECT_HARNESS=PASS paths=31 source_bound=true play_spell_ability=true manual_targets=false direct_resolve=false")

if __name__ == "__main__":
    main()
