package mage.cards.w;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DealsDamageToOpponentTriggeredAbility;
import mage.abilities.common.SimpleEvasionAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.RestrictionEffect;
import mage.abilities.effects.common.combat.CantBeBlockedSourceEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class WillieLumpkinPostman extends CardImpl {

    public WillieLumpkinPostman(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{W}{U}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.CITIZEN);
        this.power = new MageInt(1);
        this.toughness = new MageInt(3);

        // Willie Lumpkin can't be blocked.
        this.addAbility(new SimpleEvasionAbility(new CantBeBlockedSourceEffect()));

        // Whenever Willie Lumpkin deals combat damage to an opponent, you draw a card and that player may draw a card. If they do, that player can't attack you or permanents you control during their next turn.
        this.addAbility(new DealsDamageToOpponentTriggeredAbility(
                new WillieLumpkinPostmanEffect(), false, true, true
        ));
    }

    private WillieLumpkinPostman(final WillieLumpkinPostman card) {
        super(card);
    }

    @Override
    public WillieLumpkinPostman copy() {
        return new WillieLumpkinPostman(this);
    }
}

class WillieLumpkinPostmanEffect extends OneShotEffect {

    WillieLumpkinPostmanEffect() {
        super(Outcome.DrawCard);
        staticText = "you draw a card and that player may draw a card. If they do, that player "
                + "can't attack you or permanents you control during their next turn";
    }

    private WillieLumpkinPostmanEffect(final WillieLumpkinPostmanEffect effect) {
        super(effect);
    }

    @Override
    public WillieLumpkinPostmanEffect copy() {
        return new WillieLumpkinPostmanEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        controller.drawCards(1, source, game);
        Player opponent = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (opponent != null
                && opponent.chooseUse(Outcome.DrawCard, "Draw a card? If you do, you can't attack "
                + controller.getName() + " or permanents they control during your next turn.", source, game)
                && opponent.drawCards(1, source, game) > 0) {
            game.addEffect(new WillieLumpkinPostmanCantAttackEffect(opponent.getId()), source);
        }
        return true;
    }
}

class WillieLumpkinPostmanCantAttackEffect extends RestrictionEffect {

    private final UUID opponentId;

    WillieLumpkinPostmanCantAttackEffect(UUID opponentId) {
        super(Duration.UntilEndOfYourNextTurn);
        this.opponentId = opponentId;
    }

    private WillieLumpkinPostmanCantAttackEffect(final WillieLumpkinPostmanCantAttackEffect effect) {
        super(effect);
        this.opponentId = effect.opponentId;
    }

    @Override
    public WillieLumpkinPostmanCantAttackEffect copy() {
        return new WillieLumpkinPostmanCantAttackEffect(this);
    }

    @Override
    public void init(Ability source, Game game) {
        super.init(source, game);
        // "during their next turn": the duration counts the opponent's turns
        setStartingControllerAndTurnNum(game, opponentId, game.getActivePlayerId());
    }

    @Override
    public boolean applies(Permanent permanent, Ability source, Game game) {
        return game.isActivePlayer(opponentId) && permanent.isControlledBy(opponentId);
    }

    @Override
    public boolean canAttack(Permanent attacker, UUID defenderId, Ability source, Game game, boolean canUseChooseDialogs) {
        if (defenderId == null) {
            return true;
        }
        UUID controllerId = source.getControllerId();
        Permanent defender = game.getPermanent(defenderId);
        if (defender != null) {
            return !defender.isControlledBy(controllerId);
        }
        return !defenderId.equals(controllerId);
    }
}
