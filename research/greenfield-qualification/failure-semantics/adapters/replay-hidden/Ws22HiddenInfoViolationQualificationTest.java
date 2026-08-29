package forge.net;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.card.CardView;
import forge.game.player.Player;
import forge.game.player.PlayerView;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.HostedMatch;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.gamemodes.match.input.UnifiedOutcome;
import forge.gamemodes.match.input.UnifiedOutcomeCategory;
import forge.gamemodes.net.server.FServerManager;
import forge.gamemodes.net.server.RemoteClient;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** WS22 negative-path proof against the exact WS05 principal visibility detector. */
public class Ws22HiddenInfoViolationQualificationTest {
    private static final String BOB = "Bob (Remote)";
    private static final String HIDDEN_CANARY = "Elite Vanguard";

    @BeforeClass
    public static void setUp() {
        TestUtils.ensureFModelInitialized();
    }

    @Test(timeOut = 300000)
    public void actualCrossPrincipalCardViewLeakFailsClosed() throws Exception {
        final Path evidence = Path.of(System.getProperty("ws22.hiddenEvidencePath"));
        final InjectionLifecycle lifecycle = new InjectionLifecycle(evidence);

        Ws05HiddenInfoProbe.reset();
        System.setProperty("forge.ws01.externalHumanHost", "true");
        ExternalDecisionTape.setEventObserver(Ws05HiddenInfoProbe::observeReplay);
        PlayerControllerHuman.setExternalDecisionProviderFactory(player -> request -> {
            Ws05HiddenInfoProbe.observeDecision(player.getName(), player.getId(), request);
            lifecycle.injectAtFirstPriority(request);
            return decide(request);
        });

        UnifiedNetworkHarness.GameResult result = null;
        Throwable harnessFailure = null;
        try {
            result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .decks(createQualificationDecks())
                    .connectionTimeout(45000)
                    .gameTimeout(180000)
                    .execute();
        } catch (Throwable expectedControlledAbort) {
            harnessFailure = expectedControlledAbort;
        } finally {
            PlayerControllerHuman.setExternalDecisionProviderFactory(null);
            ExternalDecisionTape.setEventObserver(null);
        }

        final boolean failClosed = harnessFailure != null || result == null || !result.gameCompleted;
        lifecycle.writeEvidence(failClosed);

        Assert.assertTrue(lifecycle.injected, "controlled forbidden CardView datum was not injected");
        Assert.assertTrue(lifecycle.detected, "WS05 detector did not catch the actual cross-principal CardView identity");
        Assert.assertFalse(lifecycle.authorizedForTargetPrincipal, "qualification datum was not actually forbidden");
        Assert.assertTrue(lifecycle.actualCardViewIdentityBearing, "qualification datum was not an identity-bearing CardView");
        Assert.assertTrue(lifecycle.stateWitnessUnchanged, "hidden-info detector path changed authoritative game witness state");
        Assert.assertTrue(lifecycle.publicEnvelopeSecretSafe, "public HIDDEN_INFO_VIOLATION envelope reproduced the secret");
        Assert.assertEquals(lifecycle.leaksBefore, 0L, "baseline had a pre-existing hidden-info leak");
        Assert.assertEquals(lifecycle.leaksAfter, 1L, "controlled injection did not produce exactly one detected leak");
        Assert.assertTrue(failClosed, "hidden-info violation was followed by continued successful game execution");
        System.out.println("WS22_HIDDEN_INFO_VIOLATION=PASS");
    }

    private static final class ControlledHiddenInfoAbort extends RuntimeException {
        private ControlledHiddenInfoAbort() {
            super("WS22 controlled hidden-information boundary abort");
        }
    }

    private static final class InjectionLifecycle {
        private final Path evidence;
        private boolean injected;
        private boolean detected;
        private boolean authorizedForTargetPrincipal;
        private boolean actualCardViewIdentityBearing;
        private boolean stateWitnessUnchanged;
        private boolean publicEnvelopeSecretSafe;
        private long leaksBefore = -1;
        private long leaksAfter = -1;
        private UnifiedOutcome outcome;

        private InjectionLifecycle(final Path evidence) {
            this.evidence = evidence;
        }

