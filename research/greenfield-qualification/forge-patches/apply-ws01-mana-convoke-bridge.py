#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-mana-convoke-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one mana/convoke anchor in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


mana = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java"
replace_once(
    mana,
    "import forge.game.mana.ManaCostBeingPaid;\n",
    "import forge.game.mana.Mana;\nimport forge.game.mana.ManaCostBeingPaid;\n")
replace_once(
    mana,
    '''    protected boolean isAlreadyPaid() {
''',
    '''    public void driveExternal() {
        while (!isAlreadyPaid()) {
            byte colorCanUse = 0;
            for (final byte color : ManaAtom.MANATYPES) {
                if (manaCost.isAnyPartPayableWith(color, player.getManaPool())) {
                    colorCanUse |= color;
                }
            }
            if (manaCost.isAnyPartPayableWith((byte) ManaAtom.GENERIC, player.getManaPool())) {
                colorCanUse |= ManaAtom.GENERIC;
            }

            final List<String> actions = new ArrayList<>();
            final Map<String, Mana> poolChoices = new LinkedHashMap<>();
            int poolIndex = 0;
            for (final Mana floating : player.getManaPool()) {
                if (floating.meetsManaRestrictions(saPaidFor)
                        && saPaidFor.allowsPayingWithShard(floating.getSourceCard(), floating.getColor())
                        && manaCost.isNeeded(floating, player.getManaPool())) {
                    final String token = "POOL:" + poolIndex++;
                    poolChoices.put(token, floating);
                    actions.add(token);
                }
            }

            final Map<String, SpellAbility> abilityChoices = new LinkedHashMap<>();
            int abilityIndex = 0;
            if (colorCanUse != 0) {
                for (final Card card : game.getCardsInGame()) {
                    for (final SpellAbility ability : getAllManaAbilities(card)) {
                        ability.setActivatingPlayer(player);
                        if (!ability.isManaAbilityFor(saPaidFor, colorCanUse)) {
                            continue;
                        }
                        final String token = "ABILITY:" + abilityIndex++;
                        abilityChoices.put(token, ability);
                        actions.add(token);
                    }
                }
            }

            final boolean lifeAlternative = player.canPayLife(phyLifeToLose + 2, effect, saPaidFor)
                    && (manaCost.containsPhyrexianMana()
                    || (player.hasKeyword("PayLifeInsteadOf:B") && manaCost.hasAnyKind(ManaAtom.BLACK)));
            if (lifeAlternative) {
                actions.add("LIFE");
            }
            if (!mandatory) {
                actions.add("CANCEL");
            }
            if (actions.isEmpty()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "MANA_PAYMENT has no authoritative transition");
            }

            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,
                    "MANA_PAYMENT", value -> value).get(0);
            if ("CANCEL".equals(action)) {
                if (mandatory) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED,
                            "mandatory mana payment cannot cancel");
                }
                onCancel();
                return;
            }
            if ("LIFE".equals(action)) {
                if (!lifeAlternative) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "life payment became unavailable");
                }
                final String before = manaCost.toString();
                onPlayerSelected(player, null);
                if (before.equals(manaCost.toString())) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "life payment did not satisfy a payable shard");
                }
                continue;
            }
            final Mana selectedMana = poolChoices.get(action);
            if (selectedMana != null) {
                if (!selectedMana.meetsManaRestrictions(saPaidFor)
                        || !saPaidFor.allowsPayingWithShard(selectedMana.getSourceCard(), selectedMana.getColor())
                        || !manaCost.isNeeded(selectedMana, player.getManaPool())
                        || !player.getManaPool().tryPayCostWithMana(saPaidFor, manaCost, selectedMana, false)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "floating mana choice became stale");
                }
                saPaidFor.getPayingMana().add(selectedMana);
                getController().macros().addRememberedAction(new PayManaFromPoolAction(selectedMana.getColor()));
                onStateChanged();
                continue;
            }
            final SpellAbility selectedAbility = abilityChoices.get(action);
            if (selectedAbility != null) {
                if (!selectedAbility.canPlay(true) || !selectedAbility.isManaAbilityFor(saPaidFor, colorCanUse)
                        || !activateManaAbility(selectedAbility.getHostCard(), selectedAbility)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "mana ability choice became stale");
                }
                continue;
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "unknown mana payment action token");
        }
    }

    protected boolean isAlreadyPaid() {
''')
replace_once(
    mana,
    '''    @Override
    protected void onOk() {
        if (supportAutoPay() && !locked) { //prevent AI taking over from double-clicking Auto
''',
    '''    @Override
    protected void onOk() {
        if (getController().hasExternalDecisionProvider()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "AI mana autopay is forbidden in strict external mode");
        }
        if (supportAutoPay() && !locked) { //prevent AI taking over from double-clicking Auto
''')
replace_once(
    mana,
    '''    protected void onStateChanged() {
        if (isAlreadyPaid()) {
            done();
            stop();
        } else {
            FThreads.invokeInEdtNowOrLater(this::updateMessage);
        }
    }
''',
    '''    protected void onStateChanged() {
        if (isAlreadyPaid()) {
            done();
            stop();
        } else if (getController().hasExternalDecisionProvider()) {
            // The external loop owns the next decision. Never invoke the GUI
            // update path here because it computes an AI auto-pay preview.
            locked = false;
        } else {
            FThreads.invokeInEdtNowOrLater(this::updateMessage);
        }
    }
''')

