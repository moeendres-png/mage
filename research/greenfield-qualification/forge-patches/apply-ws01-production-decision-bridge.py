#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-production-decision-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one bridge anchor, found {count}: {old[:100]!r}")
    text = text.replace(old, new, 1)


def replace_file_once(file_path: Path, old: str, new: str) -> None:
    value = file_path.read_text(encoding="utf-8")
    count = value.count(old)
    if count != 1:
        raise SystemExit(f"expected one bridge anchor in {file_path}, found {count}: {old[:100]!r}")
    file_path.write_text(value.replace(old, new, 1), encoding="utf-8")


replace_once(
    '''    @Override
    public void autoPassCancel() {
        if (!mayAutoPass()) {
            return;
        }
''',
    '''    @Override
    public void autoPassCancel() {
        if (hasExternalDecisionProvider()) {
            // Legacy GUI yield/autopass is not a game-rule decision. In strict
            // external mode every actual priority pass is exported explicitly
            // through PRIORITY_ACTION, so this UI automation must be inert.
            return;
        }
        if (!mayAutoPass()) {
            return;
        }
''')

# Generic server-owned allocation primitive. Each unit is assigned from the
# exact set of targets whose authoritative capacity has not been exhausted.
replace_once(
    '''    public boolean mayAutoPass() {
''',
    '''    private <T> Map<T, Integer> chooseExternalAllocation(final Map<T, Integer> maxima,
                                                               final int totalAmount,
                                                               final String decisionKind,
                                                               final Function<T, String> semanticValue) {
        if (totalAmount < 0 || maxima == null) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    decisionKind + " has invalid allocation bounds");
        }
        final Map<T, Integer> result = new LinkedHashMap<>();
        for (final Map.Entry<T, Integer> entry : maxima.entrySet()) {
            final Integer cap = entry.getValue();
            if (entry.getKey() == null || cap == null || cap < 0) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        decisionKind + " contains an invalid allocation target/capacity");
            }
            result.put(entry.getKey(), 0);
        }
        for (int unit = 0; unit < totalAmount; unit++) {
            final List<T> available = new ArrayList<>();
            for (final Map.Entry<T, Integer> entry : maxima.entrySet()) {
                if (result.get(entry.getKey()) < entry.getValue()) {
                    available.add(entry.getKey());
                }
            }
            if (available.isEmpty()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        decisionKind + " total exceeds authoritative capacities");
            }
            final T selected = chooseExternalDiscrete(available, 1, 1, false, false,
                    decisionKind, semanticValue).get(0);
            result.put(selected, result.get(selected) + 1);
        }
        return result;
    }

    public boolean mayAutoPass() {
''')

replace_once(
    '''        rejectExternalDecision("SHIELD_DIVISION");
''',
    '''        if (hasExternalDecisionProvider()) {
            final Map<GameEntity, Integer> maxima = new LinkedHashMap<>();
            for (final Map.Entry<GameEntity, Integer> entry : affected.entrySet()) {
                maxima.put(entry.getKey(), entry.getValue() == null ? shieldAmount : entry.getValue());
            }
            return chooseExternalAllocation(maxima, shieldAmount, "SHIELD_DIVISION",
                    ExternalDecisionRequest::optionIdFor);
        }
''')

replace_once(
    '''        rejectExternalDecision("MANA_COMBINATION");
''',
    '''        if (hasExternalDecisionProvider()) {
            final Map<MagicColor.Color, Integer> maxima = new LinkedHashMap<>();
            for (final MagicColor.Color color : colorSet.getOrderedColors()) {
                if (color != MagicColor.Color.COLORLESS) {
                    maxima.put(color, different ? 1 : manaAmount);
                }
            }
            final Map<MagicColor.Color, Integer> assigned = chooseExternalAllocation(maxima, manaAmount,
                    "MANA_COMBINATION", color -> String.valueOf(color.getColorMask()));
            final Map<Byte, Integer> result = new HashMap<>();
            for (final Map.Entry<MagicColor.Color, Integer> entry : assigned.entrySet()) {
                result.put(entry.getKey().getColorMask(), entry.getValue());
            }
            macros().addRememberedAction(new ManaComboAction(result));
            return result;
        }
''')

