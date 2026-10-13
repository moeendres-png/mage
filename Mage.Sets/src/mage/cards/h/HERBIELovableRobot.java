package mage.cards.h;

import mage.MageInt;
import mage.abilities.condition.common.CastNoncreatureSpellThisTurnCondition;
import mage.abilities.costs.common.TapSourceCost;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.keyword.SurveilEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.abilities.mana.ActivatedManaAbilityImpl;
import mage.abilities.mana.AnyColorManaAbility;
import mage.abilities.mana.ColorlessManaAbility;
import mage.abilities.triggers.BeginningOfCombatTriggeredAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SubType;
import mage.constants.SuperType;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class HERBIELovableRobot extends CardImpl {

    public HERBIELovableRobot(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT, CardType.CREATURE}, "{2}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.ROBOT);
        this.subtype.add(SubType.SCOUT);
        this.power = new MageInt(1);
        this.toughness = new MageInt(1);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // At the beginning of combat on your turn, if you've cast a noncreature spell this turn, surveil 1.
        this.addAbility(new BeginningOfCombatTriggeredAbility(new SurveilEffect(1))
                .withInterveningIf(CastNoncreatureSpellThisTurnCondition.instance)
                .addHint(CastNoncreatureSpellThisTurnCondition.getHint()));

        // {T}: Add {C}.
        this.addAbility(new ColorlessManaAbility());

        // {1}, {T}: Add one mana of any color.
        ActivatedManaAbilityImpl ability = new AnyColorManaAbility(new GenericManaCost(1));
        ability.addCost(new TapSourceCost());
        this.addAbility(ability);
    }

    private HERBIELovableRobot(final HERBIELovableRobot card) {
        super(card);
    }

    @Override
    public HERBIELovableRobot copy() {
        return new HERBIELovableRobot(this);
    }
}
