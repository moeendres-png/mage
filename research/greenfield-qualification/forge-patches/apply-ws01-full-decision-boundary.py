#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one anchor in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"refusing to overwrite unexpected existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def patch_player_controller(root: Path) -> None:
    path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"

    replace_once(
        path,
        "public class PlayerControllerHuman extends PlayerController implements IGameController, IHasForgeLog {\n",
        "public class PlayerControllerHuman extends PlayerController implements IGameController, IHasForgeLog {\n"
        "\n"
        "    /** Qualification-only construction hook. Null in normal Forge execution. */\n"
        "    private static volatile Function<Player, ExternalDecisionProvider> externalDecisionProviderFactory;\n"
        "\n"
        "    public static void setExternalDecisionProviderFactory(final Function<Player, ExternalDecisionProvider> factory) {\n"
        "        externalDecisionProviderFactory = factory;\n"
        "    }\n"
    )

    replace_once(
        path,
        "        inputProxy = new InputProxy(this);\n"
        "        inputQueue = new InputQueue(game0.getView(), inputProxy);\n"
        "    }\n\n"
        "    public PlayerControllerHuman(final Player p, final LobbyPlayer lp, final PlayerControllerHuman owner) {",
        "        inputProxy = new InputProxy(this);\n"
        "        inputQueue = new InputQueue(game0.getView(), inputProxy);\n"
        "        final Function<Player, ExternalDecisionProvider> factory = externalDecisionProviderFactory;\n"
        "        if (factory != null) {\n"
        "            final ExternalDecisionProvider provider = factory.apply(p);\n"
        "            if (provider == null) {\n"
        "                throw new ExternalDecisionValidationException(\n"
        "                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,\n"
        "                        \"external decision provider factory returned null\");\n"
        "            }\n"
        "            setExternalDecisionProvider(provider);\n"
        "        }\n"
        "    }\n\n"
        "    public PlayerControllerHuman(final Player p, final LobbyPlayer lp, final PlayerControllerHuman owner) {"
    )

    replace_once(
        path,
        "        gui = owner.gui;\n"
        "        inputProxy = owner.inputProxy;\n"
        "        inputQueue = owner.getInputQueue();\n"
        "    }",
        "        gui = owner.gui;\n"
        "        inputProxy = owner.inputProxy;\n"
        "        inputQueue = owner.getInputQueue();\n"
        "        if (owner.hasExternalDecisionProvider()) {\n"
        "            setExternalDecisionProvider(owner.externalDecisionProvider);\n"
        "        }\n"
        "    }"
    )

    replace_once(
        path,
        "    <T> List<T> chooseExternalUiOptions(final List<T> choices, final int min, final int max,\n",
        "    public <T> List<T> chooseExternalUiOptions(final List<T> choices, final int min, final int max,\n"
    )
    replace_once(
        path,
        "    boolean chooseExternalUiBoolean(final String decisionKind) {\n",
        "    public boolean chooseExternalUiBoolean(final String decisionKind) {\n"
    )

    replace_once(
        path,
        "    @Override\n"
        "    public boolean mulliganKeepHand(final Player mulliganingPlayer, int cardsToReturn) {\n"
        "        rejectExternalDecision(\"MULLIGAN\");\n",
        "    @Override\n"
        "    public boolean mulliganKeepHand(final Player mulliganingPlayer, int cardsToReturn) {\n"
        "        if (hasExternalDecisionProvider()) {\n"
        "            return chooseExternalBoolean(\"MULLIGAN\");\n"
        "        }\n"
    )

    replace_once(
        path,
        "    @Override\n"
        "    public CardCollectionView tuckCardsViaMulligan(CardCollectionView hand, int cardsToReturn) {\n"
        "        rejectExternalDecision(\"MULLIGAN_TUCK\");\n",
        "    @Override\n"
        "    public CardCollectionView tuckCardsViaMulligan(CardCollectionView hand, int cardsToReturn) {\n"
        "        if (hasExternalDecisionProvider()) {\n"
        "            return new CardCollection(chooseExternalEntities(hand, cardsToReturn, cardsToReturn,\n"
        "                    false, null, \"MULLIGAN_TUCK\"));\n"
        "        }\n"
    )

    priority_anchor = (
        "    @Override\n"
        "    public List<SpellAbility> chooseSpellAbilityToPlay() {\n"
        "        rejectExternalDecision(\"PRIORITY_ACTION\");\n"
    )
    priority_impl = (
        "    private List<SpellAbility> collectExternalPriorityAbilities() {\n"
        "        final List<SpellAbility> result = new ArrayList<>();\n"
        "        for (final Card card : getGame().getCardsInGame()) {\n"
        "            for (final SpellAbility ability : card.getAllPossibleAbilities(player, true)) {\n"
        "                result.add(ability);\n"
        "            }\n"
        "        }\n"
        "        return result;\n"
        "    }\n"
        "\n"
        "    private List<SpellAbility> chooseExternalPriorityAction() {\n"
        "        final List<SpellAbility> abilities = collectExternalPriorityAbilities();\n"
        "        final List<Integer> choices = new ArrayList<>(abilities.size() + 1);\n"
        "        choices.add(-1);\n"
        "        for (int i = 0; i < abilities.size(); i++) {\n"
        "            choices.add(i);\n"
        "        }\n"
        "        final Integer selected = chooseExternalDiscrete(choices, 1, 1, false, false,\n"
        "                \"PRIORITY_ACTION\", index -> index < 0\n"
        "                        ? \"PASS_PRIORITY\"\n"
        "                        : \"spellability:\" + abilities.get(index).getId());\n"
        "        if (selected.get(0) < 0) {\n"
        "            return null;\n"
        "        }\n"
        "        return List.of(abilities.get(selected.get(0)));\n"
        "    }\n"
        "\n"
        "    @Override\n"
        "    public List<SpellAbility> chooseSpellAbilityToPlay() {\n"
        "        if (hasExternalDecisionProvider()) {\n"
        "            return chooseExternalPriorityAction();\n"
        "        }\n"
    )
    replace_once(path, priority_anchor, priority_impl)

    replace_once(
        path,
        "    @Override\n"
        "    public PlayerZone chooseStartingHand(List<PlayerZone> zones) {\n"
        "        rejectExternalDecision(\"STARTING_HAND\");\n",
        "    @Override\n"
        "    public PlayerZone chooseStartingHand(List<PlayerZone> zones) {\n"
        "        if (hasExternalDecisionProvider()) {\n"
        "            if (zones == null || zones.isEmpty()) {\n"
        "                throw new ExternalDecisionValidationException(\n"
        "                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,\n"
        "                        \"STARTING_HAND has no authoritative zone options\");\n"
        "            }\n"
        "            return chooseExternalDiscrete(zones, 1, 1, false, false, \"STARTING_HAND\",\n"
        "                    zone -> \"zone:\" + zone.getZoneType().name()).get(0);\n"
        "        }\n"
    )

    replace_once(
        path,
        "    @Override\n"
        "    public ReplacementEffect chooseSingleReplacementEffect(final List<ReplacementEffect> possibleReplacers) {\n"
        "        rejectExternalDecision(\"REPLACEMENT_ORDER\");\n"
        "        final ReplacementEffect first = possibleReplacers.get(0);\n",
        "    @Override\n"
        "    public ReplacementEffect chooseSingleReplacementEffect(final List<ReplacementEffect> possibleReplacers) {\n"
        "        if (hasExternalDecisionProvider()) {\n"
        "            if (possibleReplacers == null || possibleReplacers.isEmpty()) {\n"
        "                throw new ExternalDecisionValidationException(\n"
        "                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,\n"
        "                        \"REPLACEMENT_ORDER has no authoritative options\");\n"
        "            }\n"
        "            return chooseExternalDiscrete(possibleReplacers, 1, 1, false, false,\n"
        "                    \"REPLACEMENT_ORDER\", replacement -> \"replacement:\" + replacement.getId()).get(0);\n"
        "        }\n"
        "        final ReplacementEffect first = possibleReplacers.get(0);\n"
    )


