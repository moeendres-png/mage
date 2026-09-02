#!/usr/bin/env python3
"""Externalize ordinary Forge target transitions without replacing target legality."""

from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one WS33 target-selection anchor in {path}, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def remove_zero_or_one(path: Path, value: str) -> None:
    """Remove a strict-boundary rejection whether WS01 already removed it or not."""
    text = path.read_text(encoding="utf-8")
    count = text.count(value)
    if count > 1:
        raise SystemExit(f"expected at most one WS33 target-selection rejection in {path}, found {count}")
    if count == 1:
        path.write_text(text.replace(value, "", 1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    forge = args.forge_root.resolve()
    controller = forge / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    selection = forge / "forge-gui/src/main/java/forge/player/TargetSelection.java"

    remove_zero_or_one(controller, '        rejectExternalDecision("TARGET_SELECTION");\n')
    remove_zero_or_one(controller, '        rejectExternalDecision("TARGET_RESELECTION");\n')

    replace_once(
        controller,
        "    private <T extends GameEntity> List<T> chooseExternalEntities(final FCollectionView<T> optionList,\n",
        """    static final class ExternalTargetTransition {
        enum Kind { TARGET, DONE, CANCEL }

        private final Kind kind;
        private final GameEntity target;

        private ExternalTargetTransition(final Kind kind, final GameEntity target) {
            this.kind = kind;
            this.target = target;
        }

        static ExternalTargetTransition target(final GameEntity target) {
            return new ExternalTargetTransition(Kind.TARGET, target);
        }

        static ExternalTargetTransition done() {
            return new ExternalTargetTransition(Kind.DONE, null);
        }

        static ExternalTargetTransition cancel() {
            return new ExternalTargetTransition(Kind.CANCEL, null);
        }

        Kind getKind() { return kind; }
        GameEntity getTarget() { return target; }
    }

    ExternalTargetTransition chooseExternalTargetTransition(final List<GameEntity> candidates,
                                                            final boolean doneAllowed,
                                                            final boolean cancelAllowed,
                                                            final SpellAbility sa) {
        if (candidates == null) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "authoritative target candidates are unavailable");
        }
        final List<ExternalDecisionRequest.Option> options = new ArrayList<>();
        final Map<String, GameEntity> entityByOption = new LinkedHashMap<>();
        for (final GameEntity entity : candidates) {
            if (entity == null) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "authoritative target candidate is null");
            }
            final String optionId = ExternalDecisionRequest.optionIdFor(entity);
            if (entityByOption.put(optionId, entity) != null) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "authoritative target option ids are not unique");
            }
            options.add(new ExternalDecisionRequest.Option(optionId,
                    ExternalDecisionRequest.optionKindFor(entity), entity.getId()));
        }
        if (doneAllowed) {
            options.add(ExternalDecisionRequest.Option.discrete(
                    "choice:0", "TARGET_ACTION", "DONE"));
        }
        if (options.isEmpty()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "TARGET_SELECTION has no authoritative transition");
        }

        final Map<String, String> constraints = new LinkedHashMap<>();
        constraints.put("ordered", "false");
        constraints.put("choice_encoding", "entity_or_authoritative_transition");
        constraints.put("iterative", "true");
        final Map<String, String> context = new LinkedHashMap<>();
        context.put("controller", "PlayerControllerHuman:TARGET_SELECTION");
        context.put("decision_family", "TARGET_SELECTION");
        context.put("spell_ability_id", String.valueOf(sa.getId()));
        final ExternalDecisionResponse response = requestExternalSelection(
                "TARGET_SELECTION", options, 1, 1, cancelAllowed,
                ExternalDecisionRequest.DISCRETE_RESPONSE_SCHEMA, constraints, context);
        if (response.isCancel()) {
            return ExternalTargetTransition.cancel();
        }
        final String optionId = response.getSelectedOptionIds().get(0);
        if ("choice:0".equals(optionId)) {
            return ExternalTargetTransition.done();
        }
        final GameEntity selected = entityByOption.get(optionId);
        if (selected == null) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "validated target option has no server-side entity");
        }
        return ExternalTargetTransition.target(selected);
    }

    private <T extends GameEntity> List<T> chooseExternalEntities(final FCollectionView<T> optionList,
""",
    )

    selection_text = selection.read_text(encoding="utf-8")
    if "import forge.gamemodes.match.input.ExternalDecisionValidationException;\n" not in selection_text:
        replace_once(
            selection,
            "import forge.gamemodes.match.input.InputSelectTargets;\n",
            "import forge.gamemodes.match.input.ExternalDecisionValidationException;\n"
            "import forge.gamemodes.match.input.InputSelectTargets;\n",
        )

    replace_once(
        selection,
        """        if (validTargets.isEmpty()) {
""",
        """        if (controller.hasExternalDecisionProvider()) {
            return chooseExternalTargets(numTargets, filter, mandatory, canFilterMustTarget);
        }

        if (validTargets.isEmpty()) {
""",
    )
    replace_once(
        selection,
        """    private boolean chooseCardFromList(final List<Card> choices, final boolean targeted, final boolean mandatory) {
""",
        """    private List<GameEntity> currentExternalCandidates(final Predicate<GameObject> filter,
                                                               final boolean canFilterMustTarget) {
        final List<GameEntity> authoritative = getTgt().getAllCandidates(ability);
        List<Card> validCards = CardUtil.getValidCardsToTarget(ability);
        final boolean mustTargetFiltered = canFilterMustTarget
                && StaticAbilityMustTarget.filterMustTargetCards(controller.getPlayer(), validCards, ability);
        if (filter != null) {
            validCards = new CardCollection(IterableUtil.filter(validCards, filter));
        }
        final Set<Card> validCardSet = new HashSet<>(validCards);
        final List<GameEntity> result = new ArrayList<>();
        for (final GameEntity candidate : authoritative) {
            if (candidate instanceof Card card) {
                if (validCardSet.contains(card)) {
                    result.add(card);
                }
            } else if (!mustTargetFiltered) {
                result.add(candidate);
            }
        }
        return result;
    }

    private boolean chooseExternalTargets(final Integer numTargets,
                                          final Predicate<GameObject> filter,
                                          final boolean mandatory,
                                          final boolean canFilterMustTarget) {
        while (true) {
            if (ability.isMaxTargetChosen()
                    || (numTargets != null && ability.getTargets().size() == numTargets)) {
                bTargetingDone = true;
                return true;
            }
            final boolean doneAllowed = ability.isMinTargetChosen()
                    && (numTargets == null || ability.getTargets().size() == numTargets);
            final List<GameEntity> candidates = currentExternalCandidates(filter, canFilterMustTarget);
            if (candidates.isEmpty()) {
                if (doneAllowed) {
                    bTargetingDone = true;
                    return true;
                }
                return false;
            }

            final PlayerControllerHuman.ExternalTargetTransition transition =
                    controller.chooseExternalTargetTransition(candidates, doneAllowed, !mandatory, ability);
            switch (transition.getKind()) {
                case DONE:
                    if (!doneAllowed) {
                        throw new ExternalDecisionValidationException(
                                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                                "DONE is stale for the current target state");
                    }
                    bTargetingDone = true;
                    return true;
                case CANCEL:
                    if (mandatory) {
                        throw new ExternalDecisionValidationException(
                                ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED,
                                "CANCEL is stale for mandatory targeting");
                    }
                    return false;
                case TARGET:
                    final GameEntity selected = transition.getTarget();
                    final List<GameEntity> refreshed = currentExternalCandidates(filter, canFilterMustTarget);
                    if (!refreshed.contains(selected) || !ability.canTarget(selected)) {
                        throw new ExternalDecisionValidationException(
                                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                                "target option became stale before application");
                    }
                    if (!ability.getTargets().add(selected)) {
                        throw new ExternalDecisionValidationException(
                                ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                                "Forge rejected an authoritative target transition");
                    }
                    break;
                default:
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                            "unknown authoritative target transition");
            }
        }
    }

    private boolean chooseCardFromList(final List<Card> choices, final boolean targeted, final boolean mandatory) {
""",
    )

    # G-only diagnostic instrumentation.  The copied WS05 probe remains a test observer;
    # this emits only transport metadata and identity-field classes, never hidden values.
    probe = forge / "forge-gui-desktop/src/test/java/forge/net/Ws05HiddenInfoProbe.java"
    if probe.is_file():
        replace_once(
            probe,
            '                            example("transport:" + source + ":client=" + clientName + ":zone=" + zone + ":phase=" + phase);\n',
            '''                            StringBuilder ws33Kinds = new StringBuilder();
                            if (meaningful(card.getName(), "Card", "Face Down Card", "Face-down card")) ws33Kinds.append("CARD_NAME,");
                            if (meaningful(card.getOracleName())) ws33Kinds.append("CARD_ORACLE_NAME,");
                            try {
                                CardView.CardStateView ws33State = card.getCurrentState();
                                if (ws33State != null) {
                                    if (meaningful(ws33State.getName(), "Card", "Face Down Card", "Face-down card")) ws33Kinds.append("STATE_NAME,");
                                    if (meaningful(ws33State.getOracleName())) ws33Kinds.append("STATE_ORACLE_NAME,");
                                    if (meaningful(ws33State.getTrackableImageKey())) ws33Kinds.append("STATE_IMAGE_KEY,");
                                    if (meaningful(ws33State.getOracleText())) ws33Kinds.append("STATE_ORACLE_TEXT,");
                                    if (meaningful(ws33State.getRulesText())) ws33Kinds.append("STATE_RULES_TEXT,");
                                }
                            } catch (RuntimeException ignored) { }
                            System.out.println("[WS33HiddenLeak] source=" + source + " phase=" + phase
                                    + " client=" + clientName + " ownerId=" + owner.getId() + " zone=" + zone
                                    + " cardId=" + card.getId() + " fields=" + ws33Kinds);
                            example("transport:" + source + ":client=" + clientName + ":zone=" + zone + ":phase=" + phase);
''',
        )

    print("WS33_TARGET_SELECTION_EXTERNALIZATION_APPLIED=TRUE")
    print("WS33_G_HIDDEN_LEAK_METADATA_INSTRUMENTATION=TRUE")


if __name__ == "__main__":
    main()
