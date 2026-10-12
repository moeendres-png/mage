package mage.cards.a;

import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.condition.Condition;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.cost.SpellCostReductionSourceEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.WatcherScope;
import mage.constants.Zone;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.watchers.Watcher;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class Avenge extends CardImpl {

    public Avenge(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.SORCERY}, "{4}{W}{W}");

        // This spell costs {2} less to cast if a player attacked you during their last turn.
        this.addAbility(new SimpleStaticAbility(
                Zone.ALL, new SpellCostReductionSourceEffect(2, AvengeCondition.instance).setCanWorksOnStackOnly(true)
        ).setRuleAtTheTop(true), new AvengeWatcher());

        // Destroy all creatures. You gain 1 life for each creature destroyed this way.
        this.getSpellAbility().addEffect(new AvengeEffect());
    }

    private Avenge(final Avenge card) {
        super(card);
    }

    @Override
    public Avenge copy() {
        return new Avenge(this);
    }
}

enum AvengeCondition implements Condition {
    instance;

    @Override
    public boolean apply(Game game, Ability source) {
        return AvengeWatcher.attackedDuringTheirLastTurn(source.getControllerId(), game);
    }

    @Override
    public String toString() {
        return "a player attacked you during their last turn";
    }
}

/**
 * For each player, the players they attacked during their most recent turn.
 */
class AvengeWatcher extends Watcher {

    private final Map<UUID, Set<UUID>> attackedByPlayer = new HashMap<>();

    AvengeWatcher() {
        super(WatcherScope.GAME);
    }

    @Override
    public void watch(GameEvent event, Game game) {
        switch (event.getType()) {
            case BEGINNING_PHASE_PRE:
                attackedByPlayer.remove(game.getActivePlayerId());
                return;
            case ATTACKER_DECLARED:
                if (game.getPlayer(event.getTargetId()) != null) {
                    attackedByPlayer
                            .computeIfAbsent(event.getPlayerId(), k -> new HashSet<>())
                            .add(event.getTargetId());
                }
                return;
            default:
        }
    }

    static boolean attackedDuringTheirLastTurn(UUID defenderId, Game game) {
        AvengeWatcher watcher = game.getState().getWatcher(AvengeWatcher.class);
        return watcher != null && watcher.attackedByPlayer
                .entrySet()
                .stream()
                .anyMatch(entry -> !entry.getKey().equals(defenderId) && entry.getValue().contains(defenderId));
    }
}

class AvengeEffect extends OneShotEffect {

    AvengeEffect() {
        super(Outcome.DestroyPermanent);
        this.staticText = "Destroy all creatures. You gain 1 life for each creature destroyed this way";
    }

    private AvengeEffect(final AvengeEffect effect) {
        super(effect);
    }

    @Override
    public AvengeEffect copy() {
        return new AvengeEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        int destroyed = 0;
        for (Permanent creature : game.getBattlefield().getActivePermanents(
                StaticFilters.FILTER_PERMANENT_CREATURE, controller.getId(), source, game)) {
            if (creature.destroy(source, game, false)) {
                destroyed++;
            }
        }
        if (destroyed > 0) {
            game.processAction();
            controller.gainLife(destroyed, game, source);
        }
        return true;
    }
}
