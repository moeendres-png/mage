package mage.cards;

import mage.MageObjectReference;
import mage.abilities.SpellAbility;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.constants.CardType;
import mage.constants.SpellAbilityType;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;

import java.util.UUID;

/**
 * @author TheElk801
 * TODO: Implement properly
 */
public class PrepareSpellCard extends CardImpl {

    private PrepareCard prepareCardParent;

    public PrepareSpellCard(
            UUID ownerId,
            CardSetInfo setInfo,
            String preparationName,
            CardType[] cardTypes,
            String costs,
            PrepareCard prepareCardParent
    ) {
        super(
                ownerId,
                setInfo,
                cardTypes,
                costs,
                SpellAbilityType.BASE_ALTERNATE
        );

        SpellAbility newSpellAbility =
                new SpellAbility(new ManaCostsImpl<>(costs), preparationName);
        this.replaceSpellAbility(newSpellAbility);
        spellAbility = newSpellAbility;

        this.setName(preparationName);
        this.prepareCardParent = prepareCardParent;
    }

    protected PrepareSpellCard(final PrepareSpellCard card) {
        super(card);
        this.prepareCardParent = card.prepareCardParent;
    }

    @Override
    public PrepareSpellCard copy() {
        return new PrepareSpellCard(this);
    }

    @Override
    public boolean cast(
            Game game,
            Zone fromZone,
            SpellAbility ability,
            UUID controllerId
    ) {
        if (!super.cast(game, fromZone, ability, controllerId)) {
            return false;
        }

        Object prepareRef = game.getState().getValue(
                PrepareCard.getPrepareCopyKey(getId())
        );

        if (prepareRef instanceof MageObjectReference) {
            Permanent preparedPermanent =
                    ((MageObjectReference) prepareRef).getPermanent(game);

            if (preparedPermanent != null && preparedPermanent.isPrepared()) {
                preparedPermanent.setPrepared(false, game);
            }
        }

        return true;
    }
}
