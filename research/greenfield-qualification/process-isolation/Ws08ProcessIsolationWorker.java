package forge.net;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.item.PaperCard;
import forge.model.FModel;
import forge.player.PlayerControllerHuman;
import forge.util.MyRandom;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Properties;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/**
 * One WS08 worker process owns exactly one real 4P Commander runtime. All
 * decision-relevant static hooks are intentionally process-local. The parent
 * qualification test launches multiple independent JVMs concurrently.
 */
public final class Ws08ProcessIsolationWorker {
    private Ws08ProcessIsolationWorker() {}

    public static void main(final String[] args) throws Exception {
        if (args.length != 8) {
            throw new IllegalArgumentException(
                    "usage: <label> <gameId> <seed> <canary> <foreignCanary> <controllerTag> <port> <outDir>");
        }
        final String label = args[0];
        final String gameId = args[1];
        final long seed = Long.parseLong(args[2]);
        final String canary = args[3];
        final String foreignCanary = args[4];
        final String controllerTag = args[5];
        final int port = Integer.parseInt(args[6]);
        final Path outDir = Path.of(args[7]).toAbsolutePath();
        Files.createDirectories(outDir);
        final Path readyPath = outDir.resolve("ready.marker");

        final long pid = ProcessHandle.current().pid();
        final CopyOnWriteArrayList<MyRandom.RngEvent> rngEvents = new CopyOnWriteArrayList<>();
        final CopyOnWriteArrayList<ExternalDecisionTape.Event> decisionEvents = new CopyOnWriteArrayList<>();
        final CopyOnWriteArrayList<String> states = new CopyOnWriteArrayList<>();
        final AtomicLong stateSequence = new AtomicLong();
        final AtomicLong controllerInvocations = new AtomicLong();
        final AtomicBoolean readyWritten = new AtomicBoolean();

        UnifiedNetworkHarness.GameResult result = null;
        Throwable failure = null;
        try {
            TestUtils.ensureFModelInitialized();
            Ws05HiddenInfoProbe.reset();
            Ws05HiddenInfoProbe.registerSecret(canary);
            System.setProperty("ws08.foreignSentinel", foreignCanary);
            System.setProperty("forge.ws01.externalHumanHost", "true");
            System.setProperty("forge.ws06.strictGameRng", "true");

            MyRandom.beginGameScope(gameId, seed, rngEvents::add, null);
            Game.setSemanticStateObserver((game, checkpoint) -> {
                states.add(stateJson(gameId, game, stateSequence.getAndIncrement(), checkpoint));
                if (readyWritten.compareAndSet(false, true)) {
                    try {
                        Files.writeString(readyPath,
                                "pid=" + pid + "\ngame_id=" + gameId + "\ncheckpoint=" + checkpoint + "\n",
                                StandardCharsets.UTF_8);
                    } catch (IOException error) {
                        throw new IllegalStateException("unable to write WS08 ready marker", error);
                    }
                }
            });
            ExternalDecisionTape.setEventObserver(event -> {
                decisionEvents.add(event);
                Ws05HiddenInfoProbe.observeReplay(event);
            });
            PlayerControllerHuman.setExternalDecisionProviderFactory(player -> request -> {
                controllerInvocations.incrementAndGet();
                Ws05HiddenInfoProbe.observeDecision(player.getName(), player.getId(), request);
                return decide(request);
            });

            result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .decks(createQualificationDecks(canary))
                    .port(port)
                    .connectionTimeout(45_000)
                    .gameTimeout(180_000)
                    .execute();

            if (result == null || !result.passed() || !result.gameCompleted) {
                throw new IllegalStateException("WS08 4P worker failed: " + (result == null ? "null" : result.toSummary()));
            }
            if (states.isEmpty() || rngEvents.isEmpty() || decisionEvents.isEmpty()) {
                throw new IllegalStateException("WS08 worker emitted an empty authoritative stream");
            }
            if (Ws05HiddenInfoProbe.transportSamples() <= 0 || Ws05HiddenInfoProbe.requestCount() <= 0) {
                throw new IllegalStateException("WS08 worker did not exercise principal observations and decisions");
            }
        } catch (Throwable thrown) {
            failure = thrown;
            Ws05HiddenInfoProbe.observeException(thrown);
        } finally {
            try {
                writeEvidence(outDir, label, gameId, seed, canary, controllerTag, port, pid,
                        result, states, rngEvents, decisionEvents, controllerInvocations.get(), failure);
            } finally {
                PlayerControllerHuman.setExternalDecisionProviderFactory(null);
                ExternalDecisionTape.setEventObserver(null);
                Game.setSemanticStateObserver(null);
                MyRandom.endGameScope();
                System.clearProperty("forge.ws06.strictGameRng");
                System.clearProperty("forge.ws01.externalHumanHost");
                System.clearProperty("ws08.foreignSentinel");
            }
        }

        if (failure != null) {
            failure.printStackTrace(System.err);
            System.exit(1);
        }
        System.out.println("WS08_WORKER=PASS");
        System.out.println("WS08_WORKER_LABEL=" + label);
        System.out.println("WS08_WORKER_PID=" + pid);
        System.out.println("WS08_GAME_ID=" + gameId);
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
                    "WS08 qualification pilot has no explicit policy for " + request.getDecisionKind());
        }
        return new ExternalDecisionResponse(
                request.getDecisionId(), request.getToken(), request.getActorId(), request.getPrincipalId(),
                request.getResponseSchema(), selected, false);
    }

    private static String requireSemantic(final ExternalDecisionRequest request, final String semantic) {
        for (final ExternalDecisionRequest.Option option : request.getOptions()) {
            if (semantic.equals(option.getSemanticValue())) return option.getOptionId();
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                "authoritative option missing for " + request.getDecisionKind() + ": " + semantic);
    }

    private static String lowestOptionId(final ExternalDecisionRequest request) {
        String best = null;
        for (final ExternalDecisionRequest.Option option : request.getOptions()) {
            if (best == null || option.getOptionId().compareTo(best) < 0) best = option.getOptionId();
        }
        if (best == null) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "authoritative option set empty for " + request.getDecisionKind());
        }
        return best;
    }

    private static void selectLowestExact(final ExternalDecisionRequest request, final List<String> selected) {
        final List<ExternalDecisionRequest.Option> ordered = new ArrayList<>(request.getOptions());
        ordered.sort(Comparator.comparing(ExternalDecisionRequest.Option::getOptionId));
        final int count = request.getMinimumSelection();
        if (count < 0 || count > ordered.size() || count != request.getMaximumSelection()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "WS08 qualification requires exact cardinality for " + request.getDecisionKind());
        }
        for (int i = 0; i < count; i++) selected.add(ordered.get(i).getOptionId());
    }

    private static List<Deck> createQualificationDecks(final String canaryName) {
        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard("Isamaru, Hound of Konda");
        final PaperCard canary = FModel.getMagicDb().getCommonCards().getCard(canaryName);
        if (commander == null) throw new IllegalStateException("WS08 commander card unavailable");
        if (canary == null) throw new IllegalStateException("WS08 canary card unavailable: " + canaryName);
        final List<Deck> decks = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            final Deck deck = TestDeckLoader.createMinimalDeck("Plains", i == 0 ? 12 : 20);
            if (i == 0) {
                for (int j = 0; j < 8; j++) deck.getMain().add(canary);
            }
            deck.getOrCreate(DeckSection.Commander).add(commander);
            decks.add(deck);
        }
        return decks;
    }

    private static String stateJson(final String gameId, final Game game, final long sequence, final String checkpoint) {
        final StringBuilder json = new StringBuilder();
        json.append("{\"game_id\":\"").append(escape(gameId)).append('\"')
                .append(",\"sequence\":").append(sequence)
                .append(",\"checkpoint\":\"").append(escape(checkpoint)).append('\"')
                .append(",\"turn\":").append(game.getPhaseHandler().getTurn())
                .append(",\"phase\":");
        final PhaseType phase = game.getPhaseHandler().getPhase();
        appendStringOrNull(json, phase == null ? null : phase.name());
        json.append(",\"active_player\":");
        appendIntOrNull(json, game.getPhaseHandler().getPlayerTurn() == null ? null : game.getPhaseHandler().getPlayerTurn().getId());
        json.append(",\"starting_player\":");
        appendIntOrNull(json, game.getStartingPlayer() == null ? null : game.getStartingPlayer().getId());
        json.append(",\"players\":[");
        final List<Player> players = new ArrayList<>();
        for (final Player player : game.getRegisteredPlayers()) players.add(player);
        players.sort(Comparator.comparingInt(Player::getId));
        for (int i = 0; i < players.size(); i++) {
            if (i != 0) json.append(',');
            final Player player = players.get(i);
            json.append("{\"id\":").append(player.getId()).append(",\"life\":").append(player.getLife()).append(",\"zones\":{");
            appendZone(json, player, ZoneType.Library, true); json.append(',');
            appendZone(json, player, ZoneType.Hand, false); json.append(',');
            appendZone(json, player, ZoneType.Battlefield, false); json.append(',');
            appendZone(json, player, ZoneType.Graveyard, false); json.append(',');
            appendZone(json, player, ZoneType.Exile, false); json.append(',');
            appendZone(json, player, ZoneType.Command, false);
            json.append("}}");
        }
        return json.append("]}").toString();
    }

    private static void appendZone(final StringBuilder json, final Player player, final ZoneType zone, final boolean ordered) {
        final List<Card> cards = new ArrayList<>();
        for (final Card card : player.getCardsIn(zone)) cards.add(card);
        if (!ordered) cards.sort(Comparator.comparingInt(Card::getId));
        json.append('\"').append(zone.name()).append("\":[");
        for (int i = 0; i < cards.size(); i++) {
            if (i != 0) json.append(',');
            final Card card = cards.get(i);
            json.append("{\"id\":").append(card.getId()).append(",\"name\":\"")
                    .append(escape(card.getName())).append("\"}");
        }
        json.append(']');
    }

    private static void writeEvidence(
            final Path outDir, final String label, final String gameId, final long seed,
            final String canary, final String controllerTag, final int port, final long pid,
            final UnifiedNetworkHarness.GameResult result, final List<String> states,
            final List<MyRandom.RngEvent> rngEvents, final List<ExternalDecisionTape.Event> decisions,
            final long controllerInvocations, final Throwable failure) throws Exception {
        Files.write(outDir.resolve("states.jsonl"), states, StandardCharsets.UTF_8);

        final List<String> rngLines = new ArrayList<>();
        for (final MyRandom.RngEvent event : rngEvents) {
            rngLines.add(event.getEventId() + "\t" + clean(event.getGameId()) + "\t" + clean(event.getStream())
                    + "\t" + event.getDrawIndex() + "\t" + event.getBits() + "\t" + event.getValue());
        }
        Files.write(outDir.resolve("rng.tsv"), rngLines, StandardCharsets.UTF_8);

        final List<ExternalDecisionTape.Event> ordered = new ArrayList<>(decisions);
        ordered.sort((left, right) -> {
            final int p = Integer.compare(left.getPrincipalId(), right.getPrincipalId());
            return p != 0 ? p : Long.compare(left.getEventId(), right.getEventId());
        });
        final List<String> decisionLines = new ArrayList<>();
        for (final ExternalDecisionTape.Event event : ordered) {
            final String scoped = gameId + ":" + event.getPrincipalId() + ":" + event.getDecisionId() + ":" + event.getToken();
            decisionLines.add(clean(scoped) + "\t" + clean(controllerTag) + "\t" + event.getDecisionId()
                    + "\t" + event.getToken() + "\t" + clean(event.getDecisionKind()) + "\t"
                    + event.getActorId() + "\t" + event.getPrincipalId() + "\t" + event.getResponseStatus());
        }
        Files.write(outDir.resolve("decisions.tsv"), decisionLines, StandardCharsets.UTF_8);

        final Properties props = new Properties();
        props.setProperty("worker_label", label);
        props.setProperty("pid", Long.toString(pid));
        props.setProperty("game_id", gameId);
        props.setProperty("seed", Long.toString(seed));
        props.setProperty("canary", canary);
        props.setProperty("controller_tag", controllerTag);
        props.setProperty("port", Integer.toString(port));
        props.setProperty("player_count", result == null ? "0" : Integer.toString(result.playerCount));
        props.setProperty("game_completed", Boolean.toString(result != null && result.gameCompleted));
        props.setProperty("game_passed", Boolean.toString(result != null && result.passed()));
        props.setProperty("turn_count", result == null ? "-1" : Integer.toString(result.turnCount));
        props.setProperty("full_state_syncs", result == null ? "0" : Long.toString(result.fullStateSyncsReceived));
        props.setProperty("delta_packets", result == null ? "0" : Long.toString(result.deltaPacketsReceived));
        props.setProperty("state_count", Integer.toString(states.size()));
        props.setProperty("rng_count", Integer.toString(rngEvents.size()));
        props.setProperty("decision_count", Integer.toString(decisions.size()));
        props.setProperty("controller_invocations", Long.toString(controllerInvocations));
        props.setProperty("observation_samples", Long.toString(Ws05HiddenInfoProbe.transportSamples()));
        props.setProperty("pilot_visible_hidden_info_leaks", Long.toString(Ws05HiddenInfoProbe.pilotVisibleLeaks()));
        props.setProperty("cross_principal_decision_leaks", Long.toString(Ws05HiddenInfoProbe.crossPrincipalLeaks()));
        props.setProperty("cross_game_observation_leaks", Long.toString(Ws05HiddenInfoProbe.ws08CrossGameObservationLeaks()));
        props.setProperty("failure", failure == null ? "" : failure.getClass().getName() + ":" + String.valueOf(failure.getMessage()));
        props.setProperty("states_sha256", sha256(outDir.resolve("states.jsonl")));
        props.setProperty("rng_sha256", sha256(outDir.resolve("rng.tsv")));
        props.setProperty("decisions_sha256", sha256(outDir.resolve("decisions.tsv")));
        try (var writer = Files.newBufferedWriter(outDir.resolve("summary.properties"), StandardCharsets.UTF_8)) {
            props.store(writer, "WS08 worker evidence");
        }
    }

    private static String sha256(final Path path) throws Exception {
        final byte[] bytes = Files.readAllBytes(path);
        final byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
        final StringBuilder out = new StringBuilder();
        for (final byte b : digest) out.append(String.format("%02x", b));
        return out.toString();
    }

    private static String clean(final String value) {
        return value == null ? "" : value.replace("\t", " ").replace("\n", " ").replace("\r", " ");
    }

    private static void appendStringOrNull(final StringBuilder json, final String value) {
        if (value == null) json.append("null"); else json.append('\"').append(escape(value)).append('\"');
    }

    private static void appendIntOrNull(final StringBuilder json, final Integer value) {
        if (value == null) json.append("null"); else json.append(value);
    }

    private static String escape(final String value) {
        return value == null ? "" : value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }
}
