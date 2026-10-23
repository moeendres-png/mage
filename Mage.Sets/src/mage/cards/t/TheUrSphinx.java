package mage.cards.t;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.effects.Effect;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.cost.SpellsCostReductionControllerEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.Cards;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.CardsImpl;
import mage.constants.AbilityWord;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.FilterCard;
import mage.filter.StaticFilters;
import mage.filter.predicate.mageobject.AnotherPredicate;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author Claude
 */
public final class TheUrSphinx extends CardImpl {

    private static final FilterCard filter = new FilterCard("Sphinx spells");

    static {
        filter.add(SubType.SPHINX.getPredicate());
        filter.add(AnotherPredicate.instance);
    }

    public TheUrSphinx(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{6}{W}{U}{B}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.SPHINX);
        this.subtype.add(SubType.AVATAR);
        this.power = new MageInt(10);
        this.toughness = new MageInt(10);

        // Eminence -- As long as The Ur-Sphinx is in the command zone or on the battlefield,
        // other Sphinx spells you cast cost {1} less to cast.
        Effect effect = new SpellsCostReductionControllerEffect(filter, 1);
        effect.setText("As long as {this} is in the command zone or on the battlefield, other Sphinx spells you cast cost {1} less to cast");
        Ability ability = new SimpleStaticAbility(effect);
        ability.setAbilityWord(AbilityWord.EMINENCE);
        this.addAbility(ability);
        effect = new SpellsCostReductionControllerEffect(filter, 1);
        effect.setText("");
        this.addAbility(new SimpleStaticAbility(Zone.COMMAND, effect));

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Whenever one or more Sphinxes you control attack, each player mills that many cards.
        // For each player, you may cast a card that player milled this way without paying its mana cost.
        this.addAbility(new TheUrSphinxTriggeredAbility());
    }

    private TheUrSphinx(final TheUrSphinx card) {
        super(card);
    }

    @Override
    public TheUrSphinx copy() {
        return new TheUrSphinx(this);
    }
}

class TheUrSphinxTriggeredAbility extends TriggeredAbilityImpl {

    TheUrSphinxTriggeredAbility() {
        super(Zone.BATTLEFIELD, null, false);
    }

    private TheUrSphinxTriggeredAbility(final TheUrSphinxTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public TheUrSphinxTriggeredAbility copy() {
        return new TheUrSphinxTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DECLARED_ATTACKERS;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        int attackingSphinxes = 0;
        for (UUID attacker : game.getCombat().getAttackers()) {
            Permanent creature = game.getPermanent(attacker);
            if (creature != null
                    && creature.isControlledBy(this.getControllerId())
                    && creature.hasSubtype(SubType.SPHINX, game)) {
                attackingSphinxes++;
            }
        }
        if (attackingSphinxes > 0) {
            this.getEffects().clear();
            addEffect(new TheUrSphinxEffect(attackingSphinxes));
            return true;
        }
        return false;
    }

    @Override
    public String getRule() {
        return "Whenever one or more Sphinxes you control attack, each player mills that many cards. "
                + "For each player, you may cast a card that player milled this way without paying its mana cost.";
    }
}

class TheUrSphinxEffect extends OneShotEffect {

    private final int amount;

    TheUrSphinxEffect(int amount) {
        super(Outcome.PlayForFree);
        this.amount = amount;
        staticText = "each player mills that many cards. For each player, you may cast a card that player "
                + "milled this way without paying its mana cost";
    }

    private TheUrSphinxEffect(final TheUrSphinxEffect effect) {
        super(effect);
        this.amount = effect.amount;
    }

    @Override
    public TheUrSphinxEffect copy() {
        return new TheUrSphinxEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        // each player mills, in turn order starting with the controller
        Cards[] milledByPlayer = new Cards[game.getPlayerList().size()];
        UUID[] playerIds = new UUID[milledByPlayer.length];
        int index = 0;
        for (UUID playerId : game.getState().getPlayersInRange(controller.getId(), game)) {
            Player player = game.getPlayer(playerId);
            playerIds[index] = playerId;
            milledByPlayer[index] = player == null ? new CardsImpl() : player.millCards(amount, source, game);
            index++;
        }
        game.processAction();
        // for each player, you may cast a card that player milled this way
        for (int i = 0; i < index; i++) {
            Cards milled = milledByPlayer[i];
            milled.retainZone(Zone.GRAVEYARD, game);
            if (milled.isEmpty()) {
                continue;
            }
            CardUtil.castSpellWithAttributesForFree(controller, source, game, milled, StaticFilters.FILTER_CARD);
        }
        return true;
    }
}
