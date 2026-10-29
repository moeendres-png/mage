package mage.cards.r;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.abilities.effects.common.ExileTopXMayPlayUntilEffect;
import mage.abilities.effects.common.LoseLifeSourceControllerEffect;
import mage.abilities.keyword.ConspireAbility;
import mage.abilities.triggers.BeginningOfUpkeepTriggeredAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.Outcome;
import mage.constants.SubLayer;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.stack.Spell;
import mage.game.stack.StackObject;

import java.util.UUID;

/**
 * Rassilon, the War President {3}{U}{B}
 * Legendary Creature -- Time Lord Noble 3/4
 * At the beginning of your upkeep, you lose 2 life and exile the top card of your library.
 * You may play that card for as long as it remains exiled.
 * Each noncreature spell you cast from exile has conspire.
 */
public final class RassilonTheWarPresident extends CardImpl {

    public RassilonTheWarPresident(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{3}{U}{B}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.TIME_LORD);
        this.subtype.add(SubType.NOBLE);
        this.power = new MageInt(3);
        this.toughness = new MageInt(4);

        // At the beginning of your upkeep, you lose 2 life and exile the top card of your library.
        // You may play that card for as long as it remains exiled.
        Ability ability = new BeginningOfUpkeepTriggeredAbility(new LoseLifeSourceControllerEffect(2));
        ability.addEffect(new ExileTopXMayPlayUntilEffect(1, Duration.Custom).concatBy("and"));
        this.addAbility(ability);

        // Each noncreature spell you cast from exile has conspire.
        this.addAbility(new SimpleStaticAbility(new RassilonGainConspireEffect()));
    }

    private RassilonTheWarPresident(final RassilonTheWarPresident card) {
        super(card);
    }

    @Override
    public RassilonTheWarPresident copy() {
        return new RassilonTheWarPresident(this);
    }
}

class RassilonGainConspireEffect extends ContinuousEffectImpl {

    private final ConspireAbility conspireAbility;

    RassilonGainConspireEffect() {
        super(Duration.WhileOnBattlefield, Layer.AbilityAddingRemovingEffects_6, SubLayer.NA, Outcome.AddAbility);
        staticText = "each noncreature spell you cast from exile has conspire. <i>(As you cast the spell, you may tap two "
                + "untapped creatures you control that share a color with it. When you do, copy it and you may choose "
                + "new targets for the copy.)</i>";
        this.conspireAbility = new ConspireAbility(ConspireAbility.ConspireTargets.MORE);
    }

    private RassilonGainConspireEffect(final RassilonGainConspireEffect effect) {
        super(effect);
        this.conspireAbility = effect.conspireAbility;
    }

    @Override
    public RassilonGainConspireEffect copy() {
        return new RassilonGainConspireEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        for (StackObject stackObject : game.getStack()) {
            if (!(stackObject instanceof Spell) || !stackObject.isControlledBy(source.getControllerId())) {
                continue;
            }
            Spell spell = (Spell) stackObject;
            if (spell.wasCast()
                    && spell.getFromZone() == Zone.EXILED
                    && !spell.isCreature(game)) {
                game.getState().addOtherAbility(spell.getCard(), conspireAbility.setAddedById(source.getSourceId()));
            }
        }
        return true;
    }
}
