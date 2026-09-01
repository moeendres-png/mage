#!/usr/bin/env python3
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exact anchor once, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.forge_root.resolve()

    # Discretionary yes/no confirmations must cross the strict external decision
    # boundary rather than entering Forge's blocking legacy GUI input.
    confirm = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputConfirm.java"
    replace_once(
        confirm,
        """     public static boolean confirm(final PlayerControllerHuman controller, final CardView card, final SpellAbility sa, final String message, final boolean defaultIsYes, final List<String> options) {
         if (controller.getGui().isLibgdxPort()) {
""",
        """     public static boolean confirm(final PlayerControllerHuman controller, final CardView card, final SpellAbility sa, final String message, final boolean defaultIsYes, final List<String> options) {
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
""",
        "InputConfirm external decision",
    )

    # PlayerControllerHuman.reveal() is not a discretionary rules choice.  In
    # stock Forge it temporarily grants look permission, renders a zone/dialog,
    # and blocks for an acknowledgement that can also install an auto-pass UI
    # preference.  Under an external pilot, keep only the principal-scoped
    # observation semantics: grant temporary visibility, flush the authoritative
    # principal projection through the real RemoteClientGuiGame delta transport,
    # revoke visibility, and flush the revocation.  Never invoke the GUI dialog,
    # never infer a decision, and never install an auto-pass side effect.
    human = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    replace_once(
        human,
        """    protected void reveal(final CardCollectionView cards, final ZoneType zone, final PlayerView owner, String message, boolean addSuffix) {
        yieldController.maybeInterruptOnReveal();
        if (StringUtils.isBlank(message)) {
""",
        """    protected void reveal(final CardCollectionView cards, final ZoneType zone, final PlayerView owner, String message, boolean addSuffix) {
        yieldController.maybeInterruptOnReveal();
        if (hasExternalDecisionProvider()) {
            if (!cards.isEmpty()) {
                tempShowCards(cards);
                try {
                    if (gui instanceof RemoteClientGuiGame remoteGui) {
                        remoteGui.updateGameView();
                    }
                } finally {
                    endTempShowCards();
                    if (gui instanceof RemoteClientGuiGame remoteGui) {
                        remoteGui.updateGameView();
                    }
                }
            }
            return;
        }
        if (StringUtils.isBlank(message)) {
""",
        "principal-scoped external reveal observation",
    )

    print("WS33_INPUT_CONFIRM_EXTERNALIZED=TRUE")
    print("WS33_INPUT_CONFIRM_GUI_FALLBACK_EXTERNAL_MODE=0")
    print("WS33_INPUT_CONFIRM_CARD_NAME_BRANCHES=0")
    print("WS33_REVEAL_EXTERNAL_OBSERVATION=TRUE")
    print("WS33_REVEAL_GUI_BLOCK_EXTERNAL_MODE=0")
    print("WS33_REVEAL_AUTOPASS_SIDE_EFFECT_EXTERNAL_MODE=0")
    print("WS33_REVEAL_TRANSPORT=REMOTE_CLIENT_DELTA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
