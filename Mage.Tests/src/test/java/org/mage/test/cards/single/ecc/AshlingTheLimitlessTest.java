package org.mage.test.cards.single.ecc;

import mage.abilities.keyword.EvokeAbility;
import mage.abilities.keyword.HasteAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

public class AshlingTheLimitlessTest extends CardTestPlayerBase {

    private static final String ASHLING = "Ashling, the Limitless";
    private static final String CLOUDKIN = "Cloudkin Seer";

    private void setupEvokedCloudkin(boolean addWubrgPaymentMana) {
        addCard(Zone.BATTLEFIELD, playerA, ASHLING);
        addCard(Zone.HAND, playerA, CLOUDKIN);

        // Cloudkin Seer and its token copy each draw a card.
        addCard(Zone.LIBRARY, playerA, "Island", 4);

        // Four colorless sources pay only the Evoke {4}.
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 4);

        if (addWubrgPaymentMana) {
            addCard(Zone.BATTLEFIELD, playerA, "Plains", 5);
            addCard(Zone.BATTLEFIELD, playerA, "Island", 5);
            addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
            addCard(Zone.BATTLEFIELD, playerA, "Mountain", 5);
            addCard(Zone.BATTLEFIELD, playerA, "Forest", 5);
        }

        castSpell(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                CLOUDKIN
        );

        setChoice(
                playerA,
                "Cast with Evoke alternative cost: {4} (source: Cloudkin Seer"
        );
    }

    @Test
    public void evokedElementalCreatesHastyCopyThenCopyIsSacrificed() {
        setupEvokedCloudkin(false);

        // The original Cloudkin Seer is sacrificed by Evoke.
        // Ashling must create exactly one token copy from that sacrifice.
        checkPermanentCount(
                "Ashling created token copy",
                1,
                PhaseStep.BEGIN_COMBAT,
                playerA,
                CLOUDKIN,
                1
        );

        runCode(
                "Ashling token has haste until end of turn",
                1,
                PhaseStep.BEGIN_COMBAT,
                playerA,
                (info, player, game) -> {
                    Permanent token = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent ->
                                    permanent.isControlledBy(player.getId()))
                            .filter(permanent ->
                                    permanent.getName().equals(CLOUDKIN))
                            .findFirst()
                            .orElseThrow(() ->
                                    new AssertionError(
                                            "Ashling token copy not found"
                                    )
                            );

                    boolean hasHaste = token
                            .getAbilities()
                            .stream()
                            .anyMatch(ability ->
                                    ability instanceof HasteAbility);

                    Assert.assertTrue(
                            "Ashling token must gain haste until end of turn",
                            hasHaste
                    );
                }
        );

        // No WUBRG exists, so the delayed trigger must sacrifice the token.
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        // The original nontoken Cloudkin remains in the graveyard.
        assertGraveyardCount(playerA, CLOUDKIN, 1);

        // The token was sacrificed and ceased to exist.
        // Its sacrifice must NOT recursively trigger Ashling because it is a token.
        assertPermanentCount(playerA, CLOUDKIN, 0);
    }

    @Test
    public void payingWubrgKeepsCopyAndHasteExpires() {
        setupEvokedCloudkin(true);

        // Pay the delayed "unless" cost at player A's first end step.
        setChoice(playerA, true);

        runCode(
                "Ashling token initially has haste",
                1,
                PhaseStep.BEGIN_COMBAT,
                playerA,
                (info, player, game) -> {
                    Permanent token = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent ->
                                    permanent.isControlledBy(player.getId()))
                            .filter(permanent ->
                                    permanent.getName().equals(CLOUDKIN))
                            .findFirst()
                            .orElseThrow(() ->
                                    new AssertionError(
                                            "Ashling token copy not found"
                                    )
                            );

                    Assert.assertTrue(
                            "Ashling token must initially have haste",
                            token.getAbilities()
                                    .stream()
                                    .anyMatch(ability ->
                                            ability instanceof HasteAbility)
                    );
                }
        );

        runCode(
                "Ashling token remains but haste has expired",
                2,
                PhaseStep.UPKEEP,
                playerA,
                (info, player, game) -> {
                    Permanent token = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent ->
                                    permanent.isControlledBy(player.getId()))
                            .filter(permanent ->
                                    permanent.getName().equals(CLOUDKIN))
                            .findFirst()
                            .orElseThrow(() ->
                                    new AssertionError(
                                            "Paid-for Ashling token not found"
                                    )
                            );

                    Assert.assertFalse(
                            "Ashling-granted haste must expire at end of turn",
                            token.getAbilities()
                                    .stream()
                                    .anyMatch(ability ->
                                            ability instanceof HasteAbility)
                    );
                }
        );

        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertGraveyardCount(playerA, CLOUDKIN, 1);
        assertPermanentCount(playerA, CLOUDKIN, 1);
    }

    @Test
    public void nonElementalInHandDoesNotGainEvoke() {
        addCard(Zone.BATTLEFIELD, playerA, ASHLING);
        addCard(Zone.HAND, playerA, "Silvercoat Lion");

        runCode(
                "non-Elemental in hand must not gain Ashling Evoke",
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    mage.cards.Card lion = player
                            .getHand()
                            .getCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Silvercoat Lion"))
                            .findFirst()
                            .orElseThrow(() ->
                                    new AssertionError(
                                            "Silvercoat Lion not found in hand"
                                    )
                            );

                    long evokeCount = lion
                            .getAbilities(game)
                            .stream()
                            .filter(ability ->
                                    ability instanceof EvokeAbility)
                            .count();

                    Assert.assertEquals(
                            "Ashling must not grant Evoke to a non-Elemental",
                            0L,
                            evokeCount
                    );
                }
        );

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void elementalOutsideHandDoesNotGainEvoke() {
        addCard(Zone.BATTLEFIELD, playerA, ASHLING);
        addCard(Zone.GRAVEYARD, playerA, CLOUDKIN);

        runCode(
                "Elemental outside hand must not gain Ashling Evoke",
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    mage.cards.Card cloudkin = player
                            .getGraveyard()
                            .getCards(game)
                            .stream()
                            .filter(card -> card.getName().equals(CLOUDKIN))
                            .findFirst()
                            .orElseThrow(() ->
                                    new AssertionError(
                                            "Cloudkin Seer not found in graveyard"
                                    )
                            );

                    long evokeCount = cloudkin
                            .getAbilities(game)
                            .stream()
                            .filter(ability ->
                                    ability instanceof EvokeAbility)
                            .count();

                    Assert.assertEquals(
                            "Ashling must not grant Evoke outside the hand",
                            0L,
                            evokeCount
                    );
                }
        );

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
