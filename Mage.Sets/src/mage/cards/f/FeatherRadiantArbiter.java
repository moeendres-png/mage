package mage.cards.f;

import mage.MageInt;
import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.common.CopySpellForEachItCouldTargetEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.abilities.keyword.LifelinkAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.StaticFilters;
import mage.filter.common.FilterCreaturePermanent;
import mage.filter.predicate.Predicate;
import mage.filter.predicate.mageobject.MageObjectReferencePredicate;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.game.stack.Spell;
import mage.game.stack.StackObject;
import mage.players.Player;
import mage.target.Target;
import mage.target.TargetPermanent;
import mage.util.TargetAddress;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;

/**
 * Feather, Radiant Arbiter {R}{W}{W}
 * Legendary Creature -- Angel 4/3
 * Flying, lifelink
 * Whenever you cast a noncreature spell that targets only Feather, you may choose any number of other creatures
 * that spell could target and pay {2} for each of those creatures. If you do, for each of those creatures,
 * copy that spell. The copy targets that creature.
 */
public final class FeatherRadiantArbiter extends CardImpl {

    public FeatherRadiantArbiter(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{R}{W}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.ANGEL);
        this.power = new MageInt(4);
        this.toughness = new MageInt(3);

        // Flying, lifelink
        this.addAbility(FlyingAbility.getInstance());
        this.addAbility(LifelinkAbility.getInstance());

        // Whenever you cast a noncreature spell that targets only Feather, you may choose any number of other
        // creatures that spell could target and pay {2} for each of those creatures. If you do, for each of those
        // creatures, copy that spell. The copy targets that creature.
        this.addAbility(new FeatherRadiantArbiterTriggeredAbility());
    }

    private FeatherRadiantArbiter(final FeatherRadiantArbiter card) {
        super(card);
    }

    @Override
    public FeatherRadiantArbiter copy() {
        return new FeatherRadiantArbiter(this);
    }
}

class FeatherRadiantArbiterTriggeredAbility extends TriggeredAbilityImpl {

    FeatherRadiantArbiterTriggeredAbility() {
        super(Zone.BATTLEFIELD, new FeatherRadiantArbiterCopySpellEffect(), false);
    }

    private FeatherRadiantArbiterTriggeredAbility(final FeatherRadiantArbiterTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public FeatherRadiantArbiterTriggeredAbility copy() {
        return new FeatherRadiantArbiterTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.SPELL_CAST;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getPlayerId())) {
            return false;
        }
        Spell spell = game.getSpell(event.getTargetId());
        if (spell == null || spell.isCreature(game)) {
            return false;
        }
        boolean noTargets = true;
        for (TargetAddress addr : TargetAddress.walk(spell)) {
            if (addr == null) {
                continue;
            }
            noTargets = false;
            Target targetInstance = addr.getTarget(spell);
            if (targetInstance == null) {
                continue;
            }
            for (UUID target : targetInstance.getTargets()) {
                if (target == null) {
                    continue;
                }
                Permanent permanent = game.getPermanent(target);
                if (permanent == null || !permanent.getId().equals(getSourceId())) {
                    return false;
                }
            }
        }
        if (noTargets) {
            return false;
        }
        getEffects().setValue("triggeringSpell", spell);
        return true;
    }

    @Override
    public String getRule() {
        return "Whenever you cast a noncreature spell that targets only {this}, you may choose any number of other "
                + "creatures that spell could target and pay {2} for each of those creatures. If you do, for each of "
                + "those creatures, copy that spell. The copy targets that creature. "
                + "<i>(Copies of permanent spells become tokens.)</i>";
    }
}

class FeatherRadiantArbiterCopySpellEffect extends CopySpellForEachItCouldTargetEffect {

    FeatherRadiantArbiterCopySpellEffect() {
        super();
    }

    private FeatherRadiantArbiterCopySpellEffect(final FeatherRadiantArbiterCopySpellEffect effect) {
        super(effect);
    }

    @Override
    protected Player getPlayer(Game game, Ability source) {
        return game.getPlayer(source.getControllerId());
    }

    @Override
    protected List<MageObjectReferencePredicate> prepareCopiesWithTargets(StackObject stackObject, Player player, Ability source, Game game) {
        Permanent feather = source.getSourcePermanentIfItStillExists(game);
        Set<UUID> candidates = new HashSet<>();
        for (Permanent permanent : game.getBattlefield().getActivePermanents(
                StaticFilters.FILTER_PERMANENT_CREATURE, player.getId(), source, game)) {
            if (permanent != null
                    && (feather == null || !permanent.getId().equals(feather.getId()))
                    && stackObject.canTarget(game, permanent.getId())) {
                candidates.add(permanent.getId());
            }
        }
        List<MageObjectReferencePredicate> result = new ArrayList<>();
        if (candidates.isEmpty()) {
            return result;
        }

        // choose any number of those creatures, then pay {2} for each of them
        FilterCreaturePermanent filter = new FilterCreaturePermanent("other creatures that spell could target");
        filter.add((Predicate<Permanent>) (input, g) -> candidates.contains(input.getId()));
        Target target = new TargetPermanent(0, candidates.size(), filter, true);
        player.choose(Outcome.Copy, target, source, game);
        List<UUID> chosen = new ArrayList<>(target.getTargets());
        if (chosen.isEmpty()) {
            return result;
        }
        GenericManaCost cost = new GenericManaCost(2 * chosen.size());
        if (!cost.pay(source, game, source, player.getId(), false)) {
            return result;
        }
        for (UUID id : chosen) {
            Permanent permanent = game.getPermanent(id);
            if (permanent != null) {
                result.add(new MageObjectReferencePredicate(new MageObjectReference(permanent, game)));
            }
        }
        return result.stream().filter(Objects::nonNull).collect(java.util.stream.Collectors.toList());
    }

    @Override
    protected Spell getStackObject(Game game, Ability source) {
        return (Spell) getValue("triggeringSpell");
    }

    @Override
    public FeatherRadiantArbiterCopySpellEffect copy() {
        return new FeatherRadiantArbiterCopySpellEffect(this);
    }
}
