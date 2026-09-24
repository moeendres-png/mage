package org.mage.test.serverside.rg06;

import mage.abilities.effects.common.continuous.BecomesFaceDownCreatureEffect;
import mage.abilities.effects.common.continuous.BecomesFaceDownCreatureEffect.FaceDownType;
import mage.abilities.keyword.WardAbility;
import mage.cards.Card;
import mage.constants.EmptyNames;
import mage.constants.PhaseStep;
import mage.constants.WatcherScope;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.watchers.Watcher;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

/**
 * RG-06A native ordered-library and face-down state-load qualification.
 */
public class RG06HiddenStateRestoreTest extends CardTestPlayerBase {

    private static class ForbiddenRestoreEventWatcher extends Watcher {
        private int count;

        private ForbiddenRestoreEventWatcher() {
            super(WatcherScope.GAME);
        }

        @Override
        public void watch(GameEvent event, Game game) {
            switch (event.getType()) {
                case DRAW_CARD:
                case DREW_CARD:
                case SHUFFLE_LIBRARY:
                case LIBRARY_SHUFFLED:
                case MIRACLE_CARD_REVEALED:
                case ZONE_CHANGE:
                    count++;
                    break;
                default:
                    break;
            }
        }

        int getCount() {
            return count;
        }
    }

    private static UUID libraryId(Player player, Game game, String name) {
        return player.getLibrary().getCards(game).stream()
                .filter(card -> name.equals(card.getName()))
                .map(Card::getId)
                .findFirst()
                .orElseThrow(() -> new AssertionError("Library card not found: " + name));
    }

    private static Permanent permanent(Game game, String name) {
        return game.getBattlefield().getAllActivePermanents().stream()
                .filter(p -> name.equals(p.getName()))
                .findFirst()
                .orElseThrow(() -> new AssertionError("Permanent not found: " + name));
    }

