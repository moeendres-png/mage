#!/usr/bin/env python3
"""Add observation-only WS33 stack lifecycle, trigger-play prerequisite, and resolution hooks.

MagicStack callbacks report add entry, target rejection, frozen queueing, actual stack push,
hasFizzled result, and post-fizzle/pre-resolution reachability. PlaySpellAbility tracing
reports the production prerequisite stages for triggered abilities before MagicStack.add.
No hook chooses, pays, targets, changes ordering, bypasses legality/timing, or changes any
boolean result or resolution semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_STACK_RESOLUTION_REACHABILITY=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def patch_magic_stack(forge_root: Path) -> None:
    path = forge_root / "forge-game/src/main/java/forge/game/zone/MagicStack.java"
    src = path.read_text(encoding="utf-8")

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

    src = replace_once(
        src,
        """    public final void add(SpellAbility sp, SpellAbilityStackInstance si, int id) {
        final Card source = sp.getHostCard();
""",
        """    public final void add(SpellAbility sp, SpellAbilityStackInstance si, int id) {
        final Card source = sp.getHostCard();
        ws33ObserveStackLifecycle("ADD_ENTER", sp, false);
""",
        "stack add entry anchor",
    )
    src = replace_once(
        src,
        """        if (!sp.isCopied() && !hasLegalTargeting(sp)) {
            String str = source + " - [Couldn't add to stack, failed to target] - " + sp.getDescription();
""",
        """        if (!sp.isCopied() && !hasLegalTargeting(sp)) {
            ws33ObserveStackLifecycle("ADD_TARGET_REJECT", sp, true);
            String str = source + " - [Couldn't add to stack, failed to target] - " + sp.getDescription();
""",
        "stack target reject anchor",
    )
    src = replace_once(
        src,
        """        if (frozen && !sp.hasParam("IgnoreFreeze") && !sp.isCastFromPlayEffect()) {
            si = new SpellAbilityStackInstance(sp, id);
            frozenStack.push(si);
            return;
        }
""",
        """        if (frozen && !sp.hasParam("IgnoreFreeze") && !sp.isCastFromPlayEffect()) {
            si = new SpellAbilityStackInstance(sp, id);
            frozenStack.push(si);
            ws33ObserveStackLifecycle("FROZEN_QUEUE", sp, true);
            return;
        }
""",
        "frozen stack anchor",
    )
    src = replace_once(
        src,
        """        // The ability is added to stack HERE
        push(sp, si, id);
""",
        """        // The ability is added to stack HERE
        push(sp, si, id);
        ws33ObserveStackLifecycle("STACK_PUSH", sp, true);
""",
        "real stack push anchor",
    )
    src = replace_once(
        src,
        """        boolean thisHasFizzled = hasFizzled(sa, null);

        if (!thisHasFizzled) {
""",
        """        boolean thisHasFizzled = hasFizzled(sa, null);
        ws33ObserveStackLifecycle("FIZZLE_RESULT", sa, thisHasFizzled);

        if (!thisHasFizzled) {
""",
        "fizzle outcome anchor",
    )
    src = replace_once(
        src,
        """        } else if (sa.getApi() != null) {
            AbilityUtils.handleRemembering(sa);
            AbilityUtils.resolve(sa);
""",
        """        } else if (sa.getApi() != null) {
            AbilityUtils.handleRemembering(sa);
            final Ws33ResolutionObserver observer = ws33ResolutionObserver;
            if (observer != null) {
                observer.onResolve(sa);
            }
            AbilityUtils.resolve(sa);
""",
        "non-fizzled API resolution anchor",
    )

    for token in (
        "public interface Ws33ResolutionObserver",
        "public interface Ws33StackLifecycleObserver",
        "setWs33ResolutionObserver",
        "setWs33StackLifecycleObserver",
        'ws33ObserveStackLifecycle("ADD_ENTER", sp, false)',
        'ws33ObserveStackLifecycle("STACK_PUSH", sp, true)',
        'ws33ObserveStackLifecycle("FIZZLE_RESULT", sa, thisHasFizzled)',
        "observer.onResolve(sa)",
    ):
        if token not in src:
            raise SystemExit(f"WS33_STACK_RESOLUTION_REACHABILITY=FAIL missing MagicStack token {token}")

    path.write_text(src, encoding="utf-8")


def patch_play_spell_ability(forge_root: Path) -> None:
    path = forge_root / "forge-game/src/main/java/forge/game/player/PlaySpellAbility.java"
    src = path.read_text(encoding="utf-8")

    fields_anchor = """    private final PlayerController controller;
    private SpellAbility ability;
    private boolean needX = true;

"""
    fields_insert = """    private final PlayerController controller;
    private SpellAbility ability;
    private boolean needX = true;

    private static void ws33TraceTriggerPlay(final String stage, final SpellAbility ability) {
        if (ability == null || !ability.isTrigger()) {
            return;
        }
        final Card host = ability.getHostCard();
        System.err.println("WS33_TRIGGER_PLAY\\t" + stage + "\\tNA\\t" + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t" + (host == null ? -1 : host.getId()) + "\\t" + (ability.getApi() == null ? "" : ability.getApi().name()) + "\\t" + ability.getClass().getName());
    }

    private static boolean ws33TraceTriggerStage(final String stage, final SpellAbility ability, final boolean result) {
        if (ability != null && ability.isTrigger()) {
            final Card host = ability.getHostCard();
            System.err.println("WS33_TRIGGER_PLAY\\t" + stage + "\\t" + result + "\\t" + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t" + (host == null ? -1 : host.getId()) + "\\t" + (ability.getApi() == null ? "" : ability.getApi().name()) + "\\t" + ability.getClass().getName());
        }
        return result;
    }

"""
    src = replace_once(src, fields_anchor, fields_insert, "PlaySpellAbility trace helper anchor")

    entry_anchor = """        Card source = sa.getHostCard();
        sa.setActivatingPlayer(p);
"""
    entry_insert = """        Card source = sa.getHostCard();
        ws33TraceTriggerPlay("PLAY_SPELL_ENTRY", sa);
        final SpellAbility ws33OriginalAbility = sa;
        sa.setActivatingPlayer(p);
"""
    src = replace_once(src, entry_anchor, entry_insert, "playSpellAbility entry anchor")

    optional_anchor = """        sa = chooseOptionalAdditionalCosts(p, sa);
        if (sa == null) {
            return false;
        }
"""
    optional_insert = """        sa = chooseOptionalAdditionalCosts(p, sa);
        if (sa == null) {
            ws33TraceTriggerPlay("OPTIONAL_COST_SELECTION_NULL", ws33OriginalAbility);
            return false;
        }
        ws33TraceTriggerPlay("OPTIONAL_COST_SELECTION_OK", sa);
"""
    src = replace_once(src, optional_anchor, optional_insert, "optional cost selection anchor")

    req_anchor = """        final PlaySpellAbility req = new PlaySpellAbility(controller, sa);
        if (!req.playAbility(true, false, false)) {
"""
    req_insert = """        final PlaySpellAbility req = new PlaySpellAbility(controller, sa);
        if (!req.playAbility(true, false, false)) {
            ws33TraceTriggerPlay("PLAY_ABILITY_FALSE", sa);
"""
    src = replace_once(src, req_anchor, req_insert, "playAbility false anchor")

    success_anchor = """            return false;
        }
        return true;
    }

    static SpellAbility chooseOptionalAdditionalCosts"""
    success_insert = """            return false;
        }
        ws33TraceTriggerPlay("PLAY_ABILITY_TRUE", sa);
        return true;
    }

    static SpellAbility chooseOptionalAdditionalCosts"""
    src = replace_once(src, success_anchor, success_insert, "playSpellAbility success anchor")

    precost_anchor = """        boolean preCostRequisites = announceType() && announceValuesLikeX() &&
            ability.checkRestrictions(player) &&
            (!mayChooseTargets || ability.setupTargets()) &&
            ability.canCastTiming(player) &&
            ability.isLegalAfterStack();

        // Freeze the stack just before we start paying costs but after the ability is fully set up
        game.getStack().freezeStack(skipStack ? null : ability);
        final boolean prerequisitesMet = preCostRequisites && (isFree || payment.payCost(controller.getCostDecisionMaker(player, ability, ability.isTrigger())));
"""
    precost_insert = """        boolean preCostRequisites = ws33TraceTriggerStage("ANNOUNCE_TYPE", ability, announceType()) && ws33TraceTriggerStage("ANNOUNCE_X", ability, announceValuesLikeX()) &&
            ws33TraceTriggerStage("CHECK_RESTRICTIONS", ability, ability.checkRestrictions(player)) &&
            (!mayChooseTargets || ws33TraceTriggerStage("SETUP_TARGETS", ability, ability.setupTargets())) &&
            ws33TraceTriggerStage("CAST_TIMING", ability, ability.canCastTiming(player)) &&
            ws33TraceTriggerStage("LEGAL_AFTER_STACK", ability, ability.isLegalAfterStack());
        ws33TraceTriggerStage("PRECOST_REQUISITES", ability, preCostRequisites);

        // Freeze the stack just before we start paying costs but after the ability is fully set up
        game.getStack().freezeStack(skipStack ? null : ability);
        final boolean prerequisitesMet = preCostRequisites && (isFree || ws33TraceTriggerStage("PAY_COST", ability, payment.payCost(controller.getCostDecisionMaker(player, ability, ability.isTrigger()))));
        ws33TraceTriggerStage("PREREQUISITES_MET", ability, prerequisitesMet);
"""
    src = replace_once(src, precost_anchor, precost_insert, "pre-cost prerequisite anchor")

    add_anchor = """            } else {
                ensureAbilityHasDescription(ability);
                game.getStack().addAndUnfreeze(ability);
            }
"""
    add_insert = """            } else {
                ensureAbilityHasDescription(ability);
                ws33TraceTriggerPlay("ADD_AND_UNFREEZE", ability);
                game.getStack().addAndUnfreeze(ability);
            }
"""
    src = replace_once(src, add_anchor, add_insert, "addAndUnfreeze anchor")

    for token in (
        "WS33_TRIGGER_PLAY",
        "PLAY_SPELL_ENTRY",
        "OPTIONAL_COST_SELECTION_OK",
        "ANNOUNCE_TYPE",
        "CHECK_RESTRICTIONS",
        "SETUP_TARGETS",
        "CAST_TIMING",
        "LEGAL_AFTER_STACK",
        "PAY_COST",
        "PREREQUISITES_MET",
        "ADD_AND_UNFREEZE",
    ):
        if token not in src:
            raise SystemExit(f"WS33_STACK_RESOLUTION_REACHABILITY=FAIL missing PlaySpellAbility token {token}")

    path.write_text(src, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()

    patch_magic_stack(args.forge_root)
    patch_play_spell_ability(args.forge_root)
    print("WS33_STACK_RESOLUTION_REACHABILITY=PASS boundary=TRIGGER_PLAY_PREREQUISITES_ADD_TARGET_REJECT_FROZEN_PUSH_FIZZLE_POST_FIZZLE_PRE_API_RESOLVE semantics_mutated=FALSE")


if __name__ == "__main__":
    main()
