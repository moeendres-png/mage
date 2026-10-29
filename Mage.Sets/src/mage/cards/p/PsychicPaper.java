package mage.cards.p;

import mage.abilities.Ability;
import mage.abilities.common.AsBecomesAttachedToCreatureSourceAbility;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.abilities.effects.common.ChooseACardNameEffect;
import mage.abilities.effects.common.ChooseCreatureTypeEffect;
import mage.abilities.effects.common.combat.CantBeBlockedAttachedEffect;
import mage.abilities.effects.common.continuous.GainAbilityAttachedEffect;
import mage.abilities.keyword.EquipAbility;
import mage.abilities.keyword.WardAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.*;
import mage.game.Game;
import mage.game.permanent.Permanent;

import java.util.UUID;

/**
 * Psychic Paper {2}
 * Artifact -- Equipment
 * As this Equipment becomes attached to a creature, choose a creature card name and a creature type.
 * Equipped creature has ward {1}, it can't be blocked, and its name and creature type are the last chosen
 * name and creature type.
 * Equip {2}
 */
public final class PsychicPaper extends CardImpl {

    public PsychicPaper(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{2}");

        this.subtype.add(SubType.EQUIPMENT);

        // As this Equipment becomes attached to a creature, choose a creature card name and a creature type.
        Ability choose = new AsBecomesAttachedToCreatureSourceAbility(
                new ChooseACardNameEffect(ChooseACardNameEffect.TypeOfName.CREATURE_NAME),
                "choose a creature card name and a creature type."
        );
        choose.addEffect(new ChooseCreatureTypeEffect(Outcome.Neutral));
        this.addAbility(choose);

        // Equipped creature has ward {1}, it can't be blocked, and its name and creature type are the last chosen
        // name and creature type.
        Ability ability = new SimpleStaticAbility(new GainAbilityAttachedEffect(
                new WardAbility(new GenericManaCost(1)), AttachmentType.EQUIPMENT
        ));
        ability.addEffect(new CantBeBlockedAttachedEffect(AttachmentType.EQUIPMENT).setText(", it can't be blocked,"));
        ability.addEffect(new PsychicPaperNameAndTypeEffect());
        this.addAbility(ability);

        // Equip {2}
        this.addAbility(new EquipAbility(2));
    }

    private PsychicPaper(final PsychicPaper card) {
        super(card);
    }

    @Override
    public PsychicPaper copy() {
        return new PsychicPaper(this);
    }
}

class PsychicPaperNameAndTypeEffect extends ContinuousEffectImpl {

    PsychicPaperNameAndTypeEffect() {
        super(Duration.WhileOnBattlefield, Outcome.Benefit);
        staticText = "and its name and creature type are the last chosen name and creature type";
    }

    private PsychicPaperNameAndTypeEffect(final PsychicPaperNameAndTypeEffect effect) {
        super(effect);
    }

    @Override
    public PsychicPaperNameAndTypeEffect copy() {
        return new PsychicPaperNameAndTypeEffect(this);
    }

    @Override
    public boolean apply(Layer layer, SubLayer sublayer, Ability source, Game game) {
        Permanent permanent = source.getPermanentSourceAttachedToIfItStillExists(game);
        if (permanent == null) {
            return false;
        }
        switch (layer) {
            case TextChangingEffects_3:
                Object name = game.getState().getValue(source.getSourceId().toString() + ChooseACardNameEffect.INFO_KEY);
                if (name instanceof String) {
                    permanent.setName((String) name);
                }
                break;
            case TypeChangingEffects_4:
                SubType type = ChooseCreatureTypeEffect.getChosenCreatureType(source.getSourceId(), game);
                if (type != null) {
                    permanent.removeAllCreatureTypes(game);
                    permanent.addSubType(game, type);
                }
                break;
        }
        return true;
    }

    @Override
    public boolean apply(Game game, Ability source) {
        return false;
    }

    @Override
    public boolean hasLayer(Layer layer) {
        return layer == Layer.TextChangingEffects_3 || layer == Layer.TypeChangingEffects_4;
    }
}
