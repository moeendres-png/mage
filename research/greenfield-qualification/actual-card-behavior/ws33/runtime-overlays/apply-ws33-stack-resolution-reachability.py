#!/usr/bin/env python3
"""Add observation-only WS33 stack lifecycle and root-resolution hooks to pinned Forge.

The lifecycle callback reports entry into MagicStack.add, target rejection, frozen queueing,
actual stack push, and the hasFizzled result. The existing resolution callback fires only
for a non-fizzled API-bearing SpellAbility immediately before AbilityUtils.resolve(sa).
Neither callback decides legality, changes targets/choices, changes stack order, changes
fizzle behavior, or changes resolution semantics.
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

    # Exact pinned-Forge declaration at 8c7e9afb. Keep this fail-closed rather than
    # accepting a broad class regex that could silently bind a changed runtime.
    class_anchor = "public class MagicStack /* extends MyObservable */ implements Iterable<SpellAbilityStackInstance> {\n"
    class_insert = """public class MagicStack /* extends MyObservable */ implements Iterable<SpellAbilityStackInstance> {
    @FunctionalInterface
    public interface Ws33ResolutionObserver {
        void onResolve(SpellAbility ability);
    }

    @FunctionalInterface
    public interface Ws33StackLifecycleObserver {
        void onStackEvent(String stage, SpellAbility ability, boolean flag);
    }

    private static volatile Ws33ResolutionObserver ws33ResolutionObserver;
    private static volatile Ws33StackLifecycleObserver ws33StackLifecycleObserver;

    public static void setWs33ResolutionObserver(final Ws33ResolutionObserver observer) {
        ws33ResolutionObserver = observer;
    }

    public static void setWs33StackLifecycleObserver(final Ws33StackLifecycleObserver observer) {
        ws33StackLifecycleObserver = observer;
    }

    private static void ws33ObserveStackLifecycle(final String stage, final SpellAbility ability, final boolean flag) {
        final Ws33StackLifecycleObserver observer = ws33StackLifecycleObserver;
        if (observer != null) {
            observer.onStackEvent(stage, ability, flag);
        }
    }

"""
    src = replace_once(src, class_anchor, class_insert, "observer declaration anchor")

    add_anchor = """    public final void add(SpellAbility sp, SpellAbilityStackInstance si, int id) {
        final Card source = sp.getHostCard();
"""
    add_insert = """    public final void add(SpellAbility sp, SpellAbilityStackInstance si, int id) {
        final Card source = sp.getHostCard();
        ws33ObserveStackLifecycle("ADD_ENTER", sp, false);
"""
    src = replace_once(src, add_anchor, add_insert, "stack add entry anchor")

    reject_anchor = """        if (!sp.isCopied() && !hasLegalTargeting(sp)) {
            String str = source + " - [Couldn't add to stack, failed to target] - " + sp.getDescription();
"""
    reject_insert = """        if (!sp.isCopied() && !hasLegalTargeting(sp)) {
            ws33ObserveStackLifecycle("ADD_TARGET_REJECT", sp, true);
            String str = source + " - [Couldn't add to stack, failed to target] - " + sp.getDescription();
"""
    src = replace_once(src, reject_anchor, reject_insert, "stack target reject anchor")

    frozen_anchor = """        if (frozen && !sp.hasParam("IgnoreFreeze") && !sp.isCastFromPlayEffect()) {
            si = new SpellAbilityStackInstance(sp, id);
            frozenStack.push(si);
            return;
        }
"""
    frozen_insert = """        if (frozen && !sp.hasParam("IgnoreFreeze") && !sp.isCastFromPlayEffect()) {
            si = new SpellAbilityStackInstance(sp, id);
            frozenStack.push(si);
            ws33ObserveStackLifecycle("FROZEN_QUEUE", sp, true);
            return;
        }
"""
    src = replace_once(src, frozen_anchor, frozen_insert, "frozen stack anchor")

    push_anchor = """        // The ability is added to stack HERE
        push(sp, si, id);
"""
    push_insert = """        // The ability is added to stack HERE
        push(sp, si, id);
        ws33ObserveStackLifecycle("STACK_PUSH", sp, true);
"""
    src = replace_once(src, push_anchor, push_insert, "real stack push anchor")

    fizzle_anchor = """        boolean thisHasFizzled = hasFizzled(sa, null);

        if (!thisHasFizzled) {
"""
    fizzle_insert = """        boolean thisHasFizzled = hasFizzled(sa, null);
        ws33ObserveStackLifecycle("FIZZLE_RESULT", sa, thisHasFizzled);

        if (!thisHasFizzled) {
"""
    src = replace_once(src, fizzle_anchor, fizzle_insert, "fizzle outcome anchor")

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
        "public interface Ws33StackLifecycleObserver",
        "setWs33ResolutionObserver",
        "setWs33StackLifecycleObserver",
        'ws33ObserveStackLifecycle("ADD_ENTER", sp, false)',
        'ws33ObserveStackLifecycle("ADD_TARGET_REJECT", sp, true)',
        'ws33ObserveStackLifecycle("FROZEN_QUEUE", sp, true)',
        'ws33ObserveStackLifecycle("STACK_PUSH", sp, true)',
        'ws33ObserveStackLifecycle("FIZZLE_RESULT", sa, thisHasFizzled)',
        "observer.onResolve(sa)",
        "AbilityUtils.resolve(sa);",
    ):
        if token not in src:
            raise SystemExit(f"WS33_STACK_RESOLUTION_REACHABILITY=FAIL missing {token}")
    if src.index("observer.onResolve(sa)") > src.index("AbilityUtils.resolve(sa);"):
        raise SystemExit("WS33_STACK_RESOLUTION_REACHABILITY=FAIL observer is not pre-resolution")

    path.write_text(src, encoding="utf-8")
    print("WS33_STACK_RESOLUTION_REACHABILITY=PASS boundary=ADD_ENTRY_TARGET_REJECT_FROZEN_PUSH_FIZZLE_POST_FIZZLE_PRE_API_RESOLVE semantics_mutated=FALSE")


if __name__ == "__main__":
    main()
