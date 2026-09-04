#!/usr/bin/env python3
"""Apply WS33 trigger admission observation plus the adjudicated singleton-selection repair.

The trigger hook fires only after TriggerHandler accepted a trigger through its production
canRunTrigger path and admitted the WrappedAbility to the simultaneous stack. It remains
observation-only. After that patch is installed, this entry point delegates to the focused
`apply-ws33-nondiscretionary-ability-selection.py` overlay, whose separately frozen source
adjudication restores pinned Desktop Forge's no-trigger-event behavior only when the
Rules-Core-produced additional-cost ability list contains exactly one object.

No trigger legality, event fact, target, cost, RNG, stack ordering, or multi-option pilot
choice is inferred or bypassed here.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


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

    repair = Path(__file__).with_name("apply-ws33-nondiscretionary-ability-selection.py")
    if not repair.is_file():
        raise SystemExit("WS33_TRIGGER_REACHABILITY=FAIL missing adjudicated singleton-selection overlay")
    subprocess.run(
        [sys.executable, str(repair), "--forge-root", str(args.forge_root)],
        check=True,
    )

    print("WS33_TRIGGER_REACHABILITY=PASS boundary=POST_LEGALITY_POST_SIMULTANEOUS_STACK_ADMISSION observation_semantics_mutated=FALSE singleton_selection_repair=AUTHORITATIVE_SIZE_ONE_ONLY")


if __name__ == "__main__":
    main()
