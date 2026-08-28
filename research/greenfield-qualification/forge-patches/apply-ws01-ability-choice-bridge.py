#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-ability-choice-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
text = path.read_text(encoding="utf-8")
old = '''    public SpellAbility getAbilityToPlay(final Card hostCard, final List<SpellAbility> abilities,
                                         final ITriggerEvent triggerEvent) {
        spellViewCache = SpellAbilityView.getMap(abilities);
'''
new = '''    public SpellAbility getAbilityToPlay(final Card hostCard, final List<SpellAbility> abilities,
                                         final ITriggerEvent triggerEvent) {
        if (hasExternalDecisionProvider()) {
            if (abilities == null || abilities.isEmpty()) {
                return null;
            }
            final List<SpellAbility> legal = new ArrayList<>();
            for (final SpellAbility ability : abilities) {
                if (ability == null) {
                    continue;
                }
                if (ability.getActivatingPlayer() == null) {
                    ability.setActivatingPlayer(player);
                }
                // The caller supplies an authoritative candidate list. Re-check
                // current Forge play restrictions before exporting each option so
                // a stale GUI-era menu entry cannot cross the strict boundary.
                if (ability.canPlay(true)) {
                    legal.add(ability);
                }
            }
            if (legal.isEmpty()) {
                return null;
            }
            if (legal.size() == 1) {
                return legal.get(0);
            }
            final List<SpellAbility> selected = chooseExternalDiscrete(legal, 0, 1, true, false,
                    "ABILITY_TO_PLAY", ability -> "spellability:" + ability.getId());
            return selected.isEmpty() ? null : selected.get(0);
        }
        spellViewCache = SpellAbilityView.getMap(abilities);
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one getAbilityToPlay anchor, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("WS01_ABILITY_CHOICE_BRIDGE_APPLIED=TRUE")
