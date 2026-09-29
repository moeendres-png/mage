package org.mage.test.commander.multiplayer;

/**
 * F-20 at 5 players. See {@link InitiativeLeavesGameTestBase}.
 */
public class InitiativeLeavesGame5PTest extends InitiativeLeavesGameTestBase {

    @Override
    protected int playerCount() {
        return 5;
    }

    @Override
    protected int holderPosition() {
        return 2;
    }
}
