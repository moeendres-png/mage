package org.mage.test.commander.multiplayer;

/**
 * F-23 at 5 players. See {@link OpponentsCountAfterLeaveTestBase}.
 */
public class OpponentsCountAfterLeave5PTest extends OpponentsCountAfterLeaveTestBase {

    @Override
    protected int playerCount() {
        return 5;
    }
}
