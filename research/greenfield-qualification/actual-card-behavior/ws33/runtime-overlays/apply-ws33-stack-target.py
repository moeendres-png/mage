#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one WS33 stack-target anchor in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    target = args.forge_root.resolve() / "forge-gui/src/main/java/forge/player/TargetSelection.java"

    replace_once(
        target,
        "import forge.gamemodes.match.input.InputSelectTargets;\n",
        "import forge.gamemodes.match.input.ExternalDecisionValidationException;\n"
        "import forge.gamemodes.match.input.InputSelectTargets;\n",
    )
    replace_once(
        target,
        """        while (!bTargetingDone) {
            if (ability.isMaxTargetChosen() || (numTargets != null && ability.getTargets().size() == numTargets)) {
""",
        """        if (controller.hasExternalDecisionProvider()) {
            while (!bTargetingDone) {
                if (ability.isMaxTargetChosen()
                        || (numTargets != null && ability.getTargets().size() == numTargets)) {
                    bTargetingDone = true;
                    return true;
                }
                final List<String> actions = new ArrayList<>();
                if (ability.isMinTargetChosen()
                        && (numTargets == null || ability.getTargets().size() == numTargets)) {
                    actions.add("DONE");
                }
                if (!mandatory) {
                    actions.add("CANCEL");
                }
                for (final Map.Entry<StackItemView, SpellAbilityStackInstance> entry : stackItemViewCache.entrySet()) {
                    final SpellAbility candidate = entry.getValue().getSpellAbility();
                    if (!ability.isTargeting(candidate) && ability.canTargetSpellAbility(candidate)) {
                        actions.add("STACK:" + candidate.getId());
                    }
                }
                if (actions.isEmpty()) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                            "STACK_TARGET_SELECTION has no authoritative transition");
                }
                final String action = controller.chooseExternalUiOptions(
                        actions, 1, 1, false, false, "STACK_TARGET_SELECTION", value -> value).get(0);
                if ("DONE".equals(action)) {
                    bTargetingDone = true;
                    return true;
                }
                if ("CANCEL".equals(action)) {
                    return false;
                }
                if (!action.startsWith("STACK:")) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "unknown stack target action token");
                }
                final int id;
                try {
                    id = Integer.parseInt(action.substring("STACK:".length()));
                } catch (RuntimeException error) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "invalid stack target token");
                }
                SpellAbility selected = null;
                for (final SpellAbilityStackInstance instance : stackItemViewCache.values()) {
                    final SpellAbility candidate = instance.getSpellAbility();
                    if (candidate.getId() == id && !ability.isTargeting(candidate)
                            && ability.canTargetSpellAbility(candidate)) {
                        selected = candidate;
                        break;
                    }
                }
                if (selected == null) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "stale stack target token");
                }
                ability.getTargets().add(selected);
            }
        }

        while (!bTargetingDone) {
            if (ability.isMaxTargetChosen() || (numTargets != null && ability.getTargets().size() == numTargets)) {
""",
    )
    print("WS33_STACK_TARGET_EXTERNALIZATION_APPLIED=TRUE")


if __name__ == "__main__":
    main()
