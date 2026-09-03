#!/usr/bin/env python3
"""Add an observation-only WS33 AbilitySub resolution hook to pinned Forge.

The hook is inert unless a qualification test registers an observer. It runs immediately
before the existing effect.resolve(this) call and does not choose targets, legality,
options, outcomes, or replacement behavior.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"WS33_SVAR_REACHABILITY_OVERLAY=FAIL {label}: expected one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    path = args.forge_root / "forge-game/src/main/java/forge/game/spellability/AbilitySub.java"
    s = path.read_text(encoding="utf-8")
    if "setWs33ResolutionObserver" in s:
        raise SystemExit("WS33_SVAR_REACHABILITY_OVERLAY=FAIL overlay already present")
    s = replace_once(s, "import java.util.List;\n", "import java.util.List;\nimport java.util.function.Consumer;\n", "Consumer import")
    s = replace_once(
        s,
        "    private static final long serialVersionUID = 4650634415821733134L;\n\n    private SpellAbility parent;",
        "    private static final long serialVersionUID = 4650634415821733134L;\n\n    private static volatile Consumer<AbilitySub> ws33ResolutionObserver;\n\n    public static void setWs33ResolutionObserver(final Consumer<AbilitySub> observer) {\n        ws33ResolutionObserver = observer;\n    }\n\n    private SpellAbility parent;",
        "observer slot",
    )
    s = replace_once(
        s,
        "    public void resolve() {\n        effect.resolve(this);\n    }",
        "    public void resolve() {\n        final Consumer<AbilitySub> observer = ws33ResolutionObserver;\n        if (observer != null) {\n            observer.accept(this);\n        }\n        effect.resolve(this);\n    }",
        "resolution hook",
    )
    path.write_text(s, encoding="utf-8")
    print("WS33_SVAR_REACHABILITY_OVERLAY=PASS hook=AbilitySub.resolve observation_only=TRUE")


if __name__ == "__main__":
    main()
