package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.GameEntity;
import forge.game.ability.AbilityFactory;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.player.LobbyPlayerHuman;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Focused regression tests for the generic typed TARGET_SELECTION boundary. */
public final class Ws33TargetSelectionExternalizationTest extends AITest {
    @Test
    public void actualPlayerTargetUsesOnlyTypedForgeCandidates() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final Card source = addCard("Orcish Spy", actor);
        final SpellAbility ability = source.getSpellAbilities().stream()
                .filter(SpellAbility::usesTargeting)
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("Orcish Spy target ability missing"));
        ability.setActivatingPlayer(actor);

        final ScriptedProvider provider = new ScriptedProvider(optionId(opponent));
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertTrue(controller.chooseTargetsFor(ability));
        Assert.assertTrue(ability.isTargeting(opponent));
        Assert.assertEquals(provider.requests.size(), 1);
        assertTypedEntityOptions(provider.requests.get(0));
    }

    @Test
    public void iterativeSelectionRecomputesDifferentControllerCandidates() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final Player third = game.getPlayers().get(2);
        final Card actorFirst = addCard("Runeclaw Bear", actor);
        final Card actorDuplicateController = addCard("Air Elemental", actor);
        final Card opponentTarget = addCard("Runeclaw Bear", opponent);
        addCard("Runeclaw Bear", third);
        final SpellAbility ability = ability(actor,
                "AB$ Tap | Cost$ 0 | ValidTgts$ Creature | TargetMin$ 2 | TargetMax$ 2"
                        + " | TargetsWithDifferentControllers$ True");

        final ScriptedProvider provider = new ScriptedProvider(
                optionId(actorFirst), optionId(opponentTarget));
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertTrue(controller.chooseTargetsFor(ability));
        Assert.assertEquals(ability.getTargets().size(), 2);
        Assert.assertFalse(optionIds(provider.requests.get(1)).contains(optionId(actorFirst)));
        Assert.assertFalse(optionIds(provider.requests.get(1)).contains(optionId(actorDuplicateController)));
        Assert.assertTrue(optionIds(provider.requests.get(1)).contains(optionId(opponentTarget)));
    }

    @Test
    public void optionalSelectionOffersDoneAsAnExplicitTransition() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        addCard("Runeclaw Bear", game.getPlayers().get(1));
        final SpellAbility ability = ability(actor,
                "AB$ Tap | Cost$ 0 | ValidTgts$ Creature | TargetMin$ 0 | TargetMax$ 2");

        final ScriptedProvider provider = new ScriptedProvider("choice:0");
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertTrue(controller.chooseTargetsFor(ability));
        Assert.assertEquals(ability.getTargets().size(), 0);
        Assert.assertTrue(optionIds(provider.requests.get(0)).contains("choice:0"));
        Assert.assertTrue(provider.requests.get(0).isCancelAllowed());
        Assert.assertFalse(optionIds(provider.requests.get(0)).stream()
                .anyMatch(id -> id.startsWith("target-action:")));
    }

    @Test
    public void optionalTargetingUsesEnvelopeCancellationWithoutPseudoOption() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        addCard("Runeclaw Bear", game.getPlayers().get(1));
        final SpellAbility ability = ability(actor,
                "AB$ Tap | Cost$ 0 | ValidTgts$ Creature | TargetMin$ 1 | TargetMax$ 1");

        final ScriptedProvider provider = ScriptedProvider.cancel();
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertFalse(controller.chooseTargetsFor(ability));
        Assert.assertTrue(provider.requests.get(0).isCancelAllowed());
        Assert.assertFalse(optionIds(provider.requests.get(0)).stream()
                .anyMatch(id -> id.startsWith("target-action:")));
    }

    @Test
    public void mixedPlayerAndCardShapeRemainsTypedAndServerMapped() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final Card permanent = addCard("Runeclaw Bear", opponent);
        final SpellAbility ability = ability(actor,
                "AB$ Tap | Cost$ 0 | ValidTgts$ Any | TargetMin$ 1 | TargetMax$ 1");

        final ScriptedProvider provider = new ScriptedProvider(optionId(permanent));
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertTrue(controller.chooseTargetsFor(ability));
        final Set<String> ids = optionIds(provider.requests.get(0));
        Assert.assertTrue(ids.contains(optionId(permanent)));
        Assert.assertTrue(ids.contains(optionId(opponent)));
        assertTypedEntityOptions(provider.requests.get(0));
    }

    @Test
    public void forgeMustTargetFilteringRemainsAuthoritative() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final Card flagbearer = addCard("Coalition Honor Guard", opponent);
        final Card ordinary = addCard("Runeclaw Bear", opponent);
        final SpellAbility ability = ability(actor,
                "AB$ Tap | Cost$ 0 | ValidTgts$ Creature | TargetMin$ 1 | TargetMax$ 1");

        final ScriptedProvider provider = new ScriptedProvider(optionId(flagbearer));
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertTrue(controller.chooseTargetsFor(ability));
        final Set<String> ids = optionIds(provider.requests.get(0));
        Assert.assertTrue(ids.contains(optionId(flagbearer)));
        Assert.assertFalse(ids.contains(optionId(ordinary)));
        Assert.assertTrue(ability.isTargeting(flagbearer));
    }

    @Test
    public void randomTargetNeverCrossesThePilotBoundary() {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        addCard("Runeclaw Bear", actor);
        addCard("Runeclaw Bear", game.getPlayers().get(1));
        final SpellAbility ability = ability(actor,
                "AB$ Tap | Cost$ 0 | ValidTgts$ Creature | TargetMin$ 1 | TargetMax$ 1"
                        + " | TargetsAtRandom$ True");

        final ScriptedProvider provider = new ScriptedProvider();
        final PlayerControllerHuman controller = controller(game, actor, provider);
        Assert.assertTrue(controller.chooseTargetsFor(ability));
        Assert.assertEquals(ability.getTargets().size(), 1);
        Assert.assertTrue(provider.requests.isEmpty(), "random target leaked into pilot decisions");
    }

    private SpellAbility ability(final Player actor, final String definition) {
        final Card source = addCard("Sol Ring", actor);
        final SpellAbility ability = AbilityFactory.getAbility(definition, source);
        ability.setActivatingPlayer(actor);
        return ability;
    }

    private static PlayerControllerHuman controller(final Game game, final Player actor,
                                                    final ScriptedProvider provider) {
        final PlayerControllerHuman controller = new PlayerControllerHuman(
                game, actor, new LobbyPlayerHuman("ws33-target-principal"));
        controller.setExternalDecisionProvider(provider::respond);
        return controller;
    }

    private static String optionId(final GameEntity entity) {
        return ExternalDecisionRequest.optionIdFor(entity);
    }

    private static Set<String> optionIds(final ExternalDecisionRequest request) {
        final Set<String> result = new HashSet<>();
        for (final ExternalDecisionRequest.Option option : request.getOptions()) {
            result.add(option.getOptionId());
        }
        return result;
    }

    private static void assertTypedEntityOptions(final ExternalDecisionRequest request) {
        Assert.assertEquals(request.getDecisionKind(), "TARGET_SELECTION");
        Assert.assertEquals(request.getVisibilityScope(), ExternalDecisionRequest.VISIBILITY_PRINCIPAL_ONLY);
        Assert.assertEquals(request.getMinimumSelection(), 1);
        Assert.assertEquals(request.getMaximumSelection(), 1);
        for (final ExternalDecisionRequest.Option option : request.getOptions()) {
            if (option.getOptionId().startsWith("choice:")) {
                continue;
            }
            Assert.assertTrue(option.isEntityBacked());
            Assert.assertEquals(option.getOptionId(),
                    option.getEntityKind().toLowerCase() + ":" + option.getEntityId());
            Assert.assertEquals(option.getSemanticValue(), String.valueOf(option.getEntityId()));
        }
    }

    private static final class ScriptedProvider {
        private final Deque<String> responses = new ArrayDeque<>();
        private final List<ExternalDecisionRequest> requests = new ArrayList<>();
        private final boolean cancel;

        private ScriptedProvider(final String... optionIds) {
            this(false, optionIds);
        }

        private ScriptedProvider(final boolean cancel, final String... optionIds) {
            this.cancel = cancel;
            responses.addAll(List.of(optionIds));
        }

        private static ScriptedProvider cancel() {
            return new ScriptedProvider(true);
        }

        private ExternalDecisionResponse respond(final ExternalDecisionRequest request) {
            requests.add(request);
            if (cancel) {
                return new ExternalDecisionResponse(
                        request.getDecisionId(), request.getToken(), request.getActorId(),
                        request.getPrincipalId(), request.getResponseSchema(), List.of(), true);
            }
            final String optionId = responses.pollFirst();
            if (optionId == null) {
                throw new IllegalStateException("unexpected target decision request");
            }
            if (!optionIds(request).contains(optionId)) {
                throw new IllegalStateException("scripted response is absent from authoritative options: " + optionId);
            }
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(),
                    request.getPrincipalId(), request.getResponseSchema(), List.of(optionId), false);
        }
    }
}
