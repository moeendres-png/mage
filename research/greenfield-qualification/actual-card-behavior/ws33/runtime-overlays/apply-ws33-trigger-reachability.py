#!/usr/bin/env python3
"""Add a fail-closed, observation-only WS33 trigger-admission hook to pinned Forge.

The hook fires only after TriggerHandler has accepted a trigger through its production
canRunTrigger path and admitted the resulting WrappedAbility to the simultaneous stack.
It does not change trigger legality, event facts, targets, choices, stack ordering, or
resolution. Qualification harnesses use it only to prove which exact source trigger
entered the production stack.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_TRIGGER_REACHABILITY=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()

    path = args.forge_root / "forge-game/src/main/java/forge/game/trigger/TriggerHandler.java"
    src = path.read_text(encoding="utf-8")

    class_anchor = "public class TriggerHandler {\n"
    class_insert = """public class TriggerHandler {
    @FunctionalInterface
    public interface Ws33TriggerObserver {
        void onTrigger(Trigger trigger, SpellAbility ability);
    }

    private static volatile Ws33TriggerObserver ws33TriggerObserver;

    public static void setWs33TriggerObserver(final Ws33TriggerObserver observer) {
        ws33TriggerObserver = observer;
    }

"""
    src = replace_once(src, class_anchor, class_insert, "observer declaration anchor")

    admission_anchor = """        } else {
            game.getStack().addSimultaneousStackEntry(wrapperAbility);
            game.getTriggerHandler().runTrigger(TriggerType.AbilityTriggered, TriggerAbilityTriggered.getRunParams(regtrig, wrapperAbility, runParams), false);
        }
"""
    admission_insert = """        } else {
            game.getStack().addSimultaneousStackEntry(wrapperAbility);
            final Ws33TriggerObserver observer = ws33TriggerObserver;
            if (observer != null) {
                observer.onTrigger(regtrig, sa);
            }
            game.getTriggerHandler().runTrigger(TriggerType.AbilityTriggered, TriggerAbilityTriggered.getRunParams(regtrig, wrapperAbility, runParams), false);
        }
"""
    src = replace_once(src, admission_anchor, admission_insert, "simultaneous-stack admission anchor")

    required = (
        "public interface Ws33TriggerObserver",
        "setWs33TriggerObserver",
        "observer.onTrigger(regtrig, sa)",
        "game.getStack().addSimultaneousStackEntry(wrapperAbility);",
    )
    if not all(token in src for token in required):
        raise SystemExit("WS33_TRIGGER_REACHABILITY=FAIL incomplete observer route")
    if src.index("game.getStack().addSimultaneousStackEntry(wrapperAbility);") > src.index("observer.onTrigger(regtrig, sa)"):
        raise SystemExit("WS33_TRIGGER_REACHABILITY=FAIL observer precedes production stack admission")

    path.write_text(src, encoding="utf-8")
    print("WS33_TRIGGER_REACHABILITY=PASS boundary=POST_LEGALITY_POST_SIMULTANEOUS_STACK_ADMISSION semantics_mutated=FALSE")


if __name__ == "__main__":
    main()
