package mage.cards.e;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.abilities.effects.OneShotEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.Outcome;
import mage.constants.SubLayer;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.target.common.TargetCreaturePermanent;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Exchange of Words {1}{U}{U}
 * Enchantment
 * When this enchantment enters, choose two target creatures. For as long as this enchantment remains on the
 * battlefield, exchange the text boxes of those creatures.
 */
public final class ExchangeOfWords extends CardImpl {

    public ExchangeOfWords(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{1}{U}{U}");

        // When this enchantment enters, choose two target creatures. For as long as this enchantment remains on the
        // battlefield, exchange the text boxes of those creatures.
        Ability ability = new EntersBattlefieldTriggeredAbility(new ExchangeOfWordsEffect());
        ability.addTarget(new TargetCreaturePermanent(2));
        this.addAbility(ability);
    }

    private ExchangeOfWords(final ExchangeOfWords card) {
        super(card);
    }

    @Override
    public ExchangeOfWords copy() {
        return new ExchangeOfWords(this);
    }
}

class ExchangeOfWordsEffect extends OneShotEffect {

    ExchangeOfWordsEffect() {
        super(Outcome.Detriment);
        staticText = "choose two target creatures. For as long as {this} remains on the battlefield, "
                + "exchange the text boxes of those creatures";
    }

    private ExchangeOfWordsEffect(final ExchangeOfWordsEffect effect) {
        super(effect);
    }

    @Override
    public ExchangeOfWordsEffect copy() {
        return new ExchangeOfWordsEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        List<UUID> targets = getTargetPointer().getTargets(game, source);
        if (targets.size() != 2) {
            return false;
        }
        Permanent first = game.getPermanent(targets.get(0));
        Permanent second = game.getPermanent(targets.get(1));
        if (first == null || second == null) {
            return false;
        }
        game.addEffect(new ExchangeOfWordsExchangeEffect(
                new MageObjectReference(first, game), new MageObjectReference(second, game)), source);
        return true;
    }
}

/**
 * The text boxes are exchanged in layer 3, before any ability-granting or -removing effect (layer 6) applies,
 * so only the abilities a creature has from its (possibly copied) rules text move; abilities other effects
 * grant or remove stay where they are. Characteristics-defining text such as power and toughness is not touched.
 */
class ExchangeOfWordsExchangeEffect extends ContinuousEffectImpl {

    private final MageObjectReference first;
    private final MageObjectReference second;

    ExchangeOfWordsExchangeEffect(MageObjectReference first, MageObjectReference second) {
        super(Duration.Custom, Layer.TextChangingEffects_3, SubLayer.NA, Outcome.Detriment);
        this.first = first;
        this.second = second;
        staticText = "exchange the text boxes of those creatures";
    }

    private ExchangeOfWordsExchangeEffect(final ExchangeOfWordsExchangeEffect effect) {
        super(effect);
        this.first = effect.first;
        this.second = effect.second;
    }

    @Override
    public ExchangeOfWordsExchangeEffect copy() {
        return new ExchangeOfWordsExchangeEffect(this);
    }

    @Override
    public boolean isInactive(Ability source, Game game) {
        return source.getSourcePermanentIfItStillExists(game) == null
                || (first.getPermanent(game) == null && second.getPermanent(game) == null);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent permanentOne = first.getPermanent(game);
        Permanent permanentTwo = second.getPermanent(game);
        if (permanentOne == null || permanentTwo == null) {
            return false; // nothing to exchange with once one of them is gone
        }
        List<Ability> abilitiesOne = new ArrayList<>(permanentOne.getAbilities());
        List<Ability> abilitiesTwo = new ArrayList<>(permanentTwo.getAbilities());
        replaceAbilities(permanentOne, abilitiesOne, abilitiesTwo, source, game);
        replaceAbilities(permanentTwo, abilitiesTwo, abilitiesOne, source, game);
        return true;
    }

    private static void replaceAbilities(Permanent permanent, List<Ability> remove, List<Ability> add, Ability source, Game game) {
        for (Ability ability : remove) {
            permanent.removeAbility(ability, source.getSourceId(), game);
        }
        for (Ability ability : add) {
            permanent.addAbility(ability, source.getSourceId(), game, true);
        }
    }
}
