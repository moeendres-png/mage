package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.card.CardCollection;
import forge.game.card.CardLists;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.trigger.Trigger;
import forge.game.trigger.TriggerHandler;
import forge.game.zone.ZoneType;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;

/**
 * Qualification-only WS28 diagnostic harness for the largest trigger class.
 * It never dispatches TriggerHandler.runTrigger. The event is created by
 * GameAction.moveTo, so replacement handling, zone movement and trigger
 * detection remain owned by pinned Forge. Complex production conditions remain
 * fail-closed; this census is not itself the final WS28 family witness.
 */
public final class Ws28RealChangesZoneSmokeTest extends AITest {
    private static final class CaseRow {
        String pathId;
        String oracleName;
        String rootKind;
        String rootRaw;

        static CaseRow parse(String line) {
            String[] c = line.split("\\t", -1);
            if (c.length != 22) {
                throw new IllegalArgumentException("WS28 TSV ABI mismatch: " + c.length);
            }
            CaseRow r = new CaseRow();
            r.pathId = c[0];
            r.oracleName = b64d(c[3]);
            r.rootKind = c[16];
            r.rootRaw = b64d(c[17]);
            return r;
        }
    }

    @Test
    public void realChangesZoneEventsUsePinnedForge() throws Exception {
        Path cases = Path.of(System.getProperty("ws28.cases"));
        int limit = Integer.getInteger("ws28.cz.limit", 40);
        Path out = Path.of("target", "ws28-runtime", "WS28_REAL_CHANGES_ZONE_RESULTS.tsv");
        Files.createDirectories(out.getParent());
        int attempted = 0;
        int passed = 0;
        try (BufferedWriter w = Files.newBufferedWriter(out, StandardCharsets.UTF_8)) {
            for (String line : Files.readAllLines(cases, StandardCharsets.UTF_8)) {
                if (attempted >= limit) {
                    break;
                }
                CaseRow c = CaseRow.parse(line);
                if (!"T".equals(c.rootKind) || !"ChangesZone".equals(param(c.rootRaw, "Mode"))) {
                    continue;
                }
                attempted++;
                String status = "PASS";
                String reason = "";
                try {
                    executeOne(c);
                    passed++;
                } catch (Throwable t) {
                    status = "FAIL";
                    reason = t.getClass().getName() + ": " + String.valueOf(t.getMessage());
                }
                w.write(c.pathId + "\t" + status + "\t" + b64(reason));
                w.newLine();
                w.flush();
            }
        }
        System.out.println("WS28_REAL_CHANGES_ZONE attempted=" + attempted + " passed=" + passed);
        Assert.assertTrue(attempted > 0, "real ChangesZone census must select assigned cases");
        Assert.assertEquals(passed, attempted, "every attempted real ChangesZone case must pass");
    }

    private void executeOne(CaseRow c) {
        Game game = initAndCreateGame();
        Player actor = game.getPlayers().get(0);
        Player opponent = game.getPlayers().get(1);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, actor);

        String body = c.rootRaw.substring(2);
        String originRaw = param(c.rootRaw, "Origin");
        String destinationRaw = param(c.rootRaw, "Destination");
        ZoneType destination = firstZone(destinationRaw, ZoneType.Battlefield);
        ZoneType origin = firstZone(originRaw,
                destination == ZoneType.Battlefield ? ZoneType.Hand : ZoneType.Battlefield);
        boolean self = containsSelf(param(c.rootRaw, "ValidCard"));
        String forgeName = forgeCardName(c.oracleName);

        Card host;
        Card candidate;
        if (self) {
            host = addCardToZone(forgeName, actor, origin);
            host.setSickness(false);
            candidate = host;
        } else {
            ZoneType triggerZone = firstZone(firstNonBlank(
                    param(c.rootRaw, "TriggerZones"), param(c.rootRaw, "TriggerZone")),
                    ZoneType.Battlefield);
            host = addCardToZone(forgeName, actor, triggerZone);
            host.setSickness(false);
            candidate = addMatchingCandidate(game, actor, opponent, host, body, origin);
        }

        // Use the normal intrinsic-trigger lifecycle. onlyExtrinsic=true was a
        // diagnostic bug because it excludes ordinary card-script triggers.
        game.getAction().checkStaticAbilities();
        game.getTriggerHandler().resetActiveTriggers();

