package mage.cards.d;

import mage.abilities.Ability;
import mage.abilities.costs.CostImpl;
import mage.abilities.effects.OneShotEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.choices.Choice;
import mage.choices.ChoiceImpl;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.filter.common.FilterControlledCreaturePermanent;
import mage.filter.predicate.Predicates;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.game.permanent.token.DalekToken;
import mage.players.Player;
import mage.target.common.TargetSacrifice;
import mage.util.CardUtil;

import java.util.LinkedHashSet;
import java.util.Set;
import java.util.UUID;

/**
 * @author Claude
 */
public final class DoomsdayConfluence extends CardImpl {

    public DoomsdayConfluence(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.SORCERY}, "{X}{X}{B}");

        // Choose X. You may choose the same mode more than once.
        // * Each player sacrifices a nonartifact creature of their choice.
        // * Create a 3/3 black Dalek artifact creature token with menace.
        // * Each opponent discards a card.
        // The engine chooses the modes of a spell before X is announced, so the X choices are made as a cost
        // paid while X is known; they are stored with the spell and carried out in the printed order.
        this.getSpellAbility().addCost(new DoomsdayConfluenceChooseCost());
        this.getSpellAbility().addEffect(new DoomsdayConfluenceEffect());
    }

    private DoomsdayConfluence(final DoomsdayConfluence card) {
        super(card);
    }

    @Override
    public DoomsdayConfluence copy() {
        return new DoomsdayConfluence(this);
    }
}

class DoomsdayConfluenceChooseCost extends CostImpl {

    static final String TAG_SACRIFICE = "DoomsdayConfluenceSacrifice";
    static final String TAG_DALEK = "DoomsdayConfluenceDalek";
    static final String TAG_DISCARD = "DoomsdayConfluenceDiscard";

    static final String MODE_SACRIFICE = "Each player sacrifices a nonartifact creature of their choice";
    static final String MODE_DALEK = "Create a 3/3 black Dalek artifact creature token with menace";
    static final String MODE_DISCARD = "Each opponent discards a card";

    DoomsdayConfluenceChooseCost() {
        super();
        // the rules text of the choice is carried by the effect, so the cost adds nothing to the text
        this.text = "";
    }

    private DoomsdayConfluenceChooseCost(final DoomsdayConfluenceChooseCost cost) {
        super(cost);
    }

    @Override
    public DoomsdayConfluenceChooseCost copy() {
        return new DoomsdayConfluenceChooseCost(this);
    }

    @Override
    public boolean canPay(Ability ability, Ability source, UUID controllerId, Game game) {
        return game.getPlayer(controllerId) != null;
    }

    @Override
    public boolean pay(Ability ability, Game game, Ability source, UUID controllerId, boolean noMana, mage.abilities.costs.Cost costToPay) {
        Player player = game.getPlayer(controllerId);
        if (player == null) {
            return false;
        }
        int x = CardUtil.getSourceCostsTagX(game, source, 0);
        int sacrifice = 0;
        int dalek = 0;
        int discard = 0;
        for (int i = 0; i < x; i++) {
            Set<String> modes = new LinkedHashSet<>();
            modes.add(MODE_SACRIFICE);
            modes.add(MODE_DALEK);
            modes.add(MODE_DISCARD);
            Choice choice = new ChoiceImpl(true);
            choice.setMessage("Choose mode " + (i + 1) + " of " + x + " (you may choose the same mode more than once)");
            choice.setChoices(modes);
            if (!player.choose(Outcome.Benefit, choice, game) || choice.getChoice() == null) {
                return false;
            }
            switch (choice.getChoice()) {
                case MODE_SACRIFICE:
                    sacrifice++;
                    break;
                case MODE_DALEK:
                    dalek++;
                    break;
                default:
                    discard++;
            }
        }
        CardUtil.setSourceCostsTag(game, source, TAG_SACRIFICE, sacrifice);
        CardUtil.setSourceCostsTag(game, source, TAG_DALEK, dalek);
        CardUtil.setSourceCostsTag(game, source, TAG_DISCARD, discard);
        this.paid = true;
        return true;
    }
}

class DoomsdayConfluenceEffect extends OneShotEffect {

    private static final FilterControlledCreaturePermanent filter = new FilterControlledCreaturePermanent("nonartifact creature");

    static {
        filter.add(Predicates.not(CardType.ARTIFACT.getPredicate()));
    }

    DoomsdayConfluenceEffect() {
        super(Outcome.Detriment);
        staticText = "choose X. You may choose the same mode more than once."
                + "<br>&bull; Each player sacrifices a nonartifact creature of their choice."
                + "<br>&bull; Create a 3/3 black Dalek artifact creature token with menace."
                + "<br>&bull; Each opponent discards a card.";
    }

    private DoomsdayConfluenceEffect(final DoomsdayConfluenceEffect effect) {
        super(effect);
    }

    @Override
    public DoomsdayConfluenceEffect copy() {
        return new DoomsdayConfluenceEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        int sacrifice = CardUtil.getSourceCostsTag(game, source, DoomsdayConfluenceChooseCost.TAG_SACRIFICE, 0);
        int dalek = CardUtil.getSourceCostsTag(game, source, DoomsdayConfluenceChooseCost.TAG_DALEK, 0);
        int discard = CardUtil.getSourceCostsTag(game, source, DoomsdayConfluenceChooseCost.TAG_DISCARD, 0);
        // modes are carried out in the order they are printed, a mode chosen several times in a row
        for (int i = 0; i < sacrifice; i++) {
            for (UUID playerId : game.getState().getPlayersInRange(controller.getId(), game)) {
                Player player = game.getPlayer(playerId);
                if (player == null) {
                    continue;
                }
                if (!game.getBattlefield().contains(filter, player.getId(), source, game, 1)) {
                    continue;
                }
                TargetSacrifice target = new TargetSacrifice(filter);
                player.choose(Outcome.Sacrifice, target, source, game);
                Permanent permanent = game.getPermanent(target.getFirstTarget());
                if (permanent != null) {
                    permanent.sacrifice(source, game);
                }
            }
        }
        if (dalek > 0) {
            new DalekToken().putOntoBattlefield(dalek, game, source);
        }
        for (int i = 0; i < discard; i++) {
            for (UUID opponentId : game.getOpponents(controller.getId())) {
                Player opponent = game.getPlayer(opponentId);
                if (opponent != null) {
                    opponent.discard(1, false, false, source, game);
                }
            }
        }
        return true;
    }
}
