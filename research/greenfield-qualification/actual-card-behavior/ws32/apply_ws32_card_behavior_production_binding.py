#!/usr/bin/env python3
"""Apply the generic WS32 card-behavior production verifier to exact-pin Forge.

The overlay is intentionally card-agnostic.  It adds a disabled-by-default
post-resolution verifier hook to Game/MagicStack and extends the retained WS12
outcome mapper with the dedicated typed CARD_BEHAVIOR_FAILURE mapping.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"unexpected exact-pin structure for {label}: count={count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()

    forge = args.forge_root.resolve()
    here = Path(__file__).resolve().parent
    overlay = here / "forge-overlay"

    game_java = forge / "forge-game/src/main/java/forge/game/Game.java"
    stack_java = forge / "forge-game/src/main/java/forge/game/zone/MagicStack.java"
    game_main = forge / "forge-game/src/main/java/forge/game"
    mapper_java = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/UnifiedOutcomeMapper.java"
    desktop_test = forge / "forge-gui-desktop/src/test/java/forge/gamesimulationtests"

    for path in (game_java, stack_java, mapper_java):
        if not path.exists():
            raise SystemExit(f"required exact-pin/prior-overlay source missing: {path}")

    shutil.copy2(overlay / "CardBehaviorVerifier.java", game_main / "CardBehaviorVerifier.java")
    shutil.copy2(
        overlay / "CardBehaviorVerificationException.java",
        game_main / "CardBehaviorVerificationException.java",
    )
    desktop_test.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        overlay / "Ws32CardBehaviorFailureQualificationTest.java",
        desktop_test / "Ws32CardBehaviorFailureQualificationTest.java",
    )

    game = game_java.read_text(encoding="utf-8")
    game_field_old = """    private final Game maingame;
    private final GameView view;
"""
    game_field_new = """    private final Game maingame;
    private CardBehaviorVerifier cardBehaviorVerifier;
    private final GameView view;
"""
    game = replace_once(game, game_field_old, game_field_new, "Game verifier field")

    game_getter_old = """    public int getId() {
        return this.id;
    }

"""
    game_getter_new = """    public int getId() {
        return this.id;
    }

    /**
     * Installs the simulator-owned post-resolution semantic verifier.
     * Null disables verification.  The Rules Core never supplies expected
     * card semantics itself.
     */
    public void setCardBehaviorVerifier(final CardBehaviorVerifier verifier) {
        this.cardBehaviorVerifier = verifier;
    }

    /** Invoked only from the authoritative MagicStack resolution path. */
    public void verifyResolvedCardBehavior(final SpellAbility resolvedAbility) {
        if (cardBehaviorVerifier != null) {
            cardBehaviorVerifier.verify(this, resolvedAbility);
        }
    }

"""
    game = replace_once(game, game_getter_old, game_getter_new, "Game verifier accessors")
    game_java.write_text(game, encoding="utf-8")

    stack = stack_java.read_text(encoding="utf-8")
    stack_old = """        finishResolving(sa, thisHasFizzled);

        game.copyLastState();
"""
    stack_new = """        finishResolving(sa, thisHasFizzled);

        // WS32: simulator semantic state is staged until this generic
        // post-resolution verifier accepts the actual Rules Core result.
        game.verifyResolvedCardBehavior(sa);

        game.copyLastState();
"""
    stack = replace_once(stack, stack_old, stack_new, "MagicStack post-resolution verifier boundary")
    stack_java.write_text(stack, encoding="utf-8")

    mapper = mapper_java.read_text(encoding="utf-8")
    package_old = "package forge.gamemodes.match.input;\n\n"
    package_new = (
        "package forge.gamemodes.match.input;\n\n"
        "import forge.game.CardBehaviorVerificationException;\n\n"
    )
    mapper = replace_once(mapper, package_old, package_new, "UnifiedOutcomeMapper import")

    mapper_tail = """    }
}
"""
    mapper_method = """    }

    /**
     * Maps only the dedicated sanitized runtime semantic-verification signal.
     * Unknown failures stay untyped here rather than being silently coerced.
     */
    public static UnifiedOutcomeCategory fromCardBehaviorFailure(final Throwable failure) {
        if (failure instanceof CardBehaviorVerificationException) {
            return UnifiedOutcomeCategory.CARD_BEHAVIOR_FAILURE;
        }
        throw new IllegalArgumentException("failure is not a card behavior verification failure");
    }
}
"""
    if not mapper.endswith(mapper_tail):
        raise SystemExit("unexpected exact-pin UnifiedOutcomeMapper tail")
    mapper = mapper[: -len(mapper_tail)] + mapper_method
    mapper_java.write_text(mapper, encoding="utf-8")

    print("WS32_FORGE_OVERLAY=APPLIED")
    print("WS32_PRODUCTION_HOOK=forge.game.zone.MagicStack#resolveStack:post-finishResolving")
    print("WS32_EXPECTED_SEMANTICS_OWNER=EXTERNAL_SIMULATOR_VERIFIER")
    print("WS32_CARD_NAME_PRODUCTION_BRANCHES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