        private synchronized void injectAtFirstPriority(final ExternalDecisionRequest request) {
            if (injected || request == null || !"PRIORITY_ACTION".equals(request.getDecisionKind())) return;
            injected = true;

            final HostedMatch match = HeadlessGuiDesktop.getLastMatch();
            if (match == null || match.getGame() == null || match.getGame().getPlayers().size() != 4) {
                throw new IllegalStateException("4P hosted game unavailable at WS22 injection boundary");
            }
            final Game game = match.getGame();
            final Player owner = findPlayer(game, "Alice");
            final Player bob = findPlayer(game, "Bob");
            final Card target = findCanaryInLibrary(owner);
            Ws05HiddenInfoProbe.registerSecret(target.getName());

            flushPrincipalViews();
            try {
                if (!Ws05HiddenInfoProbe.awaitRemoteClients(3, 10000L)) {
                    throw new IllegalStateException("principal transport observers unavailable for WS22 injection");
                }
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("interrupted awaiting principal transport observers", interrupted);
            }

            leaksBefore = Ws05HiddenInfoProbe.pilotVisibleLeaks();
            if (leaksBefore != 0L) {
                throw new IllegalStateException("qualified Q2 boundary already reports a hidden-info leak before injection");
            }

            final CardView cardView = target.getView();
            final PlayerView bobView = bob.getView();
            authorizedForTargetPrincipal = cardView.canBeShownTo(bobView) && cardView.canFaceDownBeShownTo(bobView);
            actualCardViewIdentityBearing = cardView.getName() != null && !cardView.getName().isBlank()
                    && !"Card".equalsIgnoreCase(cardView.getName());
            if (authorizedForTargetPrincipal || !actualCardViewIdentityBearing) {
                throw new IllegalStateException("WS22 test datum is not a forbidden identity-bearing CardView");
            }

            final String before = stateWitness(owner, target);
            detected = Ws05HiddenInfoProbe.observeInjectedTransportDatum(
                    BOB, cardView, bobView, "ws22-controlled-q2-boundary");
            leaksAfter = Ws05HiddenInfoProbe.pilotVisibleLeaks();
            final String after = stateWitness(owner, target);
            stateWitnessUnchanged = before.equals(after);

            outcome = UnifiedOutcome.failure(
                    UnifiedOutcomeCategory.HIDDEN_INFO_VIOLATION,
                    "corr:ws22:hidden-info-violation",
                    "ws22-4p-hidden-info-game",
                    request.getDecisionId(),
                    bob.getId());
            final String publicEnvelope = publicEnvelope(outcome);
            final String digest = sha256(target.getName());
            publicEnvelopeSecretSafe = !publicEnvelope.contains(target.getName()) && !publicEnvelope.contains(digest);

            if (!detected || leaksAfter != 1L || !stateWitnessUnchanged || !publicEnvelopeSecretSafe) {
                throw new IllegalStateException("WS22 hidden-info adapter invariants failed");
            }
            // No response is returned. The current decision/game is aborted rather than
            // substituting pass/cancel/first/random/default behavior.
            throw new ControlledHiddenInfoAbort();
        }

        private void writeEvidence(final boolean failClosed) throws Exception {
            if (outcome == null) throw new IllegalStateException("no HIDDEN_INFO_VIOLATION outcome was emitted");
            Files.createDirectories(evidence.getParent());
            final String json = "{\n"
                    + "  \"schema\": \"commander-simulator-next.ws22-hidden-info-runtime.v1\",\n"
                    + "  \"detector_boundary\": \"WS05_CARDVIEW_PLAYERVIEW_AUTHORIZATION\",\n"
                    + "  \"actual_cardview_identity_bearing\": " + actualCardViewIdentityBearing + ",\n"
                    + "  \"authorized_for_target_principal\": " + authorizedForTargetPrincipal + ",\n"
                    + "  \"detected\": " + detected + ",\n"
                    + "  \"leaks_before\": " + leaksBefore + ",\n"
                    + "  \"leaks_after\": " + leaksAfter + ",\n"
                    + "  \"state_witness_unchanged\": " + stateWitnessUnchanged + ",\n"
                    + "  \"public_envelope_secret_safe\": " + publicEnvelopeSecretSafe + ",\n"
                    + "  \"fail_closed\": " + failClosed + ",\n"
                    + "  \"outcome\": " + publicEnvelope(outcome) + "\n"
                    + "}\n";
            Files.writeString(evidence, json, StandardCharsets.UTF_8);
        }
    }

