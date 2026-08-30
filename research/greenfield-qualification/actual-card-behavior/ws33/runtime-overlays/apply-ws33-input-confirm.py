#!/usr/bin/env python3
from pathlib import Path
import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    path = args.forge_root.resolve() / "forge-gui/src/main/java/forge/gamemodes/match/input/InputConfirm.java"
    text = path.read_text(encoding="utf-8")
    old = """     public static boolean confirm(final PlayerControllerHuman controller, final CardView card, final SpellAbility sa, final String message, final boolean defaultIsYes, final List<String> options) {
         if (controller.getGui().isLibgdxPort()) {
"""
    new = """     public static boolean confirm(final PlayerControllerHuman controller, final CardView card, final SpellAbility sa, final String message, final boolean defaultIsYes, final List<String> options) {
         if (controller.hasExternalDecisionProvider()) {
             if (options == null || options.size() != 2 || options.get(0) == null || options.get(1) == null
                     || options.get(0).equals(options.get(1))) {
                 throw new ExternalDecisionValidationException(
                         ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                         \"INPUT_CONFIRM requires two distinct authoritative options\");
             }
             final List<String> selected = controller.chooseExternalUiOptions(options, 1, 1,
                     false, false, \"INPUT_CONFIRM\",
                     option -> option.equals(options.get(0)) ? \"AFFIRM\" : \"DECLINE\");
             return selected.get(0).equals(options.get(0));
         }
         if (controller.getGui().isLibgdxPort()) {
"""
    if text.count(old) != 1:
        raise SystemExit(f"expected exact InputConfirm anchor once, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("WS33_INPUT_CONFIRM_EXTERNALIZED=TRUE")
    print("WS33_INPUT_CONFIRM_GUI_FALLBACK_EXTERNAL_MODE=0")
    print("WS33_INPUT_CONFIRM_CARD_NAME_BRANCHES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
