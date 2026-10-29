package mage.cards.s;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.LoyaltyAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.RestrictionEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.choices.ChoiceImpl;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Space Beleren {2}{W}{U}
 * Legendary Planeswalker -- Jace
 * Space sculptor (Space Beleren divides the battlefield into alpha, beta, and gamma sectors. If a creature isn't
 * assigned to a sector, its controller assigns it to one. Opponents assign first.)
 * +1: Creatures in each sector can be blocked this turn only by creatures in the same sector.
 * -1: Put a +1/+1 counter on each creature in the sector of your choice.
 * -5: Destroy all creatures in the sector of your choice.
 */
public final class SpaceBeleren extends CardImpl {

    public SpaceBeleren(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.PLANESWALKER}, "{2}{W}{U}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.JACE);
        this.setStartingLoyalty(3);

        // Space sculptor
        this.addAbility(new SpaceSculptorTriggeredAbility());

        // +1: Creatures in each sector can be blocked this turn only by creatures in the same sector.
        this.addAbility(new LoyaltyAbility(new SpaceBelerenBlockEffect(), 1));

        // -1: Put a +1/+1 counter on each creature in the sector of your choice.
        this.addAbility(new LoyaltyAbility(new SpaceBelerenCounterEffect(), -1));

        // -5: Destroy all creatures in the sector of your choice.
        this.addAbility(new LoyaltyAbility(new SpaceBelerenDestroyEffect(), -5));
    }

    private SpaceBeleren(final SpaceBeleren card) {
        super(card);
    }

    @Override
    public SpaceBeleren copy() {
        return new SpaceBeleren(this);
    }
}

/**
 * The sector of every creature is kept in the game state, per Space Beleren object. The map is replaced, never
 * changed in place, so that a rollback restores the earlier assignment.
 */
final class SpaceSectors {

    static final List<String> SECTORS = Arrays.asList("Alpha", "Beta", "Gamma");

    private SpaceSectors() {
    }

    private static String key(Ability source) {
        return "SpaceBelerenSectors" + source.getSourceId() + '_' + source.getStackMomentSourceZCC();
    }

    @SuppressWarnings("unchecked")
    static Map<MageObjectReference, String> get(Ability source, Game game) {
        Object value = game.getState().getValue(key(source));
        return value instanceof Map ? (Map<MageObjectReference, String>) value : new HashMap<>();
    }

    static void assign(Ability source, Game game, Permanent creature, String sector) {
        Map<MageObjectReference, String> sectors = new HashMap<>(get(source, game));
        sectors.put(new MageObjectReference(creature, game), sector);
        game.getState().setValue(key(source), sectors);
    }

    static String choose(Player chooser, String message, Game game) {
        ChoiceImpl choice = new ChoiceImpl(true);
        choice.setMessage(message);
        choice.setChoices(new LinkedHashSet<>(SECTORS));
        if (!chooser.choose(Outcome.Neutral, choice, game)) {
            return null;
        }
        return choice.getChoice();
    }

    static List<Permanent> creaturesIn(String sector, Ability source, Game game) {
        List<Permanent> creatures = new ArrayList<>();
        for (Map.Entry<MageObjectReference, String> entry : get(source, game).entrySet()) {
            Permanent permanent = entry.getKey().getPermanent(game);
            if (sector.equals(entry.getValue()) && permanent != null && permanent.isCreature(game)) {
                creatures.add(permanent);
            }
        }
        return creatures;
    }
}

class SpaceSculptorTriggeredAbility extends TriggeredAbilityImpl {

    SpaceSculptorTriggeredAbility() {
        super(Zone.BATTLEFIELD, new SpaceSculptorEffect(), false);
        // assigned as a creature enters (or as Space Beleren enters), before anyone can respond
        this.usesStack = false;
    }

    private SpaceSculptorTriggeredAbility(final SpaceSculptorTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public SpaceSculptorTriggeredAbility copy() {
        return new SpaceSculptorTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ENTERS_THE_BATTLEFIELD;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (event.getTargetId().equals(getSourceId())) {
            return true;
        }
        Permanent permanent = game.getPermanent(event.getTargetId());
        return permanent != null && permanent.isCreature(game);
    }

    @Override
    public String getRule() {
        return "Space sculptor <i>({this} divides the battlefield into alpha, beta, and gamma sectors. "
                + "If a creature isn't assigned to a sector, its controller assigns it to one. Opponents assign first.)</i>";
    }
}

class SpaceSculptorEffect extends OneShotEffect {

