package mage.cards.a;

import mage.abilities.Ability;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.AttachEffect;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.abilities.effects.common.GainLifeEffect;
import mage.abilities.keyword.EnchantAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.TargetPlayer;
import mage.target.common.TargetOpponent;
import mage.target.targetpointer.FixedTarget;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class Archnemesis extends CardImpl {

    public Archnemesis(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{1}{U}{B}");

        this.subtype.add(SubType.AURA);

        // Enchant opponent
        TargetPlayer auraTarget = new TargetOpponent();
        this.getSpellAbility().addTarget(auraTarget);
        this.getSpellAbility().addEffect(new AttachEffect(Outcome.Detriment));
        this.addAbility(new EnchantAbility(auraTarget));

        // Whenever you attack enchanted player, that player loses 2 life. You draw a card and gain 2 life.
        this.addAbility(new ArchnemesisAttackTriggeredAbility());

        // Whenever a player attacks you, you may attach this Aura to that player.
        this.addAbility(new ArchnemesisAttackedTriggeredAbility());
    }

    private Archnemesis(final Archnemesis card) {
        super(card);
    }

    @Override
    public Archnemesis copy() {
        return new Archnemesis(this);
    }
}

class ArchnemesisAttackTriggeredAbility extends TriggeredAbilityImpl {

    ArchnemesisAttackTriggeredAbility() {
        super(Zone.BATTLEFIELD, new ArchnemesisLoseLifeEffect(), false);
        addEffect(new DrawCardSourceControllerEffect(1).concatBy("You"));
        addEffect(new GainLifeEffect(2).concatBy("and"));
        setTriggerPhrase("Whenever you attack enchanted player, ");
    }

    private ArchnemesisAttackTriggeredAbility(final ArchnemesisAttackTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public ArchnemesisAttackTriggeredAbility copy() {
        return new ArchnemesisAttackTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DECLARED_ATTACKERS;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        Permanent enchantment = game.getPermanentOrLKIBattlefield(getSourceId());
        if (enchantment == null || enchantment.getAttachedTo() == null
                || !isControlledBy(game.getCombat().getAttackingPlayerId())
                || !game.getCombat().getPlayerDefenders(game, false).contains(enchantment.getAttachedTo())) {
            return false;
        }
        getEffects().setTargetPointer(new FixedTarget(enchantment.getAttachedTo()));
        return true;
    }
}

class ArchnemesisLoseLifeEffect extends OneShotEffect {

    ArchnemesisLoseLifeEffect() {
        super(Outcome.LoseLife);
        staticText = "that player loses 2 life";
    }

    private ArchnemesisLoseLifeEffect(final ArchnemesisLoseLifeEffect effect) {
        super(effect);
    }

    @Override
    public ArchnemesisLoseLifeEffect copy() {
        return new ArchnemesisLoseLifeEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player player = game.getPlayer(getTargetPointer().getFirst(game, source));
        return player != null && player.loseLife(2, game, source, false) > 0;
    }
}

class ArchnemesisAttackedTriggeredAbility extends TriggeredAbilityImpl {

    ArchnemesisAttackedTriggeredAbility() {
        super(Zone.BATTLEFIELD, new ArchnemesisAttachEffect(), true);
        setTriggerPhrase("Whenever a player attacks you, ");
    }

    private ArchnemesisAttackedTriggeredAbility(final ArchnemesisAttackedTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public ArchnemesisAttackedTriggeredAbility copy() {
        return new ArchnemesisAttackedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DECLARED_ATTACKERS;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        UUID attackingPlayerId = game.getCombat().getAttackingPlayerId();
        if (attackingPlayerId == null || isControlledBy(attackingPlayerId)
                || !game.getCombat().getPlayerDefenders(game, false).contains(getControllerId())) {
            return false;
        }
        getEffects().setTargetPointer(new FixedTarget(attackingPlayerId));
        return true;
    }
}

class ArchnemesisAttachEffect extends OneShotEffect {

    ArchnemesisAttachEffect() {
        super(Outcome.Benefit);
        staticText = "attach this Aura to that player";
    }

    private ArchnemesisAttachEffect(final ArchnemesisAttachEffect effect) {
        super(effect);
    }

    @Override
    public ArchnemesisAttachEffect copy() {
        return new ArchnemesisAttachEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent aura = source.getSourcePermanentIfItStillExists(game);
        Player newPlayer = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (aura == null || newPlayer == null || newPlayer.getId().equals(aura.getAttachedTo())
                || !game.getOpponents(source.getControllerId()).contains(newPlayer.getId())) {
            return false;
        }
        Player oldPlayer = game.getPlayer(aura.getAttachedTo());
        if (oldPlayer != null) {
            oldPlayer.removeAttachment(aura, source, game);
        }
        newPlayer.addAttachment(aura.getId(), source, game);
        game.informPlayers(aura.getLogName() + " is now attached to " + newPlayer.getLogName() + ".");
        return true;
    }
}
