#!/usr/bin/env python3
"""Harden A-rest AF8 around Forge's production cast/payment path and positive evidence.

Qualification-only transform. It never invents legal modes, targets, costs, payments or
rules outcomes. The source-bound parent is played through PlaySpellAbility; the pilot
chooses only options Forge emitted. Runtime observers record exact source-root/target
reachability, public-zone target effects, and real remote-client confidentiality samples.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_SVAR_AF8_RUNTIME_HARDEN=FAIL " + m)


def replace_once(t: str, old: str, new: str, label: str) -> str:
    n = t.count(old)
    require(n == 1, f"{label}: expected one anchor, got {n}")
    return t.replace(old, new, 1)


def replace_between(t: str, start: str, end: str, replacement: str, label: str) -> str:
    i = t.find(start)
    require(i >= 0, label + ": start anchor missing")
    j = t.find(end, i)
    require(j >= 0, label + ": end anchor missing")
    return t[:i] + replacement + t[j:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    p = args.harness
    t = p.read_text(encoding="utf-8")

    t = replace_once(
        t,
        "import forge.game.spellability.SpellAbility;\n",
        "import forge.game.phase.PhaseType;\nimport forge.game.player.PlaySpellAbility;\nimport forge.game.spellability.SpellAbility;\nimport forge.game.zone.MagicStack;\n",
        "production play imports",
    )

    registry = "    private static final Map<String,String> ws33DesiredModeSemantic=new ConcurrentHashMap<>();\n"
    evidence_state = registry + (
        '    private static final String WS33_AF8_BOB="Bob (Remote)",WS33_AF8_CHARLIE="Charlie (Remote)",WS33_AF8_DIANA="Diana (Remote)";\n'
        '    private static final class Af8TargetRow {int cardId,sourceCardId,rootAbilityId,childSubId,actorId;String name="",types="",beforeZone="",afterZone="UNKNOWN";boolean isCreature,beforeHasKw,afterHasKw;}\n'
        '    private static final class Af8EffectEvidence {final Set<Integer> ids=new LinkedHashSet<>();final List<Card> targets=new ArrayList<>();final List<Af8TargetRow> rows=new ArrayList<>();String kind="",expected="",error="";int positive;}\n'
        '    private static final class Af8ObservationEvidence {long bob,charlie,diana,mismatchDelta;}\n'
        '    private static final Map<String,Af8EffectEvidence> ws33Af8Effects=new ConcurrentHashMap<>();\n'
        '    private static final Map<String,Af8ObservationEvidence> ws33Af8Observations=new ConcurrentHashMap<>();\n'
        '    private static final CopyOnWriteArrayList<String> ws33Af8Selections=new CopyOnWriteArrayList<>();\n'
        '    private static final Map<String,Integer> ws33Af8SourceCard=new ConcurrentHashMap<>();\n'
        '    private static final Map<String,Integer> ws33Af8RootAbility=new ConcurrentHashMap<>();\n'
        '    private static final Map<String,Integer> ws33Af8Actor=new ConcurrentHashMap<>();\n'
    )
    t = replace_once(t, registry, evidence_state, "AF8 evidence registries")

    old_ev = 'long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions,targetExecutions;'
    new_ev = 'long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions,targetExecutions,sourceRootExecutions;'
    t = replace_once(t, old_ev, new_ev, "source-root evidence counter")

    t = replace_once(
        t,
        'final CopyOnWriteArrayList<ExternalDecisionTape.Event> allDecisions=new CopyOnWriteArrayList<>();final CopyOnWriteArrayList<String> decisionPath=new CopyOnWriteArrayList<>();',
        'final CopyOnWriteArrayList<ExternalDecisionTape.Event> allDecisions=new CopyOnWriteArrayList<>();final CopyOnWriteArrayList<String> decisionPath=new CopyOnWriteArrayList<>();final CopyOnWriteArrayList<String> playStages=new CopyOnWriteArrayList<>();',
        "play-stage evidence list",
    )

    # Source-proven X needs a positive discretionary value so TargetMax$ X actually has
    # a targetable cardinality. Selection remains strictly inside Forge's opaque options.
    # The authoritative X-announcement request for a mandatory-cost production is exactly
    # PlayerControllerHuman.chooseNumber -> external kind NUMBER (Forge pin,
    # PlaySpellAbility.announceValuesLikeX -> announceRequirements -> chooseNumber).
    # Non-mandatory announcements arrive as GUI_GET_INTEGER and unrelated numeric
    # requests arrive under other kinds; none of those may take the positive-X branch.
    policy_anchor = 'CaseSpec pathSpec=ws33CaseSpecs.get(path);'
    policy = policy_anchor + (
        'if(pathSpec!=null&&"NUMBER".equals(req.getDecisionKind())&&pathSpec.script.contains("Announce$ X")&&req.getMinimumSelection()==1&&req.getMaximumSelection()==1){'
        'ExternalDecisionRequest.Option best=null;int bestValue=Integer.MAX_VALUE;for(ExternalDecisionRequest.Option o:options){if(o.isEntityBacked())continue;try{int v=Integer.parseInt(o.getSemanticValue());if(v>0&&v<bestValue){best=o;bestValue=v;}}catch(NumberFormatException ignored){}}'
        'if(best!=null){selected.add(best.getOptionId());recordAf8Selection(path,req,selected,"POSITIVE_X_ANNOUNCEMENT");return;}}'
    )
    t = replace_once(t, policy_anchor, policy, "positive source-proven X policy")

    # Replace the synthetic pre-stack parent path with the same qualified production
    # boundary used by Direct31: remote principal, real MAIN1, PlaySpellAbility and costs.
    run_start = 'private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath)'
    run_end = 'private static SpellAbility resolveSourceParent(CaseSpec spec,Card source){'
    run = r'''private static void runCampaign(Game game,List<CaseSpec>cases,Map<String,CaseEvidence>evidence,AtomicReference<String>currentPath){
        ws33CaseSpecs.clear();ws33Af8Effects.clear();ws33Af8Observations.clear();ws33Af8Selections.clear();ws33Af8SourceCard.clear();ws33Af8RootAbility.clear();ws33Af8Actor.clear();for(CaseSpec c:cases)ws33CaseSpecs.put(c.pathId,c);
        List<Player>ps=players(game);if(ps.size()!=4)throw new IllegalStateException("AF8 requires exact 4P harness");Player actor=ps.get(1),opponent=ps.get(2);if(actor==opponent)throw new IllegalStateException("remote actor/opponent alias");
        restoreMain1(game,actor);if(game.getPhaseHandler().getPlayerTurn()!=actor||!game.getPhaseHandler().is(PhaseType.MAIN1))throw new IllegalStateException("failed to establish remote actor MAIN1");seedPayableResources(actor);
        for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);long leak0=-1,cross0=-1,mismatch0=-1;Card source=null;try{
            refreshPayableResources(actor);restoreMain1(game,actor);seedCommon(game,actor,opponent);prepareAF8PublicCandidates(actor,opponent);
            Card canary=addCard(SECRET,actor,ZoneType.Library);Ws05HiddenInfoProbe.setPhase(spec.pathId,canary.getId(),Set.of());mismatch0=Ws05HiddenInfoProbe.phaseMismatchCount();
            source=addCard(spec.cardName,actor,"SP$".equals(spec.sourceToken)?ZoneType.Hand:ZoneType.Battlefield);source.setSickness(false);source.setTapped(false);source.addRemembered(opponent);source.addRemembered(addCard("Runeclaw Bear",opponent,ZoneType.Battlefield));opponent.setNamedCard("Runeclaw Bear");actor.setNamedCard("Runeclaw Bear");
            SpellAbility sa=resolveSourceParent(spec,source);sa.setActivatingPlayer(actor);prepareSourceDependentPositiveWitness(spec,sa,source,actor);if(sa.getApi()==null||!spec.dispatch.equals(sa.getApi().name()))throw new IllegalStateException("dispatch mismatch runtime="+(sa.getApi()==null?"null":sa.getApi().name()));
            armSourceParentPolicy(spec,sa);ws33Af8SourceCard.put(spec.pathId,source.getId());ws33Af8RootAbility.put(spec.pathId,sa.getId());ws33Af8Actor.put(spec.pathId,actor.getId());awaitRemoteTransport(ps);leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks();cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();ExternalObservationTrace.setPath(spec.pathId);currentPath.set(spec.pathId);
            ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);
            if(!PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa))throw new IllegalStateException("Forge PlaySpellAbility rejected exact AF8 source parent");ce.stackAdmissions++;
            drainStack(game);if(ce.sourceRootExecutions<1)throw new IllegalStateException("exact AF8 source root did not reach MagicStack resolution");ce.stackResolutions++;game.getAction().checkStateEffects(true);awaitRemoteTransport(ps);
            assertAF8PositiveEffect(spec,ce);captureAF8Observation(spec,mismatch0);assertAF8Observation(spec);
            ce.afterState=semanticState(game);ce.afterDigest=sha256(ce.afterState);ce.status="PASS";
        }catch(Throwable x){ce.status="FAIL";ce.failureType=x.getClass().getName();ce.failureMessage=sanitize(String.valueOf(x.getMessage()));Ws05HiddenInfoProbe.observeException(x);}finally{
            ce.leakDelta=leak0<0?0:Ws05HiddenInfoProbe.pilotVisibleLeaks()-leak0;ce.crossPrincipalDelta=cross0<0?0:Ws05HiddenInfoProbe.crossPrincipalLeaks()-cross0;for(Player q:ps){ce.principalRequests.putIfAbsent(q.getId(),0L);ce.principalCardOptionRequests.putIfAbsent(q.getId(),0L);}ws33DesiredModeSemantic.remove(spec.pathId);ExternalObservationTrace.clearPath();currentPath.set(null);restoreMain1(game,actor);
        }}
    }
    '''
    t = replace_between(t, run_start, run_end, run, "production AF8 campaign")

    helper_anchor = 'private static SpellAbility resolveSourceParent(CaseSpec spec,Card source){'
    helpers = r'''private static boolean matchesSourceRoot(CaseSpec spec,SpellAbility ability){if(ability==null||ability.getApi()==null||!spec.dispatch.equals(ability.getApi().name()))return false;Map<String,String>expected=AbilityFactory.getMapParams(spec.script);return expected.equals(ability.getOriginalMapParams())||expected.equals(ability.getMapParams());}
    private static void armSourceParentPolicy(CaseSpec spec,SpellAbility sa){if(!"Charm".equals(spec.dispatch))return;String desired=desiredTargetModeSemantic(spec,sa);ws33DesiredModeSemantic.put(spec.pathId,desired);}
    private static long af8Binom(int n,int k){if(k<0||k>n)return 0;long r=1;for(int i=1;i<=k;i++)r=r*(n-k+i)/i;return r;}
    private static boolean isAf8ForcedSelection(int n,int min,int max){long total=0;for(int k=Math.max(0,min);k<=Math.min(n,max);k++){total+=af8Binom(n,k);if(total>1)return false;}return total==1;}
    private static void recordAf8Selection(String path,ExternalDecisionRequest req,List<String> selected,String basis){List<ExternalDecisionRequest.Option> opts=new ArrayList<>(req.getOptions());int n=opts.size(),min=req.getMinimumSelection(),max=req.getMaximumSelection();boolean entityBacked=false;for(ExternalDecisionRequest.Option o:opts)if(o.isEntityBacked())entityBacked=true;StringBuilder ids=new StringBuilder(),sems=new StringBuilder();if(!entityBacked){for(String id:selected)ids.append(ids.length()==0?"":",").append(id);for(ExternalDecisionRequest.Option o:opts)for(String id:selected)if(o.getOptionId().equals(id))sems.append(sems.length()==0?"":",").append(enc(o.getSemanticValue()==null?"":o.getSemanticValue()));}ws33Af8Selections.add(path+"\\t"+req.getDecisionKind()+"\\t"+req.getActorId()+"\\t"+req.getPrincipalId()+"\\t"+n+"\\t"+min+"\\t"+max+"\\t"+selected.size()+"\\t"+ids.toString()+"\\t"+sems.toString()+"\\t"+basis+"\\t"+isAf8ForcedSelection(n,min,max));}
    private static boolean af8HasKeywords(Card c,String expected){for(String kw:expected.split(" & "))if(!kw.isBlank()&&!c.hasKeyword(kw.trim()))return false;return true;}
    private static String af8ZoneName(Card c){try{return c.getZone()==null?"null":String.valueOf(c.getZone().getZoneType());}catch(Throwable x){return "UNKNOWN";}}
    private static void captureAF8TargetExecution(CaseEvidence ce,AbilitySub sub){if(ce==null||sub==null||!matchesTarget(ce.spec,sub))return;ce.targetExecutions++;Af8EffectEvidence e=ws33Af8Effects.computeIfAbsent(ce.spec.pathId,k->new Af8EffectEvidence());try{Map<String,String>m=AbilityFactory.getMapParams(ce.spec.targetScript);String api=m.get("DB");if("ChangeZone".equals(api)){e.kind="ZONE";e.expected=m.getOrDefault("Destination","");}else if("Pump".equals(api)&&m.containsKey("KW")){e.kind="KEYWORD";e.expected=m.get("KW");}else{e.error="unsupported positive effect shape "+String.valueOf(api);return;}int sourceCard=ws33Af8SourceCard.getOrDefault(ce.spec.pathId,-1);int rootAbility=ws33Af8RootAbility.getOrDefault(ce.spec.pathId,-1);int actorId=ws33Af8Actor.getOrDefault(ce.spec.pathId,-1);for(Card c:sub.getTargets().getTargetCards()){if(c==null||!e.ids.add(c.getId()))continue;e.targets.add(c);Af8TargetRow row=new Af8TargetRow();row.cardId=c.getId();row.sourceCardId=sourceCard;row.rootAbilityId=rootAbility;row.childSubId=sub.getId();row.actorId=actorId;try{row.name=c.getName();}catch(Throwable x){row.name="";}try{row.types=String.valueOf(c.getType());}catch(Throwable x){row.types="";}try{row.isCreature=c.isCreature();}catch(Throwable x){row.isCreature=false;}row.beforeZone=af8ZoneName(c);if("KEYWORD".equals(e.kind)){try{row.beforeHasKw=af8HasKeywords(c,e.expected);}catch(Throwable x){row.beforeHasKw=false;}}e.rows.add(row);}}catch(Throwable x){e.error=x.getClass().getName()+":"+String.valueOf(x.getMessage());}}
    private static Card af8RowCard(Af8EffectEvidence e,Af8TargetRow row){for(Card t:e.targets)if(t.getId()==row.cardId)return t;throw new IllegalStateException("AF8 target row without live card "+row.cardId);}
    private static void assertAF8PositiveEffect(CaseSpec spec,CaseEvidence ce){Af8EffectEvidence e=ws33Af8Effects.get(spec.pathId);if(e==null||!e.error.isEmpty()||e.targets.isEmpty())throw new IllegalStateException("missing AF8 positive target evidence "+(e==null?"":e.error));int positive=0;if("ZONE".equals(e.kind)){ZoneType z=ZoneType.smartValueOf(e.expected);if(z==null)throw new IllegalStateException("invalid AF8 destination "+e.expected);for(Af8TargetRow row:e.rows){Card c=af8RowCard(e,row);row.afterZone=af8ZoneName(c);if(!row.beforeZone.equals(e.expected)&&row.afterZone.equals(e.expected))positive++;}}else if("KEYWORD".equals(e.kind)){for(Af8TargetRow row:e.rows){Card c=af8RowCard(e,row);try{row.afterHasKw=af8HasKeywords(c,e.expected);}catch(Throwable x){row.afterHasKw=false;}row.afterZone=af8ZoneName(c);if(row.afterHasKw)positive++;}}else throw new IllegalStateException("unknown AF8 effect evidence kind "+e.kind);e.positive=positive;if(positive<1)throw new IllegalStateException("AF8 target effect did not materialize kind="+e.kind+" expected="+e.expected);if(ce.targetExecutions<1)throw new IllegalStateException("AF8 target AbilitySub did not execute");}
    private static void captureAF8Observation(CaseSpec spec,long mismatch0){Af8ObservationEvidence o=new Af8ObservationEvidence();o.bob=Ws05HiddenInfoProbe.phaseSampleCount(spec.pathId,WS33_AF8_BOB);o.charlie=Ws05HiddenInfoProbe.phaseSampleCount(spec.pathId,WS33_AF8_CHARLIE);o.diana=Ws05HiddenInfoProbe.phaseSampleCount(spec.pathId,WS33_AF8_DIANA);o.mismatchDelta=mismatch0<0?Long.MAX_VALUE:Ws05HiddenInfoProbe.phaseMismatchCount()-mismatch0;ws33Af8Observations.put(spec.pathId,o);}
    private static void assertAF8Observation(CaseSpec spec){Af8ObservationEvidence o=ws33Af8Observations.get(spec.pathId);if(o==null||o.bob<1||o.charlie<1||o.diana<1||o.mismatchDelta!=0)throw new IllegalStateException("missing/mismatched AF8 real client confidentiality samples");}
    private static void seedPayableResources(Player actor){String[]lands={"Plains","Island","Swamp","Mountain","Forest"};for(String n:lands)for(int i=0;i<10;i++){Card c=addCard(n,actor,ZoneType.Battlefield);c.setTapped(false);}}
    private static void refreshPayableResources(Player actor){for(Card c:actor.getCardsIn(ZoneType.Battlefield))if(c.isLand()&&c.isTapped())c.untap();}
    private static void restoreMain1(Game game,Player actor){game.getPhaseHandler().devModeSet(PhaseType.MAIN1,actor);game.getPhaseHandler().setCombat(null);}
    private static void drainStack(Game game){int steps=0;while(true){game.getAction().checkStateEffects(true);game.getStack().addAllTriggeredAbilitiesToStack();if(game.getStack().isEmpty())break;if(++steps>512)throw new IllegalStateException("AF8 stack did not quiesce");game.getStack().resolveStack();}if(game.getStack().isFrozen()||game.getStack().isResolving())throw new IllegalStateException("AF8 stack remained non-quiescent");}
    private static void writeAF8Evidence(Path outDir,List<CaseSpec>cases,Map<String,CaseEvidence>evidence)throws IOException{List<String>effects=new ArrayList<>(),obs=new ArrayList<>();for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);Af8EffectEvidence e=ws33Af8Effects.get(spec.pathId);Af8ObservationEvidence o=ws33Af8Observations.get(spec.pathId);effects.add(spec.pathId+"\t"+(e==null?"":e.kind)+"\t"+enc(e==null?"":e.expected)+"\t"+(e==null?0:e.targets.size())+"\t"+(e==null?0:e.positive)+"\t"+(ce==null?0:ce.sourceRootExecutions));obs.add(spec.pathId+"\t"+(o==null?0:o.bob)+"\t"+(o==null?0:o.charlie)+"\t"+(o==null?0:o.diana)+"\t"+(o==null?Long.MAX_VALUE:o.mismatchDelta));}Files.write(outDir.resolve("AF8_EFFECT_EVIDENCE.tsv"),effects,StandardCharsets.UTF_8);Files.write(outDir.resolve("AF8_CLIENT_OBSERVATION_SAMPLES.tsv"),obs,StandardCharsets.UTF_8);}
    '''
    t = replace_once(t, helper_anchor, helpers + helper_anchor, "AF8 positive/runtime evidence helpers")

    # Export per-target identity-bound rows and the per-policy selection witness
    # beside the inherited per-path summaries. Entity-backed selections record counts
    # only, never card identities, so no hidden-zone payload can leak through them.
    old_write = 'private static void writeAF8Evidence(Path outDir,List<CaseSpec>cases,Map<String,CaseEvidence>evidence)throws IOException{List<String>effects=new ArrayList<>(),obs=new ArrayList<>();for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);Af8EffectEvidence e=ws33Af8Effects.get(spec.pathId);Af8ObservationEvidence o=ws33Af8Observations.get(spec.pathId);effects.add(spec.pathId+"\\t"+(e==null?"":e.kind)+"\\t"+enc(e==null?"":e.expected)+"\\t"+(e==null?0:e.targets.size())+"\\t"+(e==null?0:e.positive)+"\\t"+(ce==null?0:ce.sourceRootExecutions));obs.add(spec.pathId+"\\t"+(o==null?0:o.bob)+"\\t"+(o==null?0:o.charlie)+"\\t"+(o==null?0:o.diana)+"\\t"+(o==null?Long.MAX_VALUE:o.mismatchDelta));}Files.write(outDir.resolve("AF8_EFFECT_EVIDENCE.tsv"),effects,StandardCharsets.UTF_8);Files.write(outDir.resolve("AF8_CLIENT_OBSERVATION_SAMPLES.tsv"),obs,StandardCharsets.UTF_8);}'
    new_write = 'private static void writeAF8Evidence(Path outDir,List<CaseSpec>cases,Map<String,CaseEvidence>evidence)throws IOException{List<String>effects=new ArrayList<>(),obs=new ArrayList<>(),targets=new ArrayList<>();for(CaseSpec spec:cases){CaseEvidence ce=evidence.get(spec.pathId);Af8EffectEvidence e=ws33Af8Effects.get(spec.pathId);Af8ObservationEvidence o=ws33Af8Observations.get(spec.pathId);effects.add(spec.pathId+"\\t"+(e==null?"":e.kind)+"\\t"+enc(e==null?"":e.expected)+"\\t"+(e==null?0:e.targets.size())+"\\t"+(e==null?0:e.positive)+"\\t"+(ce==null?0:ce.sourceRootExecutions));obs.add(spec.pathId+"\\t"+(o==null?0:o.bob)+"\\t"+(o==null?0:o.charlie)+"\\t"+(o==null?0:o.diana)+"\\t"+(o==null?Long.MAX_VALUE:o.mismatchDelta));if(e!=null)for(Af8TargetRow row:e.rows)targets.add(spec.pathId+"\\t"+row.cardId+"\\t"+enc(row.name)+"\\t"+enc(row.types)+"\\t"+row.isCreature+"\\t"+row.beforeZone+"\\t"+row.afterZone+"\\t"+row.beforeHasKw+"\\t"+row.afterHasKw+"\\t"+row.sourceCardId+"\\t"+row.rootAbilityId+"\\t"+row.childSubId+"\\t"+row.actorId);}Files.write(outDir.resolve("AF8_EFFECT_EVIDENCE.tsv"),effects,StandardCharsets.UTF_8);Files.write(outDir.resolve("AF8_CLIENT_OBSERVATION_SAMPLES.tsv"),obs,StandardCharsets.UTF_8);Files.write(outDir.resolve("AF8_TARGET_EVIDENCE.tsv"),targets,StandardCharsets.UTF_8);Files.write(outDir.resolve("AF8_SELECTION_WITNESS.tsv"),ws33Af8Selections,StandardCharsets.UTF_8);}'
    t = replace_once(t, old_write, new_write, "AF8 identity-bound evidence export")

    # Witness the authoritative fallback policy branch too: stable-order selection with
    # its forced/non-discretionary classification. Entity-backed selections record
    # counts only (see recordAf8Selection), so this adds no hidden-zone payload.
    t = replace_once(
        t,
        'for(int i=0;i<count;i++)selected.add(options.get(i).getOptionId());}',
        'for(int i=0;i<count;i++)selected.add(options.get(i).getOptionId());recordAf8Selection(path,req,selected,"AUTHORITATIVE_STABLE_ORDER");}',
        "generic policy selection witness",
    )

    # Bind observational callbacks. They may record evidence but never choose/mutate a rule result.
    old_observer = 'AbilitySub.setWs33ResolutionObserver(sub->{String p=currentPath.get();if(p!=null){CaseEvidence ce=evidence.get(p);if(ce!=null&&matchesTarget(ce.spec,sub))ce.targetExecutions++;}});ExternalDecisionTape.setEventObserver(event->{'
    new_observer = 'MagicStack.setWs33ResolutionObserver(ability->{String q=currentPath.get();if(q!=null){CaseEvidence ce=evidence.get(q);if(ce!=null&&matchesSourceRoot(ce.spec,ability))ce.sourceRootExecutions++;}});AbilitySub.setWs33ResolutionObserver(sub->{String q=currentPath.get();if(q!=null)captureAF8TargetExecution(evidence.get(q),sub);});PlaySpellAbility.setWs33PlayStageObserver((stage,ability,result)->{String q=currentPath.get();if(q!=null)playStages.add(enc(q)+"\\t"+enc(stage)+"\\t"+result+"\\t"+enc(ability==null||ability.getApi()==null?"":ability.getApi().name()));});ExternalDecisionTape.setEventObserver(event->{'
    t = replace_once(t, old_observer, new_observer, "AF8 runtime observer bindings")

    # Persist positive evidence and source-stage evidence beside inherited tapes/traces.
    trace_export = 'ExternalObservationTrace.write(outDir.resolve("PRINCIPAL_OBSERVATIONS.jsonl"));'
    t = replace_once(t, trace_export, trace_export + 'Files.write(outDir.resolve("play-stages.tsv"),playStages,StandardCharsets.UTF_8);writeAF8Evidence(outDir,cases,evidence);', "AF8 evidence export")
    t = replace_once(t, 'AbilitySub.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);', 'PlaySpellAbility.setWs33PlayStageObserver(null);MagicStack.setWs33ResolutionObserver(null);AbilitySub.setWs33ResolutionObserver(null);ExternalDecisionTape.setEventObserver(null);', "AF8 observer cleanup")

    old_summary = 'Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions),Long.toString(e.targetExecutions)))'
    new_summary = 'Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions),Long.toString(e.targetExecutions),Long.toString(e.sourceRootExecutions)))'
    t = replace_once(t, old_summary, new_summary, "source-root summary column")

    required = (
        'PlaySpellAbility.playSpellAbility(actor.getController(),actor,sa)',
        'MagicStack.setWs33ResolutionObserver',
        'PlaySpellAbility.setWs33PlayStageObserver',
        'captureAF8TargetExecution',
        'assertAF8PositiveEffect(spec,ce)',
        'AF8_CLIENT_OBSERVATION_SAMPLES.tsv',
        'AF8_TARGET_EVIDENCE.tsv',
        'AF8_SELECTION_WITNESS.tsv',
        'recordAf8Selection(path,req,selected,"POSITIVE_X_ANNOUNCEMENT")',
        'recordAf8Selection(path,req,selected,"AUTHORITATIVE_STABLE_ORDER")',
        'isAf8ForcedSelection(n,min,max)',
        'ws33Af8SourceCard.put(spec.pathId,source.getId())',
        'ws33Af8RootAbility.put(spec.pathId,sa.getId())',
        'ws33Af8Actor.put(spec.pathId,actor.getId())',
        'row.beforeZone=af8ZoneName(c)',
        'row.afterZone=af8ZoneName(c)',
        '!row.beforeZone.equals(e.expected)&&row.afterZone.equals(e.expected)',
        'Ws05HiddenInfoProbe.phaseSampleCount',
        'refreshPayableResources(actor)',
        'c.isLand()&&c.isTapped())c.untap()',
        'sourceRootExecutions',
        '"NUMBER".equals(req.getDecisionKind())&&pathSpec.script.contains("Announce$ X")',
    )
    for token in required:
        require(token in t, "missing hardened invariant " + token)
    body = t[t.find(run_start):t.find(run_end, t.find(run_start))]
    for forbidden in ('sa.resolve()', 'sa.getTargets().add(', 'bindTargets(sa)', 'prepareSourceParentChoices(spec,sa)', 'getStack().addAndUnfreeze(sa)'):
        require(forbidden not in body, "production AF8 campaign still uses shortcut " + forbidden)
    for forbidden in ('Grim Discovery','Fantastic Elasticity','Steel Sabotage','Sublime Epiphany','Profane Command','Aether Tradewinds','forge-behavior-v2:'):
        require(forbidden not in t, "card/path-specific branch forbidden " + forbidden)
    require('getManaPool().add' not in t and '.payCost(' not in t, 'mana/cost bypass present')

    p.write_text(t, encoding="utf-8")
    print("WS33_A_SVAR_AF8_RUNTIME_HARDEN=PASS paths=8 play=PlaySpellAbility actor=REMOTE_SLOT_1 phase=FORGE_MAIN1")
    print("WS33_A_SVAR_AF8_PAYMENT=FORGE_AUTHORITATIVE mana_pool_injection=0 cost_bypass=0")
    print("WS33_A_SVAR_AF8_EFFECT_EVIDENCE=TARGET_CARD_POSTCONDITION_FROM_TARGET_SCRIPT")
    print("WS33_A_SVAR_AF8_IDENTITY_EVIDENCE=SOURCE_ROOT_CHILD_ACTOR_TARGET_BEFORE_AFTER")
    print("WS33_A_SVAR_AF8_SELECTION_WITNESS=POLICY_BRANCHES_X_MODE_GENERIC_FORCED_CLASSIFIED")
    print("WS33_A_SVAR_AF8_POSITIVE_X_KIND=NUMBER")
    print("WS33_A_SVAR_AF8_CLIENT_EVIDENCE=WS05_REAL_REMOTE_PHASE_SAMPLES")
    print("WS33_A_SVAR_AF8_RULES_MUTATION=0 card_name_branch=0 path_id_branch=0")


if __name__ == "__main__":
    main()