convoke = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSelectCardsForConvokeOrImprovise.java"
replace_once(
    convoke,
    '''    public Map<Card, ManaCostShard> getConvokeMap() {
''',
    '''    private boolean applyExternalConvoke(final Card card, final byte color) {
        if (!availableCards.contains(card)) {
            return false;
        }
        if (chosenCards.containsKey(card)) {
            final ManaCostShard shard = chosenCards.remove(card);
            remainingCost.increaseShard(shard, 1);
            onSelectStateChanged(card, false);
            return true;
        }
        if (maxSelectable != null && chosenCards.size() >= maxSelectable) {
            return false;
        }
        final ManaCostShard shard = remainingCost.payManaViaConvoke(color);
        if (shard == null) {
            return false;
        }
        chosenCards.put(card, shard);
        onSelectStateChanged(card, true);
        return true;
    }

    private Map<String, Byte> externalConvokeActions() {
        final Map<String, Byte> actions = new LinkedHashMap<>();
        for (final Card card : availableCards) {
            if (chosenCards.containsKey(card)) {
                actions.put("UNSELECT:" + card.getId(), (byte) 0);
                continue;
            }
            if (maxSelectable != null && chosenCards.size() >= maxSelectable) {
                continue;
            }
            final List<Byte> colors = new ArrayList<>();
            if (artifacts) {
                colors.add(ManaCostShard.COLORLESS.getColorMask());
            } else {
                ColorSet available = card.getColor();
                if (available.isMulticolor()) {
                    available = ColorSet.fromMask(available.getColor() & remainingCost.getUnpaidColors());
                }
                if (available.isMulticolor()) {
                    for (final forge.card.MagicColor.Color color : available.getOrderedColors()) {
                        colors.add(color.getColorMask());
                    }
                } else {
                    colors.add(available.getColor());
                }
            }
            for (final byte color : colors) {
                final ManaCostBeingPaid copy = new ManaCostBeingPaid(remainingCost);
                if (copy.payManaViaConvoke(color) != null) {
                    actions.put("SELECT:" + card.getId() + ":" + color, color);
                }
            }
        }
        return actions;
    }

    public void driveExternal() {
        while (true) {
            final Map<String, Byte> transitions = externalConvokeActions();
            final List<String> actions = new ArrayList<>();
            actions.add("DONE");
            actions.addAll(transitions.keySet());
            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,
                    "CONVOKE_IMPROVISE_SELECTION", value -> value).get(0);
            if ("DONE".equals(action)) {
                onOk();
                return;
            }
            if (action.startsWith("UNSELECT:")) {
                final int id = Integer.parseInt(action.substring("UNSELECT:".length()));
                Card selected = null;
                for (final Card card : availableCards) {
                    if (card.getId() == id && chosenCards.containsKey(card)) {
                        selected = card;
                        break;
                    }
                }
                if (selected == null || !applyExternalConvoke(selected, (byte) 0)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "convoke unselect choice became stale");
                }
                continue;
            }
            final Byte color = transitions.get(action);
            if (color != null && action.startsWith("SELECT:")) {
                final String[] parts = action.split(":");
                if (parts.length != 3) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "malformed convoke selection token");
                }
                final int id = Integer.parseInt(parts[1]);
                Card selected = null;
                for (final Card card : availableCards) {
                    if (card.getId() == id) {
                        selected = card;
                        break;
                    }
                }
                if (selected == null || !applyExternalConvoke(selected, color)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "convoke selection choice became stale");
                }
                continue;
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "unknown convoke/improvise action token");
        }
    }

    public Map<Card, ManaCostShard> getConvokeMap() {
''')
# Existing imports use concrete collection types; add the two bridge collections.
replace_once(
    convoke,
    "import java.util.Collection;\n",
    "import java.util.ArrayList;\nimport java.util.Collection;\nimport java.util.LinkedHashMap;\n")

sync = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSyncronizedBase.java"
replace_once(
    sync,
    '''        if (getController().hasExternalDecisionProvider()) {
            if (this instanceof InputSelectEntitiesFromList<?> entitySelection) {
                entitySelection.driveExternal();
                return;
            }
            throw new ExternalDecisionValidationException(
''',
    '''        if (getController().hasExternalDecisionProvider()) {
            if (this instanceof InputPayMana manaPayment) {
                manaPayment.driveExternal();
                return;
            }
            if (this instanceof InputSelectCardsForConvokeOrImprovise convokeSelection) {
                convokeSelection.driveExternal();
                return;
            }
            if (this instanceof InputSelectEntitiesFromList<?> entitySelection) {
                entitySelection.driveExternal();
                return;
            }
            throw new ExternalDecisionValidationException(
''')

print("WS01_MANA_CONVOKE_BRIDGE_APPLIED=TRUE")
