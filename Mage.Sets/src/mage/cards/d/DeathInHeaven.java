package mage.cards.d;

import mage.abilities.Ability;
import mage.abilities.common.SagaAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.keyword.CybermanFaceDown;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SagaChapter;
import mage.constants.SubType;
import mage.filter.StaticFilters;
import mage.game.ExileZone;
import mage.game.Game;
import mage.players.Player;
import mage.target.TargetPlayer;
import mage.util.CardUtil;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/**
 * @author Claude
 */
public final class DeathInHeaven extends CardImpl {

    public DeathInHeaven(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{3}{B}");

        this.subtype.add(SubType.SAGA);

        // (As this Saga enters and after your draw step, add a lore counter. Sacrifice after III.)
        SagaAbility sagaAbility = new SagaAbility(this);

        // I, II -- Target player mills two cards, then exiles their graveyard.
        sagaAbility.addChapterEffect(
                this, SagaChapter.CHAPTER_I, SagaChapter.CHAPTER_II,
                new DeathInHeavenExileEffect(), new TargetPlayer()
        );

        // III -- Put all creature cards exiled with this enchantment onto the battlefield face down under your control. They're 2/2 Cyberman artifact creatures.
        sagaAbility.addChapterEffect(this, SagaChapter.CHAPTER_III, new DeathInHeavenReturnEffect());
        this.addAbility(sagaAbility);
    }

    private DeathInHeaven(final DeathInHeaven card) {
        super(card);
    }

    @Override
    public DeathInHeaven copy() {
        return new DeathInHeaven(this);
    }
}

class DeathInHeavenExileEffect extends OneShotEffect {

    DeathInHeavenExileEffect() {
        super(Outcome.Exile);
        staticText = "target player mills two cards, then exiles their graveyard";
    }

    private DeathInHeavenExileEffect(final DeathInHeavenExileEffect effect) {
        super(effect);
    }

    @Override
    public DeathInHeavenExileEffect copy() {
        return new DeathInHeavenExileEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Player player = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (controller == null || player == null) {
            return false;
        }
        player.millCards(2, source, game);
        Set<Card> cards = new HashSet<>(player.getGraveyard().getCards(game));
        controller.moveCardsToExile(
                cards, source, game, true,
                CardUtil.getExileZoneId(game, source), CardUtil.getSourceName(game, source)
        );
        return true;
    }
}

class DeathInHeavenReturnEffect extends OneShotEffect {

    DeathInHeavenReturnEffect() {
        super(Outcome.PutCreatureInPlay);
        staticText = "put all creature cards exiled with this enchantment onto the battlefield face down " +
                "under your control. They're 2/2 Cyberman artifact creatures";
    }

    private DeathInHeavenReturnEffect(final DeathInHeavenReturnEffect effect) {
        super(effect);
    }

    @Override
    public DeathInHeavenReturnEffect copy() {
        return new DeathInHeavenReturnEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        ExileZone zone = game.getExile().getExileZone(CardUtil.getExileZoneId(game, source));
        if (controller == null || zone == null) {
            return false;
        }
        Set<Card> cards = new HashSet<>(zone.getCards(StaticFilters.FILTER_CARD_CREATURE, game));
        return !CybermanFaceDown.putOntoBattlefield(game, source, controller, cards, false).isEmpty();
    }
}
