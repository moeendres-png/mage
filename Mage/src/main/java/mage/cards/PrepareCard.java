package mage.cards;

import mage.constants.CardType;

import java.util.UUID;

/**
 * @author TheElk801
 * TODO: Implement properly
 */
public abstract class PrepareCard extends CardImpl {

    public static final String PREPARE_COPY_KEY = "PrepareSpellCopy:";

    public static String getPrepareCopyKey(UUID copyId) {
        return PREPARE_COPY_KEY + copyId;
    }

    protected Card spellCard;

    protected PrepareCard(UUID ownerId, CardSetInfo setInfo, CardType[] types, String costs, String preparationName, CardType typeSpell, String costsSpell) {
        this(ownerId, setInfo, types, costs, preparationName, new CardType[]{typeSpell}, costsSpell);
    }

    protected PrepareCard(UUID ownerId, CardSetInfo setInfo, CardType[] types, String costs, String preparationName, CardType[] typesSpell, String costsSpell) {
        super(ownerId, setInfo, types, costs);
        this.spellCard = new PrepareSpellCard(ownerId, setInfo, preparationName, typesSpell, costsSpell, this);
    }

    protected PrepareCard(final PrepareCard card) {
        super(card);
        this.spellCard = card.getSpellCard().copy();
    }

    public Card getSpellCard() {
        return spellCard;
    }
}