        Card moved = game.getAction().moveTo(destination, candidate, null, null);
        Assert.assertNotNull(moved, "real GameAction zone move must return a card: " + c.pathId);
        Assert.assertTrue(moved.isInZone(destination),
                "real GameAction must reach destination: " + c.pathId);

        boolean collected = game.getTriggerHandler().runWaitingTriggers();
        Assert.assertTrue(collected,
                "real zone event must be detected by TriggerHandler: " + c.pathId);

        boolean hadSimultaneous = game.getStack().hasSimultaneousStackEntries();
        Assert.assertTrue(hadSimultaneous,
                "real zone trigger must reach simultaneous ordering boundary: " + c.pathId);
        game.getStack().addAllTriggeredAbilitiesToStack();
        Assert.assertFalse(game.getStack().isEmpty(),
                "real non-static zone trigger must create a regular stack object: " + c.pathId);

        drainTriggeredWork(game, c.pathId);
        Assert.assertTrue(game.getStack().isEmpty(),
                "real zone trigger resolution must empty regular stack: " + c.pathId);
        Assert.assertFalse(game.getStack().hasSimultaneousStackEntries(),
                "real zone trigger resolution must clear simultaneous entries: " + c.pathId);
    }

    private void drainTriggeredWork(Game game, String pathId) {
        for (int i = 0; i < 200; i++) {
            if (game.getStack().hasSimultaneousStackEntries()) {
                game.getStack().addAllTriggeredAbilitiesToStack();
            }
            if (game.getStack().isEmpty() && !game.getStack().hasSimultaneousStackEntries()) {
                return;
            }
            game.getPhaseHandler().mainLoopStep();
        }
        Assert.fail("bounded trigger drain did not quiesce: " + pathId);
    }

    private Card addMatchingCandidate(Game game, Player actor, Player opponent,
                                      Card host, String triggerBody, ZoneType origin) {
        Trigger exact = TriggerHandler.parseTrigger(triggerBody, host, true);
        String restriction = exact.getParam("ValidCard");
        String[] names = {
                "Runeclaw Bear", "Grizzly Bears", "Llanowar Elves", "Ornithopter",
                "Sol Ring", "Plains", "Island", "Swamp", "Mountain", "Forest",
                "Gateway Plaza", "Lightning Bolt", "Pacifism"
        };
        CardCollection pool = new CardCollection();
        for (String name : names) {
            Card a = addCardToZone(name, actor, origin);
            pool.add(a);
            Card b = addCardToZone(name, opponent, origin);
            pool.add(b);
        }
        if (restriction == null || restriction.isBlank()) {
            return pool.get(0);
        }
        CardCollection valid = CardLists.getValidCards(pool, restriction, actor, host, exact);
        Assert.assertFalse(valid.isEmpty(),
                "no actual helper card satisfies ValidCard in event origin");
        return valid.get(0);
    }

    private static String forgeCardName(String oracleName) {
        int split = oracleName.indexOf(" // ");
        return split < 0 ? oracleName : oracleName.substring(0, split);
    }

    private static boolean containsSelf(String value) {
        return value != null && (value.contains("Card.Self") || value.equals("Self"));
    }

    private static String firstNonBlank(String a, String b) {
        return a != null && !a.isBlank() ? a : b;
    }

    private static ZoneType firstZone(String value, ZoneType fallback) {
        if (value == null || value.isBlank() || "Any".equalsIgnoreCase(value)) {
            return fallback;
        }
        String first = value.split(",")[0].trim();
        try {
            return ZoneType.valueOf(first);
        } catch (IllegalArgumentException ex) {
            return fallback;
        }
    }

    private static String param(String raw, String key) {
        String body = raw.length() > 2 && raw.charAt(1) == ':' ? raw.substring(2) : raw;
        for (String part : body.split(" \\| ")) {
            int idx = part.indexOf('$');
            if (idx < 0) {
                continue;
            }
            if (key.equals(part.substring(0, idx).trim())) {
                return part.substring(idx + 1).trim();
            }
        }
        return null;
    }

    private static String b64d(String s) {
        return new String(Base64.getDecoder().decode(s), StandardCharsets.UTF_8);
    }

    private static String b64(String s) {
        return Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }
}
