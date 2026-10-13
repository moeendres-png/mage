package mage.cards.c;

import mage.abilities.common.SpellCastControllerTriggeredAbility;
import mage.abilities.effects.common.CopyTargetStackObjectEffect;
import mage.abilities.effects.mana.AddManaInAnyCombinationEffect;
import mage.abilities.triggers.BeginningOfFirstMainTriggeredAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SetTargetPointer;
import mage.filter.StaticFilters;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class CosmicCrucible extends CardImpl {

    public CosmicCrucible(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{4}{G}{U}");

        // At the beginning of your first main phase, add four mana in any combination of colors.
        this.addAbility(new BeginningOfFirstMainTriggeredAbility(new AddManaInAnyCombinationEffect(4)));

        // Whenever you cast a noncreature spell, you may copy it. You may choose new targets for the copy. Do this only once each turn.
        SpellCastControllerTriggeredAbility ability = new SpellCastControllerTriggeredAbility(
                new CopyTargetStackObjectEffect(true).setText("copy it. You may choose new targets for the copy"),
                StaticFilters.FILTER_SPELL_A_NON_CREATURE, true, SetTargetPointer.SPELL
        );
        ability.setDoOnlyOnceEachTurn(true);
        this.addAbility(ability);
    }

    private CosmicCrucible(final CosmicCrucible card) {
        super(card);
    }

    @Override
    public CosmicCrucible copy() {
        return new CosmicCrucible(this);
    }
}
