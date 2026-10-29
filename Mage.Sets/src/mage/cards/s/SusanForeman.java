package mage.cards.s;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.effects.ReplacementEffectImpl;
import mage.abilities.keyword.DoctorsCompanionAbility;
import mage.abilities.mana.GreenManaAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.game.Game;
import mage.game.command.Plane;
import mage.game.events.GameEvent;

import java.util.UUID;

/**
 * Susan Foreman {1}{G}
 * Legendary Creature -- Time Lord 1/1
 * If you would planeswalk, instead look at the top two cards of your planar deck, put one on the bottom of your
 * planar deck and the other on top, then planeswalk.
 * {T}: Add {G}.
 * Doctor's companion
 * <p>
 * This engine has no planar deck (a plane is put into the command zone directly), so the look-and-order step has
 * no cards to act on: the replacement is applied, tells the players so, and the planeswalk then happens as usual.
 */
public final class SusanForeman extends CardImpl {

    public SusanForeman(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{1}{G}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.TIME_LORD);
        this.power = new MageInt(1);
        this.toughness = new MageInt(1);

        // If you would planeswalk, instead look at the top two cards of your planar deck, put one on the bottom of
        // your planar deck and the other on top, then planeswalk.
        this.addAbility(new SimpleStaticAbility(new SusanForemanPlaneswalkEffect()));

        // {T}: Add {G}.
        this.addAbility(new GreenManaAbility());

        // Doctor's companion
        this.addAbility(DoctorsCompanionAbility.getInstance());
    }

    private SusanForeman(final SusanForeman card) {
        super(card);
    }

    @Override
    public SusanForeman copy() {
        return new SusanForeman(this);
    }
}

class SusanForemanPlaneswalkEffect extends ReplacementEffectImpl {

    SusanForemanPlaneswalkEffect() {
        super(Duration.WhileOnBattlefield, Outcome.Neutral);
        staticText = "if you would planeswalk, instead look at the top two cards of your planar deck, "
                + "put one on the bottom of your planar deck and the other on top, then planeswalk";
    }

    private SusanForemanPlaneswalkEffect(final SusanForemanPlaneswalkEffect effect) {
        super(effect);
    }

    @Override
    public SusanForemanPlaneswalkEffect copy() {
        return new SusanForemanPlaneswalkEffect(this);
    }

    @Override
    public boolean checksEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.PLANESWALK;
    }

    @Override
    public boolean applies(GameEvent event, Ability source, Game game) {
        Object plane = game.getObject(event.getTargetId());
        return plane instanceof Plane
                && ((Plane) plane).getControllerId().equals(source.getControllerId());
    }

    @Override
    public boolean replaceEvent(GameEvent event, Ability source, Game game) {
        // no planar deck exists in this engine: nothing to look at or reorder, the planeswalk goes on
        game.informPlayers(source.getSourceObject(game).getLogName()
                + ": there is no planar deck to look at, planeswalking");
        return false;
    }
}