    private static void expectIllegalArgument(String message, Runnable action) {
        try {
            action.run();
            Assert.fail(message);
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    @Test
    public void orderedLibraryRestoreIsExactAndEmitsNoSyntheticEvents() {
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears", 1);
        addCard(Zone.LIBRARY, playerA, "Silvercoat Lion", 1);
        addCard(Zone.LIBRARY, playerA, "Runeclaw Bear", 1);
        skipInitShuffling();

        runCode("restore exact library order", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID lion = libraryId(player, game, "Silvercoat Lion");
            UUID grizzly = libraryId(player, game, "Grizzly Bears");
            UUID runeclaw = libraryId(player, game, "Runeclaw Bear");

            ForbiddenRestoreEventWatcher watcher = new ForbiddenRestoreEventWatcher();
            game.getState().addWatcher(watcher);
            int handBefore = player.getHand().size();
            int revealedBefore = game.getState().getRevealed().size();

            player.getLibrary().restoreOrderForGameLoad(Arrays.asList(lion, grizzly, runeclaw), game);

            Assert.assertEquals(Arrays.asList(lion, grizzly, runeclaw), player.getLibrary().getCardList());
            Assert.assertEquals("Silvercoat Lion", player.getLibrary().getFromTop(game).getName());
            Assert.assertEquals("Runeclaw Bear", player.getLibrary().getFromBottom(game).getName());
            Assert.assertEquals(handBefore, player.getHand().size());
            Assert.assertEquals(revealedBefore, game.getState().getRevealed().size());
            Assert.assertEquals("Restore must not synthesize draw/shuffle/reveal/zone events", 0, watcher.getCount());
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void genuineLaterDrawUsesRestoredTopCard() {
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears", 1);
        addCard(Zone.LIBRARY, playerA, "Silvercoat Lion", 1);
        addCard(Zone.LIBRARY, playerA, "Runeclaw Bear", 1);
        skipInitShuffling();

        runCode("put Silvercoat Lion on top", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            List<UUID> order = Arrays.asList(
                    libraryId(player, game, "Silvercoat Lion"),
                    libraryId(player, game, "Grizzly Bears"),
                    libraryId(player, game, "Runeclaw Bear")
            );
            player.getLibrary().restoreOrderForGameLoad(order, game);
        });

        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertHandCount(playerA, "Silvercoat Lion", 1);
        assertLibraryCount(playerA, "Silvercoat Lion", 0);
    }

    @Test
    public void genuineShuffleOperatesOnRestoredLibraryWithoutChangingMembership() {
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears", 1);
        addCard(Zone.LIBRARY, playerA, "Silvercoat Lion", 1);
        addCard(Zone.LIBRARY, playerA, "Runeclaw Bear", 1);
        skipInitShuffling();

        runCode("restore then authoritative shuffle", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID lion = libraryId(player, game, "Silvercoat Lion");
            UUID grizzly = libraryId(player, game, "Grizzly Bears");
            UUID runeclaw = libraryId(player, game, "Runeclaw Bear");
            List<UUID> restored = Arrays.asList(lion, grizzly, runeclaw);
            player.getLibrary().restoreOrderForGameLoad(restored, game);

            player.shuffleLibrary(game);

            List<UUID> after = player.getLibrary().getCardList();
            Assert.assertEquals(3, after.size());
            Assert.assertTrue(after.containsAll(restored));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void invalidLibraryRestorePayloadsFailClosedWithoutPartialMutation() {
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears", 1);
        addCard(Zone.LIBRARY, playerA, "Silvercoat Lion", 1);
        addCard(Zone.LIBRARY, playerA, "Runeclaw Bear", 1);
        addCard(Zone.HAND, playerA, "Walking Corpse", 1);
        addCard(Zone.LIBRARY, playerB, "Centaur Courser", 1);
        skipInitShuffling();

        runCode("reject invalid library payloads", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            List<UUID> baseline = new ArrayList<>(player.getLibrary().getCardList());
            UUID first = baseline.get(0);
            UUID second = baseline.get(1);
            UUID handCard = player.getHand().getCards(game).iterator().next().getId();
            Player other = game.getPlayer(playerB.getId());
            UUID foreignCard = other.getLibrary().getCardList().get(0);

            expectIllegalArgument("duplicate id must fail", () ->
                    player.getLibrary().restoreOrderForGameLoad(Arrays.asList(first, first, second), game));
            Assert.assertEquals(baseline, player.getLibrary().getCardList());

            List<UUID> unknown = new ArrayList<>(baseline);
            unknown.set(0, UUID.randomUUID());
            expectIllegalArgument("unknown id must fail", () ->
                    player.getLibrary().restoreOrderForGameLoad(unknown, game));
            Assert.assertEquals(baseline, player.getLibrary().getCardList());

            List<UUID> wrongZone = new ArrayList<>(baseline);
            wrongZone.set(0, handCard);
            expectIllegalArgument("wrong-zone id must fail", () ->
                    player.getLibrary().restoreOrderForGameLoad(wrongZone, game));
            Assert.assertEquals(baseline, player.getLibrary().getCardList());

            List<UUID> foreign = new ArrayList<>(baseline);
            foreign.set(0, foreignCard);
            expectIllegalArgument("foreign-owned id must fail", () ->
                    player.getLibrary().restoreOrderForGameLoad(foreign, game));
            Assert.assertEquals(baseline, player.getLibrary().getCardList());

            expectIllegalArgument("null payload must fail", () ->
                    player.getLibrary().restoreOrderForGameLoad(null, game));
            expectIllegalArgument("null game must fail", () ->
                    player.getLibrary().restoreOrderForGameLoad(baseline, null));
            Assert.assertEquals(baseline, player.getLibrary().getCardList());
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void restoredMorphHasNativeCharacteristicsAndTurnsFaceUpNormally() {
        addCard(Zone.BATTLEFIELD, playerA, "Sagu Mauler", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);

        runCode("restore morph", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent p = permanent(game, "Sagu Mauler");
            ForbiddenRestoreEventWatcher watcher = new ForbiddenRestoreEventWatcher();
            game.getState().addWatcher(watcher);

            BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(p.getId(), FaceDownType.MORPHED, game);

            Assert.assertTrue(p.isFaceDown(game));
            Assert.assertTrue(p.isMorphed());
            Assert.assertEquals(EmptyNames.FACE_DOWN_CREATURE.getObjectName(), p.getName());
            Assert.assertEquals(2, p.getPower().getValue());
            Assert.assertEquals(2, p.getToughness().getValue());
            Assert.assertEquals(0, watcher.getCount());
        });

        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                "{3}{G}{U}: Turn this face-down permanent face up.");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Sagu Mauler", 1);
        assertPowerToughness(playerA, "Sagu Mauler", 6, 6);
    }

    @Test
    public void restoredManifestAndCloakRemainDistinctNativeStates() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears@manifest", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Runeclaw Bear@cloak", 1);

        runCode("restore manifest and cloak", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent manifest = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(p -> "Grizzly Bears".equals(p.getName())).findFirst().orElseThrow();
            Permanent cloak = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(p -> "Runeclaw Bear".equals(p.getName())).findFirst().orElseThrow();

            BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                    manifest.getId(), FaceDownType.MANIFESTED, game);
            BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                    cloak.getId(), FaceDownType.CLOAKED, game);

            Assert.assertTrue(manifest.isManifested());
            Assert.assertFalse(manifest.isCloaked());
            Assert.assertTrue(cloak.isCloaked());
            Assert.assertFalse(cloak.isManifested());
            Assert.assertFalse(manifest.getAbilities(game).stream().anyMatch(WardAbility.class::isInstance));
            Assert.assertTrue(cloak.getAbilities(game).stream().anyMatch(WardAbility.class::isInstance));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void restoredDisguiseReusesNativeWardTurnUpAndTriggerBehavior() {
        addCard(Zone.BATTLEFIELD, playerA, "Dog Walker", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);

        runCode("restore disguise", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent p = permanent(game, "Dog Walker");
            BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                    p.getId(), FaceDownType.DISGUISED, game);

            Assert.assertTrue(p.isFaceDown(game));
            Assert.assertTrue(p.isDisguised());
            Assert.assertTrue(p.getAbilities(game).stream().anyMatch(WardAbility.class::isInstance));
        });

        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "{R/W}{R/W}: Turn");
        waitStackResolved(1, PhaseStep.POSTCOMBAT_MAIN, playerA);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Dog Walker", 1);
        assertPermanentCount(playerA, "Dog Token", 2);
    }

