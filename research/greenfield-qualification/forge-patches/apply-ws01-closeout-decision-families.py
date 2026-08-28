#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-closeout-decision-families.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one closeout anchor, found {count}: {old[:140]!r}")
    text = text.replace(old, new, 1)


# Cost reduction is a real rules choice. The stock UI deliberately defaults to
# max unless Full Control is enabled; strict external mode must never inherit
# that UI convenience default.
replace_once(
    '''    @Override
    public int chooseNumberForCostReduction(final SpellAbility sa, final int min, final int max) {
        if (isFullControl(FullControlFlag.ChooseCostReductionOrderAndVariableAmount)) {
''',
    '''    @Override
    public int chooseNumberForCostReduction(final SpellAbility sa, final int min, final int max) {
        if (hasExternalDecisionProvider()) {
            return chooseNumber(sa, "external cost reduction", min, max);
        }
        if (isFullControl(FullControlFlag.ChooseCostReductionOrderAndVariableAmount)) {
''')

# Macro memory is a client convenience, not an external-pilot decision. Route
# strict color choices through the exact current ColorSet before consulting it.
replace_once(
    '''    private byte chooseColorCommon(final String message, final Card c, final ColorSet colors,
                                   final boolean withColorless) {
        List<MagicColor.Color> choices = Lists.newArrayList(colors.getOrderedColors());
        if (withColorless && !colors.isColorless()) {
            choices.add(MagicColor.Color.COLORLESS);
        }
        final Byte remembered = macros().consumeRememberedColorChoice(choices);
''',
    '''    private byte chooseColorCommon(final String message, final Card c, final ColorSet colors,
                                   final boolean withColorless) {
        List<MagicColor.Color> choices = Lists.newArrayList(colors.getOrderedColors());
        if (withColorless && !colors.isColorless()) {
            choices.add(MagicColor.Color.COLORLESS);
        }
        if (hasExternalDecisionProvider()) {
            return chooseExternalDiscrete(choices, 1, 1, false, false,
                    "COLOR_SELECTION", color -> String.valueOf(color.getColorMask())).get(0).getColorMask();
        }
        final Byte remembered = macros().consumeRememberedColorChoice(choices);
''')

# Simultaneous trigger ordering is discretionary. In strict mode repeatedly
# choose one member of the authoritative remaining list; no remembered GUI order
# may bypass the current pilot.
replace_once(
    '''    @Override
    public List<SpellAbility> orderSimultaneousSa(List<SpellAbility> activePlayerSAs) {
        if (activePlayerSAs.size() < 2)
''',
    '''    @Override
    public List<SpellAbility> orderSimultaneousSa(List<SpellAbility> activePlayerSAs) {
        if (hasExternalDecisionProvider() && activePlayerSAs.size() > 1) {
            final List<SpellAbility> remaining = new ArrayList<>(activePlayerSAs);
            final List<SpellAbility> ordered = new ArrayList<>(activePlayerSAs.size());
            while (!remaining.isEmpty()) {
                final SpellAbility selected = chooseExternalDiscrete(remaining, 1, 1, false, false,
                        "SIMULTANEOUS_ABILITY_ORDER",
                        ability -> "spellability:" + ability.getId()).get(0);
                ordered.add(selected);
                remaining.remove(selected);
            }
            return ordered;
        }
        if (activePlayerSAs.size() < 2)
''')

# The stock divided-as-you-choose dialog requires at least one unit on every
# chosen target. Preserve that server-side: reserve one for each already legal
# target, then externalize each remaining unit over targets with capacity left.
old = '''                final CardView vSource = CardView.get(currentAbility.getHostCard());
                final Map<Object, Integer> vTargets = new HashMap<>(size);
                for (GameEntity e : targets) {
                    vTargets.put(GameEntityView.get(e), amount);
                }
                final Map<Object, Integer> vResult = getGui().assignGenericAmount(vSource, vTargets, amount, true, label);
                for (GameEntity e : targets) {
                    currentAbility.addDividedAllocation(e, vResult.get(GameEntityView.get(e)));
                }
                if (currentAbility.getStillToDivide() > 0) {
                    return false;
                }
'''
new = '''                if (hasExternalDecisionProvider()) {
                    final Map<GameEntity, Integer> extraCapacities = new LinkedHashMap<>();
                    for (GameEntity e : targets) {
                        extraCapacities.put(e, amount - 1);
                    }
                    final int extraAmount = amount - size;
                    final Map<GameEntity, Integer> extras = chooseExternalAllocation(
                            extraCapacities, extraAmount, "DIVIDED_TARGET_ALLOCATION",
                            ExternalDecisionRequest::optionIdFor);
                    for (GameEntity e : targets) {
                        currentAbility.addDividedAllocation(e, 1 + extras.get(e));
                    }
                } else {
                    final CardView vSource = CardView.get(currentAbility.getHostCard());
                    final Map<Object, Integer> vTargets = new HashMap<>(size);
                    for (GameEntity e : targets) {
                        vTargets.put(GameEntityView.get(e), amount);
                    }
                    final Map<Object, Integer> vResult = getGui().assignGenericAmount(vSource, vTargets, amount, true, label);
                    for (GameEntity e : targets) {
                        currentAbility.addDividedAllocation(e, vResult.get(GameEntityView.get(e)));
                    }
                }
                if (currentAbility.getStillToDivide() > 0) {
                    return false;
                }
'''
replace_once(old, new)

path.write_text(text, encoding="utf-8")
print("WS01_CLOSEOUT_DECISION_FAMILIES_APPLIED=TRUE")
