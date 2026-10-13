package mage.cards.w;

import mage.MageInt;
import mage.abilities.common.AttacksWithCreaturesTriggeredAbility;
import mage.abilities.condition.Condition;
import mage.abilities.condition.common.PermanentsOnTheBattlefieldCondition;
import mage.abilities.effects.common.CreateTokenEffect;
import mage.abilities.keyword.VigilanceAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.ComparisonType;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.TargetController;
import mage.filter.FilterPermanent;
import mage.filter.common.FilterControlledArtifactPermanent;
import mage.filter.predicate.mageobject.CommanderPredicate;
import mage.filter.predicate.mageobject.ManaValuePredicate;
import mage.game.permanent.token.RhinoToken;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class WKabiShieldOfTheNation extends CardImpl {

    private static final FilterPermanent commanderFilter = new FilterPermanent("your commander");
    private static final FilterControlledArtifactPermanent artifactFilter
            = new FilterControlledArtifactPermanent("an artifact with mana value 4 or greater");

    static {
        commanderFilter.add(CommanderPredicate.instance);
        commanderFilter.add(TargetController.YOU.getOwnerPredicate());
        artifactFilter.add(new ManaValuePredicate(ComparisonType.MORE_THAN, 3));
    }

    private static final Condition condition = new PermanentsOnTheBattlefieldCondition(artifactFilter);

    public WKabiShieldOfTheNation(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{1}{G}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.WARRIOR);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(2);
        this.toughness = new MageInt(3);

        // Vigilance
        this.addAbility(VigilanceAbility.getInstance());

        // Whenever you attack with your commander, if you control an artifact with mana value 4 or greater, create a 4/4 green Rhino creature token with trample.
        this.addAbility(new AttacksWithCreaturesTriggeredAbility(
                new CreateTokenEffect(new RhinoToken()), 1, commanderFilter
        ).withInterveningIf(condition));
    }

    private WKabiShieldOfTheNation(final WKabiShieldOfTheNation card) {
        super(card);
    }

    @Override
    public WKabiShieldOfTheNation copy() {
        return new WKabiShieldOfTheNation(this);
    }
}
