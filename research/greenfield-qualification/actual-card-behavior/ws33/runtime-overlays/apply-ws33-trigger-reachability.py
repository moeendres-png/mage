#!/usr/bin/env python3
"""Apply WS33 trigger admission observation plus the adjudicated singleton-selection repair.

The trigger hook fires only after TriggerHandler accepted a trigger through its production
canRunTrigger path and admitted the WrappedAbility to the simultaneous stack. It remains
observation-only. For dynamically spawned triggers, additional stderr-only diagnostics
report the exact isTriggerActive/canRunTrigger gate that accepted or rejected the trigger.
No diagnostic changes a boolean result, event fact, target, cost, RNG, stack order, or
trigger legality.

After those patches are installed, this entry point delegates to the focused
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

    private static void ws33TraceSpawnedTriggerGate(final String stage, final Trigger trigger, final boolean result) {
        if (trigger == null || trigger.getSpawningAbility() == null) {
            return;
        }
        final SpellAbility spawning = trigger.getSpawningAbility();
        final Card host = trigger.getHostCard();
        final Card spawningHost = spawning.getHostCard();
        System.err.println(
                "WS33_TRIGGER_GATE\\t" + stage + "\\t" + result
                        + "\\ttriggerId=" + trigger.getId()
                        + "\\tmode=" + trigger.getMode()
                        + "\\thostId=" + (host == null ? -1 : host.getId())
                        + "\\thostName=" + (host == null ? "" : host.getName())
                        + "\\tspawnAbilityId=" + spawning.getId()
                        + "\\tspawnHostId=" + (spawningHost == null ? -1 : spawningHost.getId())
                        + "\\tspawnHostName=" + (spawningHost == null ? "" : spawningHost.getName()));
    }

"""
    src = replace_once(src, class_anchor, class_insert, "observer declaration anchor")

    active_old = """    private boolean isTriggerActive(final Trigger regtrig) {
        if (!regtrig.phasesCheck(game)) {
            return false; // It's not the right phase to go off.
        }

        if (regtrig.isSuppressed()) {
            return false; // Trigger removed by effect
        }

        if (TriggerType.Always.equals(regtrig.getMode()) && game.getStack().hasStateTrigger(regtrig.getId())) {
            return false; // State triggers that are already on the stack
            // don't trigger again.
        }

        // do not check delayed
        if (regtrig.getSpawningAbility() == null && !regtrig.zonesCheck(game.getZoneOf(regtrig.getHostCard()))) {
            return false; // Host card isn't where it needs to be.
        }

        for (Trigger t : this.activeTriggers) {
            // If an ID that matches this ID is already active, don't add it
            if (regtrig.getId() == t.getId()) {
                return false;
            }
        }

        return true;
    }
"""
    active_new = """    private boolean isTriggerActive(final Trigger regtrig) {
        if (!regtrig.phasesCheck(game)) {
            ws33TraceSpawnedTriggerGate("ACTIVE_PHASES", regtrig, false);
            return false; // It's not the right phase to go off.
        }

        if (regtrig.isSuppressed()) {
            ws33TraceSpawnedTriggerGate("ACTIVE_SUPPRESSED", regtrig, false);
            return false; // Trigger removed by effect
        }

        if (TriggerType.Always.equals(regtrig.getMode()) && game.getStack().hasStateTrigger(regtrig.getId())) {
            ws33TraceSpawnedTriggerGate("ACTIVE_STATE_ALREADY_PRESENT", regtrig, false);
            return false; // State triggers that are already on the stack
            // don't trigger again.
        }

        // do not check delayed
        if (regtrig.getSpawningAbility() == null && !regtrig.zonesCheck(game.getZoneOf(regtrig.getHostCard()))) {
            ws33TraceSpawnedTriggerGate("ACTIVE_ZONE", regtrig, false);
            return false; // Host card isn't where it needs to be.
        }

        for (Trigger t : this.activeTriggers) {
            // If an ID that matches this ID is already active, don't add it
            if (regtrig.getId() == t.getId()) {
                ws33TraceSpawnedTriggerGate("ACTIVE_DUPLICATE", regtrig, false);
                return false;
            }
        }

        ws33TraceSpawnedTriggerGate("ACTIVE_PASS", regtrig, true);
        return true;
    }
"""
    src = replace_once(src, active_old, active_new, "spawned trigger active-gate diagnostics")

    can_old = """    private boolean canRunTrigger(final Trigger regtrig, final TriggerType mode, final Map<AbilityKey, Object> runParams) {
        if (regtrig.getMode() != mode) {
            return false; // Not the right mode.
        }

        if (regtrig.isSuppressed()) {
            return false; // Trigger removed by effect
        }

        /* this trigger can only be activated once per turn, verify it hasn't already run */
        if (!regtrig.checkActivationLimit()) {
            return false;
        }

        if (!regtrig.requirementsCheck(game)) {
            return false; // Conditions aren't right.
        }

        if (!regtrig.meetsRequirementsOnTriggeredObjects(game, runParams)) {
            return false; // Conditions aren't right.
        }

        if (!regtrig.performTest(runParams)) {
            return false; // Test failed.
        }

        if (TriggerType.Always.equals(regtrig.getMode()) && game.getStack().hasStateTrigger(regtrig.getId())) {
            return false; // State triggers that are already on the stack
        }

        // check if any static abilities are disabling the trigger (Torpor Orb and the like)
        if (!regtrig.isStatic() && StaticAbilityDisableTriggers.disabled(game, regtrig, runParams)) {
            return false;
        }

        return true;
    }
"""
    can_new = """    private boolean canRunTrigger(final Trigger regtrig, final TriggerType mode, final Map<AbilityKey, Object> runParams) {
        if (regtrig.getMode() != mode) {
            ws33TraceSpawnedTriggerGate("CAN_MODE", regtrig, false);
            return false; // Not the right mode.
        }

        if (regtrig.isSuppressed()) {
            ws33TraceSpawnedTriggerGate("CAN_SUPPRESSED", regtrig, false);
            return false; // Trigger removed by effect
        }

        /* this trigger can only be activated once per turn, verify it hasn't already run */
        if (!regtrig.checkActivationLimit()) {
            ws33TraceSpawnedTriggerGate("CAN_ACTIVATION_LIMIT", regtrig, false);
            return false;
        }

        if (!regtrig.requirementsCheck(game)) {
            ws33TraceSpawnedTriggerGate("CAN_REQUIREMENTS", regtrig, false);
            return false; // Conditions aren't right.
        }

        if (!regtrig.meetsRequirementsOnTriggeredObjects(game, runParams)) {
            ws33TraceSpawnedTriggerGate("CAN_TRIGGERED_OBJECT_REQUIREMENTS", regtrig, false);
            return false; // Conditions aren't right.
        }

        if (!regtrig.performTest(runParams)) {
            ws33TraceSpawnedTriggerGate("CAN_PERFORM_TEST", regtrig, false);
            return false; // Test failed.
        }

        if (TriggerType.Always.equals(regtrig.getMode()) && game.getStack().hasStateTrigger(regtrig.getId())) {
            ws33TraceSpawnedTriggerGate("CAN_STATE_ALREADY_PRESENT", regtrig, false);
            return false; // State triggers that are already on the stack
        }

        // check if any static abilities are disabling the trigger (Torpor Orb and the like)
        if (!regtrig.isStatic() && StaticAbilityDisableTriggers.disabled(game, regtrig, runParams)) {
            ws33TraceSpawnedTriggerGate("CAN_STATIC_DISABLED", regtrig, false);
            return false;
        }

        ws33TraceSpawnedTriggerGate("CAN_PASS", regtrig, true);
        return true;
    }
"""
    src = replace_once(src, can_old, can_new, "spawned trigger canRun-gate diagnostics")

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
        "WS33_TRIGGER_GATE",
        "ACTIVE_PASS",
        "CAN_REQUIREMENTS",
        "CAN_PERFORM_TEST",
        "CAN_PASS",
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

    print("WS33_TRIGGER_REACHABILITY=PASS boundary=POST_LEGALITY_POST_SIMULTANEOUS_STACK_ADMISSION spawned_trigger_gate_diagnostics=OBSERVATION_ONLY observation_semantics_mutated=FALSE singleton_selection_repair=AUTHORITATIVE_SIZE_ONE_ONLY")


if __name__ == "__main__":
    main()