    @Test
    public void faceDownZoneChangeUsesNormalNewObjectSemantics() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears@bear", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 1);
        addCard(Zone.HAND, playerA, "Cloudshift", 1);

        runCode("restore manifest before blink", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent p = permanent(game, "Grizzly Bears");
            BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                    p.getId(), FaceDownType.MANIFESTED, game);
            Assert.assertTrue(p.isManifested());
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Cloudshift", "@bear", true);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Grizzly Bears", 1);
        runCode("verify returned permanent is face up", 1, PhaseStep.BEGIN_COMBAT, playerA, (info, player, game) -> {
            Permanent p = permanent(game, "Grizzly Bears");
            Assert.assertFalse(p.isFaceDown(game));
            Assert.assertFalse(p.isManifested());
            Assert.assertFalse(p.isCloaked());
            Assert.assertFalse(p.isMorphed());
            Assert.assertFalse(p.isDisguised());
        });
    }

    @Test
    public void invalidFaceDownRestoreFailsBeforeMutation() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", 1);
        addCard(Zone.HAND, playerA, "Sagu Mauler", 1);

        runCode("reject invalid face-down payloads", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent bears = permanent(game, "Grizzly Bears");
            Card handMorph = player.getHand().getCards(game).stream()
                    .filter(card -> "Sagu Mauler".equals(card.getName())).findFirst().orElseThrow();

            expectIllegalArgument("non-disguise card must reject disguise state", () ->
                    BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                            bears.getId(), FaceDownType.DISGUISED, game));
            Assert.assertFalse(bears.isFaceDown(game));
            Assert.assertEquals("Grizzly Bears", bears.getName());

            expectIllegalArgument("non-battlefield card must fail", () ->
                    BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                            handMorph.getId(), FaceDownType.MORPHED, game));
            expectIllegalArgument("unknown permanent must fail", () ->
                    BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                            UUID.randomUUID(), FaceDownType.MANIFESTED, game));
            expectIllegalArgument("manual type must fail closed", () ->
                    BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                            bears.getId(), FaceDownType.MANUAL, game));

            BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                    bears.getId(), FaceDownType.MANIFESTED, game);
            expectIllegalArgument("duplicate restore must fail", () ->
                    BecomesFaceDownCreatureEffect.restoreFaceDownStateForGameLoad(
                            bears.getId(), FaceDownType.MANIFESTED, game));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
