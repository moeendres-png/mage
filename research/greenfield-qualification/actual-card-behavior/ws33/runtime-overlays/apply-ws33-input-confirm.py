#!/usr/bin/env python3
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exact anchor once, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.forge_root.resolve()

    # Discretionary yes/no confirmations must cross the strict external decision
    # boundary rather than entering Forge's blocking legacy GUI input.
    confirm = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputConfirm.java"
    replace_once(
        confirm,
        """     public static boolean confirm(final PlayerControllerHuman controller, final CardView card, final SpellAbility sa, final String message, final boolean defaultIsYes, final List<String> options) {
         if (controller.getGui().isLibgdxPort()) {
""",
        """     public static boolean confirm(final PlayerControllerHuman controller, final CardView card, final SpellAbility sa, final String message, final boolean defaultIsYes, final List<String> options) {
         if (controller.hasExternalDecisionProvider()) {
             if (options == null || options.size() != 2 || options.get(0) == null || options.get(1) == null
                     || options.get(0).equals(options.get(1))) {
                 throw new ExternalDecisionValidationException(
                         ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                         \"INPUT_CONFIRM requires two distinct authoritative options\");
             }
             final List<String> selected = controller.chooseExternalUiOptions(options, 1, 1,
                     false, false, \"INPUT_CONFIRM\",
                     option -> option.equals(options.get(0)) ? \"AFFIRM\" : \"DECLINE\");
             return selected.get(0).equals(options.get(0));
         }
         if (controller.getGui().isLibgdxPort()) {
""",
        "InputConfirm external decision",
    )

    # The WS33 qualification harness needs a transport barrier that proves the remote
    # principal has processed all previously queued deltas without sending a full-state
    # snapshot and without manufacturing a pilot/rules decision. Add a payload-free,
    # Boolean-returning protocol method. GameClientHandler dispatches server protocol
    # calls to the same GUI event queue as applyDelta; the reply is therefore emitted
    # only after earlier deltas have been applied by the client-side GUI projection.
    gui_interface = root / "forge-gui/src/main/java/forge/gui/interfaces/IGuiGame.java"
    replace_once(
        gui_interface,
        """    default void setGameView(GameView gameView, long sequenceNumber) {
        setGameView(gameView);
    }
    void setGameView(GameView gameView);
""",
        """    default void setGameView(GameView gameView, long sequenceNumber) {
        setGameView(gameView);
    }
    default boolean ws33TransportBarrier() {
        return true;
    }
    void setGameView(GameView gameView);
""",
        "WS33 payload-free transport barrier interface",
    )

    protocol = root / "forge-gui/src/main/java/forge/gamemodes/net/ProtocolMethod.java"
    replace_once(
        protocol,
        """    setGameView         (Mode.SERVER, Void.TYPE, GameView.class, Long.TYPE),
    openView            (Mode.SERVER, Void.TYPE, TrackableCollection/*PlayerView*/.class),
""",
        """    setGameView         (Mode.SERVER, Void.TYPE, GameView.class, Long.TYPE),
    ws33TransportBarrier(Mode.SERVER, Boolean.TYPE),
    openView            (Mode.SERVER, Void.TYPE, TrackableCollection/*PlayerView*/.class),
""",
        "WS33 payload-free transport barrier protocol",
    )

    remote = root / "forge-gui/src/main/java/forge/gamemodes/net/server/RemoteClientGuiGame.java"
    replace_once(
        remote,
        """    public void updateGameView() {
        updateGameView(true);
    }
    private void updateGameView(boolean flush) {
""",
        """    public void updateGameView() {
        updateGameView(true);
    }

    public void awaitWs33TransportBarrier() {
        final Boolean acknowledged = sender.sendAndWait(ProtocolMethod.ws33TransportBarrier);
        if (!Boolean.TRUE.equals(acknowledged)) {
            throw new IllegalStateException(\"WS33 remote transport barrier was not acknowledged\");
        }
    }

    private void updateGameView(boolean flush) {
""",
        "WS33 remote client processed transport barrier",
    )

    # Qualification-only observer. It never changes legality, options, state, or RNG.
    # Authoritative identity is compared in memory against the decoded principal view;
    # retained evidence contains only opaque ids and a boolean identity-match result.
    trace = root / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalObservationTrace.java"
    trace.write_text(r'''package forge.gamemodes.match.input;

import forge.game.GameView;
import forge.game.card.Card;
import forge.game.card.CardView;
import forge.game.player.PlayerView;
import forge.game.zone.ZoneType;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

/** Qualification trace for principal-scoped hidden-card observations. */
public final class ExternalObservationTrace {
    private ExternalObservationTrace() { }

    private static final Set<ZoneType> ZONES = Collections.unmodifiableSet(new LinkedHashSet<>(Arrays.asList(
            ZoneType.Hand, ZoneType.Library, ZoneType.Exile, ZoneType.Sideboard,
            ZoneType.Battlefield, ZoneType.Command, ZoneType.PlanarDeck,
            ZoneType.AttractionDeck, ZoneType.ContraptionDeck)));
    private static final AtomicLong sequence = new AtomicLong();
    private static final List<Event> events = new CopyOnWriteArrayList<>();
    private static final Map<String, Boolean> lastIdentity = new ConcurrentHashMap<>();
    private static final Map<String, String> expectedOracleName = new ConcurrentHashMap<>();
    private static volatile String pathId;

    private record Event(long sequence, String pathId, String kind, int principalId,
                         int cardId, String decisionKind, boolean identityMatch) { }

    public static void reset() {
        sequence.set(0);
        events.clear();
        lastIdentity.clear();
        expectedOracleName.clear();
        pathId = null;
    }

    public static void setPath(final String value) { pathId = value; }
    public static void clearPath() { pathId = null; }

    private static String key(final String path, final int principalId, final int cardId) {
        return path + "|" + principalId + "|" + cardId;
    }

    public static void serverGrant(final int principalId, final Card card, final String decisionKind) {
        final String path = pathId;
        if (path == null || card == null) return;
        expectedOracleName.put(key(path, principalId, card.getId()), card.getName());
        events.add(new Event(sequence.incrementAndGet(), path, "SERVER_GRANT", principalId,
                card.getId(), decisionKind == null ? "OBSERVATION" : decisionKind, true));
    }

    public static void serverRevoke(final int principalId, final Card card, final String decisionKind) {
        final String path = pathId;
        if (path == null || card == null) return;
        events.add(new Event(sequence.incrementAndGet(), path, "SERVER_REVOKE", principalId,
                card.getId(), decisionKind == null ? "OBSERVATION" : decisionKind, true));
    }

    public static void observeClient(final String clientName, final GameView gameView, final String source) {
        final String path = pathId;
        if (path == null || clientName == null || gameView == null || gameView.getPlayers() == null) return;
        PlayerView viewer = null;
        for (final PlayerView p : gameView.getPlayers()) {
            if (clientName.equals(p.getName())) { viewer = p; break; }
        }
        if (viewer == null) return;
        final int principalId = viewer.getId();
        for (final PlayerView owner : gameView.getPlayers()) {
            for (final ZoneType zone : ZONES) {
                try {
                    final Iterable<CardView> cards = owner.getCards(zone);
                    if (cards == null) continue;
                    for (final CardView card : cards) {
                        if (card == null) continue;
                        final String expectedKey = key(path, principalId, card.getId());
                        final String expected = expectedOracleName.get(expectedKey);
                        if (expected == null) continue;
                        final boolean identity = identityBearing(card);
                        final String stateKey = principalId + "|" + card.getId();
                        final Boolean previous = lastIdentity.put(stateKey, identity);
                        if (previous == null || previous == identity) continue;
                        if (identity) {
                            final String actual = card.getOracleName();
                            final boolean match = expected.equals(actual) || expected.equals(card.getName());
                            events.add(new Event(sequence.incrementAndGet(), path, "CLIENT_VISIBLE", principalId,
                                    card.getId(), source == null ? "CLIENT" : source, match));
                        } else {
                            events.add(new Event(sequence.incrementAndGet(), path, "CLIENT_HIDDEN", principalId,
                                    card.getId(), source == null ? "CLIENT" : source, true));
                            expectedOracleName.remove(expectedKey);
                        }
                    }
                } catch (RuntimeException ignored) {
                    // Variant zones can be absent for ordinary players.
                }
            }
        }
    }

    private static boolean identityBearing(final CardView card) {
        if (meaningful(card.getName(), "Card", "Face Down Card", "Face-down card")) return true;
        if (meaningful(card.getOracleName())) return true;
        try {
            final CardView.CardStateView state = card.getCurrentState();
            if (state != null) {
                if (meaningful(state.getName(), "Card", "Face Down Card", "Face-down card")) return true;
                if (meaningful(state.getOracleName())) return true;
                if (meaningful(state.getTrackableImageKey())) return true;
                if (meaningful(state.getOracleText())) return true;
                if (meaningful(state.getRulesText())) return true;
            }
        } catch (RuntimeException ignored) { }
        return false;
    }

    private static boolean meaningful(final String value, final String... neutral) {
        if (value == null || value.isBlank()) return false;
        for (final String n : neutral) if (value.equalsIgnoreCase(n)) return false;
        return true;
    }

    private static String esc(final String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }

    public static void write(final Path path) throws Exception {
        final List<Event> copy = new ArrayList<>(events);
        copy.sort(Comparator.comparingLong(Event::sequence));
        final List<String> lines = new ArrayList<>();
        for (final Event e : copy) {
            lines.add("{\"sequence\":" + e.sequence()
                    + ",\"path_id\":\"" + esc(e.pathId()) + "\""
                    + ",\"kind\":\"" + esc(e.kind()) + "\""
                    + ",\"principal_id\":" + e.principalId()
                    + ",\"card_id\":" + e.cardId()
                    + ",\"decision_kind\":\"" + esc(e.decisionKind()) + "\""
                    + ",\"identity_match\":" + e.identityMatch() + "}");
        }
        Files.write(path, lines, StandardCharsets.UTF_8);
    }
}
''', encoding="utf-8")

    # Client-side observation is sampled only after NetworkGuiGame has applied each
    # delta/full sync. This is the actual principal projection, not server intent.
    client = root / "forge-gui-desktop/src/test/java/forge/net/HeadlessNetworkClient.java"
    replace_once(
        client,
        '            Ws05HiddenInfoProbe.observe(client.username, getGameView(), "delta:" + packet.getSequenceNumber());\n',
        '            Ws05HiddenInfoProbe.observe(client.username, getGameView(), "delta:" + packet.getSequenceNumber());\n'
        '            forge.gamemodes.match.input.ExternalObservationTrace.observeClient(client.username, getGameView(), "delta:" + packet.getSequenceNumber());\n',
        "principal observation after delta apply",
    )
    replace_once(
        client,
        '                Ws05HiddenInfoProbe.observe(client.username, getGameView(), "full:" + sequenceNumber);\n',
        '                Ws05HiddenInfoProbe.observe(client.username, getGameView(), "full:" + sequenceNumber);\n'
        '                forge.gamemodes.match.input.ExternalObservationTrace.observeClient(client.username, getGameView(), "full:" + sequenceNumber);\n',
        "principal observation after full apply",
    )

    human = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"

    # WS01 exports exact legal entity/discrete options but intentionally carries no
    # hidden CardView payload. Restore stock-Forge observation semantics for the bound
    # principal only: temporarily grant look permission for authoritative Card choices,
    # flush the real RemoteClientGuiGame projection, wait until the client applied it,
    # then revoke and wait for redaction before returning to rules execution.
    replace_once(
        human,
        """    private <T> List<T> chooseExternalDiscrete(final List<T> choices, final int min, final int max,
""",
        """    private static final class Ws33ExternalObservation {
        private final Player principal;
        private final CardCollection cards;
        private final String decisionKind;
        private Ws33ExternalObservation(final Player principal, final CardCollection cards, final String decisionKind) {
            this.principal = principal;
            this.cards = cards;
            this.decisionKind = decisionKind;
        }
        private boolean isEmpty() { return cards.isEmpty(); }
    }

    private Ws33ExternalObservation beginWs33ExternalCardObservation(final Iterable<?> choices,
                                                                     final String decisionKind) {
        final Player actor = getPlayer();
        if (actor == null) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    \"principal observation actor is unavailable\");
        }
        final Player principal = actor.getControllingPlayer() == null ? actor : actor.getControllingPlayer();
        final PlayerView viewer = PlayerView.get(principal);
        final CardCollection hidden = new CardCollection();
        if (choices != null) {
            for (final Object choice : choices) {
                if (!(choice instanceof Card card)) continue;
                final CardView view = CardView.get(card);
                final boolean alreadyVisible = view != null
                        && view.canBeShownTo(viewer) && view.canFaceDownBeShownTo(viewer);
                if (!alreadyVisible) hidden.add(card);
            }
        }
        final Ws33ExternalObservation observation = new Ws33ExternalObservation(principal, hidden, decisionKind);
        if (observation.isEmpty()) return observation;
        if (!(gui instanceof RemoteClientGuiGame remoteGui)) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    \"hidden authoritative Card choices require RemoteClient principal observation\");
        }
        for (final Card card : hidden) {
            ExternalObservationTrace.serverGrant(principal.getId(), card, decisionKind);
            card.addMayLookTemp(principal);
        }
        remoteGui.updateGameView();
        remoteGui.awaitWs33TransportBarrier();
        return observation;
    }

    private void endWs33ExternalCardObservation(final Ws33ExternalObservation observation) {
        if (observation == null || observation.isEmpty()) return;
        if (!(gui instanceof RemoteClientGuiGame remoteGui)) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    \"hidden Card observation lost RemoteClient transport\");
        }
        for (final Card card : observation.cards) {
            card.removeMayLookTemp(observation.principal);
            ExternalObservationTrace.serverRevoke(observation.principal.getId(), card, observation.decisionKind);
        }
        remoteGui.updateGameView();
        remoteGui.awaitWs33TransportBarrier();
    }

    private <T> List<T> chooseExternalDiscrete(final List<T> choices, final int min, final int max,
""",
        "external principal card observation helpers",
    )

    replace_once(
        human,
        """        final ExternalDecisionResponse response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                cancelAllowed, ExternalDecisionRequest.DISCRETE_RESPONSE_SCHEMA, constraints, context);
        if (response.isCancel()) {
""",
        """        final ExternalDecisionResponse response;
        final Ws33ExternalObservation observation = beginWs33ExternalCardObservation(choices, decisionKind);
        try {
            response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                    cancelAllowed, ExternalDecisionRequest.DISCRETE_RESPONSE_SCHEMA, constraints, context);
        } finally {
            endWs33ExternalCardObservation(observation);
        }
        if (response.isCancel()) {
""",
        "discrete principal observation lifetime",
    )

    replace_once(
        human,
        """            final ExternalDecisionResponse response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                    cancelAllowed, ExternalDecisionRequest.RESPONSE_SCHEMA, constraints, context);
            if (response.isCancel()) {
""",
        """            final ExternalDecisionResponse response;
            final Ws33ExternalObservation observation = beginWs33ExternalCardObservation(optionList, decisionKind);
            try {
                response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                        cancelAllowed, ExternalDecisionRequest.RESPONSE_SCHEMA, constraints, context);
            } finally {
                endWs33ExternalCardObservation(observation);
            }
            if (response.isCancel()) {
""",
        "entity principal observation lifetime",
    )

    # PlayerControllerHuman.reveal() is not a discretionary rules choice. In stock Forge
    # it temporarily grants look permission and presents it. Under an external pilot,
    # reuse the exact same principal-observation transport without creating a decision.
    replace_once(
        human,
        """    protected void reveal(final CardCollectionView cards, final ZoneType zone, final PlayerView owner, String message, boolean addSuffix) {
        yieldController.maybeInterruptOnReveal();
        if (StringUtils.isBlank(message)) {
""",
        """    protected void reveal(final CardCollectionView cards, final ZoneType zone, final PlayerView owner, String message, boolean addSuffix) {
        yieldController.maybeInterruptOnReveal();
        if (hasExternalDecisionProvider()) {
            final Ws33ExternalObservation observation = beginWs33ExternalCardObservation(cards, \"REVEAL_OBSERVATION\");
            endWs33ExternalCardObservation(observation);
            return;
        }
        if (StringUtils.isBlank(message)) {
""",
        "principal-scoped external reveal observation",
    )

    print("WS33_INPUT_CONFIRM_EXTERNALIZED=TRUE")
    print("WS33_INPUT_CONFIRM_GUI_FALLBACK_EXTERNAL_MODE=0")
    print("WS33_INPUT_CONFIRM_CARD_NAME_BRANCHES=0")
    print("WS33_REVEAL_EXTERNAL_OBSERVATION=TRUE")
    print("WS33_REVEAL_GUI_BLOCK_EXTERNAL_MODE=0")
    print("WS33_REVEAL_AUTOPASS_SIDE_EFFECT_EXTERNAL_MODE=0")
    print("WS33_REVEAL_TRANSPORT=REMOTE_CLIENT_DELTA")
    print("WS33_ENTITY_CARD_OBSERVATION=PRINCIPAL_SCOPED_REMOTE_DELTA")
    print("WS33_ENTITY_CARD_OBSERVATION_DECISION_PAYLOAD_IDENTITY=0")
    print("WS33_PRINCIPAL_OBSERVATION_TRACE=IDENTITY_MATCH_BOOLEAN_ONLY")
    print("WS33_TRANSPORT_BARRIER=CLIENT_PROCESSED_REPLY")
    print("WS33_TRANSPORT_BARRIER_FULL_STATE=0")
    print("WS33_TRANSPORT_BARRIER_DECISION=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
