package org.mage.test.commander.multiplayer;

/**
 * F-20 at 6 players. See {@link InitiativeLeavesGameTestBase}.
 */
public class InitiativeLeavesGame6PTest extends InitiativeLeavesGameTestBase {

    @Override
    protected int playerCount() {
        return 6;
    }

    @Override
    protected int holderPosition() {
        return 2;
    }
}
