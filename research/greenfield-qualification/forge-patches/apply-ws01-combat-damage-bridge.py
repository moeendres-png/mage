#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-combat-damage-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one combat-damage bridge anchor, found {count}: {old[:120]!r}")
    text = text.replace(old, new, 1)


replace_once(
    '''        rejectExternalDecision("COMBAT_DAMAGE_ASSIGNMENT");
''',
    '''        if (hasExternalDecisionProvider()) {
            return assignExternalCombatDamage(attacker, blockers, remaining, damageDealt, defender, overrideOrder);
        }
''')

replace_once(
    '''    private <T> Map<T, Integer> chooseExternalAllocation(final Map<T, Integer> maxima,
''',
    '''    private int externalCombatLethalDamage(final Card attacker, final Card blocker) {
        final CardView blockerView = CardView.get(blocker);
        int lethal = Math.max(0, blockerView.getLethalDamage());
        if (blockerView.getCurrentState().isPlaneswalker()) {
            lethal = Integer.parseInt(blockerView.getCurrentState().getLoyalty());
        } else if (CardView.get(attacker).getCurrentState().hasDeathtouch()) {
            lethal = Math.min(lethal, 1);
        }
        return lethal;
    }

    private Map<Card, Integer> assignExternalCombatDamage(final Card attacker,
                                                          final CardCollectionView blockers,
                                                          final CardCollectionView remaining,
                                                          final int damageDealt,
                                                          final GameEntity defender,
                                                          final boolean overrideOrder) {
        if (damageDealt < 0) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "combat damage amount cannot be negative");
        }
        final boolean divideDamage = attacker.hasKeyword(
                "You may assign CARDNAME's combat damage divided as you choose among "
                        + "defending player and/or any number of creatures they control.")
                && overrideOrder && !blockers.isEmpty();
        final boolean complex = (attacker.hasKeyword(Keyword.TRAMPLE) && defender != null)
                || blockers.size() > 1
                || divideDamage
                || (attacker.hasKeyword("Trample:Planeswalker") && defender instanceof Card);
        final Map<Card, Integer> assigned = new LinkedHashMap<>();
        if (!complex) {
            assigned.put(blockers.isEmpty() ? null : blockers.get(0), damageDealt);
            return assigned;
        }

        for (final Card blocker : blockers) {
            assigned.put(blocker, 0);
        }
        final boolean mayAssignDefender = (attacker.hasKeyword(Keyword.TRAMPLE) && defender != null)
                || divideDamage
                || (attacker.hasKeyword("Trample:Planeswalker") && defender instanceof Card);
        if (mayAssignDefender) {
            assigned.put(null, 0);
        }

        for (int point = 0; point < damageDealt; point++) {
            final List<String> legal = new ArrayList<>();
            boolean allBlockersLethal = true;
            if (overrideOrder) {
                for (final Card blocker : blockers) {
                    legal.add("CARD:" + blocker.getId());
                    if (assigned.get(blocker) < externalCombatLethalDamage(attacker, blocker)) {
                        allBlockersLethal = false;
                    }
                }
                if (mayAssignDefender && (divideDamage || allBlockersLethal)) {
                    legal.add("DEFENDER");
                }
            } else {
                for (final Card blocker : blockers) {
                    legal.add("CARD:" + blocker.getId());
                    if (assigned.get(blocker) < externalCombatLethalDamage(attacker, blocker)) {
                        allBlockersLethal = false;
                        break;
                    }
                }
                if (mayAssignDefender && allBlockersLethal) {
                    legal.add("DEFENDER");
                }
            }
            if (legal.isEmpty()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "combat damage has no authoritative assignee");
            }
            final String choice = chooseExternalDiscrete(legal, 1, 1, false, false,
                    "COMBAT_DAMAGE_ASSIGNMENT", Function.identity()).get(0);
            if ("DEFENDER".equals(choice)) {
                if (!mayAssignDefender || (!divideDamage && !allBlockersLethal)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "combat damage defender choice became stale");
                }
                assigned.put(null, assigned.get(null) + 1);
                continue;
            }
            if (!choice.startsWith("CARD:")) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                        "unknown combat damage assignee token");
            }
            final int id;
            try {
                id = Integer.parseInt(choice.substring("CARD:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                        "invalid combat damage card token");
            }
            Card selected = null;
            for (final Card blocker : blockers) {
                if (blocker.getId() == id) {
                    selected = blocker;
                    break;
                }
            }
            if (selected == null || !legal.contains("CARD:" + selected.getId())) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                        "combat damage card choice became stale");
            }
            assigned.put(selected, assigned.get(selected) + 1);
        }
        return assigned;
    }

    private <T> Map<T, Integer> chooseExternalAllocation(final Map<T, Integer> maxima,
''')

path.write_text(text, encoding="utf-8")
print("WS01_COMBAT_DAMAGE_BRIDGE_APPLIED=TRUE")