def patch_tape(root: Path) -> None:
    path = root / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionTape.java"
    replace_once(
        path,
        "public final class ExternalDecisionTape {\n",
        "public final class ExternalDecisionTape {\n"
        "    @FunctionalInterface\n"
        "    public interface EventObserver {\n"
        "        void onEvent(Event event);\n"
        "    }\n"
        "\n"
        "    private static volatile EventObserver eventObserver;\n"
        "\n"
        "    public static void setEventObserver(final EventObserver observer) {\n"
        "        eventObserver = observer;\n"
        "    }\n"
    )
    replace_once(
        path,
        "        events.add(new Event(eventSequence.incrementAndGet(), request, response, status, errorCode));\n",
        "        final Event event = new Event(eventSequence.incrementAndGet(), request, response, status, errorCode);\n"
        "        events.add(event);\n"
        "        final EventObserver observer = eventObserver;\n"
        "        if (observer != null) {\n"
        "            observer.onEvent(event);\n"
        "        }\n"
    )


def patch_network_harness(root: Path) -> None:
    path = root / "forge-gui-desktop/src/test/java/forge/net/UnifiedNetworkHarness.java"
    replace_once(
        path,
        "                if (i == 0) {\n"
        "                    // Host is always local AI\n"
        "                    slot.setType(LobbySlotType.AI);\n",
        "                if (i == 0) {\n"
        "                    // WS01 qualification can force the host through a real local Human controller.\n"
        "                    slot.setType(Boolean.getBoolean(\"forge.ws01.externalHumanHost\")\n"
        "                            ? LobbySlotType.LOCAL : LobbySlotType.AI);\n"
    )