replace_once(
    '''        rejectExternalDecision("DECLARE_ATTACKERS");
''',
    '''        if (hasExternalDecisionProvider()) {
            final InputAttack input = new InputAttack(this, attackingPlayer, combat);
            input.startExternalSelection();
            while (true) {
                final List<String> actions = input.getExternalActionTokens();
                if (actions.isEmpty()) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                            "DECLARE_ATTACKERS has no authoritative transition");
                }
                final String action = chooseExternalDiscrete(actions, 1, 1, false, false,
                        "DECLARE_ATTACKERS", Function.identity()).get(0);
                input.applyExternalAction(action);
                if ("DONE".equals(action)) {
                    return;
                }
            }
        }
''')

replace_once(
    '''        rejectExternalDecision("DECLARE_BLOCKERS");
''',
    '''        if (hasExternalDecisionProvider()) {
            final InputBlock input = new InputBlock(this, defender, combat);
            input.startExternalSelection();
            while (true) {
                final List<String> actions = input.getExternalActionTokens();
                if (actions.isEmpty()) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                            "DECLARE_BLOCKERS has no authoritative transition");
                }
                final String action = chooseExternalDiscrete(actions, 1, 1, false, false,
                        "DECLARE_BLOCKERS", Function.identity()).get(0);
                input.applyExternalAction(action);
                if ("DONE".equals(action)) {
                    return;
                }
            }
        }
''')

path.write_text(text, encoding="utf-8")

# InputAttack remains the authority for attack legality and combat mutation.
attack = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputAttack.java"
replace_file_once(
    attack,
    '''    @Override
    public final void showMessage() {
''',
    '''    public void startExternalSelection() {
        if (currentDefender == null) {
            currentDefender = defenders.getFirst();
            if (currentDefender == null) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "DECLARE_ATTACKERS has no defender");
            }
            potentialBanding = isBandingPossible();
        }
    }

    public List<String> getExternalActionTokens() {
        startExternalSelection();
        final Set<String> actions = new java.util.LinkedHashSet<>();
        actions.add("DONE");
        actions.add("RESET_OR_ALPHA");
        for (final GameEntity defender : defenders) {
            if (defender instanceof Player p && defender != currentDefender) {
                actions.add("PLAYER:" + p.getId());
            } else if (defender instanceof Card c && getActivateAction(c) != null) {
                actions.add("CARD:" + c.getId());
            }
        }
        for (final Card card : playerAttacks.getCardsIn(ZoneType.Battlefield)) {
            if (getActivateAction(card) != null) {
                actions.add("CARD:" + card.getId());
            }
        }
        return new ArrayList<>(actions);
    }

    public void applyExternalAction(final String action) {
        if ("DONE".equals(action)) {
            onOk();
            return;
        }
        if ("RESET_OR_ALPHA".equals(action)) {
            onCancel();
            return;
        }
        if (action != null && action.startsWith("PLAYER:")) {
            final int id;
            try {
                id = Integer.parseInt(action.substring("PLAYER:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "invalid attacker defender token");
            }
            for (final GameEntity defender : defenders) {
                if (defender instanceof Player p && p.getId() == id && defender != currentDefender) {
                    onPlayerSelected(p, null);
                    return;
                }
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "stale attacker defender token");
        }
        if (action != null && action.startsWith("CARD:")) {
            final int id;
            try {
                id = Integer.parseInt(action.substring("CARD:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "invalid attacker card token");
            }
            Card selected = null;
            for (final GameEntity defender : defenders) {
                if (defender instanceof Card c && c.getId() == id) {
                    selected = c;
                    break;
                }
            }
            if (selected == null) {
                for (final Card card : playerAttacks.getCardsIn(ZoneType.Battlefield)) {
                    if (card.getId() == id) {
                        selected = card;
                        break;
                    }
                }
            }
            if (selected == null || getActivateAction(selected) == null
                    || !onCardSelected(selected, null, null)) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "stale attacker card token");
            }
            return;
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "unknown attacker action token");
    }

    @Override
    public final void showMessage() {
''')

