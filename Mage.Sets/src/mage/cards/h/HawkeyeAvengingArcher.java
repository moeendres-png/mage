package mage.cards.h;

import mage.MageInt;
import mage.abilities.Ability;
import mage.MageObject;
import mage.MageObjectReference;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.SimpleActivatedAbility;
import mage.abilities.costs.common.TapSourceCost;
import mage.abilities.effects.common.DamageTargetEffect;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.abilities.keyword.ReachAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.permanent.Permanent;
import mage.target.common.TargetAnyTarget;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class HawkeyeAvengingArcher extends CardImpl {

    public HawkeyeAvengingArcher(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{U}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.ARCHER);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(3);
        this.toughness = new MageInt(4);

        // Reach
        this.addAbility(ReachAbility.getInstance());

        // Whenever a creature an opponent controls dies, if Hawkeye dealt damage to it this turn, draw a card.
        this.addAbility(new HawkeyeAvengingArcherTriggeredAbility());

        // {T}: Hawkeye deals 1 damage to any target.
        Ability ability = new SimpleActivatedAbility(new DamageTargetEffect(1), new TapSourceCost());
        ability.addTarget(new TargetAnyTarget());
        this.addAbility(ability);
    }

    private HawkeyeAvengingArcher(final HawkeyeAvengingArcher card) {
        super(card);
    }

    @Override
    public HawkeyeAvengingArcher copy() {
        return new HawkeyeAvengingArcher(this);
    }
}

class HawkeyeAvengingArcherTriggeredAbility extends TriggeredAbilityImpl {

    HawkeyeAvengingArcherTriggeredAbility() {
        super(Zone.BATTLEFIELD, new DrawCardSourceControllerEffect(1), false);
        setLeavesTheBattlefieldTrigger(true);
        setTriggerPhrase("Whenever a creature an opponent controls dies, if {this} dealt damage to it this turn, ");
    }

    private HawkeyeAvengingArcherTriggeredAbility(final HawkeyeAvengingArcherTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public HawkeyeAvengingArcherTriggeredAbility copy() {
        return new HawkeyeAvengingArcherTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ZONE_CHANGE;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        ZoneChangeEvent zEvent = (ZoneChangeEvent) event;
        if (!zEvent.isDiesEvent() || !zEvent.isPermanentMoved()) {
            return false;
        }
        Permanent died = zEvent.getTarget();
        if (died == null || !died.isCreature(game)
                || !game.getOpponents(getControllerId()).contains(died.getControllerId())) {
            return false;
        }
        for (MageObjectReference mor : died.getDealtDamageByThisTurn()) {
            if (mor.refersTo(game.getLastKnownInformation(getSourceId(), Zone.BATTLEFIELD), game)
                    || mor.refersTo(getSourceObject(game), game)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public boolean isInUseableZone(Game game, MageObject sourceObject, GameEvent event) {
        return TriggeredAbilityImpl.isInUseableZoneDiesTrigger(this, sourceObject, event, game);
    }
}
