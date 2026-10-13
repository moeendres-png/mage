package mage.cards.p;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.AttacksWithCreaturesTriggeredAbility;
import mage.abilities.common.OneOrMoreDamagePlayerTriggeredAbility;
import mage.abilities.effects.common.CreateTokenEffect;
import mage.abilities.effects.common.combat.CantBlockTargetEffect;
import mage.abilities.effects.common.combat.GoadTargetEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.SetTargetPointer;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.FilterPermanent;
import mage.filter.StaticFilters;
import mage.filter.common.FilterCreaturePermanent;
import mage.filter.predicate.permanent.GoadedPredicate;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.token.TreasureToken;
import mage.target.TargetPermanent;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class PuppetMasterStringPuller extends CardImpl {

    public PuppetMasterStringPuller(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.ARTIFICER);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(2);
        this.toughness = new MageInt(4);

        // Whenever you attack, goad target creature an opponent controls. It can't block this turn.
        Ability ability = new AttacksWithCreaturesTriggeredAbility(new GoadTargetEffect(), 1);
        ability.addEffect(new CantBlockTargetEffect(Duration.EndOfTurn).setText("It can't block this turn"));
        ability.addTarget(new TargetPermanent(StaticFilters.FILTER_OPPONENTS_PERMANENT_CREATURE));
        this.addAbility(ability);

        // Whenever one or more goaded creatures deal combat damage to one of your opponents, create a Treasure token.
        this.addAbility(new PuppetMasterStringPullerTriggeredAbility());
    }

    private PuppetMasterStringPuller(final PuppetMasterStringPuller card) {
        super(card);
    }

    @Override
    public PuppetMasterStringPuller copy() {
        return new PuppetMasterStringPuller(this);
    }
}

class PuppetMasterStringPullerTriggeredAbility extends OneOrMoreDamagePlayerTriggeredAbility {

    private static final FilterPermanent filter = new FilterCreaturePermanent("goaded creatures");

    static {
        filter.add(GoadedPredicate.instance);
    }

    PuppetMasterStringPullerTriggeredAbility() {
        super(Zone.BATTLEFIELD, new CreateTokenEffect(new TreasureToken()), filter,
                true, false, SetTargetPointer.NONE, false);
        setTriggerPhrase("Whenever one or more goaded creatures deal combat damage to one of your opponents, ");
    }

    private PuppetMasterStringPullerTriggeredAbility(final PuppetMasterStringPullerTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public PuppetMasterStringPullerTriggeredAbility copy() {
        return new PuppetMasterStringPullerTriggeredAbility(this);
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        return game.getOpponents(getControllerId()).contains(event.getTargetId())
                && super.checkTrigger(event, game);
    }
}