# InputBlock remains the authority for canBlock/validateBlocks and combat mutation.
block = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputBlock.java"
replace_file_once(
    block,
    '''                if (CombatUtil.canBlock(attacker, c, combat)) {
                    //must set current attacker on EDT
                    FThreads.invokeInEdtNowOrLater(() -> setCurrentAttacker(attacker));
                    return;
                }
''',
    '''                if (CombatUtil.canBlock(attacker, c, combat)) {
                    if (controller.hasExternalDecisionProvider()) {
                        currentAttacker = attacker;
                    } else {
                        //must set current attacker on EDT
                        FThreads.invokeInEdtNowOrLater(() -> setCurrentAttacker(attacker));
                    }
                    return;
                }
''')
replace_file_once(
    block,
    '''    /** {@inheritDoc} */
    @Override
    protected final void showMessage() {
''',
    '''    public void startExternalSelection() {
        if (currentAttacker != null) {
            return;
        }
        for (final Card attacker : combat.getAttackers()) {
            for (final Card candidate : defender.getCreaturesInPlay()) {
                if (CombatUtil.canBlock(attacker, candidate, combat)) {
                    currentAttacker = attacker;
                    return;
                }
            }
        }
    }

    public List<String> getExternalActionTokens() {
        startExternalSelection();
        final List<String> actions = new java.util.ArrayList<>();
        if (CombatUtil.validateBlocks(combat, defender) == null) {
            actions.add("DONE");
        }
        for (final Card attacker : combat.getAttackers()) {
            actions.add("ATTACKER:" + attacker.getId());
        }
        if (currentAttacker != null) {
            for (final Card blocker : defender.getCreaturesInPlay()) {
                if (combat.isBlocking(blocker, currentAttacker)
                        || CombatUtil.canBlock(currentAttacker, blocker, combat)) {
                    actions.add("BLOCKER:" + blocker.getId());
                }
            }
        }
        return actions;
    }

    public void applyExternalAction(final String action) {
        if ("DONE".equals(action)) {
            if (CombatUtil.validateBlocks(combat, defender) != null) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "block declaration is not complete");
            }
            onOk();
            return;
        }
        if (action != null && action.startsWith("ATTACKER:")) {
            final int id;
            try {
                id = Integer.parseInt(action.substring("ATTACKER:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "invalid blocker attacker token");
            }
            for (final Card attacker : combat.getAttackers()) {
                if (attacker.getId() == id) {
                    setCurrentAttacker(attacker);
                    return;
                }
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "stale blocker attacker token");
        }
        if (action != null && action.startsWith("BLOCKER:")) {
            final int id;
            try {
                id = Integer.parseInt(action.substring("BLOCKER:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "invalid blocker card token");
            }
            for (final Card blocker : defender.getCreaturesInPlay()) {
                if (blocker.getId() == id && currentAttacker != null
                        && (combat.isBlocking(blocker, currentAttacker)
                        || CombatUtil.canBlock(currentAttacker, blocker, combat))) {
                    if (!onCardSelected(blocker, null, null)) {
                        throw new ExternalDecisionValidationException(
                                ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "blocker transition rejected");
                    }
                    return;
                }
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "stale blocker card token");
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "unknown blocker action token");
    }

    /** {@inheritDoc} */
    @Override
    protected final void showMessage() {
''')

print("WS01_PRODUCTION_DECISION_BRIDGE_APPLIED=TRUE")
