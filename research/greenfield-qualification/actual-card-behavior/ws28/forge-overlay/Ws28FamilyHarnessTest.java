package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.ability.AbilityFactory;
import forge.game.ability.AbilityKey;
import forge.game.card.Card;
import forge.game.card.CardCollection;
import forge.game.card.CardLists;
import forge.game.phase.PhaseType;
import forge.game.player.PlaySpellAbility;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.trigger.Trigger;
import forge.game.trigger.TriggerHandler;
import forge.game.zone.ZoneType;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/**
 * WS28 qualification-only actual-card harness. This class is copied into the
 * exact pinned Forge checkout by CI and is never part of the production core.
 * It deliberately drives trigger detection/ordering/resolution and normal
 * PlaySpellAbility cost/target/stack processing; it never calls an effect's
 * resolve() method directly.
 */
public final class Ws28FamilyHarnessTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";

    private static final class CaseRow {
        String pathId;
        String oracleId;
        String oracleName;
        String dispatchDomain;
        String dispatchToken;
        String implementationTarget;
        boolean decisionRequired;
        boolean rngRequired;
        boolean hiddenRequired;
        boolean replayRequired;
        String rootKind;
        String rootRaw;
        String rootKey;
        String rootToken;

        static CaseRow parse(String line) {
            String[] c = line.split("\\t", -1);
            if (c.length != 22) {
                throw new IllegalArgumentException("WS28 TSV ABI mismatch: " + c.length);
            }
            CaseRow r = new CaseRow();
            r.pathId = c[0];
            r.oracleId = c[2];
            r.oracleName = b64d(c[3]);
            r.dispatchDomain = c[4];
            r.dispatchToken = c[5];
            r.implementationTarget = b64d(c[6]);
            r.decisionRequired = "1".equals(c[7]);
            r.rngRequired = "1".equals(c[8]);
            r.hiddenRequired = "1".equals(c[9]);
            r.replayRequired = "1".equals(c[10]);
            r.rootKind = c[16];
            r.rootRaw = b64d(c[17]);
            r.rootKey = c[18];
            r.rootToken = b64d(c[19]);
            return r;
        }
    }

    private static final class Execution {
        String driver;
        String initial;
        String event;
        String finalState;
        String detection = "false";
        String stackInsertion = "false";
        String resolution = "false";
        String reason = "";

        String semanticDigest() throws Exception {
            return sha256(driver + "|" + initial + "|" + event + "|" + finalState
                    + "|" + detection + "|" + stackInsertion + "|" + resolution);
        }
    }

    @Test
    public void executeAssignedFamilyPathsThroughPinnedForge() throws Exception {
        String casesProperty = System.getProperty("ws28.cases");
        Assert.assertNotNull(casesProperty, "-Dws28.cases is required");
        Path cases = Path.of(casesProperty);
        Assert.assertTrue(Files.isRegularFile(cases), "WS28 case matrix must exist");
        int limit = Integer.getInteger("ws28.limit", Integer.MAX_VALUE);
        Path out = Path.of("target", "ws28-runtime", "WS28_ENGINE_RESULTS.tsv");
        Files.createDirectories(out.getParent());

        int executed = 0;
        int failed = 0;
        try (BufferedWriter w = Files.newBufferedWriter(out, StandardCharsets.UTF_8)) {
            for (String line : Files.readAllLines(cases, StandardCharsets.UTF_8)) {
                if (line.isBlank() || executed >= limit) {
                    continue;
                }
                CaseRow c = CaseRow.parse(line);
                Execution e;
                String status = "PASS";
                try {
                    e = execute(c);
                } catch (Throwable t) {
                    e = new Execution();
                    e.driver = "FAIL_CLOSED";
                    e.reason = t.getClass().getName() + ": " + String.valueOf(t.getMessage());
                    status = "FAIL";
                    failed++;
                }
                String digest;
                try {
                    digest = e.semanticDigest();
                } catch (Throwable t) {
                    digest = "";
                }
                w.write(String.join("\t",
                        c.pathId,
                        status,
                        b64(e.driver),
                        b64(e.initial),
                        b64(e.event),
                        e.detection,
                        e.stackInsertion,
                        e.resolution,
                        b64(e.finalState),
                        digest,
                        b64(e.reason),
                        Long.toString(ProcessHandle.current().pid()),
                        FORGE_PIN));
                w.newLine();
                w.flush();
                executed++;
            }
        }
        System.out.println("WS28_ENGINE_SUMMARY executed=" + executed + " failed=" + failed);
        Assert.assertTrue(executed > 0, "WS28 must execute at least one assigned path");
        Assert.assertEquals(failed, 0, "Every attempted WS28 path must be dynamically proven");
    }

    private Execution execute(CaseRow c) throws Exception {
        switch (c.rootKind) {
            case "T":
                return executeTrigger(c);
            case "A":
                return executeAbility(c);
            default:
                throw new IllegalStateException("no dynamic driver yet for production root kind " + c.rootKind);
        }
    }

    private Execution executeTrigger(CaseRow c) throws Exception {
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);

        ZoneType hostZone = parseHostZone(c.rootRaw, ZoneType.Battlefield);
        final Card host = addCardToZone(c.oracleName, actor, hostZone);
        host.setSickness(false);
        prepareRichState(game, actor, opponent, host);

        final String body = c.rootRaw.substring(2);
        final Trigger trigger = TriggerHandler.parseTrigger(body, host, true);
        Assert.assertTrue(game.getTriggerHandler().registerOneTrigger(trigger),
                "exact parsed trigger must be active in its declared zone: " + c.pathId);
        final Map<AbilityKey, Object> params = synthTriggerParams(game, actor, opponent, host, trigger);
        Assert.assertTrue(trigger.performTest(params),
                "synthesized event must satisfy exact trigger predicate before dispatch: " + c.pathId);

        Execution e = new Execution();
        e.driver = "TRIGGER_HANDLER_EVENT_STACK_RESOLUTION";
        e.initial = stateFingerprint(game, host);
        e.event = trigger.getMode().name() + ":" + eventFingerprint(params);

        game.getTriggerHandler().runTrigger(trigger.getMode(), params, true);
        boolean collected = game.getTriggerHandler().runWaitingTriggers();
        boolean simultaneous = game.getStack().hasSimultaneousStackEntries();
        e.detection = Boolean.toString(collected && simultaneous);
        Assert.assertTrue(collected, "TriggerHandler must detect exact assigned trigger: " + c.pathId);
        Assert.assertTrue(simultaneous, "detected trigger must enter simultaneous ordering boundary: " + c.pathId);

        boolean ordered = game.getStack().addAllTriggeredAbilitiesToStack();
        e.stackInsertion = Boolean.toString(ordered && !game.getStack().isEmpty());
        Assert.assertTrue(ordered, "trigger must be authoritatively ordered onto regular stack: " + c.pathId);
        Assert.assertFalse(game.getStack().isEmpty(), "trigger must be on regular stack: " + c.pathId);

        playUntilStackClear(game);
        e.resolution = Boolean.toString(game.getStack().isEmpty() && !game.getStack().hasSimultaneousStackEntries());
        Assert.assertTrue(game.getStack().isEmpty(), "resolution must empty regular stack: " + c.pathId);
        Assert.assertFalse(game.getStack().hasSimultaneousStackEntries(),
                "resolution must empty simultaneous trigger entries: " + c.pathId);
        e.finalState = stateFingerprint(game, host);
        return e;
    }

    private Execution executeAbility(CaseRow c) throws Exception {
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);

        ZoneType hostZone = parseActivationZone(c.rootRaw, ZoneType.Battlefield);
        final Card host = addCardToZone(c.oracleName, actor, hostZone);
        host.setSickness(false);
        prepareRichState(game, actor, opponent, host);
        final SpellAbility sa = AbilityFactory.getAbility(c.rootRaw.substring(2), host);
        sa.setActivatingPlayer(actor);

        Execution e = new Execution();
        e.driver = "PLAY_SPELL_ABILITY_COST_TARGET_STACK_RESOLUTION";
        e.initial = stateFingerprint(game, host);
        e.event = "PLAY:" + String.valueOf(sa.getApi());

        boolean played = PlaySpellAbility.playSpellAbility(actor.getController(), actor, sa);
        Assert.assertTrue(played, "normal PlaySpellAbility path must accept exact root ability: " + c.pathId);
        e.detection = "true";
        if (!game.getStack().isEmpty()) {
            e.stackInsertion = "true";
            playUntilStackClear(game);
        } else if (sa.isManaAbility()) {
            e.stackInsertion = "MANA_ABILITY_NO_STACK";
        } else {
            throw new AssertionError("non-mana ability bypassed regular stack: " + c.pathId);
        }
        Assert.assertTrue(game.getStack().isEmpty(), "ability resolution must empty stack: " + c.pathId);
        e.resolution = "true";
        e.finalState = stateFingerprint(game, host);
        return e;
    }

    private void prepareRichState(Game game, Player actor, Player opponent, Card host) {
        String[] battlefield = {"Runeclaw Bear", "Grizzly Bears", "Sol Ring", "Plains", "Island", "Swamp", "Mountain", "Forest"};
        for (String name : battlefield) {
            Card a = addCardToZone(name, actor, ZoneType.Battlefield);
            a.setSickness(false);
            Card b = addCardToZone(name, opponent, ZoneType.Battlefield);
            b.setSickness(false);
        }
        String[] utility = {"Runeclaw Bear", "Grizzly Bears", "Lightning Bolt", "Pacifism", "Sol Ring", "Island"};
        for (ZoneType zone : List.of(ZoneType.Hand, ZoneType.Graveyard, ZoneType.Exile, ZoneType.Library)) {
            for (String name : utility) {
                addCardToZone(name, actor, zone);
                addCardToZone(name, opponent, zone);
            }
        }
        game.getAction().checkStaticAbilities();
    }

    private Map<AbilityKey, Object> synthTriggerParams(Game game, Player actor, Player opponent,
                                                        Card host, Trigger trigger) {
        Map<AbilityKey, Object> p = new EnumMap<>(AbilityKey.class);
        Card candidate = chooseValidCard(game, actor, host, trigger, trigger.getParam("ValidCard"));
        Card other = chooseOtherCreature(game, actor, candidate);
        SpellAbility cause = new SpellAbility.EmptySa(host, actor);
        CardCollection cards = new CardCollection();
        cards.add(candidate);
        if (other != candidate) {
            cards.add(other);
        }

        p.put(AbilityKey.Card, candidate);
        p.put(AbilityKey.CardLKI, candidate);
        p.put(AbilityKey.NewCard, candidate);
        p.put(AbilityKey.Cards, cards);
        p.put(AbilityKey.Player, actor);
        p.put(AbilityKey.Activator, actor);
        p.put(AbilityKey.AttackingPlayer, actor);
        p.put(AbilityKey.DefendingPlayer, opponent);
        p.put(AbilityKey.Attacker, candidate);
        p.put(AbilityKey.Attackers, cards);
        p.put(AbilityKey.Blocker, other);
        p.put(AbilityKey.Blockers, cards);
        p.put(AbilityKey.Attacked, opponent);
        p.put(AbilityKey.AttackedTarget, opponent);
        p.put(AbilityKey.Defender, opponent);
        p.put(AbilityKey.DamageSource, candidate);
        p.put(AbilityKey.DamageTarget, opponent);
        p.put(AbilityKey.Source, candidate);
        p.put(AbilityKey.Target, opponent);
        p.put(AbilityKey.SpellAbility, cause);
        p.put(AbilityKey.SourceSA, cause);
        p.put(AbilityKey.StackSa, cause);
        p.put(AbilityKey.Cause, cause);
        p.put(AbilityKey.DamageAmount, 3);
        p.put(AbilityKey.LifeAmount, 3);
        p.put(AbilityKey.Number, 1);
        p.put(AbilityKey.Num, 1);
        p.put(AbilityKey.CounterAmount, 1);
        p.put(AbilityKey.CounterNum, 1);
        p.put(AbilityKey.FirstTime, true);
        p.put(AbilityKey.IsCombatDamage, true);
        p.put(AbilityKey.IsCombat, true);
        p.put(AbilityKey.Fizzle, false);
        p.put(AbilityKey.Origin, chooseZoneString(trigger.getParam("Origin"), "Hand"));
        p.put(AbilityKey.Destination, chooseZoneString(trigger.getParam("Destination"), "Battlefield"));
        p.put(AbilityKey.LastStateBattlefield, new CardCollection(game.getCardsIn(ZoneType.Battlefield)));
        p.put(AbilityKey.LastStateGraveyard, new CardCollection(game.getCardsIn(ZoneType.Graveyard)));
        p.put(AbilityKey.Phase, phaseFor(trigger.getParam("Phase")));
        return p;
    }

    private Card chooseValidCard(Game game, Player actor, Card host, Trigger trigger, String restriction) {
        CardCollection all = new CardCollection();
        for (ZoneType z : List.of(ZoneType.Battlefield, ZoneType.Hand, ZoneType.Graveyard,
                ZoneType.Exile, ZoneType.Library)) {
            all.addAll(game.getCardsIn(z));
        }
        if (restriction != null && !restriction.isBlank()) {
            CardCollection valid = CardLists.getValidCards(all, restriction, actor, host, trigger);
            if (!valid.isEmpty()) {
                return valid.get(0);
            }
        }
        for (Card c : all) {
            if (c.isCreature()) {
                return c;
            }
        }
        return host;
    }

    private Card chooseOtherCreature(Game game, Player actor, Card not) {
        for (Card c : game.getCardsIn(ZoneType.Battlefield)) {
            if (c != not && c.isCreature()) {
                return c;
            }
        }
        return not;
    }

    private static ZoneType parseHostZone(String raw, ZoneType fallback) {
        String value = param(raw, "TriggerZones");
        if (value == null) {
            value = param(raw, "TriggerZone");
        }
        return parseFirstZone(value, fallback);
    }

    private static ZoneType parseActivationZone(String raw, ZoneType fallback) {
        return parseFirstZone(param(raw, "ActivationZone"), fallback);
    }

    private static ZoneType parseFirstZone(String value, ZoneType fallback) {
        if (value == null || value.isBlank() || "Any".equals(value)) {
            return fallback;
        }
        String first = value.split(",")[0];
        try {
            return ZoneType.valueOf(first);
        } catch (IllegalArgumentException ex) {
            return fallback;
        }
    }

    private static String chooseZoneString(String value, String fallback) {
        if (value == null || value.isBlank() || "Any".equals(value)) {
            return fallback;
        }
        return value.split(",")[0];
    }

    private static PhaseType phaseFor(String value) {
        if (value == null || value.isBlank()) {
            return PhaseType.MAIN1;
        }
        String first = value.split(",")[0];
        try {
            return PhaseType.smartValueOf(first);
        } catch (Throwable ignored) {
            return PhaseType.MAIN1;
        }
    }

    private static String param(String raw, String key) {
        String body = raw.length() > 2 && raw.charAt(1) == ':' ? raw.substring(2) : raw;
        for (String part : body.split(" \\| ")) {
            int d = part.indexOf('$');
            if (d > 0 && key.equals(part.substring(0, d).trim())) {
                return part.substring(d + 1).trim();
            }
        }
        return null;
    }

    private static String stateFingerprint(Game game, Card host) {
        List<String> pieces = new ArrayList<>();
        for (Player p : game.getPlayers()) {
            pieces.add("P:" + p.getName() + ":life=" + p.getLife()
                    + ":bf=" + p.getCardsIn(ZoneType.Battlefield).size()
                    + ":hand=" + p.getCardsIn(ZoneType.Hand).size()
                    + ":gy=" + p.getCardsIn(ZoneType.Graveyard).size()
                    + ":ex=" + p.getCardsIn(ZoneType.Exile).size()
                    + ":lib=" + p.getCardsIn(ZoneType.Library).size());
        }
        ZoneType hz = game.getZoneOf(host) == null ? ZoneType.None : game.getZoneOf(host).getZoneType();
        pieces.add("HOST:" + host.getName() + ":zone=" + hz + ":tapped=" + host.isTapped());
        pieces.add("STACK:" + game.getStack().size() + ":sim=" + game.getStack().hasSimultaneousStackEntries());
        Collections.sort(pieces);
        return String.join(";", pieces);
    }

    private static String eventFingerprint(Map<AbilityKey, Object> p) {
        List<String> keys = new ArrayList<>();
        for (AbilityKey k : p.keySet()) {
            Object v = p.get(k);
            if (v instanceof Card) {
                keys.add(k.name() + "=Card:" + ((Card) v).getName());
            } else if (v instanceof Player) {
                keys.add(k.name() + "=Player:" + ((Player) v).getName());
            } else if (v instanceof Number || v instanceof Boolean || v instanceof String || v instanceof PhaseType) {
                keys.add(k.name() + "=" + String.valueOf(v));
            }
        }
        Collections.sort(keys);
        return String.join(",", keys);
    }

    private static String b64(String s) {
        if (s == null) {
            s = "";
        }
        return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }

    private static String b64d(String s) {
        if (s == null || s.isEmpty()) {
            return "";
        }
        return new String(Base64.getDecoder().decode(s), StandardCharsets.UTF_8);
    }

    private static String sha256(String s) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder();
        for (byte b : digest) {
            out.append(String.format("%02x", b));
        }
        return out.toString();
    }
}
