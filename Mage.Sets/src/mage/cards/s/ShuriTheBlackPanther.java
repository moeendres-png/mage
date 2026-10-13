package mage.cards.s;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.condition.Condition;
import mage.abilities.condition.common.PermanentsOnTheBattlefieldCondition;
import mage.abilities.decorator.ConditionalOneShotEffect;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.abilities.effects.common.continuous.BoostControlledEffect;
import mage.abilities.keyword.LifelinkAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.ComparisonType;
import mage.constants.Duration;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.filter.StaticFilters;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class ShuriTheBlackPanther extends CardImpl {

    private static final Condition threeArtifacts = new PermanentsOnTheBattlefieldCondition(
            StaticFilters.FILTER_CONTROLLED_PERMANENT_ARTIFACT, ComparisonType.MORE_THAN, 2
    );
    private static final Condition sixArtifacts = new PermanentsOnTheBattlefieldCondition(
            StaticFilters.FILTER_CONTROLLED_PERMANENT_ARTIFACT, ComparisonType.MORE_THAN, 5
    );

    public ShuriTheBlackPanther(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{G}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.NOBLE);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(2);
        this.toughness = new MageInt(3);

        // Lifelink
        this.addAbility(LifelinkAbility.getInstance());

        // Whenever Shuri attacks, draw a card if you control three or more artifacts. Then if you control six or more artifacts, creatures you control get +2/+2 until end of turn.
        Ability ability = new AttacksTriggeredAbility(new ConditionalOneShotEffect(
                new DrawCardSourceControllerEffect(1), threeArtifacts,
                "draw a card if you control three or more artifacts"
        ));
        ability.addEffect(new ConditionalOneShotEffect(
                new mage.abilities.effects.common.AddContinuousEffectToGame(
                        new BoostControlledEffect(2, 2, Duration.EndOfTurn)
                ), sixArtifacts,
                "Then if you control six or more artifacts, creatures you control get +2/+2 until end of turn"
        ));
        this.addAbility(ability);
    }

    private ShuriTheBlackPanther(final ShuriTheBlackPanther card) {
        super(card);
    }

    @Override
    public ShuriTheBlackPanther copy() {
        return new ShuriTheBlackPanther(this);
    }
}
