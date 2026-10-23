package mage.cards.t;

import mage.abilities.Ability;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.ExileSpellEffect;
import mage.abilities.effects.common.PhaseOutAllEffect;
import mage.abilities.keyword.ProtectionFromEverythingAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.Outcome;
import mage.constants.SubLayer;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.common.TargetOpponent;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * @author Claude
 */
public final class TeferisReproach extends CardImpl {

    public TeferisReproach(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.INSTANT}, "{2}{W}");

        // Choose target opponent. Until that player's next turn, they gain protection from everything and their life total can't change.
        // All nonland permanents they control phase out.
        this.getSpellAbility().addTarget(new TargetOpponent());
        this.getSpellAbility().addEffect(new TeferisReproachEffect());
        this.getSpellAbility().addEffect(new TeferisReproachPhaseOutEffect());

        // Exile Teferi's Reproach.
        this.getSpellAbility().addEffect(new ExileSpellEffect());
    }

    private TeferisReproach(final TeferisReproach card) {
        super(card);
    }

    @Override
    public TeferisReproach copy() {
        return new TeferisReproach(this);
    }
}

/**
 * The target player has protection from everything and cannot gain or lose life
 * until the beginning of that player's next turn.
 */
class TeferisReproachEffect extends ContinuousEffectImpl {

    TeferisReproachEffect() {
        super(Duration.UntilYourNextTurn, Layer.PlayerEffects, SubLayer.NA, Outcome.Protect);
        staticText = "Choose target opponent. Until that player's next turn, they gain protection from everything "
                + "and their life total can't change.";
    }

    private TeferisReproachEffect(final TeferisReproachEffect effect) {
        super(effect);
    }

    @Override
    public TeferisReproachEffect copy() {
        return new TeferisReproachEffect(this);
    }

    @Override
    public void init(Ability source, Game game) {
        super.init(source, game);
        // "until that player's next turn": the duration counts from the target's turn, not from the caster's
        setStartingControllerAndTurnNum(game, source.getFirstTarget(), game.getActivePlayerId());
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player player = game.getPlayer(source.getFirstTarget());
        if (player == null) {
            discard();
            return false;
        }
        player.setLifeTotalCanChange(false);
        player.addAbility(new ProtectionFromEverythingAbility());
        return true;
    }
}

class TeferisReproachPhaseOutEffect extends OneShotEffect {

    TeferisReproachPhaseOutEffect() {
        super(Outcome.Detriment);
        staticText = "All nonland permanents they control phase out. <i>(While they're phased out, they're treated "
                + "as though they don't exist. They phase in before that player untaps during their next untap step.)</i>";
    }

    private TeferisReproachPhaseOutEffect(final TeferisReproachPhaseOutEffect effect) {
        super(effect);
    }

    @Override
    public TeferisReproachPhaseOutEffect copy() {
        return new TeferisReproachPhaseOutEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player opponent = game.getPlayer(source.getFirstTarget());
        if (opponent == null) {
            return false;
        }
        List<UUID> permanentIds = new ArrayList<>();
        for (Permanent permanent : game.getBattlefield().getActivePermanents(
                StaticFilters.FILTER_CONTROLLED_PERMANENT_NON_LAND, opponent.getId(), source, game)) {
            permanentIds.add(permanent.getId());
        }
        return new PhaseOutAllEffect(permanentIds).apply(game, source);
    }
}
