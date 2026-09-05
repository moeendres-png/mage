#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_A1_CARDINALITY_HARNESS_REPAIR=FAIL " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label} anchor count={count}")
    return text.replace(old, new, 1)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--test", type=Path, required=True)
    args = p.parse_args()
    require(args.test.is_file(), f"missing test {args.test}")
    text = args.test.read_text(encoding="utf-8")

    # TriggeredCardController is resolved by Forge through AbilityKey.Card.
    old = '''        if (c.validTgts.contains("TriggeredDefendingPlayer")) {
            ability.setTriggeringObject(AbilityKey.DefendingPlayer, opponent);
        }
'''
    new = '''        if (c.validTgts.contains("TriggeredDefendingPlayer")) {
            ability.setTriggeringObject(AbilityKey.DefendingPlayer, opponent);
        }
        if ("TriggeredCardController".equals(ability.getParam("TargetsWithDefinedController"))) {
            ability.setTriggeringObject(AbilityKey.Card, source);
        }
'''
    text = replace_once(text, old, new, "TriggeredCardController context")

    # Remove the qualification-only 1/1 rejection. Forge's actual target
    # restriction object is authoritative for dynamic min/max cardinality.
    old = '''            if (ability.getMinTargets() != 1 || ability.getMaxTargets() != 1) {
                continue;
            }
            matches.add(ability);
'''
    new = '''            matches.add(ability);
'''
    text = replace_once(text, old, new, "hard-coded single-target filter")

    # Provision a named, explicit filler whitelist. The pilot never chooses an
    # arbitrary legal option: it may choose only the intended target, DONE, or
    # one of these predeclared semantic identities when Forge requires another
    # target before DONE becomes legal.
    old = '''        final PlayerControllerHuman controller = new PlayerControllerHuman(
                game, actor, new LobbyPlayerHuman("ws33-target-principal"));
        final Provider provider = new Provider(c, intended, replay);
'''
    new = '''        final List<GameObject> fillerTargets = provisionQualificationFillers(game, actor, opponent, intended);
        final PlayerControllerHuman controller = new PlayerControllerHuman(
                game, actor, new LobbyPlayerHuman("ws33-target-principal"));
        final Provider provider = new Provider(c, intended, fillerTargets, replay);
'''
    text = replace_once(text, old, new, "provider filler provisioning")

    # Bind final assertions to authoritative dynamic min/max, not 1/1.
    old = '''        final int initialTargetCount = ability.getTargets().size();
        if (initialTargetCount != 0) {
            throw new IllegalStateException("actual ability already has targets before qualification");
        }
        final boolean chooseResult = controller.chooseTargetsFor(ability);
        provider.assertConsumed();
        if (!chooseResult) {
            throw new IllegalStateException("Forge target selection returned false");
        }
        if (!ability.isTargeting(intended)) {
            throw new IllegalStateException("Forge did not retain fixture-designated authoritative target");
        }
        if (ability.getTargets().size() != 1) {
            throw new IllegalStateException("conservative single-target shard selected "
                    + ability.getTargets().size() + " targets");
        }
        if (!ability.isTargetNumberValid()) {
            throw new IllegalStateException("Forge reports selected target count invalid");
        }
'''
    new = '''        final int initialTargetCount = ability.getTargets().size();
        if (initialTargetCount != 0) {
            throw new IllegalStateException("actual ability already has targets before qualification");
        }
        final TargetRestrictions authoritativeRestrictions = ability.getTargetRestrictions();
        final int authoritativeMinTargets = authoritativeRestrictions.getMinTargets(ability.getHostCard(), ability);
        final int authoritativeMaxTargets = authoritativeRestrictions.getMaxTargets(ability.getHostCard(), ability);
        if (authoritativeMinTargets < 0 || authoritativeMaxTargets < authoritativeMinTargets) {
            throw new IllegalStateException("invalid authoritative target cardinality min="
                    + authoritativeMinTargets + " max=" + authoritativeMaxTargets);
        }
        final boolean chooseResult = controller.chooseTargetsFor(ability);
        provider.assertConsumed();
        if (!chooseResult) {
            throw new IllegalStateException("Forge target selection returned false");
        }
        if (!ability.isTargeting(intended)) {
            throw new IllegalStateException("Forge did not retain fixture-designated authoritative target");
        }
        final int finalTargetCount = ability.getTargets().size();
        if (finalTargetCount < authoritativeMinTargets || finalTargetCount > authoritativeMaxTargets) {
            throw new IllegalStateException("selected target count outside authoritative range count="
                    + finalTargetCount + " min=" + authoritativeMinTargets + " max=" + authoritativeMaxTargets);
        }
        if (!ability.isTargetNumberValid()) {
            throw new IllegalStateException("Forge reports selected target count invalid");
        }
'''
    text = replace_once(text, old, new, "authoritative cardinality assertions")

    old = '''        final String canonical = "target_count=1"
                + "|target_number_valid=true"
'''
    new = '''        final String canonical = "target_count=" + finalTargetCount
                + "|target_min=" + authoritativeMinTargets
                + "|target_max=" + authoritativeMaxTargets
                + "|target_number_valid=true"
'''
    text = replace_once(text, old, new, "canonical target cardinality")

    old = '''        return new Result(
                initialTargetCount,
                ability.getTargets().size(),
                ability.isTargetNumberValid(),
'''
    new = '''        return new Result(
                initialTargetCount,
                finalTargetCount,
                authoritativeMinTargets,
                authoritativeMaxTargets,
                ability.isTargetNumberValid(),
'''
    text = replace_once(text, old, new, "Result cardinality arguments")

    # Insert real Forge filler fixtures before findAbility.
    marker = '''    private SpellAbility findAbility(final Card source, final Case c) {
'''
    helper = '''    private List<GameObject> provisionQualificationFillers(
            final Game game, final Player actor, final Player opponent, final GameObject intended) {
        final Player third = game.getPlayers().get(2);
        final List<GameObject> fillers = new ArrayList<>();
        fillers.add(actor);
        fillers.add(opponent);
        fillers.add(third);
        for (final Player owner : List.of(actor, opponent, third)) {
            fillers.add(addCardToZone("Ornithopter", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Runeclaw Bear", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Walking Corpse", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Isamaru, Hound of Konda", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Air Elemental", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Assembly-Worker", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Vampire Nighthawk", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Fusion Elemental", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Sol Ring", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Glorious Anthem", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Island", owner, ZoneType.Battlefield));
            fillers.add(addCardToZone("Ornithopter", owner, ZoneType.Graveyard));
            fillers.add(addCardToZone("Runeclaw Bear", owner, ZoneType.Graveyard));
            fillers.add(addCardToZone("Walking Corpse", owner, ZoneType.Graveyard));
            fillers.add(addCardToZone("Shock", owner, ZoneType.Graveyard));
            fillers.add(addCardToZone("Sol Ring", owner, ZoneType.Graveyard));
            fillers.add(addCardToZone("Pacifism", owner, ZoneType.Graveyard));
        }
        fillers.removeIf(candidate -> candidate == intended);
        return fillers;
    }

'''
    text = replace_once(text, marker, helper + marker, "filler helper insertion")

    # Provider: exact intended semantic first, then DONE if offered, otherwise
    # only a predeclared filler semantic. Replay remains exact tape matching.
    old = '''        private final List<ReplayDecision> replay;
        private int replayIndex;
        private boolean selected;
        private boolean sawIntended;
        private final List<CapturedDecision> captured = new ArrayList<>();

        Provider(final Case c, final GameObject intended, final List<ReplayDecision> replay) {
            this.intended = intended;
            this.replay = replay;
        }
'''
    new = '''        private final List<ReplayDecision> replay;
        private final List<String> fillerSemantics;
        private final List<String> usedFillerSemantics = new ArrayList<>();
        private int replayIndex;
        private boolean selected;
        private boolean sawIntended;
        private final List<CapturedDecision> captured = new ArrayList<>();

        Provider(final Case c, final GameObject intended, final List<GameObject> fillerTargets,
                 final List<ReplayDecision> replay) {
            this.intended = intended;
            this.replay = replay;
            this.fillerSemantics = new ArrayList<>();
            for (final GameObject filler : fillerTargets) {
                final String semantic = semanticFor(filler);
                if (!semantic.equals(semanticFor(intended)) && !this.fillerSemantics.contains(semantic)) {
                    this.fillerSemantics.add(semantic);
                }
            }
        }
'''
    text = replace_once(text, old, new, "Provider filler fields")

    old = '''            } else {
                final String desiredSemantic;
                if (!selected) {
                    desiredSemantic = intended instanceof Player
                            ? "PLAYER:" + ((Player) intended).getId()
                            : intended instanceof SpellAbility
                            ? "STACK:" + ((SpellAbility) intended).getId()
                            : "CARD:" + ((Card) intended).getId();
                } else {
                    desiredSemantic = "DONE";
                }
                chosen = request.getOptions().stream()
                        .filter(option -> desiredSemantic.equals(option.getSemanticValue()))
                        .findFirst()
                        .orElseThrow(() -> new IllegalStateException(
                                "fixture-designated target transition not offered by Forge: " + desiredSemantic));
            }
'''
    new = '''            } else {
                if (!selected) {
                    final String desiredSemantic = semanticFor(intended);
                    chosen = request.getOptions().stream()
                            .filter(option -> desiredSemantic.equals(option.getSemanticValue()))
                            .findFirst()
                            .orElseThrow(() -> new IllegalStateException(
                                    "fixture-designated target transition not offered by Forge: " + desiredSemantic));
                } else {
                    final ExternalDecisionRequest.Option done = request.getOptions().stream()
                            .filter(option -> "DONE".equals(option.getSemanticValue()))
                            .findFirst().orElse(null);
                    if (done != null) {
                        chosen = done;
                    } else {
                        ExternalDecisionRequest.Option fillerChoice = null;
                        for (final String semantic : fillerSemantics) {
                            if (usedFillerSemantics.contains(semantic)) continue;
                            fillerChoice = request.getOptions().stream()
                                    .filter(option -> semantic.equals(option.getSemanticValue()))
                                    .findFirst().orElse(null);
                            if (fillerChoice != null) {
                                usedFillerSemantics.add(semantic);
                                break;
                            }
                        }
                        if (fillerChoice == null) {
                            throw new IllegalStateException(
                                    "Forge requires another target but exposes no predeclared qualification filler");
                        }
                        chosen = fillerChoice;
                    }
                }
            }
'''
    text = replace_once(text, old, new, "Provider explicit filler policy")

    marker = '''        void assertConsumed() {
'''
    semantic_helper = '''        private static String semanticFor(final GameObject object) {
            return object instanceof Player
                    ? "PLAYER:" + ((Player) object).getId()
                    : object instanceof SpellAbility
                    ? "STACK:" + ((SpellAbility) object).getId()
                    : "CARD:" + ((Card) object).getId();
        }

'''
    text = replace_once(text, marker, semantic_helper + marker, "Provider semantic helper")

    # Record schema: retain actual cardinality and assert the authoritative
    # range instead of falsely asserting a single target.
    old = '''                + "\\\"final_semantic_state\\\":{"\n                + "\\\"target_count\\\":1,"
'''
    new = '''                + "\\\"final_semantic_state\\\":{"\n                + "\\\"target_count\\\":" + result.finalTargetCount + ","
                + "\\\"target_min\\\":" + result.authoritativeMinTargets + ","
                + "\\\"target_max\\\":" + result.authoritativeMaxTargets + ","
'''
    text = replace_once(text, old, new, "record final target count")

    old = '''                + "\\\"state_assertions\\\":["
                + assertion("target-count", 1, result.finalTargetCount) + ","
                + assertion("target-number-valid", true, result.targetNumberValid) + ","
'''
    new = '''                + "\\\"state_assertions\\\":["
                + assertion("target-count-within-authoritative-range", true,
                        result.finalTargetCount >= result.authoritativeMinTargets
                                && result.finalTargetCount <= result.authoritativeMaxTargets) + ","
                + assertion("target-number-valid", true, result.targetNumberValid) + ","
'''
    text = replace_once(text, old, new, "record range assertion")

    old = '''                + "\\\"assertion_ids\\\":[\\\"target-count\\\",\\\"target-number-valid\\\",\\\"intended-target-selected\\\",\\\"authoritative-option-contained-intended\\\"]"
'''
    new = '''                + "\\\"assertion_ids\\\":[\\\"target-count-within-authoritative-range\\\",\\\"target-number-valid\\\",\\\"intended-target-selected\\\",\\\"authoritative-option-contained-intended\\\"]"
'''
    text = replace_once(text, old, new, "record assertion ids")

    old = '''        final int finalTargetCount;
        final boolean targetNumberValid;
'''
    new = '''        final int finalTargetCount;
        final int authoritativeMinTargets;
        final int authoritativeMaxTargets;
        final boolean targetNumberValid;
'''
    text = replace_once(text, old, new, "Result cardinality fields")

    old = '''        Result(int initialTargetCount, int finalTargetCount, boolean targetNumberValid,
               boolean intendedTargetSelected, boolean sawIntended, String selectedKind,
'''
    new = '''        Result(int initialTargetCount, int finalTargetCount,
               int authoritativeMinTargets, int authoritativeMaxTargets, boolean targetNumberValid,
               boolean intendedTargetSelected, boolean sawIntended, String selectedKind,
'''
    text = replace_once(text, old, new, "Result constructor signature")

    old = '''            this.initialTargetCount = initialTargetCount;
            this.finalTargetCount = finalTargetCount;
            this.targetNumberValid = targetNumberValid;
'''
    new = '''            this.initialTargetCount = initialTargetCount;
            this.finalTargetCount = finalTargetCount;
            this.authoritativeMinTargets = authoritativeMinTargets;
            this.authoritativeMaxTargets = authoritativeMaxTargets;
            this.targetNumberValid = targetNumberValid;
'''
    text = replace_once(text, old, new, "Result constructor assignments")

    args.test.write_text(text, encoding="utf-8")
    print("WS33_A1_CARDINALITY_HARNESS_REPAIR=PASS")
    print("WS33_A1_CARDINALITY_AUTHORITY=FORGE_TARGET_RESTRICTIONS")
    print("WS33_A1_FILLER_POLICY=PREDECLARED_SEMANTIC_WHITELIST")
    print("WS33_A1_SILENT_FALLBACK=FALSE")
    print("WS33_A1_RULES_MUTATION=FALSE")


if __name__ == "__main__":
    main()
