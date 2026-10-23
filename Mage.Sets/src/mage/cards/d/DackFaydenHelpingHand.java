package mage.cards.d;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.combat.GoadTargetEffect;
import mage.abilities.effects.common.continuous.GainControlTargetEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.FilterOpponent;
import mage.filter.predicate.Predicates;
import mage.filter.predicate.other.PlayerIdPredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.TargetPlayer;
import mage.target.targetpointer.FixedTarget;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * @author Claude
 */
public final class DackFaydenHelpingHand extends CardImpl {

    public DackFaydenHelpingHand(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{4}{W}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.ADVISOR);
        this.power = new MageInt(4);
        this.toughness = new MageInt(6);

        // When Dack Fayden enters, reveal cards from the top of your library until you reveal X creature cards,
        // where X is the number of opponents you have. Put those creature cards onto the battlefield, then shuffle.
        // They're goaded for the rest of the game. For each of those permanents, choose a different opponent.
        // Each opponent gains control of the permanent for which they were chosen.
        this.addAbility(new EntersBattlefieldTriggeredAbility(new DackFaydenHelpingHandEffect()));
    }

    private DackFaydenHelpingHand(final DackFaydenHelpingHand card) {
        super(card);
    }

    @Override
    public DackFaydenHelpingHand copy() {
        return new DackFaydenHelpingHand(this);
    }
}

class DackFaydenHelpingHandEffect extends OneShotEffect {

    DackFaydenHelpingHandEffect() {
        super(Outcome.Detriment);
        staticText = "reveal cards from the top of your library until you reveal X creature cards, "
                + "where X is the number of opponents you have. Put those creature cards onto the battlefield, "
                + "then shuffle. They're goaded for the rest of the game. For each of those permanents, "
                + "choose a different opponent. Each opponent gains control of the permanent for which they were chosen";
    }

    private DackFaydenHelpingHandEffect(final DackFaydenHelpingHandEffect effect) {
        super(effect);
    }

    @Override
    public DackFaydenHelpingHandEffect copy() {
        return new DackFaydenHelpingHandEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        int opponents = game.getOpponents(controller.getId(), true).size();
        Cards revealed = new CardsImpl();
        Cards creatures = new CardsImpl();
        if (opponents > 0) {
            for (Card card : controller.getLibrary().getCards(game)) {
                revealed.add(card);
                if (card.isCreature(game)) {
                    creatures.add(card);
                    if (creatures.size() >= opponents) {
                        break;
                    }
                }
            }
        }
        controller.revealCards(source, revealed, game);
        controller.moveCards(creatures, Zone.BATTLEFIELD, source, game);
        controller.shuffleLibrary(source, game);
        game.processAction();

        List<Permanent> permanents = new ArrayList<>();
        for (UUID cardId : creatures) {
            Permanent permanent = game.getPermanent(cardId);
            if (permanent != null) {
                permanents.add(permanent);
            }
        }
        // goaded for the rest of the game
        for (Permanent permanent : permanents) {
            GoadTargetEffect goad = new GoadTargetEffect(Duration.EndOfGame);
            goad.setTargetPointer(new FixedTarget(permanent, game));
            game.addEffect(goad, source);
        }
        // a different opponent for each permanent
        Set<UUID> chosen = new HashSet<>();
        for (Permanent permanent : permanents) {
            FilterOpponent filter = new FilterOpponent("an opponent to gain control of " + permanent.getLogName());
            for (UUID used : chosen) {
                filter.add(Predicates.not(new PlayerIdPredicate(used)));
            }
            TargetPlayer target = new TargetPlayer(1, 1, true, filter);
            if (!target.canChoose(controller.getId(), source, game)) {
                break;
            }
            controller.choose(Outcome.Detriment, target, source, game);
            UUID opponentId = target.getFirstTarget();
            if (opponentId == null) {
                break;
            }
            chosen.add(opponentId);
            game.addEffect(new GainControlTargetEffect(Duration.EndOfGame, true, opponentId)
                    .setTargetPointer(new FixedTarget(permanent, game)), source);
        }
        return true;
    }
}
