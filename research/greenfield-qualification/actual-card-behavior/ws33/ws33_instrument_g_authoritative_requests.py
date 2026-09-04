#!/usr/bin/env python3
"""Run frozen WS33 request instrumentation, obligation fixtures, systemic entity binding, and cost tracing."""
from __future__ import annotations
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "ws33_instrument_g_authoritative_requests_base_33858197355.py"
FIXTURE = ROOT / "ws33_patch_g_svar_obligation_fixture.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_G_COST_TRACE=FAIL {label}: expected exactly one anchor, got {count}")
    return text.replace(old, new, 1)


def find_forge_root(harness: Path) -> Path:
    resolved = harness.resolve()
    for candidate in resolved.parents:
        if (candidate / "forge-game").is_dir() and (candidate / "forge-gui").is_dir():
            return candidate
    raise SystemExit("WS33_G_COST_TRACE=FAIL could not resolve Forge root from harness path")


def patch_authoritative_entity_list_binding(harness: Path) -> None:
    """Replace WS01's generic choice:N synchronized entity bridge with typed entity identity.

    Forge remains authoritative for validChoices, min/max, and cancel legality. The external
    request carries entity option ids directly and uses the ABI cancel channel; the existing
    strict input methods revalidate membership/counts when applying the response.
    """
    forge_root = find_forge_root(harness)
    human = forge_root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    human_text = human.read_text(encoding="utf-8")

    helper_anchor = '''    private <T extends GameEntity> List<T> chooseExternalEntities(final FCollectionView<T> optionList,
'''
    helper_insert = r'''    public <T extends GameEntity> ExternalDecisionResponse requestWs33ExternalEntityInput(
            final FCollectionView<T> optionList, final int min, final int max,
            final boolean cancelAllowed, final SpellAbility sa, final String decisionKind) {
        if (optionList == null || optionList.isEmpty()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "external entity input requires a non-empty authoritative option set");
        }
        if (min < 0 || max < min || min > optionList.size()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "invalid authoritative entity-input bounds");
        }
        final int effectiveMax = Math.min(max, optionList.size());
        final List<ExternalDecisionRequest.Option> options = new ArrayList<>();
        final Set<String> optionIds = new HashSet<>();
        for (final T entity : optionList) {
            final String optionId = ExternalDecisionRequest.optionIdFor(entity);
            if (!optionIds.add(optionId)) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "authoritative entity-input option ids are not unique");
            }
            options.add(new ExternalDecisionRequest.Option(optionId,
                    ExternalDecisionRequest.optionKindFor(entity), entity.getId()));
        }
        final Map<String, String> constraints = new LinkedHashMap<>();
        constraints.put("ordered", "false");
        final Map<String, String> context = new LinkedHashMap<>();
        context.put("controller", "PlayerControllerHuman:" + decisionKind);
        context.put("decision_family", "ENTITY_SELECTION");
        final ExternalDecisionResponse response;
        final Ws33ExternalObservation observation = beginWs33ExternalCardObservation(optionList, decisionKind);
        try {
            response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                    cancelAllowed, ExternalDecisionRequest.RESPONSE_SCHEMA, constraints, context);
        } finally {
            endWs33ExternalCardObservation(observation);
        }
        return response;
    }

    private <T extends GameEntity> List<T> chooseExternalEntities(final FCollectionView<T> optionList,
'''
    human_text = replace_once(human_text, helper_anchor, helper_insert, "typed external entity-input helper")
    for token in (
        "requestWs33ExternalEntityInput(",
        "ExternalDecisionRequest.optionIdFor(entity)",
        "ExternalDecisionRequest.optionKindFor(entity)",
        "beginWs33ExternalCardObservation(optionList, decisionKind)",
        "cancelAllowed, ExternalDecisionRequest.RESPONSE_SCHEMA",
    ):
        if token not in human_text:
            raise SystemExit("WS33_G_ENTITY_LIST_BINDING=FAIL missing PlayerControllerHuman invariant: " + token)
    human.write_text(human_text, encoding="utf-8")

    entities = forge_root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSelectEntitiesFromList.java"
    entity_text = entities.read_text(encoding="utf-8")
    drive_anchor = r'''    public void driveExternal() {
        while (true) {
            final List<String> actions = new ArrayList<>();
            if (hasEnoughTargets()) {
                actions.add("DONE");
            }
            if (allowCancel) {
                actions.add("CANCEL");
            }
            for (final T entity : validChoices) {
                actions.add("ENTITY:" + ExternalDecisionRequest.optionIdFor(entity));
            }
            if (actions.isEmpty()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "entity selection has no authoritative transition");
            }
            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,
                    "ENTITY_LIST_SELECTION", value -> value).get(0);
            if ("DONE".equals(action)) {
                if (!hasEnoughTargets()) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "entity selection minimum is not satisfied");
                }
                onOk();
                return;
            }
            if ("CANCEL".equals(action)) {
                if (!allowCancel) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED,
                            "entity selection cannot cancel");
                }
                onCancel();
                return;
            }
            if (action != null && action.startsWith("ENTITY:")) {
                final String optionId = action.substring("ENTITY:".length());
                T selectedEntity = null;
                for (final T candidate : validChoices) {
                    if (ExternalDecisionRequest.optionIdFor(candidate).equals(optionId)) {
                        selectedEntity = candidate;
                        break;
                    }
                }
                if (selectedEntity == null || !selectEntity(selectedEntity)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "entity selection token became stale");
                }
                if (hasAllTargets()) {
                    onOk();
                    return;
                }
                continue;
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "unknown entity selection action token");
        }
    }
'''
    drive_insert = r'''    public void driveExternal() {
        if (validChoices.isEmpty()) {
            if (min != 0) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "entity selection minimum cannot be satisfied by an empty option set");
            }
            applyExternalSelection(List.of());
            return;
        }
        final ExternalDecisionResponse response = getController().requestWs33ExternalEntityInput(
                validChoices, min, max, allowCancel, sa, "ENTITY_LIST_SELECTION");
        if (response.isCancel()) {
            applyExternalCancel();
        } else {
            applyExternalSelection(response.getSelectedOptionIds());
        }
    }
'''
    entity_text = replace_once(entity_text, drive_anchor, drive_insert, "typed synchronized entity-list drive")
    forbidden = (
        'actions.add("CANCEL")',
        'actions.add("ENTITY:"',
        'chooseExternalUiOptions(actions',
        'action.startsWith("ENTITY:")',
    )
    for token in forbidden:
        if token in entity_text:
            raise SystemExit("WS33_G_ENTITY_LIST_BINDING=FAIL stale generic bridge token: " + token)
    for token in (
        "requestWs33ExternalEntityInput(",
        "applyExternalCancel();",
        "applyExternalSelection(response.getSelectedOptionIds());",
    ):
        if token not in entity_text:
            raise SystemExit("WS33_G_ENTITY_LIST_BINDING=FAIL missing InputSelectEntitiesFromList invariant: " + token)
    entities.write_text(entity_text, encoding="utf-8")

    print("WS33_G_ENTITY_LIST_BINDING=PASS option_identity=AUTHORITATIVE_ENTITY cancel=ABI_CHANNEL membership=STRICT_INPUT_REVALIDATION hidden_observation=PRINCIPAL_SCOPED")


