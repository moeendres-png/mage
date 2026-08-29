package org.mage.test.ws09;

import mage.game.GameImpl;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommander3PlayersFFA;

/** RNG- and decision-free WS09 witness on the exact pinned XMage fixture. */
public class WS09XMageSharedScenarioTest extends CardTestCommander3PlayersFFA {

    @Test
    public void constructedThreePlayerCommanderState() {
        Assert.assertEquals("three Commander players must be constructed", 3, currentGame.getPlayers().size());
        Assert.assertTrue("XMage Commander fixture must expose GameImpl rules configuration", currentGame instanceof GameImpl);
        Assert.assertEquals("Commander configured starting life", 40, ((GameImpl) currentGame).getStartingLife());
    }
}
