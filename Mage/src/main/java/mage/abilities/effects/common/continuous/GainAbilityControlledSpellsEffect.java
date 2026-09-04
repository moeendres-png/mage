package mage.abilities.effects.common.continuous;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.cards.Card;
import mage.constants.*;
import mage.filter.FilterCard;
import mage.filter.common.FilterNonlandCard;
import mage.game.Game;
import mage.game.stack.Spell;
import mage.game.stack.StackObject;
import mage.players.Player;
import mage.target.targetpointer.FixedTarget;
import mage.util.CardUtil;

import java.util.HashSet;
import java.util.Set;

/**
 * @author Styxo
 */
public class GainAbilityControlledSpellsEffect extends ContinuousEffectImpl {

    private final Ability ability;
    private final FilterCard filter;

    // null = preserve historical behavior and grant in all supported zones
    private final Zone castFromZone;

    // Rule 610.5-style support for abilities gained "as you cast":
    // keep the gained ability on the permanent the spell becomes.
    private final boolean persistThroughResolution;

    // Prevent creating the card-to-permanent bridge more than once for the
    // same spell during repeated continuous-effect rebuilds.
    private final Set<MageObjectReference> bridgedSpells = new HashSet<>();

    public GainAbilityControlledSpellsEffect(Ability ability, FilterNonlandCard filter) {
        this(ability, filter, null, false);
    }

    public GainAbilityControlledSpellsEffect(
            Ability ability,
            FilterCard filter,
            Zone castFromZone,
            boolean persistThroughResolution
    ) {
        super(
                Duration.WhileOnBattlefield,
                Layer.AbilityAddingRemovingEffects_6,
                SubLayer.NA,
                Outcome.AddAbility
        );
        this.ability = ability;
        this.filter = filter;
        this.castFromZone = castFromZone;
        this.persistThroughResolution = persistThroughResolution;

        String verb = persistThroughResolution ? " gain " : " have ";
        String suffix = persistThroughResolution ? " as you cast them" : "";

        staticText = filter.getMessage()
                + verb
                + CardUtil.getTextWithFirstCharLowerCase(
                        CardUtil.stripReminderText(ability.getRule())
                )
                + suffix;
    }

    private GainAbilityControlledSpellsEffect(
            final GainAbilityControlledSpellsEffect effect
    ) {
        super(effect);
        this.ability = effect.ability;
        this.filter = effect.filter;
        this.castFromZone = effect.castFromZone;
        this.persistThroughResolution = effect.persistThroughResolution;
        this.bridgedSpells.addAll(effect.bridgedSpells);
    }

    @Override
    public GainAbilityControlledSpellsEffect copy() {
        return new GainAbilityControlledSpellsEffect(this);
    }

    private boolean appliesInZone(Zone zone) {
        return castFromZone == null || castFromZone == zone;
    }

    private void addAbilityToCard(Card card, Player player, Ability source, Game game) {
        if (filter.match(card, player.getId(), source, game)) {
            game.getState().addOtherAbility(card, ability);
        }
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player player = game.getPlayer(source.getControllerId());

        if (player == null) {
            return false;
        }

        if (appliesInZone(Zone.EXILED)) {
            for (Card card : game.getExile().getCardsInRange(
                    game,
                    source.getControllerId()
            )) {
                addAbilityToCard(card, player, source, game);
            }
        }

        if (appliesInZone(Zone.LIBRARY)) {
            for (Card card : player.getLibrary().getCards(game)) {
                addAbilityToCard(card, player, source, game);
            }
        }

        if (appliesInZone(Zone.HAND)) {
            for (Card card : player.getHand().getCards(game)) {
                addAbilityToCard(card, player, source, game);
            }
        }

        if (appliesInZone(Zone.GRAVEYARD)) {
            for (Card card : player.getGraveyard().getCards(game)) {
                addAbilityToCard(card, player, source, game);
            }
        }

        // Workaround to gain cost-reduction / alternative-cost abilities
        // to commanders before cast.
        if (appliesInZone(Zone.COMMAND)) {
            game.getCommanderCardsFromCommandZone(
                            player,
                            CommanderCardType.ANY
                    )
                    .stream()
                    .filter(card -> filter.match(
                            card,
                            player.getId(),
                            source,
                            game
                    ))
                    .forEach(card ->
                            game.getState().addOtherAbility(card, ability)
                    );
        }

        for (StackObject stackObject : game.getStack()) {
            if (!(stackObject instanceof Spell)
                    || !stackObject.isControlledBy(source.getControllerId())) {
                continue;
            }

            Spell spell = (Spell) stackObject;

            if (castFromZone != null && spell.getFromZone() != castFromZone) {
                continue;
            }

            Card card = game.getCard(stackObject.getSourceId());

            if (card == null
                    || !filter.match(
                            spell,
                            player.getId(),
                            source,
                            game
                    )) {
                continue;
            }

            // TODO: Distinguish "you cast" to exclude copies.
            game.getState().addOtherAbility(card, ability);

            if (!persistThroughResolution || !card.isPermanent()) {
                continue;
            }

            MageObjectReference spellCardMOR =
                    new MageObjectReference(card, game);

            if (!bridgedSpells.add(spellCardMOR)) {
                continue;
            }

            // Existing XMage card-to-permanent bridge pattern:
            // keep granting the ability to this card while it is a spell,
            // then to the permanent that card becomes.
            GainAbilityTargetEffect bridge =
                    new CastPersistentGainAbilityTargetEffect(ability);

            bridge.setTargetPointer(new FixedTarget(card, game));
            game.addEffect(bridge, source);
        }

        return true;
    }
    /**
     * Rule 610.5-style bridge for an ability gained as a spell is cast.
     *
     * GainAbilityTargetEffect normally determines whether its affected
     * objects are static from the type of the source ability. Ashling's
     * source is a StaticAbility, but the object that has already been cast
     * must be locked in at this point and followed through resolution.
     *
     * Force the static-object path so GainAbilityTargetEffect can use its
     * existing card -> permanent waiting mechanism.
     */
    private static final class CastPersistentGainAbilityTargetEffect
            extends GainAbilityTargetEffect {

        private CastPersistentGainAbilityTargetEffect(Ability ability) {
            super(ability, Duration.Custom, null, true);
        }

        private CastPersistentGainAbilityTargetEffect(
                final CastPersistentGainAbilityTargetEffect effect
        ) {
            super(effect);
        }

        @Override
        public void init(Ability source, Game game) {
            setAffectedObjectsSet(true);
            super.init(source, game);
        }

        @Override
        public CastPersistentGainAbilityTargetEffect copy() {
            return new CastPersistentGainAbilityTargetEffect(this);
        }
    }
}
