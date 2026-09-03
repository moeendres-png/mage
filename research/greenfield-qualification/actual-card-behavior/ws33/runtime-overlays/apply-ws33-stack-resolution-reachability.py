#!/usr/bin/env python3
"""Add an observation-only WS33 root stack-resolution hook to pinned Forge.

The callback fires only for a non-fizzled API-bearing SpellAbility after MagicStack has
completed its target/fizzle adjudication and immediately before AbilityUtils.resolve(sa).
It cannot change legality, targets, choices, stack order, or resolution semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_STACK_RESOLUTION_REACHABILITY=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()

    path = args.forge_root / "forge-game/src/main/java/forge/game/zone/MagicStack.java"
    src = path.read_text(encoding="utf-8")

    class_anchor = "public class MagicStack implements Iterable<SpellAbilityStackInstance> {\n"
    class_insert = """public class MagicStack implements Iterable<SpellAbilityStackInstance> {
    @FunctionalInterface
    public interface Ws33ResolutionObserver {
        void onResolve(SpellAbility ability);
    }

    private static volatile Ws33ResolutionObserver ws33ResolutionObserver;

    public static void setWs33ResolutionObserver(final Ws33ResolutionObserver observer) {
        ws33ResolutionObserver = observer;
    }

"""
    src = replace_once(src, class_anchor, class_insert, "observer declaration anchor")

    resolve_anchor = """        } else if (sa.getApi() != null) {
            AbilityUtils.handleRemembering(sa);
            AbilityUtils.resolve(sa);
"""
    resolve_insert = """        } else if (sa.getApi() != null) {
            AbilityUtils.handleRemembering(sa);
            final Ws33ResolutionObserver observer = ws33ResolutionObserver;
            if (observer != null) {
                observer.onResolve(sa);
            }
            AbilityUtils.resolve(sa);
"""
    src = replace_once(src, resolve_anchor, resolve_insert, "non-fizzled API resolution anchor")

    for token in (
        "public interface Ws33ResolutionObserver",
        "setWs33ResolutionObserver",
        "observer.onResolve(sa)",
        "AbilityUtils.resolve(sa);",
    ):
        if token not in src:
            raise SystemExit(f"WS33_STACK_RESOLUTION_REACHABILITY=FAIL missing {token}")
    if src.index("observer.onResolve(sa)") > src.index("AbilityUtils.resolve(sa);"):
        raise SystemExit("WS33_STACK_RESOLUTION_REACHABILITY=FAIL observer is not pre-resolution")

    path.write_text(src, encoding="utf-8")
    print("WS33_STACK_RESOLUTION_REACHABILITY=PASS boundary=POST_FIZZLE_PRE_API_RESOLVE semantics_mutated=FALSE")


if __name__ == "__main__":
    main()
