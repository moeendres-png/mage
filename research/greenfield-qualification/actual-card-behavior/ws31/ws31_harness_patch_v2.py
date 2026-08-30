#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {n}")
    return text.replace(old, new, 1)

def regex_once(text: str, pattern: str, repl: str, label: str, flags: int = 0) -> str:
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one regex match, found {n}")
    return new

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("java_file", type=Path)
    ns = ap.parse_args()
    p = ns.java_file
    text = p.read_text(encoding="utf-8")

    text = replace_once(text, "import forge.game.ability.AbilityFactory;",
        "import forge.game.ability.AbilityFactory;\nimport forge.game.ability.AbilityKey;", "AbilityKey import")
    text = replace_once(text, "import forge.game.card.Card;",
        "import forge.game.card.Card;\nimport forge.game.card.CounterEnumType;", "Counter import")
    text = replace_once(text, "import forge.game.player.Player;",
        "import forge.game.player.Player;\nimport forge.game.player.PlaySpellAbility;", "PlaySpellAbility import")
    text = replace_once(text, "import forge.game.zone.ZoneType;",
        "import forge.game.phase.PhaseType;\nimport forge.game.zone.ZoneType;", "PhaseType import")
    text = replace_once(text, "import forge.model.FModel;",
        "import forge.model.FModel;\nimport forge.localinstance.properties.ForgePreferences.FPref;", "FPref import")

    text = regex_once(
        text,
        r'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script; final int sourceLine; final boolean hidden,rng,replay,decision;',
        'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script,costShape,executionMode; final int sourceLine; final boolean hidden,rng,replay,decision,targeted;',
        "CaseSpec fields",
    )
    text = regex_once(
        text,
        r'CaseSpec\(String\[\] f\)\{ordinal=Integer\.parseInt\(f\[0\]\);pathId=f\[1\];oracleId=f\[2\];cardName=f\[3\];dispatch=f\[4\];implementation=f\[5\];sourcePath=f\[6\];sourceLine=Integer\.parseInt\(f\[7\]\);sourceDirective=f\[8\];sourceToken=f\[9\];hidden="1"\.equals\(f\[10\]\);rng="1"\.equals\(f\[11\]\);replay="1"\.equals\(f\[12\]\);decision="1"\.equals\(f\[13\]\);script=new String\(Base64\.getDecoder\(\)\.decode\(f\[14\]\),StandardCharsets\.UTF_8\);\}',
        'CaseSpec(String[] f){ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);costShape=new String(Base64.getDecoder().decode(f[15]),StandardCharsets.UTF_8);targeted="1".equals(f[16]);executionMode=f[17];}',
        "CaseSpec constructor",
    )

    text = replace_once(
        text,
        "TestUtils.ensureFModelInitialized();",
        'TestUtils.ensureFModelInitialized();FModel.getPreferences().setPref(FPref.UI_SELECT_FROM_CARD_DISPLAYS,"false");',
        "headless reveal preference",
    )

    text = regex_once(
        text,
        r'private static boolean ready\(Game game\)\{if\(game\.getAge\(\)!=GameStage\.Play\|\|game\.getRegisteredPlayers\(\)\.size\(\)!=4\)return false;for\(Player p:game\.getRegisteredPlayers\(\)\)if\(!\(p\.getController\(\) instanceof PlayerControllerHuman\)\)return false;return true;\}',
        'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4||!game.getPhaseHandler().is(PhaseType.MAIN1))return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;return game.getPhaseHandler().getPlayerTurn()!=null;}',
        "MAIN1 ready boundary",
    )

    new_campaign = '''private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath){List<Player>ps=players(game);Player actor=game.getPhaseHandler().getPlayerTurn();if(actor==null)throw new IllegalStateException("no active player at MAIN1");Player opponent=null;for(Player p:ps)if(p!=actor){opponent=p;break;}if(opponent==null)throw new IllegalStateException("no opponent");seedPayableResources(actor);for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);currentPath.set(spec.pathId);long leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks(),cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();try{seedCommon(game,actor,opponent);Card source=addCard(spec.cardName,actor,ZoneType.Battlefield);prepareSourceForPayment(spec,source,actor);source.addRemembered(opponent);Card remembered=addCard("Runeclaw Bear",opponent,ZoneType.Battlefield);source.addRemembered(remembered);opponent.setNamedCard("Runeclaw Bear");actor.setNamedCard("Runeclaw Bear");SpellAbility sa=AbilityFactory.getAbility(spec.script,source);sa.setActivatingPlayer(actor);prepareAbilityContext(spec,sa,actor);if(sa.getApi()==null||!spec.dispatch.equals(sa.getApi().name()))throw new IllegalStateException("dispatch mismatch runtime="+(sa.getApi()==null?"null":sa.getApi().name()));ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);if("COST_PAYMENT".equals(spec.executionMode)){if(!PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa))throw new IllegalStateException("PlaySpellAbility/CostPayment rejected exact path");}else{if(sa.usesTargeting()&&!sa.setupTargets())throw new IllegalStateException("authoritative target selection rejected exact path");game.getStack().add(sa);}drainStack(game);ce.afterState=semanticState(game);ce.afterDigest=sha256(ce.afterState);ce.status="PASS";}catch(Throwable t){ce.status="FAIL";ce.failureType=t.getClass().getName();ce.failureMessage=sanitize(String.valueOf(t.getMessage()));Ws05HiddenInfoProbe.observeException(t);}finally{ce.leakDelta=Ws05HiddenInfoProbe.pilotVisibleLeaks()-leak0;ce.crossPrincipalDelta=Ws05HiddenInfoProbe.crossPrincipalLeaks()-cross0;for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}currentPath.set(null);}}}'''
    text = regex_once(
        text,
        r'private static void runCampaign\(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath\)\{[^\n]*\}',
        new_campaign,
        "runCampaign replacement",
    )

    new_seed = '''private static void seedCommon(Game game,Player actor,Player opponent){String[]library={"Sol Ring","Island","Serra Angel","Lightning Bolt","Darksteel Ingot","Runeclaw Bear","Plains","Grizzly Bears","Ornithopter","Forest","Mountain","Swamp"};for(String n:library){addCard(n,actor,ZoneType.Library);addCard(n,opponent,ZoneType.Library);}for(int i=0;i<3;i++){addCard("Runeclaw Bear",actor,ZoneType.Hand);addCard("Grizzly Bears",opponent,ZoneType.Hand);}}
    private static void seedPayableResources(Player actor){String[]lands={"Plains","Island","Mountain","Forest","Swamp"};for(String land:lands)for(int i=0;i<8;i++)addCard(land,actor,ZoneType.Battlefield);}
    private static void prepareSourceForPayment(CaseSpec spec,Card source,Player actor){source.setSickness(false);source.setTapped(false);if(spec.costShape.contains("CHARGE"))source.setCounters(CounterEnumType.CHARGE,4);if(spec.costShape.contains("LOYALTY"))source.setCounters(CounterEnumType.LOYALTY,10);}
    private static void prepareAbilityContext(CaseSpec spec,SpellAbility sa,Player actor){if(spec.costShape.contains("TriggeredSources")){Card triggerSource=addCard("Runeclaw Bear",actor,ZoneType.Battlefield);triggerSource.setSickness(false);sa.setTriggeringObject(AbilityKey.Card,triggerSource);sa.setTriggeringObject(AbilityKey.Cards,List.of(triggerSource));sa.setTriggeringObject(AbilityKey.Source,triggerSource);sa.setTriggeringObject(AbilityKey.Sources,List.of(triggerSource));}}
    private static void drainStack(Game game){int guard=0;while(true){game.getAction().checkStateEffects(true);game.getStack().addAllTriggeredAbilitiesToStack();if(game.getStack().isEmpty())return;if(++guard>256)throw new IllegalStateException("stack did not quiesce");game.getStack().resolveStack();}}'''
    text = regex_once(
        text,
        r'private static void seedCommon\(Game game,Player actor,Player opponent\)\{[^\n]*\}',
        new_seed,
        "seed helpers",
    )

    text = regex_once(
        text,
        r'\n    private static void bindTarget\(SpellAbility sa,Game game,Player actor,Player opponent\)\{[^\n]*\}',
        "",
        "remove bindTarget",
    )

    new_decks = '''private static List<Deck>createDecks(){List<Deck>d=new ArrayList<>();PaperCard commander=FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");PaperCard secret=FModel.getMagicDb().getCommonCards().getCard(SECRET);if(commander==null||secret==null)throw new IllegalStateException("qualification card unavailable");for(int i=0;i<4;i++){Deck x=TestDeckLoader.createMinimalDeck("Plains",12);x.getOrCreate(DeckSection.Commander).add(commander);x.getOrCreate(DeckSection.Sideboard).add(secret);d.add(x);}return d;}'''
    text = regex_once(text, r'private static List<Deck>createDecks\(\)\{[^\n]*\}', new_decks, "sideboard canary decks")

    new_semantic = '''private static String semanticState(Game game){StringBuilder s=new StringBuilder();for(Player p:players(game)){s.append("P|").append(p.getId()).append('|').append(p.getLife()).append("|MANA:");int manaCount=0;for(forge.game.mana.Mana ignored:p.getManaPool())manaCount++;s.append(manaCount);for(ZoneType z:new ZoneType[]{ZoneType.Library,ZoneType.Hand,ZoneType.Battlefield,ZoneType.Graveyard,ZoneType.Exile,ZoneType.Command,ZoneType.Sideboard}){s.append('|').append(z.name()).append(':');List<String>names=new ArrayList<>();for(Card c:p.getCardsIn(z))names.add(c.getName()+"#T"+c.isTapped()+"#L"+c.getCounters(CounterEnumType.LOYALTY)+"#C"+c.getCounters(CounterEnumType.CHARGE));if(z!=ZoneType.Library)names.sort(String::compareTo);for(String n:names)s.append(n).append(',');}}return s.toString();}'''
    text = regex_once(text, r'private static String semanticState\(Game game\)\{[^\n]*\}', new_semantic, "semantic state")

    text = replace_once(
        text,
        'if(f.length!=15)throw new IllegalArgumentException("bad case TSV fields="+f.length);',
        'if(f.length!=18)throw new IllegalArgumentException("bad case TSV fields="+f.length);',
        "case TSV width",
    )

    text = replace_once(
        text,
        '  \\"phase_mismatches\\":"+Ws05HiddenInfoProbe.phaseMismatchCount()+",\\n  \\"outer_failure\\":',
        '  \\"phase_mismatches\\":"+Ws05HiddenInfoProbe.phaseMismatchCount()+",\\n  \\"decoded_transport_samples\\":"+Ws05HiddenInfoProbe.transportSamples()+",\\n  \\"face_down_hidden_samples\\":"+Ws05HiddenInfoProbe.faceDownSamples()+",\\n  \\"decision_requests\\":"+Ws05HiddenInfoProbe.requestCount()+",\\n  \\"replay_events\\":"+Ws05HiddenInfoProbe.replayCount()+",\\n  \\"outer_failure\\":',
        "process hidden metrics",
    )

    if "bindTarget(" in text:
        raise SystemExit("bindTarget bypass still present")
    if "sa.resolve()" in text:
        raise SystemExit("direct sa.resolve bypass still present")
    for required in ("PlaySpellAbility.playSpellAbility", "sa.setupTargets()", "game.getStack().resolveStack()", "ZoneType.Sideboard"):
        if required not in text:
            raise SystemExit(f"required harness path missing: {required}")

    p.write_text(text, encoding="utf-8")
    print("WS31_BIND_TARGET_BYPASS=FALSE")
    print("WS31_DIRECT_RESOLVE_BYPASS=FALSE")
    print("WS31_COST_PAYMENT_PATH=TRUE")
    print("WS31_MAGIC_STACK_PATH=TRUE")
    print("WS31_SIDEBOARD_CANARY=TRUE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
