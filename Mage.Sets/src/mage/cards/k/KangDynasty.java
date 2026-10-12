package mage.cards.k;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.common.SagaAbility;
import mage.abilities.dynamicvalue.common.CardsInControllerHandCount;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.abilities.effects.common.combat.CantBeBlockedTargetEffect;
import mage.abilities.effects.common.combat.GoadTargetEffect;
import mage.abilities.effects.common.continuous.BoostTargetEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SagaChapter;
import mage.constants.SubType;
import mage.game.Game;
import mage.game.events.DamagedEvent;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.target.common.TargetControlledCreaturePermanent;
import mage.target.common.TargetCreaturePermanent;
import mage.target.targetadjustment.ForEachPlayerTargetsAdjuster;
import mage.target.targetpointer.FixedTarget;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class KangDynasty extends CardImpl {

    public KangDynasty(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{3}{U}");

        this.subtype.add(SubType.SAGA);

        // (As this Saga enters and after your draw step, add a lore counter. Sacrifice after III.)
        SagaAbility sagaAbility = new SagaAbility(this);

        // I, II -- For each opponent, tap up to one target creature that player controls. Goad those creatures. Until your next turn, whenever any of those creatures deals combat damage to a player, draw a card.
        sagaAbility.addChapterEffect(this, SagaChapter.CHAPTER_I, SagaChapter.CHAPTER_II, ability -> {
            ability.addEffect(new KangDynastyEffect());
            ability.addTarget(new TargetCreaturePermanent(0, 1));
            ability.setTargetAdjuster(new ForEachPlayerTargetsAdjuster(false, true));
        });

        // III -- Target creature you control gets +1/+1 until end of turn for each card in your hand and can't be blocked this turn.
        sagaAbility.addChapterEffect(this, SagaChapter.CHAPTER_III, ability -> {
            ability.addEffect(new BoostTargetEffect(CardsInControllerHandCount.ANY, CardsInControllerHandCount.ANY, Duration.EndOfTurn)
                    .setText("target creature you control gets +1/+1 until end of turn for each card in your hand"));
            ability.addEffect(new CantBeBlockedTargetEffect(Duration.EndOfTurn).setText("and can't be blocked this turn"));
            ability.addTarget(new TargetControlledCreaturePermanent());
        });
        this.addAbility(sagaAbility);
    }

    private KangDynasty(final KangDynasty card) {
        super(card);
    }

    @Override
    public KangDynasty copy() {
        return new KangDynasty(this);
    }
}

class KangDynastyEffect extends OneShotEffect {

    KangDynastyEffect() {
        super(Outcome.Detriment);
        staticText = "for each opponent, tap up to one target creature that player controls. Goad those creatures. "
                + "Until your next turn, whenever any of those creatures deals combat damage to a player, draw a card";
    }

    private KangDynastyEffect(final KangDynastyEffect effect) {
        super(effect);
    }

    @Override
    public KangDynastyEffect copy() {
        return new KangDynastyEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        List<MageObjectReference> creatures = new ArrayList<>();
        for (UUID targetId : getTargetPointer().getTargets(game, source)) {
            Permanent creature = game.getPermanent(targetId);
            if (creature == null) {
                continue;
            }
            creature.tap(source, game);
            game.addEffect(new GoadTargetEffect().setTargetPointer(new FixedTarget(creature, game)), source);
            creatures.add(new MageObjectReference(creature, game));
        }
        if (!creatures.isEmpty()) {
            game.addDelayedTriggeredAbility(new KangDynastyDelayedTriggeredAbility(creatures), source);
        }
        return true;
    }
}

class KangDynastyDelayedTriggeredAbility extends DelayedTriggeredAbility {

    private final List<MageObjectReference> creatures;

    KangDynastyDelayedTriggeredAbility(List<MageObjectReference> creatures) {
        super(new DrawCardSourceControllerEffect(1), Duration.UntilYourNextTurn, false, false);
        this.creatures = creatures;
        setTriggerPhrase("Until your next turn, whenever any of those creatures deals combat damage to a player, ");
    }

    private KangDynastyDelayedTriggeredAbility(final KangDynastyDelayedTriggeredAbility ability) {
        super(ability);
        this.creatures = new ArrayList<>(ability.creatures);
    }

    @Override
    public KangDynastyDelayedTriggeredAbility copy() {
        return new KangDynastyDelayedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DAMAGED_PLAYER;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        return ((DamagedEvent) event).isCombatDamage()
                && creatures.stream().anyMatch(mor -> mor.refersTo(event.getSourceId(), game));
    }
}