    private static String stateWitness(final Player owner, final Card target) {
        return target.getId() + "|" + owner.getCardsIn(ZoneType.Library).size()
                + "|" + target.isInZone(ZoneType.Library) + "|" + target.isFaceDown();
    }

    private static String publicEnvelope(final UnifiedOutcome outcome) {
        return "{"
                + "\"schema\":\"" + escape(UnifiedOutcome.SCHEMA) + "\","
                + "\"category\":\"" + outcome.getCategory().name() + "\","
                + "\"correlation_id\":\"" + escape(outcome.getCorrelationId()) + "\","
                + "\"game_id\":\"" + escape(outcome.getGameId()) + "\","
                + "\"decision_id\":" + (outcome.getDecisionId() == null ? "null" : outcome.getDecisionId()) + ","
                + "\"principal_id\":" + (outcome.getPrincipalId() == null ? "null" : outcome.getPrincipalId()) + ","
                + "\"public_message\":\"" + escape(outcome.getPublicMessage()) + "\","
                + "\"state_committed\":" + outcome.isStateCommitted()
                + "}";
    }

    private static String escape(final String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }

    private static String sha256(final String value) {
        try {
            final byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8));
            final StringBuilder out = new StringBuilder();
            for (byte b : digest) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception error) {
            throw new IllegalStateException(error);
        }
    }

    private static void flushPrincipalViews() {
        final FServerManager server = FServerManager.getInstance();
        for (int slot = 1; slot <= 3; slot++) {
            final RemoteClient client = server.getClientBySlotIndex(slot);
            if (client == null || client.getGui() == null) {
                throw new IllegalStateException("remote principal projection unavailable for slot " + slot);
            }
            client.getGui().updateGameView();
        }
    }

    private static Player findPlayer(final Game game, final String prefix) {
        for (Player player : game.getPlayers()) if (player.getName().startsWith(prefix)) return player;
        throw new IllegalStateException("player not found: " + prefix);
    }

    private static Card findCanaryInLibrary(final Player owner) {
        for (Card card : owner.getCardsIn(ZoneType.Library)) {
            if (HIDDEN_CANARY.equals(card.getName())) return card;
        }
        throw new IllegalStateException("hidden canary did not remain in host library");
    }

    private static List<Deck> createQualificationDecks() {
        final List<Deck> decks = new ArrayList<>();
        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");
        final PaperCard canary = FModel.getMagicDb().getCommonCards().getCard(HIDDEN_CANARY);
        if (commander == null || canary == null) throw new IllegalStateException("qualification cards unavailable");
        for (int i = 0; i < 4; i++) {
            final Deck deck = TestDeckLoader.createMinimalDeck("Plains", i == 0 ? 12 : 20);
            if (i == 0) for (int j = 0; j < 8; j++) deck.getMain().add(canary);
            deck.getOrCreate(DeckSection.Commander).add(commander);
            decks.add(deck);
        }
        return decks;
    }

    private static ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
        final List<String> selected = new ArrayList<>();
        switch (request.getDecisionKind()) {
            case "MULLIGAN" -> selected.add(requireSemantic(request, "true"));
            case "PRIORITY_ACTION" -> selected.add(requireSemantic(request, "PASS_PRIORITY"));
            case "STARTING_PLAYER", "STARTING_HAND" -> selected.add(lowestOptionId(request));
            case "MAX_HAND_SIZE_DISCARD" -> selectLowestExact(request, selected);
            case "DECLARE_ATTACKERS", "DECLARE_BLOCKERS" -> selected.add(requireSemantic(request, "DONE"));
            default -> throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "WS22 pilot has no explicit policy for " + request.getDecisionKind());
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
                    "WS22 qualification policy requires exact cardinality for " + request.getDecisionKind());
        }
        for (int i = 0; i < count; i++) selected.add(ordered.get(i).getOptionId());
    }
}
