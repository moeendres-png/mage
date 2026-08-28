package forge.net;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.HostedMatch;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

/** Real 4P Commander WS05 campaign over network views and the strict external-pilot boundary. */
public class Ws05HiddenInfoQualificationTest {
    private static final String BOB = "Bob (Remote)";
    private static final String CHARLIE = "Charlie (Remote)";
    private static final String DIANA = "Diana (Remote)";
    private static final Set<String> NONE = Collections.emptySet();

    @BeforeClass
    public static void setUp() {
        TestUtils.ensureFModelInitialized();
    }

    @Test(timeOut = 240000)
    public void fourPlayerPrincipalScopedHiddenInformationBoundary() throws Exception {
        final Path evidence = Path.of(System.getProperty("ws05.evidencePath"));
        final Path secretPath = Path.of(System.getProperty("ws05.secretPath"));
        final AtomicBoolean lifecycleComplete = new AtomicBoolean(false);
        final AtomicReference<Throwable> lifecycleFailure = new AtomicReference<>();

        Ws05HiddenInfoProbe.reset();
        System.setProperty("forge.ws01.externalHumanHost", "true");
        ExternalDecisionTape.setEventObserver(Ws05HiddenInfoProbe::observeReplay);
        PlayerControllerHuman.setExternalDecisionProviderFactory(player -> request -> {
            Ws05HiddenInfoProbe.observeDecision(player.getName(), player.getId(), request);
            return decide(request);
        });

        final Thread lifecycle = new Thread(() -> {
            try {
                exerciseVisibilityLifecycle(secretPath);
                lifecycleComplete.set(true);
            } catch (Throwable error) {
                lifecycleFailure.set(error);
                Ws05HiddenInfoProbe.observeException(error);
            }
        }, "WS05-Hidden-Info-Lifecycle");
        lifecycle.setDaemon(true);
        lifecycle.start();

        UnifiedNetworkHarness.GameResult result = null;
        try {
            result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .decks(createQualificationDecks())
                    .connectionTimeout(45000)
                    .gameTimeout(120000)
                    .execute();
            lifecycle.join(30000L);
        } finally {
            PlayerControllerHuman.setExternalDecisionProviderFactory(null);
            ExternalDecisionTape.setEventObserver(null);
        }

        if (result == null) throw new IllegalStateException("network harness returned no result");
        final boolean coverage = lifecycleComplete.get() && requiredLifecycleCoverage();
        Ws05HiddenInfoProbe.writeEvidence(
                evidence, result.gameCompleted, result.playerCount, result.gameFormat,
                result.fullStateSyncsReceived, result.deltaPacketsReceived, coverage);

        if (lifecycleFailure.get() != null) {
            throw new AssertionError("WS05 lifecycle exercise failed", lifecycleFailure.get());
        }
        Assert.assertTrue(result.passed(), "4P Commander network game must complete: " + result.toSummary());
        Assert.assertTrue(coverage, "all principal/lifecycle phase observations must be present");
        Assert.assertEquals(Ws05HiddenInfoProbe.pilotVisibleLeaks(), 0L, "pilot-visible hidden identity leak");
        Assert.assertEquals(Ws05HiddenInfoProbe.crossPrincipalLeaks(), 0L, "cross-principal DecisionRequest leak");
        Assert.assertEquals(Ws05HiddenInfoProbe.phaseMismatchCount(), 0L, "look/reveal lifecycle mismatch");
        Assert.assertTrue(Ws05HiddenInfoProbe.faceDownSamples() > 0, "face-down hidden transport not exercised");
        Assert.assertTrue(Ws05HiddenInfoProbe.requestCount() > 0, "strict DecisionRequest path not exercised");
        Assert.assertTrue(Ws05HiddenInfoProbe.replayCount() > 0, "replay-facing DecisionTape not exercised");

        exceptionSurfaceContract();
        System.out.println("WS05_PILOT_VISIBLE_HIDDEN_INFO_LEAKS=0");
        System.out.println("WS05_CROSS_PRINCIPAL_DECISION_LEAKS=0");
        System.out.println("WS05_LOOK_REVEAL_LIFECYCLE=PASS");
        System.out.println("WS05_HIDDEN_INFO=PASS");
    }

