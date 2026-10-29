package mage.cards.t;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DealsDamageSourceTriggeredAbility;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.combat.CantBeBlockedByMoreThanOneSourceEffect;
import mage.abilities.effects.common.combat.MustBeBlockedByAtLeastOneSourceEffect;
import mage.abilities.keyword.ForetellAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.game.Game;
import mage.game.permanent.Permanent;

import java.util.UUID;

/**
 * The Foretold Soldier {2}{G}{G}
 * Creature -- Alien Zombie Soldier 6/6
 * This creature must be blocked if able.
 * This creature can't be blocked by more than one creature.
 * Whenever this creature deals damage, exile it face down. It becomes foretold.
 * Foretell {1}{G}
 */
public final class TheForetoldSoldier extends CardImpl {

    public TheForetoldSoldier(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{G}{G}");

        this.subtype.add(SubType.ALIEN);
        this.subtype.add(SubType.ZOMBIE);
        this.subtype.add(SubType.SOLDIER);
        this.power = new MageInt(6);
        this.toughness = new MageInt(6);

        // This creature must be blocked if able.
        this.addAbility(new SimpleStaticAbility(new MustBeBlockedByAtLeastOneSourceEffect(Duration.WhileOnBattlefield)));

        // This creature can't be blocked by more than one creature.
        this.addAbility(new SimpleStaticAbility(new CantBeBlockedByMoreThanOneSourceEffect()));

        // Whenever this creature deals damage, exile it face down. It becomes foretold.
        this.addAbility(new DealsDamageSourceTriggeredAbility(new TheForetoldSoldierEffect()));

        // Foretell {1}{G}
        this.addAbility(new ForetellAbility(this, "{1}{G}"));
    }

    private TheForetoldSoldier(final TheForetoldSoldier card) {
        super(card);
    }

    @Override
    public TheForetoldSoldier copy() {
        return new TheForetoldSoldier(this);
    }
}

class TheForetoldSoldierEffect extends OneShotEffect {

    TheForetoldSoldierEffect() {
        super(Outcome.Benefit);
        staticText = "exile it face down. It becomes foretold";
    }

    private TheForetoldSoldierEffect(final TheForetoldSoldierEffect effect) {
        super(effect);
    }

    @Override
    public TheForetoldSoldierEffect copy() {
        return new TheForetoldSoldierEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        // only while it is still the same object on the battlefield
        Permanent permanent = source.getSourcePermanentIfItStillExists(game);
        if (permanent == null) {
            return false;
        }
                // the foretell cost is the printed {1}{G}, not a reduction of the mana cost
        Card card = permanent.getMainCard();
        return ForetellAbility.doExileBecomesForetold(card, game, source, 0, "{1}{G}");
    }
}
