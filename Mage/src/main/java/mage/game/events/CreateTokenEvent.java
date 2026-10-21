package mage.game.events;

import mage.abilities.Ability;
import mage.game.permanent.token.Token;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class CreateTokenEvent extends GameEvent {

    // insertion order: tokens carry no hashCode, so a HashMap would create them in an order that
    // changes from run to run (Wurmcoil Engine's two Wurms)
    private final Map<Token, Integer> tokens = new LinkedHashMap<>();

    /**
     * Multiple tokens per event (Double Season and other effects can change amount and tokens list with it)
     *
     * @param source
     * @param controllerId
     * @param amount
     * @param tokensList
     */
    public CreateTokenEvent(Ability source, UUID controllerId, int amount, List<Token> tokensList) {
        super(GameEvent.EventType.CREATE_TOKEN, null, source, controllerId, amount, false);
        if (tokensList != null) {
            for (Token token : tokensList) {
                tokens.put(token, amount);
            }
        }
    }

    public Map<Token, Integer> getTokens() {
        return tokens;
    }

    public void multiplyTokens(int factor) {
        multiplyTokens(factor, null);
    }

    public interface ConditionOnToken {
        boolean apply(Token token);
    }

    public void multiplyTokens(int factor, ConditionOnToken condition) {
        for (Map.Entry<Token, Integer> entry : tokens.entrySet()) {
            if (condition == null || condition.apply(entry.getKey())) {
                entry.setValue(entry.getValue() * factor);
            }
        }
    }

    @Override
    public int getAmount() {
        int amount = 0;
        for (Integer num : tokens.values()) {
            amount += num;
        }
        return amount;
    }

    @Override
    public void setAmount(int amount) {
        throw new UnsupportedOperationException("Do not use event.setAmount for tokens. Amount must be set individually in event.getTokens");
    }
}