def patch_triggered_sources_sacrifice_cost(harness: Path) -> None:
    forge_root = find_forge_root(harness)
    path = forge_root / "forge-gui/src/main/java/forge/player/HumanCostDecision.java"
    text = path.read_text(encoding="utf-8")

    class_anchor = "public class HumanCostDecision extends CostDecisionMakerBase {\n"
    class_insert = r'''public class HumanCostDecision extends CostDecisionMakerBase {
    private static boolean ws33TraceTriggeredSourcesSacrifice(final SpellAbility ability, final String type) {
        return ability != null && ability.isTrigger() && type != null && type.contains("TriggeredSources");
    }

    private static String ws33CardIds(final Object value) {
        if (value == null) return "";
        if (value instanceof Card card) return Integer.toString(card.getId());
        if (!(value instanceof Iterable<?> values)) return "NON_ITERABLE";
        final StringBuilder out = new StringBuilder();
        for (final Object item : values) {
            if (!(item instanceof Card card)) continue;
            if (out.length() > 0) out.append(',');
            out.append(card.getId());
        }
        return out.toString();
    }

    private static String ws33AbilityIdentity(final SpellAbility ability) {
        final Card host = ability == null ? null : ability.getHostCard();
        return (ability == null ? "-1" : Integer.toString(ability.getId())) + "\t"
                + (ability == null ? "-1" : Integer.toString(ability.getSourceTrigger())) + "\t"
                + (host == null ? "-1" : Integer.toString(host.getId())) + "\t"
                + (ability == null || ability.getApi() == null ? "" : ability.getApi().name());
    }
'''
    text = replace_once(text, class_anchor, class_insert, "HumanCostDecision class helper")

    amount_anchor = '''        CardCollectionView list = CardLists.filter(player.getCardsIn(ZoneType.Battlefield), CardPredicates.canBeSacrificedBy(ability, isEffect()));
        list = CardLists.getValidCards(list, type.split(";"), player, source, ability);

        if (amount.equals("All")) {
            return PaymentDecision.card(list);
        }

        int c = cost.getAbilityAmount(ability);
        if (0 == c) {
'''
    amount_insert = '''        CardCollectionView list = CardLists.filter(player.getCardsIn(ZoneType.Battlefield), CardPredicates.canBeSacrificedBy(ability, isEffect()));
        list = CardLists.getValidCards(list, type.split(";"), player, source, ability);

        if (amount.equals("All")) {
            return PaymentDecision.card(list);
        }

        int c = cost.getAbilityAmount(ability);
        if (ws33TraceTriggeredSourcesSacrifice(ability, type)) {
            final SpellAbility ws33Root = ability.getRootAbility();
            final Object ws33Sources = ws33Root == null ? null : ws33Root.getTriggeringObject(forge.game.ability.AbilityKey.Sources);
            System.err.println("WS33_SACRIFICE_COST\\tCANDIDATES\\t" + ws33AbilityIdentity(ability)
                    + "\\trequired=" + c + "\\tmandatory=" + mandatory
                    + "\\tsources=" + ws33CardIds(ws33Sources)
                    + "\\tcandidates=" + ws33CardIds(list) + "\\tcandidateCount=" + list.size());
        }
        if (0 == c) {
'''
    text = replace_once(text, amount_anchor, amount_insert, "CostSacrifice TriggeredSources candidate site")

    selection_anchor = '''        final InputSelectCardsFromList inp = new InputSelectCardsFromList(controller, c, c, list, ability);
        inp.setMessage(Localizer.getInstance().getMessage("lblSelectATargetToSacrifice", cost.getDescriptiveType(), "%d"));
        inp.setCancelAllowed(!mandatory);
        inp.showAndWait();
        if (inp.hasCancelled()) {
            return null;
        }

        return PaymentDecision.card(inp.getSelected());
'''
    selection_insert = '''        final InputSelectCardsFromList inp = new InputSelectCardsFromList(controller, c, c, list, ability);
        inp.setMessage(Localizer.getInstance().getMessage("lblSelectATargetToSacrifice", cost.getDescriptiveType(), "%d"));
        inp.setCancelAllowed(!mandatory);
        inp.showAndWait();
        final boolean ws33Cancelled = inp.hasCancelled();
        if (ws33TraceTriggeredSourcesSacrifice(ability, type)) {
            System.err.println("WS33_SACRIFICE_COST\\tSELECTION\\t" + ws33AbilityIdentity(ability)
                    + "\\tcancelled=" + ws33Cancelled
                    + "\\tselectedCount=" + (ws33Cancelled ? -1 : inp.getSelected().size())
                    + "\\tselected=" + (ws33Cancelled ? "" : ws33CardIds(inp.getSelected())));
        }
        if (ws33Cancelled) {
            return null;
        }

        return PaymentDecision.card(inp.getSelected());
'''
    text = replace_once(text, selection_anchor, selection_insert, "CostSacrifice TriggeredSources selection site")

    for token in (
        "WS33_SACRIFICE_COST",
        "getRootAbility()",
        "AbilityKey.Sources",
        "candidateCount=",
        "selectedCount=",
        "ws33Cancelled",
    ):
        if token not in text:
            raise SystemExit("WS33_G_COST_TRACE=FAIL missing generated HumanCostDecision invariant: " + token)
    path.write_text(text, encoding="utf-8")

    cost_payment = forge_root / "forge-game/src/main/java/forge/game/cost/CostPayment.java"
    payment_text = cost_payment.read_text(encoding="utf-8")
    payment_anchor = '''                PaymentDecision pd = part.accept(decisionMaker);

                // Right before we start paying as decided, we need to transfer the CostPayments matrix over?
                if (pd != null) {
                    pd.matrix = this;
                }

                if (pd == null || !part.payAsDecided(decisionMaker.getPlayer(), pd, ability, decisionMaker.isEffect())) {
                    return false;
                }
                this.paidCostParts.add(part);
'''
    payment_insert = '''                PaymentDecision pd = part.accept(decisionMaker);
                final boolean ws33TriggeredSourcesSacrifice = part instanceof CostSacrifice
                        && ability != null && ability.isTrigger()
                        && ((CostSacrifice) part).getType() != null
                        && ((CostSacrifice) part).getType().contains("TriggeredSources");
                if (ws33TriggeredSourcesSacrifice) {
                    System.err.println("WS33_SACRIFICE_COST\\tDECISION\\t"
                            + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t"
                            + (ability.getHostCard() == null ? -1 : ability.getHostCard().getId()) + "\\t"
                            + (ability.getApi() == null ? "" : ability.getApi().name())
                            + "\\tdecisionNull=" + (pd == null));
                }

                // Right before we start paying as decided, we need to transfer the CostPayments matrix over?
                if (pd != null) {
                    pd.matrix = this;
                }

                if (pd == null) {
                    if (ws33TriggeredSourcesSacrifice) {
                        System.err.println("WS33_SACRIFICE_COST\\tRESULT\\t"
                                + ability.getId() + "\\t" + ability.getSourceTrigger()
                                + "\\tresult=false\\treason=DECISION_NULL");
                    }
                    return false;
                }
                final boolean ws33PaidAsDecided = part.payAsDecided(decisionMaker.getPlayer(), pd, ability, decisionMaker.isEffect());
                if (ws33TriggeredSourcesSacrifice) {
                    System.err.println("WS33_SACRIFICE_COST\\tRESULT\\t"
                            + ability.getId() + "\\t" + ability.getSourceTrigger()
                            + "\\tresult=" + ws33PaidAsDecided + "\\treason=PAY_AS_DECIDED");
                }
                if (!ws33PaidAsDecided) {
                    return false;
                }
                this.paidCostParts.add(part);
'''
    payment_text = replace_once(payment_text, payment_anchor, payment_insert, "CostPayment human payment result site")
    for token in (
        "ws33TriggeredSourcesSacrifice",
        "decisionNull=",
        "reason=DECISION_NULL",
        "reason=PAY_AS_DECIDED",
    ):
        if token not in payment_text:
            raise SystemExit("WS33_G_COST_TRACE=FAIL missing generated CostPayment invariant: " + token)
    cost_payment.write_text(payment_text, encoding="utf-8")

    print("WS33_G_COST_TRACE=PASS boundary=TRIGGERED_SOURCES_SACRIFICE observation_only=TRUE root_sources=TRUE selection=TRUE payment_result=TRUE ids_only=TRUE")


def main() -> None:
    original = list(sys.argv)
    runpy.run_path(str(BASE), run_name="__main__")
    try:
        i = original.index("--harness")
        harness = Path(original[i + 1])
    except (ValueError, IndexError) as exc:
        raise SystemExit("WS33_G_SVAR_OBLIGATION_FIXTURE=FAIL missing --harness") from exc
    subprocess.check_call([sys.executable, str(FIXTURE), "--harness", str(harness)])
    patch_authoritative_entity_list_binding(harness)
    patch_triggered_sources_sacrifice_cost(harness)


if __name__ == "__main__":
    main()
