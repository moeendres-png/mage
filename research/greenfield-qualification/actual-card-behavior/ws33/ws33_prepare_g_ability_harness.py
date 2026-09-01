#!/usr/bin/env python3
"""Prepare a fail-closed Generation-2 direct-ABILITY G harness.

Historical WS31 contributes scenario/case infrastructure only. The historical direct
SpellAbility.resolve() shortcut and manual target injection are explicitly removed.
The prepared harness uses Forge's own SpellAbility.setupTargets() traversal, admits the
actual parsed ability through MagicStack.addAndUnfreeze(), and resolves through
MagicStack.resolveStack(). Every case records explicit stack-admission and completed-
resolution evidence; a silent MagicStack target rejection therefore cannot become PASS.
Runtime observation-only UI paths (for example reveal/look presentation) are expected to
be externalized by the Gen2 overlay stack without becoming pilot decisions.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_G_ABILITY_HARNESS_PREP=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    s = args.source.read_text(encoding="utf-8")

    # Historical WS31 manually scanned GameObjects and injected a target. Gen2 must
    # instead use the production SpellAbility target-setup traversal, so GameObject is
    # no longer required by the generated harness.
    s = replace_once(s, "import forge.game.GameObject;\n", "", "obsolete GameObject import")
    s = replace_once(
        s,
        "import forge.gamemodes.match.input.ExternalDecisionValidationException;\n",
        "import forge.gamemodes.match.input.ExternalDecisionValidationException;\nimport forge.gamemodes.net.server.RemoteClientGuiGame;\n",
        "remote transport barrier import",
    )
    s = replace_once(
        s,
        'if(cases.size()!=81)throw new IllegalStateException("WS31 expected 81 cases, got "+cases.size());',
        'if(cases.size()!=28)throw new IllegalStateException("WS33 G-ABILITY expected 28 cases, got "+cases.size());',
        "case cardinality",
    )
    s = replace_once(
        s,
        'Card source=addCard(spec.cardName,actor,ZoneType.Battlefield);',
        'Card source=addCard(spec.cardName,actor,"SP$".equals(spec.sourceToken)?ZoneType.Hand:ZoneType.Battlefield);',
        "source zone",
    )

    # The semantic-state observer can fire while Forge is legitimately resolving an
    # unrelated production stack entry. Starting the campaign there made every case
    # fail the strict pre-admission gate even though the campaign had not touched the
    # stack. Defer campaign start until Forge itself reaches a quiescent checkpoint;
    # never clear, thaw, or resolve the pre-existing stack from qualification code.
    old_ready = 'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4)return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;return true;}'
    new_ready = 'private static boolean ready(Game game){if(game.getAge()!=GameStage.Play||game.getRegisteredPlayers().size()!=4)return false;for(Player p:game.getRegisteredPlayers())if(!(p.getController() instanceof PlayerControllerHuman))return false;if(!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving())return false;return true;}'
    s = replace_once(s, old_ready, new_ready, "production-quiescent campaign entry")

    old_evidence = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta;'
    new_evidence = 'final CaseSpec spec; String status="UNKNOWN",failureType="",failureMessage="",beforeDigest="",afterDigest="",beforeState="",afterState=""; long decisionEvents,rngEvents,leakDelta,crossPrincipalDelta,stackAdmissions,stackResolutions;'
    s = replace_once(s, old_evidence, new_evidence, "stack evidence fields")

    old_resolution = 'bindTarget(sa,game,actor,opponent);ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);sa.resolve();game.getAction().checkStateEffects(true);'
    new_resolution = (
        'bindTargets(sa);'
        'if(!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving())'
        'throw new IllegalStateException("non-quiescent stack before exact path");'
        'ce.beforeState=semanticState(game);ce.beforeDigest=sha256(ce.beforeState);'
        'game.getStack().addAndUnfreeze(sa);'
        'if(game.getStack().isEmpty())throw new IllegalStateException("MagicStack admission failed for exact path");'
        'ce.stackAdmissions++;int stackSteps=0;'
        'while(!game.getStack().isEmpty()){if(++stackSteps>256)throw new IllegalStateException("stack did not quiesce after exact path");game.getStack().resolveStack();}'
        'if(game.getStack().isFrozen()||game.getStack().isResolving())throw new IllegalStateException("stack remained non-quiescent after exact path");'
        'ce.stackResolutions++;game.getAction().checkStateEffects(true);awaitRemoteTransport(ps);'
    )
    s = replace_once(s, old_resolution, new_resolution, "production stack resolution")

    # WS31 started path attribution before scenario construction. Keep all scenario
    # setup and AbilityFactory parsing outside the path-scoped evidence window.
    s = replace_once(
        s,
        'currentPath.set(spec.pathId);long leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks(),cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();try{seedCommon(game,actor,opponent);',
        'long leak0=-1,cross0=-1;try{seedCommon(game,actor,opponent);',
        "scenario setup outside path evidence window",
    )
    attribution_anchor = 'if(sa.getApi()==null||!spec.dispatch.equals(sa.getApi().name()))throw new IllegalStateException("dispatch mismatch runtime="+(sa.getApi()==null?"null":sa.getApi().name()));bindTargets(sa);'
    attribution_replacement = 'if(sa.getApi()==null||!spec.dispatch.equals(sa.getApi().name()))throw new IllegalStateException("dispatch mismatch runtime="+(sa.getApi()==null?"null":sa.getApi().name()));awaitRemoteTransport(ps);leak0=Ws05HiddenInfoProbe.pilotVisibleLeaks();cross0=Ws05HiddenInfoProbe.crossPrincipalLeaks();currentPath.set(spec.pathId);bindTargets(sa);'
    s = replace_once(s, attribution_anchor, attribution_replacement, "path evidence attribution boundary")
    s = replace_once(
        s,
        'finally{ce.leakDelta=Ws05HiddenInfoProbe.pilotVisibleLeaks()-leak0;ce.crossPrincipalDelta=Ws05HiddenInfoProbe.crossPrincipalLeaks()-cross0;',
        'finally{ce.leakDelta=leak0<0?0:Ws05HiddenInfoProbe.pilotVisibleLeaks()-leak0;ce.crossPrincipalDelta=cross0<0?0:Ws05HiddenInfoProbe.crossPrincipalLeaks()-cross0;',
        "setup-failure evidence guard",
    )

    # RemoteClientGuiGame.updateGameView() only enqueues network transport. A server-side
    # flush is therefore not a path evidence barrier. sendFullState() is channel-ordered
    # after prior deltas; the derived WS05 probe below counts the full-state callback only
    # after the headless client has applied it. Waiting on that dedicated counter prevents
    # unrelated in-flight deltas from satisfying the barrier.
    s = replace_once(
        s,
        'private static void seedCommon(Game game,Player actor,Player opponent){',
        'private static void awaitRemoteTransport(List<Player> ps){long before=Ws05HiddenInfoProbe.fullStateSamples();int remotes=0;for(Player p:ps){if(p.getController() instanceof PlayerControllerHuman human&&human.getGui() instanceof RemoteClientGuiGame remoteGui){remoteGui.updateGameView();remoteGui.sendFullState();remotes++;}}long target=before+remotes,deadline=System.currentTimeMillis()+10000L;while(Ws05HiddenInfoProbe.fullStateSamples()<target&&System.currentTimeMillis()<deadline){try{Thread.sleep(10L);}catch(InterruptedException e){Thread.currentThread().interrupt();throw new IllegalStateException("interrupted awaiting remote transport barrier",e);}}if(Ws05HiddenInfoProbe.fullStateSamples()<target)throw new IllegalStateException("remote transport barrier timeout got="+Ws05HiddenInfoProbe.fullStateSamples()+" expected="+target);}\n    private static void seedCommon(Game game,Player actor,Player opponent){',
        "client-processed full-state transport barrier",
    )

    # A deterministic generic top-of-library fixture gives the hidden/RNG family enough
    # legal material without card-specific branching. Index zero is Forge's library top.
    # Final top order is: Island, Plains, Runeclaw Bear, Sol Ring. This provides multiple
    # pre-match cards for random-rest operations, a small creature selector hit, and a
    # noncreature/nonland selector hit while leaving all legality to Forge.
    s = replace_once(
        s,
        'for(int i=0;i<3;i++){addCard("Runeclaw Bear",actor,ZoneType.Hand);addCard("Grizzly Bears",opponent,ZoneType.Hand);}}',
        'for(int i=0;i<3;i++){addCard("Runeclaw Bear",actor,ZoneType.Hand);addCard("Grizzly Bears",opponent,ZoneType.Hand);}addCardAtTop("Sol Ring",actor);addCardAtTop("Runeclaw Bear",actor);addCardAtTop("Plains",actor);addCardAtTop("Island",actor);addCardAtTop("Sol Ring",opponent);addCardAtTop("Runeclaw Bear",opponent);addCardAtTop("Plains",opponent);addCardAtTop("Island",opponent);}',
        "generic decision/RNG-bearing library fixture",
    )
    s = replace_once(
        s,
        'private static Card addCard(String name,Player player,ZoneType zone){PaperCard pc=FModel.getMagicDb().getCommonCards().getCard(name);if(pc==null)throw new IllegalStateException("card unavailable: "+name);Card c=Card.fromPaperCard(pc,player);c.setGameTimestamp(player.getGame().getNextTimestamp());player.getZone(zone).add(c);return c;}',
        'private static Card addCardAtTop(String name,Player player){PaperCard pc=FModel.getMagicDb().getCommonCards().getCard(name);if(pc==null)throw new IllegalStateException("card unavailable: "+name);Card c=Card.fromPaperCard(pc,player);c.setGameTimestamp(player.getGame().getNextTimestamp());player.getZone(ZoneType.Library).add(c,0);return c;}\n    private static Card addCard(String name,Player player,ZoneType zone){PaperCard pc=FModel.getMagicDb().getCommonCards().getCard(name);if(pc==null)throw new IllegalStateException("card unavailable: "+name);Card c=Card.fromPaperCard(pc,player);c.setGameTimestamp(player.getGame().getNextTimestamp());player.getZone(zone).add(c);return c;}',
        "top-of-library fixture helper",
    )

    old_target = 'private static void bindTarget(SpellAbility sa,Game game,Player actor,Player opponent){if(!sa.usesTargeting())return;List<GameObject>candidates=new ArrayList<>();candidates.add(opponent);candidates.add(actor);for(Player p:game.getPlayers())if(!candidates.contains(p))candidates.add(p);for(Card c:game.getCardsInGame())candidates.add(c);for(GameObject c:candidates){try{if(sa.canTarget(c)){sa.getTargets().add(c);return;}}catch(RuntimeException ignored){}}throw new IllegalStateException("no legal target available for exact path");}'
    new_target = 'private static void bindTargets(SpellAbility sa){for(SpellAbility cur=sa;cur!=null;cur=cur.getSubAbility())if(!cur.getTargets().isEmpty())throw new IllegalStateException("pre-populated targets forbidden");if(!sa.setupTargets())throw new IllegalStateException("Forge SpellAbility.setupTargets rejected exact path");for(SpellAbility cur=sa;cur!=null;cur=cur.getSubAbility())if(cur.usesTargeting()&&!cur.isTargetNumberValid())throw new IllegalStateException("Forge target count invalid after SpellAbility.setupTargets");}'
    s = replace_once(s, old_target, new_target, "authoritative recursive target setup")

    old_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState)))'
    new_summary = 'enc(e.failureType),enc(e.failureMessage),enc(e.beforeState),enc(e.afterState),Long.toString(e.stackAdmissions),Long.toString(e.stackResolutions)))'
    s = replace_once(s, old_summary, new_summary, "case-summary stack evidence")

    s = s.replace("Ws31HiddenRngReplayQualificationTest", "Ws33GAbilityQualificationTest")
    s = s.replace("WS31 exact-path hidden/RNG/replay qualification campaign.", "WS33 Gen2 direct-ABILITY hidden/RNG/replay diagnostic campaign.")
    s = s.replace("WS31 has no explicit qualification policy", "WS33 G-ABILITY has no explicit qualification policy")
    s = s.replace("WS31 campaign", "WS33 G-ABILITY campaign")

    require("sa.resolve()" not in s, "direct SpellAbility.resolve remains")
    require("getStack().add(sa)" not in s, "raw MagicStack.add remains")
    require("getStack().addAndUnfreeze(sa)" in s and "getStack().resolveStack()" in s, "production MagicStack route missing")
    require("sa.getTargets().add(" not in s, "manual target injection remains")
    require("sa.setupTargets()" in s, "Forge recursive target-setup boundary missing")
    require("chooseTargetsFor(sa)" not in s, "root-only target helper remains")
    require("stackAdmissions" in s and "stackResolutions" in s, "stack admission/resolution evidence missing")
    require("!game.getStack().isEmpty()||game.getStack().isFrozen()||game.getStack().isResolving()" in s, "production-quiescent campaign gate missing")
    require("import forge.game.GameObject;" not in s, "obsolete target-search import remains")
    require("RemoteClientGuiGame" in s and "awaitRemoteTransport(ps)" in s, "client-processed transport barrier missing")
    require("remoteGui.sendFullState()" in s and "Ws05HiddenInfoProbe.fullStateSamples()" in s, "transport barrier lacks dedicated full-state acknowledgement")
    require(all(token in s for token in ('addCardAtTop("Island",actor)','addCardAtTop("Plains",actor)','addCardAtTop("Runeclaw Bear",actor)','addCardAtTop("Sol Ring",actor)')), "generic decision/RNG library fixture missing")

    # Static regression gates: all setup, parsing and setup transport must finish before
    # path attribution; all path transport must be drained before the evidence delta is
    # finalized. No card-name branch is introduced in runCampaign.
    campaign = s[s.index("private static void runCampaign"):s.index("private static void seedCommon")]
    require(campaign.index("seedCommon(game,actor,opponent)") < campaign.index("awaitRemoteTransport(ps)"), "transport barrier occurs before scenario setup")
    require(campaign.index("AbilityFactory.getAbility(spec.script,source)") < campaign.index("awaitRemoteTransport(ps)"), "transport barrier occurs before AbilityFactory parsing")
    require(campaign.index("awaitRemoteTransport(ps)") < campaign.index("currentPath.set(spec.pathId)"), "path attribution starts before setup transport is client-processed")
    require(campaign.index("currentPath.set(spec.pathId)") < campaign.index("bindTargets(sa)"), "path attribution must cover Forge target setup")
    require(campaign.count("awaitRemoteTransport(ps)") >= 2, "path transport is not drained after execution")
    require("long leak0=-1,cross0=-1" in campaign, "setup-safe evidence baseline declaration missing")

    # Derive a G-only qualification probe from the retained WS05 observer. The base WS05
    # evidence contract remains untouched; this adds only a transport synchronization
    # counter keyed to already-decoded full-state callbacks. It exposes no card identity.
    probe_path = args.out.parent / "Ws05HiddenInfoProbe.java"
    require(probe_path.is_file(), "copied WS05 hidden-info probe missing")
    probe = probe_path.read_text(encoding="utf-8")
    probe = replace_once(
        probe,
        "    private static final AtomicLong decodedTransportSamples = new AtomicLong();\n",
        "    private static final AtomicLong decodedTransportSamples = new AtomicLong();\n    private static final AtomicLong fullStateSamples = new AtomicLong();\n",
        "full-state sample counter field",
    )
    probe = replace_once(
        probe,
        "        identityBearingIdHashLeaks.set(0); faceDownHiddenSamples.set(0); decodedTransportSamples.set(0);\n",
        "        identityBearingIdHashLeaks.set(0); faceDownHiddenSamples.set(0); decodedTransportSamples.set(0); fullStateSamples.set(0);\n",
        "full-state sample counter reset",
    )
    probe = replace_once(
        probe,
        "        decodedTransportSamples.incrementAndGet();\n\n        for (PlayerView owner : gameView.getPlayers()) {\n",
        "        decodedTransportSamples.incrementAndGet();\n        if (source != null && source.startsWith(\"full:\")) fullStateSamples.incrementAndGet();\n\n        for (PlayerView owner : gameView.getPlayers()) {\n",
        "full-state decoded callback count",
    )
    probe = replace_once(
        probe,
        "    public static long transportSamples() { return decodedTransportSamples.get(); }\n",
        "    public static long transportSamples() { return decodedTransportSamples.get(); }\n    public static long fullStateSamples() { return fullStateSamples.get(); }\n",
        "full-state sample getter",
    )
    require("fullStateSamples" in probe and 'source.startsWith("full:")' in probe, "derived full-state probe missing")
    probe_path.write_text(probe, encoding="utf-8")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(s, encoding="utf-8")
    print("WS33_G_ABILITY_HARNESS_PREP=PASS cases=28 direct_resolution=0 manual_target_injection=0 target_setup=SpellAbility.setupTargets stack_entry=MagicStack.addAndUnfreeze stack_resolution=MagicStack.resolveStack admission_gate=STRICT campaign_entry=PRODUCTION_QUIESCENT evidence_window=FULL_STATE_ACK_BARRIER generic_library_fixture=LAND_LAND_CREATURE_NONCREATURE observation_ui=EXTERNAL_OVERLAY")

if __name__ == "__main__":
    main()