    private static ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
        final List<String> selected = new ArrayList<>();
        switch (request.getDecisionKind()) {
            case "MULLIGAN" -> selected.add(requireSemantic(request, "true"));
            case "PRIORITY_ACTION" -> selected.add(requireSemantic(request, "PASS_PRIORITY"));
            case "STARTING_PLAYER", "STARTING_HAND" -> selected.add(lowestOptionId(request));
            case "MAX_HAND_SIZE_DISCARD" -> selectLowestExact(request, selected);
            default -> throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "WS05 pilot has no explicit policy for " + request.getDecisionKind());
        }
        return new ExternalDecisionResponse(
                request.getDecisionId(), request.getToken(), request.getActorId(), request.getPrincipalId(),
                request.getResponseSchema(), selected, false);
    }

    private static String requireSemantic(final ExternalDecisionRequest request, final String semantic) {
        for (ExternalDecisionRequest.Option option : request.getOptions()) {
            if (semantic.equals(option.getSemanticValue())) return option.getOptionId();
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                "authoritative option missing for " + request.getDecisionKind());
    }

    private static String lowestOptionId(final ExternalDecisionRequest request) {
        String best = null;
        for (ExternalDecisionRequest.Option option : request.getOptions()) {
            if (best == null || option.getOptionId().compareTo(best) < 0) best = option.getOptionId();
        }
        if (best == null) throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                "authoritative option set empty for " + request.getDecisionKind());
        return best;
    }

    private static void selectLowestExact(final ExternalDecisionRequest request, final List<String> selected) {
        final List<ExternalDecisionRequest.Option> ordered = new ArrayList<>(request.getOptions());
        ordered.sort(java.util.Comparator.comparing(ExternalDecisionRequest.Option::getOptionId));
        final int count = request.getMinimumSelection();
        if (count < 0 || count > ordered.size() || count != request.getMaximumSelection()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "WS05 qualification policy requires exact cardinality for " + request.getDecisionKind());
        }
        for (int i = 0; i < count; i++) selected.add(ordered.get(i).getOptionId());
    }

    private static List<Deck> createQualificationDecks() {
        final List<Deck> decks = new ArrayList<>();
        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");
        if (commander == null) throw new IllegalStateException("qualification commander card is unavailable");
        for (int i = 0; i < 4; i++) {
            final Deck deck = TestDeckLoader.createMinimalDeck("Plains", 12);
            deck.getOrCreate(DeckSection.Commander).add(commander);
            decks.add(deck);
        }
        return decks;
    }

    private static void exerciseVisibilityLifecycle(final Path secretPath) throws Exception {
        Assert.assertTrue(Ws05HiddenInfoProbe.awaitRemoteClients(3, 45000), "three remote principal views required");
        Game game = awaitGame(45000L);
        Player owner = findPlayer(game, "Alice");
        Player bob = findPlayer(game, "Bob");
        Player charlie = findPlayer(game, "Charlie");
        Player diana = findPlayer(game, "Diana");

        Card target = deepLibraryCard(owner, false);
        Files.createDirectories(secretPath.getParent());
        Files.writeString(secretPath, target.getName(), StandardCharsets.UTF_8);
        Ws05HiddenInfoProbe.registerSecret(target.getName());

        Ws05HiddenInfoProbe.setPhase("HIDDEN_BASE", target.getId(), NONE);
        target.addMayLookTemp(owner);
        awaitPhase("HIDDEN_BASE");
        target.removeMayLookTemp(owner);

        Ws05HiddenInfoProbe.setPhase("PRIVATE_LOOK", target.getId(), Set.of(BOB));
        target.addMayLookTemp(bob);
        awaitPhase("PRIVATE_LOOK");
        Ws05HiddenInfoProbe.setPhase("HIDDEN_AFTER_LOOK", target.getId(), NONE);
        target.removeMayLookTemp(bob);
        awaitPhase("HIDDEN_AFTER_LOOK");

        long revealTimestamp = game.getNextTimestamp();
        Ws05HiddenInfoProbe.setPhase("PUBLIC_REVEAL", target.getId(), Set.of(BOB, CHARLIE, DIANA));
        target.addMayLookAt(revealTimestamp, game.getPlayers());
        awaitPhase("PUBLIC_REVEAL");
        Ws05HiddenInfoProbe.setPhase("HIDDEN_AFTER_REVEAL", target.getId(), NONE);
        target.removeMayLookAt(revealTimestamp);
        awaitPhase("HIDDEN_AFTER_REVEAL");

        Ws05HiddenInfoProbe.setPhase("PRIVATE_SEARCH", target.getId(), Set.of(CHARLIE));
        target.addMayLookTemp(charlie);
        awaitPhase("PRIVATE_SEARCH");
        Ws05HiddenInfoProbe.setPhase("HIDDEN_AFTER_SEARCH", target.getId(), NONE);
        target.removeMayLookTemp(charlie);
        awaitPhase("HIDDEN_AFTER_SEARCH");

        Ws05HiddenInfoProbe.setPhase("KNOWN_TOP", target.getId(), Set.of(DIANA));
        target.addMayLookTemp(diana);
        awaitPhase("KNOWN_TOP");
        Ws05HiddenInfoProbe.setPhase("HIDDEN_AFTER_KNOWN_TOP", target.getId(), NONE);
        target.removeMayLookTemp(diana);
        awaitPhase("HIDDEN_AFTER_KNOWN_TOP");

        Card faceDown = target;
        if (!faceDown.turnFaceDown(true)) throw new IllegalStateException("failed to turn qualification card face down");
        Ws05HiddenInfoProbe.setPhase("FACE_DOWN_BATTLEFIELD", faceDown.getId(), NONE);
        Card moved = game.getAction().moveToPlay(faceDown, owner, null, null);
        if (moved == null || !moved.isInZone(ZoneType.Battlefield) || !moved.isFaceDown()) {
            throw new IllegalStateException("face-down battlefield setup did not persist");
        }
        awaitPhase("FACE_DOWN_BATTLEFIELD");
    }

    private static Game awaitGame(final long timeoutMs) throws Exception {
        long deadline = System.currentTimeMillis() + timeoutMs;
        while (System.currentTimeMillis() < deadline) {
            HostedMatch match = HeadlessGuiDesktop.getLastMatch();
            if (match != null && match.getGame() != null && match.getGame().getPlayers().size() == 4) return match.getGame();
            Thread.sleep(50L);
        }
        throw new IllegalStateException("4P server game not available for lifecycle exercise");
    }

    private static Player findPlayer(final Game game, final String prefix) {
        for (Player player : game.getPlayers()) if (player.getName().startsWith(prefix)) return player;
        throw new IllegalStateException("player not found: " + prefix);
    }

    private static Card deepLibraryCard(final Player owner, final boolean requireLand) {
        int seen = 0;
        Card fallback = null;
        for (Card card : owner.getCardsIn(ZoneType.Library)) {
            if (fallback == null) fallback = card;
            if (requireLand && !card.isLand()) continue;
            if (++seen >= 12) return card;
        }
        if (fallback != null && (!requireLand || fallback.isLand())) return fallback;
        if (requireLand) {
            for (Card card : owner.getCardsIn(ZoneType.Library)) if (card.isPermanent()) return card;
        }
        if (fallback != null) return fallback;
        throw new IllegalStateException("library has no suitable qualification card");
    }

    private static void awaitPhase(final String phase) throws InterruptedException {
        final long deadline = System.currentTimeMillis() + 5000L;
        while (System.currentTimeMillis() < deadline) {
            if (Ws05HiddenInfoProbe.phaseSampleCount(phase, BOB) > 0
                    && Ws05HiddenInfoProbe.phaseSampleCount(phase, CHARLIE) > 0
                    && Ws05HiddenInfoProbe.phaseSampleCount(phase, DIANA) > 0) return;
            Thread.sleep(50L);
        }
        throw new IllegalStateException("missing decoded client observation for phase " + phase);
    }

    private static boolean requiredLifecycleCoverage() {
        String[] phases = {
                "HIDDEN_BASE", "PRIVATE_LOOK", "HIDDEN_AFTER_LOOK", "PUBLIC_REVEAL",
                "HIDDEN_AFTER_REVEAL", "PRIVATE_SEARCH", "HIDDEN_AFTER_SEARCH", "KNOWN_TOP",
                "HIDDEN_AFTER_KNOWN_TOP", "FACE_DOWN_BATTLEFIELD"
        };
        String[] clients = {BOB, CHARLIE, DIANA};
        for (String phase : phases) {
            for (String client : clients) {
                if (Ws05HiddenInfoProbe.phaseSampleCount(phase, client) < 1) return false;
            }
        }
        return true;
    }

    private static void exceptionSurfaceContract() {
        final String syntheticSecret = "WS05_SYNTHETIC_SECRET_CHOICE_DO_NOT_ECHO";
        ExternalDecisionRequest request = new ExternalDecisionRequest(
                9001L, 9002L, "SECRET_CHOICE", 1, 1,
                ExternalDecisionRequest.VISIBILITY_PRINCIPAL_ONLY,
                List.of(ExternalDecisionRequest.Option.discrete("choice:0", "CHOICE", syntheticSecret)),
                1, 1, false, Collections.emptyMap(),
                ExternalDecisionRequest.DISCRETE_RESPONSE_SCHEMA, Collections.emptyMap());
        ExternalDecisionResponse wrongPrincipal = new ExternalDecisionResponse(
                request.getDecisionId(), request.getToken(), request.getActorId(), 2,
                request.getResponseSchema(), List.of("choice:0"), false);
        try {
            forge.gamemodes.match.input.ExternalDecisionValidator.validate(
                    request, wrongPrincipal, request.getToken(), request.getActorId(), request.getPrincipalId(), false, false);
            Assert.fail("wrong-principal secret choice response must be rejected");
        } catch (ExternalDecisionValidationException expected) {
            Ws05HiddenInfoProbe.observeException(expected);
            Assert.assertFalse(String.valueOf(expected.getMessage()).contains(syntheticSecret),
                    "validation exception echoed secret choice semantics");
        }
    }
}
