package mage.game.events;

import mage.game.permanent.token.ElfDruidToken;
import mage.game.permanent.token.ElfKnightToken;
import mage.game.permanent.token.GoblinRogueToken;
import mage.game.permanent.token.GoblinToken;
import mage.game.permanent.token.GoblinWizardToken;
import mage.game.permanent.token.Token;
import org.junit.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertSame;

/**
 * Tokens carry no hashCode, so a hash-ordered token map creates the tokens of one event (Wurmcoil
 * Engine's deathtouch and lifelink Wurms) in an order that changes from run to run, which makes a
 * game with the same seed diverge. The event keeps the order the tokens were given in.
 */
public class CreateTokenEventOrderTest {

    private static final int FRESH_EVENTS = 64;

    private static List<Token> freshTokens() {
        return Arrays.asList(
                new GoblinToken(),
                new ElfDruidToken(),
                new ElfKnightToken(),
                new GoblinRogueToken(),
                new GoblinWizardToken()
        );
    }

    @Test
    public void testTokensKeepTheOrderTheyWereGiven() {
        for (int run = 0; run < FRESH_EVENTS; run++) {
            List<Token> given = freshTokens();
            CreateTokenEvent event = new CreateTokenEvent(null, UUID.randomUUID(), 1, given);
            List<Token> created = new ArrayList<>(event.getTokens().keySet());
            assertEquals(given.size(), created.size());
            for (int index = 0; index < given.size(); index++) {
                assertSame("event " + run + ", token " + index, given.get(index), created.get(index));
            }
        }
    }

    @Test
    public void testMultiplyingTokensKeepsTheOrder() {
        for (int run = 0; run < FRESH_EVENTS; run++) {
            List<Token> given = freshTokens();
            CreateTokenEvent event = new CreateTokenEvent(null, UUID.randomUUID(), 2, given);
            event.multiplyTokens(2);
            List<Token> created = new ArrayList<>(event.getTokens().keySet());
            for (int index = 0; index < given.size(); index++) {
                assertSame("event " + run + ", token " + index, given.get(index), created.get(index));
                assertEquals(4, (int) event.getTokens().get(given.get(index)));
            }
        }
    }
}
