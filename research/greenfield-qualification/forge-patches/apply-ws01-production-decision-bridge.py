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

# Generic server-owned allocation primitive.  Each unit is assigned from the
# exact set of targets whose authoritative capacity has not been exhausted.
# This represents every valid integer composition without an arbitrary range cap
# and never lets the pilot submit a free-form allocation map.
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

path.write_text(text, encoding="utf-8")
print("WS01_PRODUCTION_DECISION_BRIDGE_APPLIED=TRUE")
