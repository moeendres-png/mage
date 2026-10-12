package mage.cards.k;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.DealsCombatDamageToAPlayerTriggeredAbility;
import mage.abilities.effects.ContinuousEffect;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.continuous.GainAbilitySourceEffect;
import mage.abilities.effects.common.asthought.MayLookAtTargetCardEffect;
import mage.abilities.keyword.DeathtouchAbility;
import mage.abilities.keyword.IndestructibleAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.stack.Spell;
import mage.players.Player;
import mage.target.targetpointer.FixedTarget;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class KlawMasterOfSound extends CardImpl {

    public KlawMasterOfSound(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{B}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.ELEMENTAL);
        this.subtype.add(SubType.ROGUE);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(3);
        this.toughness = new MageInt(3);

        // Deathtouch
        this.addAbility(DeathtouchAbility.getInstance());

        // Whenever you play a card from exile, Klaw gains indestructible until end of turn.
        this.addAbility(new KlawMasterOfSoundTriggeredAbility());

        // Whenever Klaw deals combat damage to a player, look at the top card of that player's library, then exile it face down. You may play it for as long as it remains exiled. Mana of any type can be spent to cast a spell this way.
        this.addAbility(new DealsCombatDamageToAPlayerTriggeredAbility(new KlawMasterOfSoundEffect(), false, true));
    }

    private KlawMasterOfSound(final KlawMasterOfSound card) {
        super(card);
    }

    @Override
    public KlawMasterOfSound copy() {
        return new KlawMasterOfSound(this);
    }
}

class KlawMasterOfSoundTriggeredAbility extends TriggeredAbilityImpl {

    KlawMasterOfSoundTriggeredAbility() {
        super(Zone.BATTLEFIELD, new GainAbilitySourceEffect(IndestructibleAbility.getInstance(), Duration.EndOfTurn), false);
        setTriggerPhrase("Whenever you play a card from exile, ");
    }

    private KlawMasterOfSoundTriggeredAbility(final KlawMasterOfSoundTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public KlawMasterOfSoundTriggeredAbility copy() {
        return new KlawMasterOfSoundTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.SPELL_CAST
                || event.getType() == GameEvent.EventType.LAND_PLAYED;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getPlayerId())) {
            return false;
        }
        if (event.getType() == GameEvent.EventType.LAND_PLAYED) {
            return event.getZone() == Zone.EXILED;
        }
        Spell spell = game.getSpell(event.getTargetId());
        return spell != null && spell.getFromZone() == Zone.EXILED;
    }
}

class KlawMasterOfSoundEffect extends OneShotEffect {

    KlawMasterOfSoundEffect() {
        super(Outcome.Exile);
        staticText = "look at the top card of that player's library, then exile it face down. "
                + "You may play it for as long as it remains exiled. "
                + "Mana of any type can be spent to cast a spell this way";
    }

    private KlawMasterOfSoundEffect(final KlawMasterOfSoundEffect effect) {
        super(effect);
    }

    @Override
    public KlawMasterOfSoundEffect copy() {
        return new KlawMasterOfSoundEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Player damagedPlayer = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (controller == null || damagedPlayer == null) {
            return false;
        }
        Card card = damagedPlayer.getLibrary().getFromTop(game);
        if (card == null) {
            return false;
        }
        controller.lookAtCards(source, null, new mage.cards.CardsImpl(card), game);
        UUID exileZoneId = CardUtil.getExileZoneId(game, source);
        String exileName = CardUtil.getSourceName(game, source);
        if (controller.moveCardsToExile(card, source, game, false, exileZoneId, exileName)) {
            card.setFaceDown(true, game);
            CardUtil.makeCardPlayable(game, source, card, false, Duration.Custom, true, controller.getId(), null);
            ContinuousEffect effect = new MayLookAtTargetCardEffect(controller.getId());
            effect.setTargetPointer(new FixedTarget(card.getId(), game));
            game.addEffect(effect, source);
        }
        return true;
    }
}
