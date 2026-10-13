package mage.cards.t;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.CreateTokenEffect;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.abilities.effects.common.GainLifeEffect;
import mage.abilities.effects.common.LoseLifeOpponentsEffect;
import mage.abilities.hint.common.ControllerDiscardedHint;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.choices.Choice;
import mage.choices.ChoiceImpl;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.game.Game;
import mage.game.permanent.token.TreasureToken;
import mage.players.Player;
import mage.util.RandomUtil;
import mage.watchers.common.DiscardedCardWatcher;

import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class TyphoidMaryFractured extends CardImpl {

    public TyphoidMaryFractured(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{1}{B}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.MUTANT);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(3);
        this.toughness = new MageInt(3);

        // Whenever Typhoid Mary attacks, choose one at random. If you discarded a card this turn, you choose one instead.
        // * Mary -- Create a Treasure token.
        // * Typhoid Mary -- Draw a card.
        // * Bloody Mary -- Each opponent loses 2 life and you gain 2 life.
        this.addAbility(new AttacksTriggeredAbility(new TyphoidMaryFracturedEffect())
                .addHint(ControllerDiscardedHint.instance), new DiscardedCardWatcher());
    }

    private TyphoidMaryFractured(final TyphoidMaryFractured card) {
        super(card);
    }

    @Override
    public TyphoidMaryFractured copy() {
        return new TyphoidMaryFractured(this);
    }
}

class TyphoidMaryFracturedEffect extends OneShotEffect {

    private static final String MARY = "Mary — Create a Treasure token.";
    private static final String TYPHOID = "Typhoid Mary — Draw a card.";
    private static final String BLOODY = "Bloody Mary — Each opponent loses 2 life and you gain 2 life.";
    private static final List<String> MODES = Arrays.asList(MARY, TYPHOID, BLOODY);

    TyphoidMaryFracturedEffect() {
        super(Outcome.Benefit);
        staticText = "choose one at random. If you discarded a card this turn, you choose one instead."
                + "<br>&bull; " + MARY + "<br>&bull; " + TYPHOID + "<br>&bull; " + BLOODY;
    }

    private TyphoidMaryFracturedEffect(final TyphoidMaryFracturedEffect effect) {
        super(effect);
    }

    @Override
    public TyphoidMaryFracturedEffect copy() {
        return new TyphoidMaryFracturedEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        String mode;
        if (DiscardedCardWatcher.checkPlayerDiscarded(controller.getId(), game)) {
            Choice choice = new ChoiceImpl(true);
            choice.setMessage("Choose one");
            choice.setChoices(new LinkedHashSet<>(MODES));
            if (!controller.choose(Outcome.Benefit, choice, game) || choice.getChoice() == null) {
                return false;
            }
            mode = choice.getChoice();
        } else {
            mode = RandomUtil.randomFromCollection(MODES, game.getRulesRandom());
        }
        game.informPlayers(controller.getLogName() + " chose: " + mode);
        if (MARY.equals(mode)) {
            return new CreateTokenEffect(new TreasureToken()).apply(game, source);
        }
        if (TYPHOID.equals(mode)) {
            return new DrawCardSourceControllerEffect(1).apply(game, source);
        }
        new LoseLifeOpponentsEffect(2).apply(game, source);
        return new GainLifeEffect(2).apply(game, source);
    }
}
