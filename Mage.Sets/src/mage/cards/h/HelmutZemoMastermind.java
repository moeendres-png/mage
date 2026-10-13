package mage.cards.h;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.effects.ContinuousEffect;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.replacement.ThatSpellGraveyardExileReplacementEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.counters.CounterType;
import mage.filter.FilterCard;
import mage.filter.common.FilterInstantOrSorceryCard;
import mage.filter.predicate.card.ManaValueLessThanOrEqualToSourcePowerPredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.common.TargetCardInYourGraveyard;
import mage.target.targetpointer.FixedTarget;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class HelmutZemoMastermind extends CardImpl {

    private static final FilterCard filter = new FilterInstantOrSorceryCard(
            "instant or sorcery card with mana value less than or equal to his power from your graveyard"
    );

    static {
        filter.add(ManaValueLessThanOrEqualToSourcePowerPredicate.instance);
    }

    public HelmutZemoMastermind(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{U}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.NOBLE);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(2);
        this.toughness = new MageInt(2);

        // Whenever Helmut Zemo attacks, you may cast target instant or sorcery card with mana value less than or equal to his power from your graveyard. If that spell would be put into your graveyard, exile it instead. If you cast a spell this way, put a +1/+1 counter on Helmut Zemo.
        Ability ability = new AttacksTriggeredAbility(new HelmutZemoMastermindEffect());
        ability.addTarget(new TargetCardInYourGraveyard(filter));
        this.addAbility(ability);
    }

    private HelmutZemoMastermind(final HelmutZemoMastermind card) {
        super(card);
    }

    @Override
    public HelmutZemoMastermind copy() {
        return new HelmutZemoMastermind(this);
    }
}

class HelmutZemoMastermindEffect extends OneShotEffect {

    HelmutZemoMastermindEffect() {
        super(Outcome.PlayForFree);
        staticText = "you may cast target instant or sorcery card with mana value less than or equal to his power "
                + "from your graveyard. If that spell would be put into your graveyard, exile it instead. "
                + "If you cast a spell this way, put a +1/+1 counter on {this}";
    }

    private HelmutZemoMastermindEffect(final HelmutZemoMastermindEffect effect) {
        super(effect);
    }

    @Override
    public HelmutZemoMastermindEffect copy() {
        return new HelmutZemoMastermindEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (controller == null || card == null
                || !controller.chooseUse(outcome, "Cast " + card.getLogName() + '?', source, game)) {
            return false;
        }
        FixedTarget fixedTarget = new FixedTarget(card, game);
        game.getState().setValue("PlayFromNotOwnHandZone" + card.getId(), Boolean.TRUE);
        boolean cast = CardUtil.castSingle(controller, source, game, card, false, null);
        game.getState().setValue("PlayFromNotOwnHandZone" + card.getId(), null);
        if (!cast) {
            return false;
        }
        ContinuousEffect effect = new ThatSpellGraveyardExileReplacementEffect(true);
        effect.setTargetPointer(fixedTarget);
        game.addEffect(effect, source);
        Permanent permanent = source.getSourcePermanentIfItStillExists(game);
        if (permanent != null) {
            permanent.addCounters(CounterType.P1P1.createInstance(), source, game);
        }
        return true;
    }
}
