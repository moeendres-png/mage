package org.mage.test.ws09;

import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommander3PlayersFFA;

/**
 * WS09 common-state witness against the exact pinned XMage engine.
 *
 * The assertions are deliberately made on the constructed engine fixture before execute(),
 * so the differential boundary contains no discretionary decisions, no shuffles, and no RNG.
 */
public class WS09XMageSharedScenarioTest extends CardTestCommander3PlayersFFA {

    @Test
    public void constructedThreePlayerCommanderState() {
        Assert.assertEquals("three Commander players must be constructed", 3, currentGame.getPlayers().size());
        Assert.assertEquals("P1 starting life", 40, playerA.getLife());
        Assert.assertEquals("P2 starting life", 40, playerB.getLife());
        Assert.assertEquals("P3 starting life", 40, playerC.getLife());
    }
}
