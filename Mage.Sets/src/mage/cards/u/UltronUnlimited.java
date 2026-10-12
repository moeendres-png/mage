package mage.cards.u;

import mage.MageInt;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.common.ConnivesCreatureYouControlTriggeredAbility;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.common.CreateTokenEffect;
import mage.abilities.effects.common.DoIfCostPaid;
import mage.abilities.effects.keyword.ConniveSourceEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.game.permanent.token.RobotVillainToken;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class UltronUnlimited extends CardImpl {

    public UltronUnlimited(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT, CardType.CREATURE}, "{1}{U}{B}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.ROBOT);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(2);
        this.toughness = new MageInt(2);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Whenever Ultron attacks, he connives.
        this.addAbility(new AttacksTriggeredAbility(new ConniveSourceEffect("{this}")));

        // Whenever a creature you control connives, you may pay {1}. If you do, create a 2/2 colorless Robot Villain artifact creature token.
        this.addAbility(new ConnivesCreatureYouControlTriggeredAbility(
                new DoIfCostPaid(new CreateTokenEffect(new RobotVillainToken()), new GenericManaCost(1)), false, false
        ));
    }

    private UltronUnlimited(final UltronUnlimited card) {
        super(card);
    }

    @Override
    public UltronUnlimited copy() {
        return new UltronUnlimited(this);
    }
}