    SpaceSculptorEffect() {
        super(Outcome.Neutral);
    }

    private SpaceSculptorEffect(final SpaceSculptorEffect effect) {
        super(effect);
    }

    @Override
    public SpaceSculptorEffect copy() {
        return new SpaceSculptorEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent sculptor = source.getSourcePermanentIfItStillExists(game);
        if (sculptor == null) {
            return false;
        }
        // opponents assign first, in turn order, and the controller last
        List<UUID> order = new ArrayList<>();
        for (UUID playerId : game.getState().getPlayerList(source.getControllerId())) {
            if (!playerId.equals(source.getControllerId())) {
                order.add(playerId);
            }
        }
        order.add(source.getControllerId());
        for (UUID playerId : order) {
            Player player = game.getPlayer(playerId);
            if (player == null || !player.canRespond()) {
                continue;
            }
            for (Permanent creature : game.getBattlefield().getAllActivePermanents(playerId)) {
                if (!creature.isCreature(game)) {
                    continue;
                }
                if (SpaceSectors.get(source, game).containsKey(new MageObjectReference(creature, game))) {
                    continue;
                }
                String sector = SpaceSectors.choose(player,
                        "Assign " + creature.getName() + " to a sector", game);
                if (sector != null) {
                    SpaceSectors.assign(source, game, creature, sector);
                    game.informPlayers(player.getLogName() + " assigns " + creature.getLogName() + " to the " + sector + " sector");
                }
            }
        }
        return true;
    }
}

class SpaceBelerenBlockEffect extends RestrictionEffect {

    SpaceBelerenBlockEffect() {
        super(Duration.EndOfTurn);
        staticText = "creatures in each sector can be blocked this turn only by creatures in the same sector";
    }

    private SpaceBelerenBlockEffect(final SpaceBelerenBlockEffect effect) {
        super(effect);
    }

    @Override
    public SpaceBelerenBlockEffect copy() {
        return new SpaceBelerenBlockEffect(this);
    }

    @Override
    public boolean applies(Permanent permanent, Ability source, Game game) {
        return permanent.isCreature(game);
    }

    @Override
    public boolean canBeBlocked(Permanent attacker, Permanent blocker, Ability source, Game game, boolean canUseChooseDialogs) {
        if (blocker == null) {
            return true;
        }
        Map<MageObjectReference, String> sectors = SpaceSectors.get(source, game);
        String attackerSector = sectors.get(new MageObjectReference(attacker, game));
        String blockerSector = sectors.get(new MageObjectReference(blocker, game));
        return attackerSector == null || blockerSector == null || attackerSector.equals(blockerSector);
    }
}

class SpaceBelerenCounterEffect extends OneShotEffect {

    SpaceBelerenCounterEffect() {
        super(Outcome.BoostCreature);
        staticText = "put a +1/+1 counter on each creature in the sector of your choice";
    }

    private SpaceBelerenCounterEffect(final SpaceBelerenCounterEffect effect) {
        super(effect);
    }

    @Override
    public SpaceBelerenCounterEffect copy() {
        return new SpaceBelerenCounterEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        String sector = SpaceSectors.choose(controller, "Choose a sector to put +1/+1 counters on", game);
        if (sector == null) {
            return false;
        }
        for (Permanent creature : SpaceSectors.creaturesIn(sector, source, game)) {
            creature.addCounters(CounterType.P1P1.createInstance(), source.getControllerId(), source, game);
        }
        return true;
    }
}

class SpaceBelerenDestroyEffect extends OneShotEffect {

    SpaceBelerenDestroyEffect() {
        super(Outcome.DestroyPermanent);
        staticText = "destroy all creatures in the sector of your choice";
    }

    private SpaceBelerenDestroyEffect(final SpaceBelerenDestroyEffect effect) {
        super(effect);
    }

    @Override
    public SpaceBelerenDestroyEffect copy() {
        return new SpaceBelerenDestroyEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        String sector = SpaceSectors.choose(controller, "Choose a sector to destroy all creatures in", game);
        if (sector == null) {
            return false;
        }
        for (Permanent creature : SpaceSectors.creaturesIn(sector, source, game)) {
            creature.destroy(source, game, false);
        }
        return true;
    }
}
