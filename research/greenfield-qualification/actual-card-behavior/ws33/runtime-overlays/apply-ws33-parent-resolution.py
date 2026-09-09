#!/usr/bin/env python3
"""Add an observation-only WS33 parent-resolution hook to pinned Forge.

The hook is inert unless a qualification test registers an observer. It
fires in AbilityUtils.resolveApiAbility immediately after the parent
effect sa.resolve() returns on the direct (non-UnlessCost) path, i.e.
strictly before resolveSubAbilities enters the production child. It does
not choose targets, legality, options, outcomes, or replacement behavior.

Scope note: UnlessCost abilities return early via handleUnlessCost and do
not emit this event. Batch selection must exclude UnlessCost scripts while
this single-site contract holds.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"WS33_PARENT_RESOLUTION_OVERLAY=FAIL {label}: expected one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    path = args.forge_root / "forge-game/src/main/java/forge/game/ability/AbilityUtils.java"
    s = path.read_text(encoding="utf-8")
    if "setWs33ParentResolutionObserver" in s:
        raise SystemExit("WS33_PARENT_RESOLUTION_OVERLAY=FAIL overlay already present")
    s = replace_once(
        s,
        "import forge.game.trigger.TriggerType;",
        "import forge.game.trigger.TriggerType;\nimport java.util.function.Consumer;",
        "Consumer import",
    )
    s = replace_once(
        s,
        "public class AbilityUtils {",
        "public class AbilityUtils {\n\n    private static volatile Consumer<SpellAbility> ws33ParentResolutionObserver;\n\n    public static void setWs33ParentResolutionObserver(final Consumer<SpellAbility> observer) {\n        ws33ParentResolutionObserver = observer;\n    }\n\n    private static void ws33NoteParentResolved(final SpellAbility sa) {\n        final Consumer<SpellAbility> observer = ws33ParentResolutionObserver;\n        if (observer != null) {\n            observer.accept(sa);\n        }\n    }",
        "observer slot",
    )
    s = replace_once(
        s,
        '            if (sa.isWrapper() || StringUtils.isBlank(sa.getParam("UnlessCost"))) {\n                sa.resolve();\n',
        '            if (sa.isWrapper() || StringUtils.isBlank(sa.getParam("UnlessCost"))) {\n                sa.resolve();\n                ws33NoteParentResolved(sa);\n',
        "parent hook",
    )
    path.write_text(s, encoding="utf-8")
    print("WS33_PARENT_RESOLUTION_OVERLAY=PASS hook=AbilityUtils.resolveApiAbility observation_only=TRUE")


if __name__ == "__main__":
    main()
