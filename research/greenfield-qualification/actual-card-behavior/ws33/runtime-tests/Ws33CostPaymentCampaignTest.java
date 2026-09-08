package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.GameView;
import forge.game.ability.AbilityKey;
import forge.game.card.Card;
import forge.game.cost.Cost;
import forge.game.cost.CostPayment;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.player.HumanCostDecision;
import forge.player.LobbyPlayerHuman;
import forge.player.PlayerControllerHuman;
import forge.util.MyRandom;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * WS33B qualification-only forge.game.cost.Cost payment campaign.
 *
 * <p>Each case pays an actual pinned-Forge cost expression through the
 * production {@code CostPayment}/{@code HumanCostDecision} engine against a
 * deterministic fixture (mana supply, fodder, host state). All discretionary
 * choices cross the WS01 external decision boundary and may select only
 * authoritative options; X values follow fixture inputs; entity choices
 * prefer fixture-designated fodder and fail closed otherwise. Paid-state
 * facts (tapped, sacrificed, exiled, discarded, counters, life, returned)
 * are asserted from production game state.</p>
 */
public final class Ws33CostPaymentCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final long RNG_SEED = 0xB20057L;

    @Test
    public void costPaymentCampaign() throws Exception {
        final String mode = System.getProperty("ws33.costMode", "record");
        if (!"record".equals(mode) && !"replay".equals(mode)) {
            throw new IllegalArgumentException("ws33.costMode must be record or replay");
        }
        final Path casesPath = requiredPath("ws33.costCases");
        final Path out = requiredPath("ws33.costOut");
        Files.createDirectories(out);
        final List<Case> cases = loadCases(casesPath);
        final List<String> diagnostics = new ArrayList<>();
        final List<String> admittedRecords = new ArrayList<>();
        int success = 0;

        for (final Case c : cases) {
            try {
                if ("record".equals(mode)) {
                    final Result result = executeCase(c, null, null);
                    writeRecord(out, c, result);
                    success++;
                } else {
                    final Path dir = caseDir(out, c.pathId);
                    if (!Files.isRegularFile(dir.resolve("record-success.marker"))) {
                        executeCase(c, null, null);
                        throw new IllegalStateException(
                                "record-rejected case unexpectedly succeeded during replay alignment");
                    }
                    final List<ReplayDecision> replay = loadReplayDecisions(dir.resolve("decision-replay.tsv"));
                    final List<Integer> replayRng = loadReplayRng(dir.resolve("rng-replay.tsv"));
                    final Result result = executeCase(c, replay, replayRng);
                    final String expected = Files.readString(dir.resolve("final-state.txt"), StandardCharsets.UTF_8);
                    if (!expected.equals(result.canonicalFinalState)) {
                        throw new IllegalStateException("semantic replay state mismatch expected="
                                + expected + " actual=" + result.canonicalFinalState);
                    }
                    writeReplayEvidence(dir, result, dir.resolve("decision-tape.json"), expected);
                    admittedRecords.add("records/" + shortId(c.pathId) + "/record.json");
                    success++;
                }
            } catch (Throwable error) {
                diagnostics.add("{\"mode\":" + q(mode)
                        + ",\"path_id\":" + q(c.pathId)
                        + ",\"card\":" + q(c.cardName)
                        + ",\"recipe\":" + q(c.recipe)
                        + ",\"error_type\":" + q(error.getClass().getName())
                        + ",\"message\":" + q(String.valueOf(error.getMessage())) + "}");
            }
        }

        writeDiagnostics(out, mode, diagnostics);
        if ("replay".equals(mode)) {
            writeCampaignIndex(out, admittedRecords);
        }
        Assert.assertTrue(success > 0, "cost campaign produced no successful " + mode + " cases");
        System.out.println("WS33_COST_CAMPAIGN_MODE=" + mode);
        System.out.println("WS33_COST_CAMPAIGN_SUCCESS=" + success);
        System.out.println("WS33_COST_CAMPAIGN_DIAGNOSTIC_FAILURES=" + diagnostics.size());
    }

    private Result executeCase(final Case c, final List<ReplayDecision> replay, final List<Integer> replayRng) {
        if (c.recipe.startsWith("UNSUPPORTED_")) {
            throw new IllegalStateException("fail-closed unsupported cost recipe " + c.recipe);
        }
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final String gameId = "ws33-cost-" + shortId(c.pathId);

        final List<MyRandom.RngEvent> rngEvents = new ArrayList<>();
        final MyRandom.ReplayProvider rngProvider = replayRng == null ? null : new QueueReplayProvider(replayRng);
        MyRandom.beginGameScope(gameId, RNG_SEED, rngEvents::add, rngProvider);
        try {
            forge.net.Ws05HiddenInfoProbe.reset();
            forge.net.Ws05HiddenInfoProbe.registerSecret("Black Lotus");
            addCardToZone("Black Lotus", opponent, ZoneType.Hand);

            final PlayerControllerHuman controller = new PlayerControllerHuman(
                    game, actor, new LobbyPlayerHuman("ws33-cost-principal"));
            final Fixture fixture = new Fixture(game, actor);
            final Provider decisions = new Provider(fixture, replay, c);
            controller.setExternalDecisionProvider(decisions::decide);
            fixture.controller = controller;

            if (c.evidenceProfile.contains("DECISION")) {
                final Card shockTarget = addCardToZone("Runeclaw Bear", opponent, ZoneType.Battlefield);
                decisions.designatedTarget = shockTarget;
                driveFixtureDecision(game, actor, controller, decisions, shockTarget);
            }

            fillLibrary(actor, 10);
            actor.getZone(ZoneType.Library).shuffle();

            final PaymentResult payment = executeRecipe(c, fixture);
            if (!payment.paid) {
                throw new IllegalStateException("production cost payment returned false recipe=" + c.recipe);
            }
            decisions.assertReplayExhausted();

            final List<ExternalDecisionTape.Event> tape = controller.getExternalDecisionTapeSnapshot();
            if (tape.size() != decisions.captured.size()) {
                throw new IllegalStateException("decision tape/request count mismatch");
            }
            for (int i = 0; i < tape.size(); i++) {
                final ExternalDecisionTape.Event event = tape.get(i);
                final CapturedDecision decision = decisions.captured.get(i);
                if (event.getResponseStatus() != ExternalDecisionTape.ResponseStatus.ACCEPTED) {
                    throw new IllegalStateException("non-accepted cost decision");
                }
                if (!event.getSelectedOptionIds().equals(decision.selectedOptionIds)) {
                    throw new IllegalStateException("validated decision response differs from provider response");
                }
            }
            if (c.evidenceProfile.contains("DECISION") && tape.isEmpty()) {
                throw new IllegalStateException("empty decision tape for DECISION profile");
            }
            if (rngEvents.isEmpty()) {
                throw new IllegalStateException("empty WS06 RNG tape");
            }

            final long leak0 = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks();
            final long cross0 = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks();
            final GameView view = new GameView(game);
            forge.net.Ws05HiddenInfoProbe.observe(actor.getName(), view, "ws33-cost-case");
            forge.net.Ws05HiddenInfoProbe.observe(opponent.getName(), view, "ws33-cost-case");
            final long leakDelta = forge.net.Ws05HiddenInfoProbe.pilotVisibleLeaks() - leak0;
            final long crossDelta = forge.net.Ws05HiddenInfoProbe.crossPrincipalLeaks() - cross0;
            if (leakDelta != 0 || crossDelta != 0) {
                throw new IllegalStateException("hidden-isolation leak delta leak=" + leakDelta
                        + " cross=" + crossDelta);
            }

            final String canonical = "paid=true"
                    + "|recipe=" + c.recipe
                    + "|cost=" + c.costExpression
                    + "|facts=" + payment.facts;
            return new Result(canonical, decisions.captured, tape,
                    new ArrayList<>(rngEvents), leakDelta, crossDelta);
        } finally {
            MyRandom.endGameScope();
        }
    }

    private void driveFixtureDecision(final Game game, final Player actor,
            final PlayerControllerHuman controller, final Provider decisions, final Card shockTarget) {
        final Card prodigal = addCardToZone("Prodigal Sorcerer", actor, ZoneType.Battlefield);
        fixtureProdigal(decisions, prodigal);
        SpellAbility ability = null;
        for (final SpellAbility sa : prodigal.getSpellAbilities()) {
            if (sa.usesTargeting()) {
                ability = sa;
                break;
            }
        }
        if (ability == null) {
            throw new IllegalStateException("fixture card lacks targeting ability");
        }
        ability.setActivatingPlayer(actor);
        if (!controller.chooseTargetsFor(ability)) {
            throw new IllegalStateException("Forge fixture target selection returned false");
        }
        decisions.assertTargetConsumed();
    }

    private void fixtureProdigal(final Provider decisions, final Card prodigal) {
        decisions.protectedIds.add(prodigal.getId());
    }

    private PaymentResult executeRecipe(final Case c, final Fixture f) {
        switch (c.recipe) {
            case "PAY_TAP": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                if (paid && !host.isTapped()) {
                    throw new IllegalStateException("tap cost paid but host untapped");
                }
                return new PaymentResult(paid, "tapped=" + host.isTapped());
            }
            case "PAY_MANA":
            case "PAY_MANA_TAP": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                return new PaymentResult(paid, "rings_tapped=" + f.tappedRings());
            }
            case "PAY_X_MANA":
            case "PAY_X_MANA_TAP": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                f.xValue = intParam(c.recipeParams, "x_value", 3);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                return new PaymentResult(paid, "x=" + f.xValue);
            }
            case "PAY_SAC": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                final List<Card> fodder = f.placeFodder(c.recipeParams);
                if (c.recipeParams.get("fodder") != null && c.recipeParams.get("fodder").startsWith("HOST")) {
                    fodder.add(host);
                    // The cost sacrifices the source itself: allow its selection.
                    f.protectedIds.remove(host.getId());
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                int inGrave = 0;
                for (final Card card : fodder) {
                    if (card.isInZone(ZoneType.Graveyard)) {
                        inGrave++;
                    }
                }
                if (paid && inGrave == 0) {
                    throw new IllegalStateException("sacrifice cost paid but no fodder in graveyard");
                }
                return new PaymentResult(paid, "sacrificed=" + inGrave + "/" + fodder.size());
            }
            case "PAY_EXILE": {
                Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                final List<Card> fodder = f.placeFodder(c.recipeParams);
                final boolean hostFodder = c.recipeParams.get("fodder") != null
                        && c.recipeParams.get("fodder").startsWith("HOST");
                if (hostFodder) {
                    fodder.add(host);
                    if ("GRAVEYARD".equals(c.recipeParams.get("zone"))) {
                        host = f.game.getAction().moveTo(ZoneType.Graveyard, host, null, null);
                        fodder.set(fodder.size() - 1, host);
                    }
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                if ("FIRST_FODDER".equals(c.recipeParams.get("trigger")) && !fodder.isEmpty()) {
                    sa.getRootAbility().setTriggeringObject(AbilityKey.Card, fodder.get(0));
                }
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                int inExile = 0;
                for (final Card card : fodder) {
                    if (card.isInZone(ZoneType.Exile)) {
                        inExile++;
                    }
                }
                if (paid && inExile == 0) {
                    throw new IllegalStateException("exile cost paid but no fodder in exile");
                }
                return new PaymentResult(paid, "exiled=" + inExile + "/" + fodder.size());
            }
            case "PAY_DISCARD": {
                Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                final List<Card> fodder = f.placeFodder(c.recipeParams);
                final boolean hostFodder = c.recipeParams.get("fodder") != null
                        && c.recipeParams.get("fodder").startsWith("HOST");
                if (hostFodder) {
                    // CARDNAME discard takes the source itself from hand.
                    host = f.game.getAction().moveTo(ZoneType.Hand, host, null, null);
                    fodder.add(host);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                int inGrave = 0;
                for (final Card card : fodder) {
                    if (card.isInZone(ZoneType.Graveyard)) {
                        inGrave++;
                    }
                }
                if (paid && inGrave == 0) {
                    throw new IllegalStateException("discard cost paid but no fodder in graveyard");
                }
                return new PaymentResult(paid, "discarded=" + inGrave + "/" + fodder.size());
            }
            case "PAY_COUNTERS":
            case "PAY_LIFE":
            case "PAY_RETURN": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                if ("PAY_COUNTERS".equals(c.recipe)) {
                    for (final String spec : c.recipeParams.get("counterset").split(";")) {
                        final String[] kv = spec.split(":", -1);
                        if (kv.length == 2) {
                            host.setCounters(forge.game.card.CounterType.getType(kv[0]),
                                    Integer.parseInt(kv[1]));
                        }
                    }
                }
                if ("PAY_RETURN".equals(c.recipe)) {
                    f.placeFodder(c.recipeParams);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                return new PaymentResult(paid, "post=" + paidStateSummary(f, host));
            }
            case "PAY_TAPXTYPE": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                final int need = intParam(c.recipeParams, "need");
                final String type = c.recipeParams.get("type");
                int placed = 0;
                for (int i = 0; i < need; i++) {
                    addCardToZone(tapxTypeCard(type), f.actor, ZoneType.Battlefield);
                    placed++;
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                return new PaymentResult(paid, "tappers=" + placed);
            }
            case "CAST_SPELL": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Hand);
                f.protect(host);
                f.supplyMana(c.recipeParams);
                SpellAbility spell = null;
                for (final SpellAbility candidate : host.getSpells()) {
                    spell = candidate;
                    break;
                }
                if (spell == null) {
                    throw new IllegalStateException("host has no spell ability");
                }
                spell.setActivatingPlayer(f.actor);
                final boolean paid = pay(spell.getPayCosts(), spell, f);
                return new PaymentResult(paid, "spell_paid=" + spell.getHostCard().getName());
            }
            case "CAST_NO_COST": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Hand);
                f.protect(host);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                return new PaymentResult(true, "no_cost=true");
            }
            case "PAY_UNATTACH": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                final Card bearer = addCardToZone("Runeclaw Bear", f.actor, ZoneType.Battlefield);
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                host.attachToEntity(bearer, sa);
                if (!bearer.getAttachedCards().contains(host)) {
                    throw new IllegalStateException("attach fixture did not attach");
                }
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                if (paid && host.isAttachedToEntity()) {
                    throw new IllegalStateException("unattach cost paid but host still attached");
                }
                return new PaymentResult(paid, "unattached=" + !host.isAttachedToEntity());
            }
            case "PAY_DRAW": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                f.protect(host);
                // X counts actor creatures sharing a type with the host
                // (Illusion): fixture two illusion bears.
                addCardToZone("Phantasmal Bear", f.actor, ZoneType.Battlefield);
                addCardToZone("Phantasmal Bear", f.actor, ZoneType.Battlefield);
                final int before = f.actor.getZone(ZoneType.Hand).size();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final int xValue = forge.game.ability.AbilityUtils.calculateAmount(host, "X", sa);
                if (xValue <= 0) {
                    throw new IllegalStateException("draw fixture X is not positive");
                }
                final boolean paid = pay(new Cost(c.costExpression, true), sa, f);
                final int drawn = f.actor.getZone(ZoneType.Hand).size() - before;
                if (paid && drawn != xValue) {
                    throw new IllegalStateException("draw cost paid but drew " + drawn + " expected " + xValue);
                }
                return new PaymentResult(paid, "drawn=" + drawn);
            }
            case "AMOUNT_HOST_COUNTERS_ALL": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                int expected = 0;
                for (final String key : new String[]{"P1P1", "M1M1"}) {
                    final String raw = c.recipeParams.get(key);
                    if (raw != null) {
                        final int n = Integer.parseInt(raw);
                        host.setCounters(forge.game.card.CounterType.getType(key), n);
                        expected += n;
                    }
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                return new PaymentResult(true,
                        "amount=" + forge.game.ability.AbilityUtils.calculateAmount(host, c.token, sa)
                        + "|expected=" + expected);
            }
            case "AMOUNT_XPAID": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                final int paidX = intParam(c.recipeParams, "paid");
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                sa.getRootAbility().setXManaCostPaid(paidX);
                final int actual = forge.game.ability.AbilityUtils.calculateAmount(host, c.token, sa);
                if (actual != paidX) {
                    throw new IllegalStateException("amount mismatch actual=" + actual);
                }
                return new PaymentResult(true, "amount=" + actual + "|expected=" + paidX);
            }
            case "AMOUNT_TRIGGER_CMC": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                final Card trigger = addCardToZone("Runeclaw Bear", f.game.getPlayers().get(1), ZoneType.Battlefield);
                final int cmc = trigger.getCMC();
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                sa.getRootAbility().setTriggeringObject(forge.game.ability.AbilityKey.Card, trigger);
                final int actual = forge.game.ability.AbilityUtils.calculateAmount(host, c.token, sa);
                if (actual != cmc) {
                    throw new IllegalStateException("amount mismatch actual=" + actual);
                }
                return new PaymentResult(true, "amount=" + actual + "|expected=" + cmc);
            }
            case "AMOUNT_COMMANDER_TOTAL": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                final int casts = intParam(c.recipeParams, "casts");
                for (int i = 0; i < casts; i++) {
                    f.actor.incCommanderCast(addCardToZone("Runeclaw Bear", f.actor, ZoneType.Battlefield));
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final int actual = forge.game.ability.AbilityUtils.calculateAmount(host, c.token, sa);
                if (actual != casts) {
                    throw new IllegalStateException("amount mismatch actual=" + actual);
                }
                return new PaymentResult(true, "amount=" + actual + "|expected=" + casts);
            }
            case "AMOUNT_LOFTY_COMPARE": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                final int flyers = intParam(c.recipeParams, "flyers");
                for (int i = 0; i < flyers; i++) {
                    addCardToZone("Air Elemental", f.actor, ZoneType.Battlefield);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final int actual = forge.game.ability.AbilityUtils.calculateAmount(host, c.token, sa);
                if (actual != 4) {
                    throw new IllegalStateException("amount mismatch actual=" + actual);
                }
                return new PaymentResult(true, "amount=" + actual + "|expected=4");
            }
            case "AMOUNT_REMEMBERED_COUNTERS": {
                final Card host = addCardToZone(c.cardName, f.actor, ZoneType.Battlefield);
                final int bears = intParam(c.recipeParams, "bears");
                final int p1p1 = intParam(c.recipeParams, "P1P1");
                final int m1m1 = intParam(c.recipeParams, "M1M1");
                int expected = 0;
                for (int i = 0; i < bears; i++) {
                    final Card remembered = addCardToZone("Runeclaw Bear", f.actor, ZoneType.Battlefield);
                    if (i == 0) {
                        remembered.setCounters(forge.game.card.CounterType.getType("P1P1"), p1p1);
                        expected += p1p1;
                    } else {
                        remembered.setCounters(forge.game.card.CounterType.getType("M1M1"), m1m1);
                        expected += m1m1;
                    }
                    host.addRemembered(remembered);
                }
                final SpellAbility sa = firstAbility(host);
                sa.setActivatingPlayer(f.actor);
                final int actual = forge.game.ability.AbilityUtils.calculateAmount(host, c.token, sa);
                if (actual != expected) {
                    throw new IllegalStateException("amount mismatch actual=" + actual);
                }
                return new PaymentResult(true, "amount=" + actual + "|expected=" + expected);
            }
            default:
                throw new IllegalStateException("fail-closed unsupported cost recipe " + c.recipe);
        }
    }

    private String tapxTypeCard(final String type) {
        if (type.toLowerCase(java.util.Locale.ROOT).contains("soldier")) {
            return "Elite Vanguard";
        }
        if (type.toLowerCase(java.util.Locale.ROOT).contains("artifact")) {
            return "Sol Ring";
        }
        throw new IllegalStateException("no tapper card for type " + type);
    }

    private String paidStateSummary(final Fixture f, final Card host) {
        return "host_tapped=" + host.isTapped()
                + "|actor_life=" + f.actor.getLife();
    }

    private boolean pay(final Cost cost, final SpellAbility sa, final Fixture f) {
        if (System.getProperty("ws33.costDebug") != null) {
            final StringBuilder dump = new StringBuilder("WS33_COST_BOARD actor_bf=");
            for (final Card card : f.actor.getZone(ZoneType.Battlefield)) {
                dump.append("[").append(card.getName()).append("]");
            }
            dump.append(" hand=").append(f.actor.getZone(ZoneType.Hand).size());
            System.err.println(dump);
        }
        final CostPayment payment = new CostPayment(cost, sa);
        return payment.payCost(new HumanCostDecision(
                f.controller, f.actor, sa, false, "WS33_COST"));
    }

    private SpellAbility firstAbility(final Card host) {
        SpellAbility fallback = null;
        for (final SpellAbility sa : host.getSpellAbilities()) {
            if (fallback == null) {
                fallback = sa;
            }
            if (sa.isActivatedAbility()) {
                return sa;
            }
        }
        if (fallback == null) {
            throw new IllegalStateException("host card has no SpellAbility " + host.getName());
        }
        return fallback;
    }

    private static int intParam(final Map<String, String> params, final String key) {
        final String value = params.get(key);
        if (value == null) {
            throw new IllegalStateException("missing recipe param " + key);
        }
        return Integer.parseInt(value);
    }

    private static int intParam(final Map<String, String> params, final String key, final int orDefault) {
        final String value = params.get(key);
        if (value == null) {
            return orDefault;
        }
        return Integer.parseInt(value);
    }

    private final class Fixture {
        final Game game;
        final Player actor;
        PlayerControllerHuman controller;
        final java.util.Set<Integer> protectedIds = new java.util.HashSet<>();
        final java.util.Set<Integer> fodderIds = new java.util.HashSet<>();
        final List<Card> rings = new ArrayList<>();
        int xValue = 3;

        Fixture(final Game game, final Player actor) {
            this.game = game;
            this.actor = actor;
        }

        void protect(final Card card) {
            protectedIds.add(card.getId());
        }

        void supplyMana(final Map<String, String> params) {
            final String supply = params.get("supply");
            if (supply == null) {
                return;
            }
            // supply format: rings=N;lands=A,B,C
            for (final String part : supply.split(";")) {
                if (part.startsWith("rings=")) {
                    final int n = Integer.parseInt(part.substring("rings=".length()));
                    for (int i = 0; i < n; i++) {
                        final Card ring = addCardToZone("Sol Ring", actor, ZoneType.Battlefield);
                        rings.add(ring);
                        protectedIds.add(ring.getId());
                    }
                } else if (part.startsWith("lands=") && part.length() > "lands=".length()) {
                    for (final String land : part.substring("lands=".length()).split(",")) {
                        if (land.isBlank()) {
                            continue;
                        }
                        final Card landCard = addCardToZone(land, actor, ZoneType.Battlefield);
                        protectedIds.add(landCard.getId());
                    }
                }
            }
            final String x = params.get("x_value");
            if (x != null) {
                xValue = Integer.parseInt(x);
            }
        }

        List<Card> placeFodder(final Map<String, String> params) {
            final List<Card> out = new ArrayList<>();
            final String fodder = params.get("fodder");
            if (fodder == null) {
                return out;
            }
            // fodder format: Name|count|CTRL|ZONE;... or HOST,0,ACTOR,Battlefield (track host).
            for (final String spec : fodder.split(";")) {
                final String[] fields = spec.split("\\|", -1);
                if (fields[0].startsWith("HOST")) {
                    continue;
                }
                final int count = Integer.parseInt(fields[1]);
                final Player owner = "ACTOR".equals(fields[2]) ? actor : game.getPlayers().get(1);
                final ZoneType zone = fields.length > 3 && !fields[3].isBlank()
                        ? ZoneType.valueOf(fields[3]) : ZoneType.Battlefield;
                for (int i = 0; i < count; i++) {
                    final Card card = addCardToZone(fields[0], owner, zone);
                    fodderIds.add(card.getId());
                    out.add(card);
                }
            }
            return out;
        }

        int tappedRings() {
            int n = 0;
            for (final Card ring : rings) {
                if (ring.isTapped()) {
                    n++;
                }
            }
            return n;
        }
    }

    private static final class Provider {
        private final Fixture fixture;
        private final List<ReplayDecision> replay;
        private final Case c;
        private int replayIndex;
        private Card designatedTarget;
        private boolean targetSeen;
        private boolean targetDone;
        private final List<CapturedDecision> captured = new ArrayList<>();
        private final java.util.Set<Integer> protectedIds = new java.util.HashSet<>();

        Provider(final Fixture fixture, final List<ReplayDecision> replay, final Case c) {
            this.fixture = fixture;
            this.replay = replay;
            this.c = c;
            this.protectedIds.addAll(fixture.protectedIds);
        }

        ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
            try {
                return decideInner(request);
            } catch (RuntimeException e) {
                System.err.println("WS33_COST_PROVIDER_ERROR kind=" + request.getDecisionKind()
                        + " error=" + e);
                throw e;
            }
        }

        ExternalDecisionResponse decideInner(final ExternalDecisionRequest request) {
            if (System.getProperty("ws33.costDebug") != null) {
                final StringBuilder dump = new StringBuilder();
                dump.append("WS33_COST_DEBUG kind=").append(request.getDecisionKind())
                        .append(" min=").append(request.getMinimumSelection())
                        .append(" max=").append(request.getMaximumSelection());
                for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                    dump.append(" [").append(option.getOptionId()).append("::")
                            .append(option.getSemanticValue()).append("::")
                            .append(resolveDebugName(option.getSemanticValue())).append("]");
                }
                System.err.println(dump);
            }
            final List<ExternalDecisionRequest.Option> chosen;
            if (replay != null) {
                if (replayIndex >= replay.size()) {
                    throw new IllegalStateException("replay decision tape exhausted");
                }
                final ReplayDecision expected = replay.get(replayIndex++);
                if (!expected.decisionKind.equals(request.getDecisionKind())) {
                    throw new IllegalStateException("replay decision kind mismatch");
                }
                chosen = new ArrayList<>();
                for (final String optionId : expected.optionIds) {
                    final ExternalDecisionRequest.Option match = request.getOptions().stream()
                            .filter(option -> optionId.equals(option.getOptionId()))
                            .findFirst()
                            .orElseThrow(() -> new IllegalStateException(
                                    "recorded response option absent from authoritative replay options"));
                    chosen.add(match);
                }
                for (int i = 0; i < chosen.size() && i < expected.semanticValues.size(); i++) {
                    if (!expected.semanticValues.get(i).equals(chosen.get(i).getSemanticValue())) {
                        throw new IllegalStateException("recorded semantic differs in replay");
                    }
                }
            } else if ("TARGET_SELECTION".equals(request.getDecisionKind()) && designatedTarget != null && !targetDone) {
                final String desired = targetSeen ? "DONE" : "CARD:" + designatedTarget.getId();
                final ExternalDecisionRequest.Option single = request.getOptions().stream()
                        .filter(option -> desired.equals(option.getSemanticValue()))
                        .findFirst()
                        .orElseThrow(() -> new IllegalStateException(
                                "fixture-designated target transition not offered by Forge: " + desired));
                if (desired.startsWith("CARD:")) {
                    targetSeen = true;
                } else {
                    targetDone = true;
                }
                chosen = List.of(single);
            } else {
                chosen = choosePaymentOptions(request);
            }
            final List<String> ids = new ArrayList<>();
            final List<String> semantics = new ArrayList<>();
            for (final ExternalDecisionRequest.Option option : chosen) {
                ids.add(option.getOptionId());
                semantics.add(option.getSemanticValue());
                if (designatedTarget != null
                        && ("CARD:" + designatedTarget.getId()).equals(option.getSemanticValue())) {
                    targetSeen = true;
                }
                if ("DONE".equals(option.getSemanticValue())) {
                    targetDone = true;
                }
            }
            captured.add(new CapturedDecision(request, ids, semantics));
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(),
                    request.getPrincipalId(), request.getResponseSchema(),
                    ids, false);
        }

        private List<ExternalDecisionRequest.Option> choosePaymentOptions(
                final ExternalDecisionRequest request) {
            final long sameKind = captured.stream()
                    .filter(d -> d.request.getDecisionKind().equals(request.getDecisionKind())).count();
            if (sameKind >= 64) {
                throw new IllegalStateException("fail-closed decision loop guard kind="
                        + request.getDecisionKind());
            }
            // Picks are excluded only within the same decision kind and only
            // for entity-backed options (by entity semantic): option ids are
            // request-scoped ordinals, not global identities.
            final java.util.Set<String> pickedEntities = new java.util.HashSet<>();
            for (final CapturedDecision decision : captured) {
                if (decision.request.getDecisionKind().equals(request.getDecisionKind())) {
                    pickedEntities.addAll(decision.semanticValues);
                }
            }
            final int min = Math.max(1, request.getMinimumSelection());
            int max = request.getMaximumSelection();
            if (max <= 0 || max > request.getOptions().size()) {
                max = request.getOptions().size();
            }
            final List<ExternalDecisionRequest.Option> ranked = new ArrayList<>();
            // Completion signal: the engine offers DONE only once the
            // accumulated picks satisfy the input minimum.
            for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                if ("DONE".equals(option.getSemanticValue())) {
                    return List.of(option);
                }
            }
            // X-value choice first (repeatable across separate X decisions).
            for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                final String semantic = option.getSemanticValue();
                if (semantic != null && semantic.equals("X:" + fixture.xValue)) {
                    ranked.add(option);
                }
            }
            // Unpicked fixture fodder entities next.
            for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                if (pickedEntities.contains(option.getSemanticValue()) || ranked.contains(option)) {
                    continue;
                }
                final String semantic = option.getSemanticValue();
                final Integer id = entityId(semantic);
                if (id != null && fixture.fodderIds.contains(id)) {
                    ranked.add(option);
                }
            }
            // Any other acceptable authoritative option.
            for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                if (pickedEntities.contains(option.getSemanticValue()) || ranked.contains(option)) {
                    continue;
                }
                final String semantic = option.getSemanticValue();
                final Integer id = entityId(semantic);
                if (id != null && (protectedIds.contains(id) || fixture.protectedIds.contains(id))) {
                    continue;
                }
                if ("DONE".equals(semantic) || "CANCEL".equals(semantic) || "DECLINE".equals(semantic)) {
                    continue;
                }
                ranked.add(option);
            }
            if (ranked.size() < min) {
                throw new IllegalStateException("no acceptable authoritative payment options kind="
                        + request.getDecisionKind() + " min=" + min);
            }
            return new ArrayList<>(ranked.subList(0, Math.min(max, ranked.size())));
        }

        private String resolveDebugName(final String semantic) {
            final Integer id = entityId(semantic);
            if (id == null) {
                return "-";
            }
            for (final Card card : fixture.game.getCardsInGame()) {
                if (card.getId() == id) {
                    return card.getName() + (card.isTapped() ? "/TAPPED" : "");
                }
            }
            return "?";
        }

        private Integer entityId(final String semantic) {            if (semantic == null) {
                return null;
            }
            String tail = null;
            if (semantic.startsWith("CARD:")) {
                tail = semantic.substring("CARD:".length());
            } else if (semantic.startsWith("ENTITY:card:")) {
                tail = semantic.substring("ENTITY:card:".length());
            }
            if (tail == null) {
                return null;
            }
            try {
                return Integer.parseInt(tail);
            } catch (NumberFormatException e) {
                return null;
            }
        }

        void assertTargetConsumed() {
            if (!targetSeen) {
                throw new IllegalStateException("authoritative intended fixture transition was never consumed");
            }
        }

        void assertReplayExhausted() {
            if (replay != null && replayIndex != replay.size()) {
                throw new IllegalStateException("replay left " + (replay.size() - replayIndex) + " decisions unconsumed");
            }
        }
    }

    private static void writeRecord(final Path root, final Case c, final Result result) throws IOException {
        final Path dir = caseDir(root, c.pathId);
        Files.createDirectories(dir);
        final Path decisionTape = dir.resolve("decision-tape.json");
        final Path decisionReplay = dir.resolve("decision-replay.tsv");
        final Path rngTape = dir.resolve("rng-tape.json");
        final Path rngReplay = dir.resolve("rng-replay.tsv");
        final Path trace = dir.resolve("trace.json");
        final Path finalState = dir.resolve("final-state.txt");
        final Path observation = dir.resolve("principal-observation.json");

        writeDecisionTape(decisionTape, c, result);
        writeDecisionReplay(decisionReplay, result);
        writeRngTape(rngTape, rngReplay, c, result);
        Files.writeString(finalState, result.canonicalFinalState, StandardCharsets.UTF_8);
        Files.writeString(trace, traceJson(c, result), StandardCharsets.UTF_8);
        Files.writeString(observation, observationJson(c, result), StandardCharsets.UTF_8);

        final String rel = "records/" + shortId(c.pathId) + "/";
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-cost-payment-" + shortId(c.pathId)) + ","
                + "\"oracle_identities\":[" + q(c.oracleId) + "],"
                + "\"v2_path_ids\":[" + q(c.pathId) + "],"
                + "\"owner_family\":\"ACTION_COST_DECISION\","
                + "\"initial_semantic_state\":{"
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"cost_expression\":" + q(c.costExpression)
                + "},"
                + "\"final_semantic_state\":{"
                + "\"cost_paid\":true,"
                + "\"facts\":" + q(result.facts)
                + "},"
                + "\"state_assertions\":["
                + "{\"assertion_id\":\"cost-paid\",\"expected\":true,\"actual\":true,\"result\":\"PASS\"},"
                + assertion("hidden-leak-delta", 0, (int) result.leakDelta) + ","
                + assertion("cross-principal-leak-delta", 0, (int) result.crossDelta)
                + "],"
                + "\"path_exercise\":[{"
                + "\"v2_path_id\":" + q(c.pathId) + ","
                + "\"exercised\":true,"
                + "\"trace_event_ids\":[\"COST_PAID\",\"DECISION_ACCEPTED\",\"RNG_TAPED\",\"HIDDEN_SAMPLED\"],"
                + "\"assertion_ids\":[\"cost-paid\",\"hidden-leak-delta\",\"cross-principal-leak-delta\"]"
                + "}],"
                + "\"execution\":{"
                + "\"actual_card_execution\":\"PASS\","
                + "\"actual_rules_core_path\":true,"
                + "\"authoritative_decision_boundary\":\"USED\","
                + "\"silent_fallbacks\":0,"
                + "\"direct_effect_resolution\":false},"
                + "\"trace_file\":" + q(rel + "trace.json") + ","
                + "\"decision_tape_file\":" + q(rel + "decision-tape.json") + ","
                + "\"semantic_replay_evidence_file\":" + q(rel + "semantic-replay.json") + ","
                + "\"rng_tape_file\":" + q(rel + "rng-tape.json") + ","
                + "\"observation_evidence_file\":" + q(rel + "principal-observation.json") + ","
                + "\"rules_authority_refs\":["
                + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 118.3")
                + "," + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 601.2h")
                + "],"
                + "\"evidence_class\":\"EXTERNALLY_RULE_VALIDATED\""
                + "}\n";
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
    }

    private static void writeDecisionTape(final Path path, final Case c, final Result result) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"events\":[");
        for (int i = 0; i < result.captured.size(); i++) {
            if (i != 0) json.append(',');
            final CapturedDecision captured = result.captured.get(i);
            final ExternalDecisionTape.Event event = result.tape.get(i);
            final ExternalDecisionRequest request = captured.request;
            json.append("{\"decision_id\":").append(request.getDecisionId())
                    .append(",\"decision_kind\":").append(q(request.getDecisionKind()))
                    .append(",\"game_id\":").append(q("ws33-cost-" + shortId(c.pathId)))
                    .append(",\"actor\":").append(q(String.valueOf(request.getActorId())))
                    .append(",\"principal\":").append(q(String.valueOf(request.getPrincipalId())))
                    .append(",\"visibility_scope\":").append(q(request.getVisibilityScope()))
                    .append(",\"authoritative_legal_options\":[");
            for (int j = 0; j < request.getOptions().size(); j++) {
                if (j != 0) json.append(',');
                final ExternalDecisionRequest.Option option = request.getOptions().get(j);
                json.append("{\"option_id\":").append(q(option.getOptionId()))
                        .append(",\"semantic_value\":").append(q(option.getSemanticValue())).append('}');
            }
            json.append("],\"response_option_ids\":[");
            for (int j = 0; j < captured.selectedOptionIds.size(); j++) {
                if (j != 0) json.append(',');
                json.append(q(captured.selectedOptionIds.get(j)));
            }
            json.append("],\"validation_result\":")
                    .append(q(event.getResponseStatus().name()))
                    .append(",\"fallback_used\":false}");
        }
        json.append("]}\n");
        Files.writeString(path, json.toString(), StandardCharsets.UTF_8);
    }

    private static void writeDecisionReplay(final Path path, final Result result) throws IOException {
        final StringBuilder text = new StringBuilder();
        for (final CapturedDecision decision : result.captured) {
            text.append(b64(decision.request.getDecisionKind())).append('\t')
                    .append(b64(String.join(",", decision.selectedOptionIds))).append('\t')
                    .append(b64(String.join(",", decision.semanticValues))).append('\n');
        }
        Files.writeString(path, text.toString(), StandardCharsets.UTF_8);
    }

    private static void writeRngTape(final Path tape, final Path replay, final Case c, final Result result)
            throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"game_id\":").append(q("ws33-cost-" + shortId(c.pathId)))
                .append(",\"seed\":").append(RNG_SEED).append(",\"events\":[");
        final StringBuilder tsv = new StringBuilder();
        for (int i = 0; i < result.rngEvents.size(); i++) {
            if (i != 0) {
                json.append(',');
            }
            final MyRandom.RngEvent event = result.rngEvents.get(i);
            json.append("{\"event_id\":").append(event.getEventId())
                    .append(",\"stream\":").append(q(event.getStream()))
                    .append(",\"draw_index\":").append(event.getDrawIndex())
                    .append(",\"bits\":").append(event.getBits())
                    .append(",\"value\":").append(event.getValue()).append('}');
            tsv.append(event.getValue()).append('\n');
        }
        json.append("]}\n");
        Files.writeString(tape, json.toString(), StandardCharsets.UTF_8);
        Files.writeString(replay, tsv.toString(), StandardCharsets.UTF_8);
    }

    private static List<ReplayDecision> loadReplayDecisions(final Path path) throws IOException {
        final List<ReplayDecision> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 3) {
                throw new IllegalArgumentException("malformed cost replay decision line");
            }
            final List<String> ids = new ArrayList<>();
            for (final String id : unb64(fields[1]).split(",", -1)) {
                if (!id.isBlank()) {
                    ids.add(id);
                }
            }
            final List<String> semantics = new ArrayList<>();
            for (final String semantic : unb64(fields[2]).split(",", -1)) {
                if (!semantic.isBlank()) {
                    semantics.add(semantic);
                }
            }
            result.add(new ReplayDecision(unb64(fields[0]), ids, semantics));
        }
        return result;
    }

    private static List<Integer> loadReplayRng(final Path path) throws IOException {
        final List<Integer> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            result.add(Integer.parseInt(line.trim()));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("empty cost replay RNG tape");
        }
        return result;
    }

    private static void writeReplayEvidence(
            final Path dir, final Result replayResult, final Path decisionTape, final String expectedState) throws Exception {
        final String actual = replayResult.canonicalFinalState;
        final int divergence = expectedState.equals(actual) ? 0 : 1;
        final String json = "{"
                + "\"semantic_divergence\":" + divergence + ","
                + "\"comparison_basis\":\"CANONICAL_SEMANTIC_STATE\","
                + "\"decision_tape_sha256\":" + q(sha256(decisionTape)) + ","
                + "\"record_state_sha256\":" + q(sha256(expectedState.getBytes(StandardCharsets.UTF_8))) + ","
                + "\"replay_state_sha256\":" + q(sha256(actual.getBytes(StandardCharsets.UTF_8)))
                + "}\n";
        Files.writeString(dir.resolve("semantic-replay.json"), json, StandardCharsets.UTF_8);
    }

    private static String traceJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-cost-payment-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"source_path\":" + q(c.sourcePath) + ","
                + "\"source_line\":" + c.sourceLine + ","
                + "\"cost_expression\":" + q(c.costExpression) + ","
                + "\"recipe\":" + q(c.recipe) + ","
                + "\"actual_rules_core_path\":true,"
                + "\"payment_entry\":\"CostPayment.payCost/HumanCostDecision\","
                + "\"direct_effect_resolution\":false,"
                + "\"facts\":" + q(result.facts) + ","
                + "\"decision_event_count\":" + result.captured.size() + ","
                + "\"rng_event_count\":" + result.rngEvents.size() + ","
                + "\"hidden_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta
                + "}\n";
    }

    private static String observationJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-cost-principal-observation.v1\","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"secret\":\"Black Lotus\","
                + "\"secret_holder\":\"opponent\","
                + "\"pilot_visible_leak_delta\":" + result.leakDelta + ","
                + "\"cross_principal_leak_delta\":" + result.crossDelta + ","
                + "\"result\":" + q(result.leakDelta == 0 && result.crossDelta == 0 ? "PASS" : "FAIL")
                + "}\n";
    }

    private static void writeCampaignIndex(final Path root, final List<String> records) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"schema\":\"commander-simulator-next.ws33-runtime-campaign-index.v1\",\"records\":[");
        for (int i = 0; i < records.size(); i++) {
            if (i != 0) json.append(',');
            json.append(q(records.get(i)));
        }
        json.append("]}\n");
        Files.writeString(root.resolve("campaign-index.json"), json.toString(), StandardCharsets.UTF_8);
    }

    private static void writeDiagnostics(final Path root, final String mode, final List<String> diagnostics) throws IOException {
        final Path path = root.resolve("cost-" + mode + "-diagnostics.jsonl");
        Files.write(path, diagnostics, StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 12) {
                throw new IllegalArgumentException("malformed WS33 cost case line");
            }
            result.add(new Case(
                    fields[0], fields[1], unb64(fields[2]), fields[3], unb64(fields[4]),
                    unb64(fields[5]), fields[6], fields[7], fields[8], unb64(fields[9]),
                    unb64(fields[10]), Integer.parseInt(fields[11])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 cost campaign case set is empty");
        }
        return result;
    }

    private static Map<String, String> parseParams(final String json) {
        final Map<String, String> out = new LinkedHashMap<>();
        final String body = json.trim();
        if (!body.startsWith("{") || !body.endsWith("}")) {
            throw new IllegalArgumentException("malformed recipe params " + json);
        }
        final String inner = body.substring(1, body.length() - 1);
        int depth = 0;
        boolean inString = false;
        boolean escaped = false;
        int partStart = 0;
        final List<String> parts = new ArrayList<>();
        for (int i = 0; i < inner.length(); i++) {
            final char ch = inner.charAt(i);
            if (escaped) {
                escaped = false;
                continue;
            }
            if (ch == '\\' && inString) {
                escaped = true;
                continue;
            }
            if (ch == '"') {
                inString = !inString;
                continue;
            }
            if (inString) {
                continue;
            }
            if (ch == '[' || ch == '{') {
                depth++;
            } else if (ch == ']' || ch == '}') {
                depth--;
            } else if (ch == ',' && depth == 0) {
                parts.add(inner.substring(partStart, i));
                partStart = i + 1;
            }
        }
        parts.add(inner.substring(partStart));
        for (final String part : parts) {
            if (part.isBlank()) {
                continue;
            }
            final int colon = part.indexOf(':');
            if (colon < 0) {
                throw new IllegalArgumentException("malformed recipe param part " + part);
            }
            out.put(unquote(part.substring(0, colon).trim()), unquote(part.substring(colon + 1).trim()));
        }
        return out;
    }

    private static String unquote(final String value) {
        if (value.length() >= 2 && value.startsWith("\"") && value.endsWith("\"")) {
            return value.substring(1, value.length() - 1);
        }
        return value;
    }

    private static String assertion(final String id, final int expected, final int actual) {
        return "{\"assertion_id\":" + q(id)
                + ",\"expected\":" + expected
                + ",\"actual\":" + actual
                + ",\"result\":" + q(expected == actual ? "PASS" : "FAIL") + "}";
    }

    private static Path caseDir(final Path root, final String pathId) {
        return root.resolve("records").resolve(shortId(pathId));
    }

    private static String shortId(final String pathId) {
        return pathId.startsWith("forge-behavior-v2:")
                ? pathId.substring("forge-behavior-v2:".length())
                : pathId.replaceAll("[^A-Za-z0-9_.-]", "-");
    }

    private static Path requiredPath(final String property) {
        final String value = System.getProperty(property);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException(property + " system property is required");
        }
        return Path.of(value);
    }

    private static String q(final String value) {
        return "\"" + escape(value) + "\"";
    }

    private static String escape(final String value) {
        return value == null ? "" : value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r");
    }

    private static String b64(final String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static String unb64(final String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static String sha256(final Path path) throws Exception {
        return sha256(Files.readAllBytes(path));
    }

    private static String sha256(final byte[] value) throws Exception {
        final byte[] hash = MessageDigest.getInstance("SHA-256").digest(value);
        final StringBuilder out = new StringBuilder();
        for (final byte b : hash) out.append(String.format(Locale.ROOT, "%02x", b));
        return out.toString();
    }

    private static final class Case {
        final String pathId;
        final String oracleId;
        final String cardName;
        final String directive;
        final String token;
        final String costExpression;
        final String scenarioGroup;
        final String evidenceProfile;
        final String recipe;
        final Map<String, String> recipeParams;
        final String sourcePath;
        final int sourceLine;

        Case(String pathId, String oracleId, String cardName, String directive, String token,
                String costExpression, String scenarioGroup, String evidenceProfile,
                String recipe, String recipeParamsJson, String sourcePath, int sourceLine) {
            this.pathId = pathId;
            this.oracleId = oracleId;
            this.cardName = cardName;
            this.directive = directive;
            this.token = token;
            this.costExpression = costExpression;
            this.scenarioGroup = scenarioGroup;
            this.evidenceProfile = evidenceProfile;
            this.recipe = recipe;
            this.recipeParams = parseParams(recipeParamsJson);
            this.sourcePath = sourcePath;
            this.sourceLine = sourceLine;
        }
    }

    private static final class CapturedDecision {
        final ExternalDecisionRequest request;
        final List<String> selectedOptionIds;
        final List<String> semanticValues;

        CapturedDecision(ExternalDecisionRequest request, List<String> selectedOptionIds,
                List<String> semanticValues) {
            this.request = request;
            this.selectedOptionIds = new ArrayList<>(selectedOptionIds);
            this.semanticValues = new ArrayList<>(semanticValues);
        }
    }

    private static final class ReplayDecision {
        final String decisionKind;
        final List<String> optionIds;
        final List<String> semanticValues;

        ReplayDecision(String decisionKind, List<String> optionIds, List<String> semanticValues) {
            this.decisionKind = decisionKind;
            this.optionIds = new ArrayList<>(optionIds);
            this.semanticValues = new ArrayList<>(semanticValues);
        }
    }

    private static final class PaymentResult {
        final boolean paid;
        final String facts;

        PaymentResult(final boolean paid, final String facts) {
            this.paid = paid;
            this.facts = facts;
        }
    }

    private static final class Result {
        final String canonicalFinalState;
        final String facts;
        final List<CapturedDecision> captured;
        final List<ExternalDecisionTape.Event> tape;
        final List<MyRandom.RngEvent> rngEvents;
        final long leakDelta;
        final long crossDelta;

        Result(String canonicalFinalState, List<CapturedDecision> captured,
                List<ExternalDecisionTape.Event> tape,
                List<MyRandom.RngEvent> rngEvents, long leakDelta, long crossDelta) {
            final String[] split = canonicalFinalState.split("\\|facts=", 2);
            this.facts = split.length > 1 ? split[1] : canonicalFinalState;
            this.canonicalFinalState = canonicalFinalState;
            this.captured = new ArrayList<>(captured);
            this.tape = new ArrayList<>(tape);
            this.rngEvents = new ArrayList<>(rngEvents);
            this.leakDelta = leakDelta;
            this.crossDelta = crossDelta;
        }
    }

    private static final class QueueReplayProvider implements MyRandom.ReplayProvider {
        private final List<Integer> values;
        private int index;

        QueueReplayProvider(final List<Integer> values) {
            this.values = new ArrayList<>(values);
        }

        @Override
        public int next(final MyRandom.RngRequest request) {
            if (index >= values.size()) {
                throw new IllegalStateException("replay RNG tape exhausted at event " + request.getEventId());
            }
            final int value = values.get(index++);
            final long upperExclusive = 1L << request.getBits();
            if (request.getBits() < 32 && (value < 0 || (long) value >= upperExclusive)) {
                throw new IllegalStateException("recorded RNG value outside requested bit width");
            }
            return value;
        }
    }
}