def add_full_game_runner(root: Path) -> None:
    path = root / "forge-gui-desktop/src/test/java/forge/net/ExternalDecisionFullGameRunner.java"
    write_new(path, r'''package forge.net;

import forge.game.player.Player;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.player.PlayerControllerHuman;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * WS01 qualification entry point. Runs a real four-player Commander game with
 * all player controllers on the strict external decision boundary. The pilot is
 * intentionally non-strategic: keep the opening hand and explicitly choose the
 * authoritative PASS_PRIORITY option. No AI/default/random/pass fallback is
 * invoked inside the rules/controller path.
 */
public final class ExternalDecisionFullGameRunner {
    private ExternalDecisionFullGameRunner() {}

    private static final class QualificationPilot {
        ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
            final List<String> selected = new ArrayList<>();
            switch (request.getDecisionKind()) {
                case "MULLIGAN" -> selected.add(requireSemantic(request, "true"));
                case "PRIORITY_ACTION" -> selected.add(requireSemantic(request, "PASS_PRIORITY"));
                case "STARTING_PLAYER" -> selected.add(lowestOptionId(request));
                case "STARTING_HAND" -> selected.add(lowestOptionId(request));
                default -> throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "qualification pilot has no explicit policy for " + request.getDecisionKind());
            }
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(), request.getPrincipalId(),
                    request.getResponseSchema(), selected, false);
        }

        private static String requireSemantic(final ExternalDecisionRequest request, final String semantic) {
            for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                if (semantic.equals(option.getSemanticValue())) {
                    return option.getOptionId();
                }
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "authoritative option missing from " + request.getDecisionKind() + ": " + semantic);
        }

        private static String lowestOptionId(final ExternalDecisionRequest request) {
            String best = null;
            for (final ExternalDecisionRequest.Option option : request.getOptions()) {
                if (best == null || option.getOptionId().compareTo(best) < 0) {
                    best = option.getOptionId();
                }
            }
            if (best == null) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                        "authoritative option set is empty for " + request.getDecisionKind());
            }
            return best;
        }
    }

    public static void main(final String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("usage: ExternalDecisionFullGameRunner <decision-tape-json>");
        }
        final Path out = Path.of(args[0]);
        final CopyOnWriteArrayList<ExternalDecisionTape.Event> events = new CopyOnWriteArrayList<>();
        final QualificationPilot pilot = new QualificationPilot();

        System.setProperty("forge.ws01.externalHumanHost", "true");
        ExternalDecisionTape.setEventObserver(events::add);
        PlayerControllerHuman.setExternalDecisionProviderFactory((Player ignored) -> pilot::decide);
        try {
            final UnifiedNetworkHarness.GameResult result = new UnifiedNetworkHarness()
                    .playerCount(4)
                    .remoteClients(3)
                    .useAiForRemotePlayers(false)
                    .commander(true)
                    .gameTimeout(300000)
                    .execute();
            writeTape(out, events, result);
            if (!result.passed()) {
                throw new IllegalStateException("4P strict external full game failed: " + result.toSummary());
            }
            if (events.isEmpty()) {
                throw new IllegalStateException("full game completed without DecisionTape events");
            }
            boolean sawPriority = false;
            boolean sawMulligan = false;
            for (final ExternalDecisionTape.Event event : events) {
                if (event.getResponseStatus() != ExternalDecisionTape.ResponseStatus.ACCEPTED) {
                    throw new IllegalStateException("non-accepted DecisionTape event in qualification game: "
                            + event.getDecisionKind() + "/" + event.getResponseStatus());
                }
                sawPriority |= "PRIORITY_ACTION".equals(event.getDecisionKind());
                sawMulligan |= "MULLIGAN".equals(event.getDecisionKind());
            }
            if (!sawPriority || !sawMulligan) {
                throw new IllegalStateException("full-game tape did not observe required priority/mulligan families");
            }
            System.out.println("WS01_FULL_GAME_DECISION_TAPE=PASS");
            System.out.println("WS01_FULL_GAME_EVENTS=" + events.size());
            System.out.println("WS01_FULL_GAME_TURNS=" + result.turnCount);
        } finally {
            PlayerControllerHuman.setExternalDecisionProviderFactory(null);
            ExternalDecisionTape.setEventObserver(null);
            System.clearProperty("forge.ws01.externalHumanHost");
        }
    }

    private static void writeTape(final Path out, final List<ExternalDecisionTape.Event> events,
                                  final UnifiedNetworkHarness.GameResult result) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\n  \"schema\": \"commander-simulator-next.full-game-decision-tape.v1\",");
        json.append("\n  \"player_count\": 4,");
        json.append("\n  \"format\": \"Commander\",");
        json.append("\n  \"game_completed\": ").append(result.gameCompleted).append(',');
        json.append("\n  \"turn_count\": ").append(result.turnCount).append(',');
        json.append("\n  \"event_count\": ").append(events.size()).append(',');
        json.append("\n  \"events\": [");
        for (int i = 0; i < events.size(); i++) {
            final ExternalDecisionTape.Event e = events.get(i);
            if (i != 0) json.append(',');
            json.append("\n    {\"event_id\":").append(e.getEventId())
                    .append(",\"decision_id\":").append(e.getDecisionId())
                    .append(",\"token\":").append(e.getToken())
                    .append(",\"decision_kind\":\"").append(escape(e.getDecisionKind())).append('\"')
                    .append(",\"actor_id\":").append(e.getActorId())
                    .append(",\"principal_id\":").append(e.getPrincipalId())
                    .append(",\"response_status\":\"").append(e.getResponseStatus()).append('\"')
                    .append(",\"selected_option_ids\":[");
            for (int j = 0; j < e.getSelectedOptionIds().size(); j++) {
                if (j != 0) json.append(',');
                json.append('\"').append(escape(e.getSelectedOptionIds().get(j))).append('\"');
            }
            json.append(']');
            if (e.getErrorCode() != null) {
                json.append(",\"error_code\":\"").append(escape(e.getErrorCode())).append('\"');
            }
            json.append('}');
        }
        json.append("\n  ]\n}\n");
        Files.createDirectories(out.toAbsolutePath().getParent());
        Files.writeString(out, json.toString(), StandardCharsets.UTF_8);
    }

    private static String escape(final String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
''')


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: apply-ws01-full-decision-boundary.py <forge-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    patch_player_controller(root)
    patch_tape(root)
    patch_network_harness(root)
    add_full_game_runner(root)
    print("WS01_FULL_DECISION_PATCH_APPLIED=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
