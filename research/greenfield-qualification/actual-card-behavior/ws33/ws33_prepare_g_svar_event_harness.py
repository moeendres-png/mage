#!/usr/bin/env python3
"""Transform the stack-qualified Direct-G harness into the non-AF G trigger-parent campaign.

The generated Java test executes all 33 source-proven parent entrypoints for the 32
remaining effective G SVar paths. Forge TriggerHandler remains the authority for trigger
legality: qualification only constructs mode-appropriate event facts and fixture state,
then invokes production runTrigger / spell-cast paths. Observation-only hooks prove the
exact source trigger was admitted and the exact Execute target SVar reached non-fizzled
MagicStack resolution. Target SVars are never entered directly.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_G_SVAR_EVENT_HARNESS=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    i = text.find(start)
    require(i >= 0, f"{label}: start anchor missing")
    j = text.find(end, i)
    require(j >= 0, f"{label}: end anchor missing")
    return text[:i] + replacement + text[j:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    s = args.harness.read_text(encoding="utf-8")

    s = s.replace("Ws33GAbilityQualificationTest", "Ws33GSVarEventQualificationTest")
    s = s.replace("WS33 G-ABILITY", "WS33 G-SVAR-EVENT")

    s = replace_once(
        s,
        "import forge.game.ability.AbilityFactory;\n",
        "import forge.game.ability.AbilityFactory;\nimport forge.game.ability.AbilityKey;\nimport forge.game.card.CardCollection;\nimport forge.game.card.CardCopyService;\nimport forge.game.combat.Combat;\nimport forge.game.phase.PhaseType;\nimport forge.game.trigger.Trigger;\nimport forge.game.trigger.TriggerHandler;\nimport forge.game.trigger.TriggerType;\nimport forge.game.trigger.WrappedAbility;\nimport forge.game.zone.MagicStack;\n",
        "event runtime imports",
    )

    s = replace_once(
        s,
        'if(cases.size()!=28)throw new IllegalStateException("WS33 G-SVAR-EVENT expected 28 cases, got "+cases.size());',
        'if(cases.size()!=33)throw new IllegalStateException("WS33 G-SVAR-EVENT expected 33 parent cases, got "+cases.size());',
        "parent cardinality",
    )

    old_case = 'final int ordinal; final String pathId,oracleId,cardName,dispatch,implementation,sourcePath,sourceDirective,sourceToken,script; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){ordinal=Integer.parseInt(f[0]);pathId=f[1];oracleId=f[2];cardName=f[3];dispatch=f[4];implementation=f[5];sourcePath=f[6];sourceLine=Integer.parseInt(f[7]);sourceDirective=f[8];sourceToken=f[9];hidden="1".equals(f[10]);rng="1".equals(f[11]);replay="1".equals(f[12]);decision="1".equals(f[13]);script=new String(Base64.getDecoder().decode(f[14]),StandardCharsets.UTF_8);}'
    new_case = 'final int ordinal,entryIndex,parentCount; final String pathId,oracleId,cardName,targetSVar,dispatch,implementation,sourcePath,sourceDirective,parentSVar,consumerField,mode,targetScript,parentScript; final int sourceLine; final boolean hidden,rng,replay,decision;\n        CaseSpec(String[] f){if(f.length!=21)throw new IllegalArgumentException("WS33 G-SVAR-EVENT expected 21 case fields, got "+f.length);ordinal=Integer.parseInt(f[0]);pathId=f[1];entryIndex=Integer.parseInt(f[2]);parentCount=Integer.parseInt(f[3]);oracleId=f[4];cardName=f[5];targetSVar=f[6];dispatch=f[7];implementation=f[8];sourcePath=f[9];sourceLine=Integer.parseInt(f[10]);sourceDirective=f[11];parentSVar=f[12];consumerField=f[13];mode=f[14];hidden="1".equals(f[15]);rng="1".equals(f[16]);replay="1".equals(f[17]);decision="1".equals(f[18]);targetScript=new String(Base64.getDecoder().decode(f[19]),StandardCharsets.UTF_8);parentScript=new String(Base64.getDecoder().decode(f[20]),StandardCharsets.UTF_8);}'
    s = replace_once(s, old_case, new_case, "event case ABI")
    s = replace_once(s, 'if(f.length!=15)throw new IllegalArgumentException("bad case TSV fields="+f.length);', 'if(f.length!=21)throw new IllegalArgumentException("bad case TSV fields="+f.length);', "case TSV loader ABI")

    old_ev = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions;'
    new_ev = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions;'
    s = replace_once(s, old_ev, new_ev, "path evidence ABI")

    class_anchor = '    private static final String SECRET = "Black Lotus";\n'
    class_insert = '''    private static final String SECRET = "Black Lotus";\n    private static final AtomicReference<String> ws33CurrentParentKey=new AtomicReference<>();\n    private static final Map<String,ParentEvidence> ws33ParentEvidence=new LinkedHashMap<>();\n    private static final Map<String,CaseSpec> ws33ParentSpecs=new LinkedHashMap<>();\n    private static final class ParentEvidence {\n        final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",admittedApi="",admittedOriginalMapHash="",admittedCurrentMapHash=""; long triggerAdmissions,targetBindings,targetExecutions,resolutionCallbacks; int sourceCardId=-1,admittedAbilityId=-1,admittedSourceTrigger=-1,admittedHostId=-1; Trigger expectedTrigger; SpellAbility producerAbility; final List<String> resolutionTrace=new ArrayList<>();\n        ParentEvidence(CaseSpec s){spec=s;}\n    }\n'''
    s = replace_once(s, class_anchor, class_insert, "parent evidence registry")

    s = replace_once(
        s,
        'final AtomicReference<String> currentPath=new AtomicReference<>();final Map<String,CaseEvidence> evidence=new LinkedHashMap<>();for(CaseSpec c:cases)evidence.put(c.pathId,new CaseEvidence(c));',
        'final AtomicReference<String> currentPath=new AtomicReference<>();final Map<String,CaseEvidence> evidence=new LinkedHashMap<>();for(CaseSpec c:cases)evidence.putIfAbsent(c.pathId,new CaseEvidence(c));ws33ParentEvidence.clear();ws33ParentSpecs.clear();for(CaseSpec c:cases){String k=parentKey(c);if(ws33ParentEvidence.put(k,new ParentEvidence(c))!=null)throw new IllegalStateException("duplicate parent key "+k);ws33ParentSpecs.put(k,c);}',
        "32-path / 33-parent evidence initialization",
    )

    observer_anchor = 'Game.setSemanticStateObserver((game,checkpoint)->'
    observer_setup = '''TriggerHandler.setWs33TriggerObserver((trigger,ability)->{String k=ws33CurrentParentKey.get();if(k==null)return;ParentEvidence pe=ws33ParentEvidence.get(k);if(pe==null)return;boolean match;if("TRIGGER".equals(pe.spec.sourceDirective)){match=pe.expectedTrigger==trigger;}else{match=pe.sourceCardId==trigger.getHostCard().getId()&&pe.producerAbility!=null&&trigger.getSpawningAbility()==pe.producerAbility&&AbilityFactory.getMapParams(pe.spec.parentScript).equals(trigger.getOriginalMapParams());}if(match){pe.triggerAdmissions++;pe.admittedAbilityId=ability.getId();pe.admittedSourceTrigger=ability.getSourceTrigger();pe.admittedHostId=ability.getHostCard()==null?-1:ability.getHostCard().getId();pe.admittedApi=ability.getApi()==null?"":ability.getApi().name();pe.admittedOriginalMapHash=mapHash(ability.getOriginalMapParams());pe.admittedCurrentMapHash=mapHash(ability.getMapParams());if(matchesTarget(pe.spec,ability))pe.targetBindings++;}});\n        MagicStack.setWs33ResolutionObserver(ability->{String k=ws33CurrentParentKey.get();if(k==null)return;ParentEvidence pe=ws33ParentEvidence.get(k);if(pe==null)return;boolean wrapper=ability instanceof WrappedAbility;SpellAbility effective=wrapper?((WrappedAbility)ability).getWrappedAbility():ability;pe.resolutionCallbacks++;boolean targetMatch=matchesTarget(pe.spec,effective);pe.resolutionTrace.add("wrapper="+(wrapper?1:0)+",abilityId="+effective.getId()+",sourceTrigger="+effective.getSourceTrigger()+",hostId="+(effective.getHostCard()==null?-1:effective.getHostCard().getId())+",api="+(effective.getApi()==null?"":effective.getApi().name())+",originalMap="+mapHash(effective.getOriginalMapParams())+",currentMap="+mapHash(effective.getMapParams())+",targetMatch="+(targetMatch?1:0));if(targetMatch)pe.targetExecutions++;});\n        Game.setSemanticStateObserver((game,checkpoint)->'''
    s = replace_once(s, observer_anchor, observer_setup, "production reachability observers")

    cleanup_old = 'PlayerControllerHuman.setExternalDecisionProviderFactory(null);ExternalDecisionTape.setEventObserver(null);Game.setSemanticStateObserver(null);MyRandom.endGameScope();'
    cleanup_new = 'PlayerControllerHuman.setExternalDecisionProviderFactory(null);TriggerHandler.setWs33TriggerObserver(null);MagicStack.setWs33ResolutionObserver(null);ws33CurrentParentKey.set(null);ws33ParentEvidence.clear();ws33ParentSpecs.clear();ExternalDecisionTape.setEventObserver(null);Game.setSemanticStateObserver(null);MyRandom.endGameScope();'
    s = replace_once(s, cleanup_old, cleanup_new, "observer cleanup")

    write_call_old = 'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);'
    write_call_new = 'writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);writeResolutionLineage(outDir);'
    s = replace_once(s, write_call_old, write_call_new, "32-path plus 33-parent evidence output")

    run_start = 'private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath)'
    run_end = 'private static void awaitRemoteTransport(List<Player> ps)'
    run_method = r'''private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath){List<Player>ps=players(game);Player actor=ps.get(1),opponent=ps.get(2);for(CaseSpec spec:cases){String pk=parentKey(spec);ParentEvidence pe=ws33ParentEvidence.get(pk);CaseEvidence ce=evidence.get(spec.pathId);Card source=null;long leak0=-1,cross0=-1;try{seedCommon(game,actor,opponent);Card canary=addCard(SECRET,actor,ZoneType.Library);Ws05HiddenInfoProbe.setPhase(spec.pathId,canary.getId(),Set.of());preparePreSourceHistory(spec,game,actor,opponent);source=addCard(spec.cardName,actor,ZoneType.Battlefield);source.addRemembered(opponent);source.addRemembered(addCard("Runeclaw Bear",opponent,ZoneType.Battlefield));source.setChosenPlayer(opponent);source.setChosenType("Bear");opponent.setNamedCard("Runeclaw Bear");actor.setNamedCard("Runeclaw Bear");prepareSourceFixture(spec,game,actor,opponent,source,pe);game.getTriggerHandler().resetActiveTriggers();bindExpectedParent(spec,source,pe);awaitRemoteTransport(ps);leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks();cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();currentPath.set(spec.pathId);ws33CurrentParentKey.set(pk);if(ce.beforeState.isEmpty()){ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);}dispatchSourceEvent(spec,game,actor,opponent,source,pe);settleTriggeredStack(game);if(pe.triggerAdmissions!=1)throw new IllegalStateException("source-proven trigger admission count="+pe.triggerAdmissions+" parent="+pk);if(pe.targetBindings!=1)throw new IllegalStateException("Execute target binding count="+pe.targetBindings+" parent="+pk);if(pe.targetExecutions<1)throw new IllegalStateException("target SVar did not reach non-fizzled root resolution parent="+pk);pe.status="PASS";ce.stackAdmissions+=pe.triggerAdmissions;ce.stackResolutions+=pe.targetExecutions;ce.afterState=semanticState(game);ce.afterDigest=sha256(ce.afterState);}catch(Throwable t){pe.status="FAIL";pe.failureType=t.getClass().getName();pe.failureMessage=sanitize(String.valueOf(t.getMessage()));Ws05HiddenInfoProbe.observeException(t);}finally{ce.leakDelta+=leak0<0?0:Ws05HiddenInfoProbe.pilotVisibleLeaks()-leak0;ce.crossPrincipalDelta+=cross0<0?0:Ws05HiddenInfoProbe.crossPrincipalLeaks()-cross0;for(Player p:ps){ce.principalRequests.putIfAbsent(p.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(p.getId(),0L);}ws33CurrentParentKey.set(null);currentPath.set(null);retireSource(game,actor,source);game.getTriggerHandler().resetActiveTriggers();}}for(CaseEvidence ce:evidence.values()){List<ParentEvidence> parents=new ArrayList<>();for(ParentEvidence pe:ws33ParentEvidence.values())if(pe.spec.pathId.equals(ce.spec.pathId))parents.add(pe);boolean pass=!parents.isEmpty();for(ParentEvidence pe:parents)pass&="PASS".equals(pe.status);if(pass){ce.status="PASS";}else{ce.status="FAIL";for(ParentEvidence pe:parents)if(!"PASS".equals(pe.status)){ce.failureType=pe.failureType;ce.failureMessage=pe.failureMessage;break;}}}}
    '''
    s = replace_between(s, run_start, run_end, run_method, "event campaign replacement")

    helper_anchor = 'private static void awaitRemoteTransport(List<Player> ps)'
    helpers = r'''private static String parentKey(CaseSpec s){return s.pathId+"#"+s.entryIndex;}
    private static List<CaseSpec> uniqueCases(List<CaseSpec> cases){LinkedHashMap<String,CaseSpec>m=new LinkedHashMap<>();for(CaseSpec c:cases)m.putIfAbsent(c.pathId,c);if(m.size()!=32)throw new IllegalStateException("WS33 G-SVAR-EVENT expected 32 effective paths, got "+m.size());return new ArrayList<>(m.values());}
    private static String mapHash(Map<String,String> map){java.util.TreeMap<String,String> sorted=new java.util.TreeMap<>();if(map!=null)sorted.putAll(map);return sha256(sorted.toString());}
    private static boolean matchesTarget(CaseSpec spec,SpellAbility sa){if(sa==null||sa.getApi()==null||!spec.dispatch.equals(sa.getApi().name()))return false;Map<String,String>expected=AbilityFactory.getMapParams(spec.targetScript);return expected.equals(sa.getOriginalMapParams())||expected.equals(sa.getMapParams());}
    private static void bindExpectedParent(CaseSpec spec,Card source,ParentEvidence pe){if("TRIGGER".equals(spec.sourceDirective)){Map<String,String>expected=AbilityFactory.getMapParams(spec.parentScript);Trigger match=null;int matches=0;for(Trigger t:source.getTriggers())if(spec.mode.equals(t.getMode().toString())&&expected.equals(t.getOriginalMapParams())){match=t;matches++;}if(matches!=1)throw new IllegalStateException("actual-card parent trigger match count="+matches+" for "+parentKey(spec));pe.expectedTrigger=match;pe.sourceCardId=source.getId();return;}if("SVAR".equals(spec.sourceDirective)){if(spec.parentSVar.isEmpty()||!source.getCurrentState().hasSVar(spec.parentSVar))throw new IllegalStateException("missing source-proven parent SVar "+spec.parentSVar);if(!spec.parentScript.equals(source.getCurrentState().getSVar(spec.parentSVar)))throw new IllegalStateException("parent SVar script mismatch "+parentKey(spec));pe.sourceCardId=source.getId();return;}throw new IllegalStateException("unsupported parent directive "+spec.sourceDirective);}
    private static void preparePreSourceHistory(CaseSpec spec,Game game,Player actor,Player opponent){if(spec.parentScript.contains("CheckSVar$ RaidTest")){Card attacker=addCard("Runeclaw Bear",actor,ZoneType.Battlefield);actor.addCreaturesAttackedThisTurn(attacker,opponent);}if(spec.parentScript.contains("CheckSVar$ X")&&spec.cardName.equals("H.E.R.B.I.E., Lovable Robot")){castAndResolveFixtureSpell(game,actor,"Sol Ring");}}
    private static void prepareSourceFixture(CaseSpec spec,Game game,Player actor,Player opponent,Card source,ParentEvidence pe){if(spec.parentScript.contains("Count$ValidExile Creature.ExiledWithSource")||source.getSVar("X").contains("Count$ValidExile Creature.ExiledWithSource")){for(int i=0;i<4;i++){Card c=addCard(i%2==0?"Runeclaw Bear":"Grizzly Bears",actor,ZoneType.Exile);c.setExiledWith(source);c.setExiledBy(actor);source.addExiledCard(c);}}if("SVAR".equals(spec.sourceDirective)){SpellAbility producer=null;int n=0;for(SpellAbility sa:source.getSpellAbilities())if(sa.getManaPart()!=null&&sa.getManaPart().getTriggersWhenSpent()){producer=sa;n++;}if(n!=1)throw new IllegalStateException("expected one TriggersWhenSpent mana producer, got "+n);pe.producerAbility=producer;}}
    private static void dispatchSourceEvent(CaseSpec spec,Game game,Player actor,Player opponent,Card source,ParentEvidence pe){if("SpellCast".equals(spec.mode)){if("SVAR".equals(spec.sourceDirective)){Card commander=addCard("Serra Angel",actor,ZoneType.Command);commander.setCommander(true);actor.incCommanderCast(commander);SpellAbility spell=commander.getFirstSpellAbility();spell.setActivatingPlayer(actor);pe.producerAbility.getManaPart().addTriggersWhenSpent(spell);game.getStack().addAndUnfreeze(spell);return;}Card spellCard=addCard("Sol Ring",opponent,ZoneType.Hand);SpellAbility spell=spellCard.getFirstSpellAbility();spell.setActivatingPlayer(opponent);game.getStack().addAndUnfreeze(spell);return;}Map<AbilityKey,Object>rp=AbilityKey.newMap();if("ChangesZone".equals(spec.mode)){Card moved=spec.parentScript.contains("ValidCard$ Card.Self")?source:addCard("Runeclaw Bear",actor,ZoneType.Hand);Card lki=recordBattlefieldEntry(actor,moved);rp.put(AbilityKey.Card,moved);rp.put(AbilityKey.CardLKI,lki);rp.put(AbilityKey.Origin,ZoneType.Hand.name());rp.put(AbilityKey.Destination,ZoneType.Battlefield.name());}else if("Attacks".equals(spec.mode)){Card attacker=source;if(spec.parentScript.contains("Card.AttachedBy")){attacker=addCard("Runeclaw Bear",actor,ZoneType.Battlefield);source.attachToEntity(attacker,null);}game.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,actor);Combat combat=new Combat(actor);combat.addAttacker(attacker,opponent);game.getPhaseHandler().setCombat(combat);rp.put(AbilityKey.Attacker,attacker);rp.put(AbilityKey.Attacked,opponent);rp.put(AbilityKey.DefendingPlayer,opponent);}else if("AttackersDeclared".equals(spec.mode)){game.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,actor);Combat combat=new Combat(actor);CardCollection attackers=new CardCollection();int n=spec.parentScript.contains("ValidAttackersAmount$ GE4")?4:1;for(int i=0;i<n;i++){Card a=i==0&&source.isCreature()?source:addCard("Runeclaw Bear",actor,ZoneType.Battlefield);attackers.add(a);combat.addAttacker(a,opponent);actor.addCreaturesAttackedThisTurn(a,opponent);}game.getPhaseHandler().setCombat(combat);rp.put(AbilityKey.AttackingPlayer,actor);rp.put(AbilityKey.AttackedTarget,opponent);rp.put(AbilityKey.Attackers,attackers);}else if("DamageDone".equals(spec.mode)){rp.put(AbilityKey.DamageSource,source);rp.put(AbilityKey.DamageTarget,opponent);rp.put(AbilityKey.IsCombatDamage,true);}else if("DamageDoneOnce".equals(spec.mode)){Card dealer=addCard("Runeclaw Bear",actor,ZoneType.Battlefield);Map<Card,Integer>damage=new LinkedHashMap<>();damage.put(dealer,1);rp.put(AbilityKey.DamageTarget,opponent);rp.put(AbilityKey.DamageMap,damage);rp.put(AbilityKey.IsCombatDamage,true);}else if("Sacrificed".equals(spec.mode)){Card sacrificed=addCard("Runeclaw Bear",actor,ZoneType.Graveyard);rp.put(AbilityKey.Card,sacrificed);rp.put(AbilityKey.Player,actor);}else if("Phase".equals(spec.mode)){String phase=AbilityFactory.getMapParams(spec.parentScript).get("Phase");if(phase==null)throw new IllegalStateException("Phase trigger missing Phase param");game.getPhaseHandler().devModeSet(PhaseType.smartValueOf(phase),actor);rp.put(AbilityKey.Player,actor);}else throw new IllegalStateException("unsupported event mode "+spec.mode);game.getTriggerHandler().runTrigger(TriggerType.smartValueOf(spec.mode),rp,false);}
    private static Card recordBattlefieldEntry(Player actor,Card card){if(card.isInZone(ZoneType.Battlefield)){actor.getZone(ZoneType.Battlefield).remove(card);actor.getZone(ZoneType.Hand).add(card);}Card lki=CardCopyService.getLKICopy(card);actor.getZone(ZoneType.Hand).remove(card);actor.getZone(ZoneType.Battlefield).add(card,null,lki);return lki;}
    private static void castAndResolveFixtureSpell(Game game,Player player,String name){Card c=addCard(name,player,ZoneType.Hand);SpellAbility sa=c.getFirstSpellAbility();sa.setActivatingPlayer(player);game.getStack().addAndUnfreeze(sa);settleTriggeredStack(game);}
    private static void settleTriggeredStack(Game game){int steps=0;while(true){game.getStack().addAllTriggeredAbilitiesToStack();if(game.getStack().isEmpty())break;if(++steps>512)throw new IllegalStateException("event stack did not quiesce");game.getStack().resolveStack();}if(game.getStack().isFrozen()||game.getStack().isResolving())throw new IllegalStateException("event stack remained non-quiescent");}
    private static void retireSource(Game game,Player actor,Card source){if(source==null)return;forge.game.zone.Zone z=game.getZoneOf(source);if(z!=null)z.remove(source);actor.getZone(ZoneType.Exile).add(source);}
    '''
    s = replace_once(s, helper_anchor, helpers + helper_anchor, "event helpers")

    sha_anchor = 'private static String sha256(String value)'
    parent_writer = r'''private static void writeParentEvidence(Path out)throws IOException{try(var w=Files.newBufferedWriter(out.resolve("parent-summary.tsv"),StandardCharsets.UTF_8)){for(ParentEvidence pe:ws33ParentEvidence.values()){CaseSpec c=pe.spec;w.write(String.join("\t",c.pathId,Integer.toString(c.entryIndex),Integer.toString(c.parentCount),c.oracleId,c.cardName,c.mode,c.sourceDirective,c.parentSVar,c.targetSVar,c.dispatch,pe.status,Long.toString(pe.triggerAdmissions),Long.toString(pe.targetBindings),Long.toString(pe.targetExecutions),enc(pe.failureType),enc(pe.failureMessage)));w.newLine();}}}
    private static void writeResolutionLineage(Path out)throws IOException{try(var w=Files.newBufferedWriter(out.resolve("resolution-lineage.tsv"),StandardCharsets.UTF_8)){for(ParentEvidence pe:ws33ParentEvidence.values()){CaseSpec c=pe.spec;String trace=String.join(";",pe.resolutionTrace);String traceB64=Base64.getEncoder().encodeToString(trace.getBytes(StandardCharsets.UTF_8));w.write(String.join("\t",c.pathId,Integer.toString(c.entryIndex),Integer.toString(c.parentCount),c.oracleId,c.cardName,c.mode,c.sourceDirective,c.targetSVar,c.dispatch,Long.toString(pe.triggerAdmissions),Long.toString(pe.targetBindings),Long.toString(pe.targetExecutions),Long.toString(pe.resolutionCallbacks),Integer.toString(pe.admittedAbilityId),Integer.toString(pe.admittedSourceTrigger),Integer.toString(pe.admittedHostId),pe.admittedApi,pe.admittedOriginalMapHash,pe.admittedCurrentMapHash,traceB64));w.newLine();}}}
    '''
    s = replace_once(s, sha_anchor, parent_writer + sha_anchor, "parent and resolution-lineage evidence writers")

    # Static fail-closed invariants: production trigger admission and stack resolution only.
    for forbidden in (
        "ensureAbility().resolve(",
        "getOverridingAbility().resolve(",
        "AbilityFactory.getAbility(spec.targetScript",
        "performTest(",
        "requirementsCheck(",
        "meetsRequirementsOnTriggeredObjects(",
    ):
        require(forbidden not in s, f"forbidden trigger/rules shortcut remains: {forbidden}")
    for required in (
        "runTrigger(TriggerType.smartValueOf(spec.mode),rp,false)",
        "addAllTriggeredAbilitiesToStack()",
        "TriggerHandler.setWs33TriggerObserver",
        "MagicStack.setWs33ResolutionObserver",
        "addTriggersWhenSpent(spell)",
        "parent-summary.tsv",
        "resolution-lineage.tsv",
        "uniqueCases(cases)",
        "expected 33 parent cases",
        "expected 32 effective paths",
    ):
        require(required in s, f"missing production/evidence route: {required}")

    args.harness.write_text(s, encoding="utf-8")
    print("WS33_G_SVAR_EVENT_HARNESS=PASS parents=33 effective_paths=32 trigger_legality=FORGE_TRIGGER_HANDLER target_direct_entry=FALSE parent_observer=POST_LEGALITY_ADMISSION target_observer=POST_FIZZLE_PRE_RESOLVE resolution_lineage=OBSERVATION_ONLY")


if __name__ == "__main__":
    main()
