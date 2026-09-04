#!/usr/bin/env python3
"""Run frozen WS33 request instrumentation, generic obligation fixtures, and observation-only cost tracing."""
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
    patch_triggered_sources_sacrifice_cost(harness)


if __name__ == "__main__":
    main()
