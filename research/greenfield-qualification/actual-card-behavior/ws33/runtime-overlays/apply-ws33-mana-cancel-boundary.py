#!/usr/bin/env python3
"""Normalize WS01 MANA_PAYMENT cancellation onto the external response cancel channel.

Applied after the immutable WS01 mana/convoke bridge. Forge remains sole authority for
payment transitions. This overlay changes only representation of an already-authorized
cancel transition: `CANCEL` is no longer a normal discrete option; non-mandatory payment
uses ExternalDecisionRequest.cancelAllowed and ExternalDecisionResponse.cancel instead.
It does not add/filter mana payment transitions, inspect mana colors in the pilot, mutate
mana/cost state, or bypass CostPayment.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_MANA_CANCEL_BOUNDARY=FAIL " + m)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    path = args.forge_root.resolve() / "forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java"
    src = path.read_text(encoding="utf-8")

    src = replace_once(
        src,
        '''            if (!mandatory) {\n                actions.add("CANCEL");\n            }\n            if (actions.isEmpty()) {\n''',
        '''            if (actions.isEmpty()) {\n''',
        "ordinary CANCEL option removal",
    )

    src = replace_once(
        src,
        '''            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,\n                    "MANA_PAYMENT", value -> value).get(0);\n            if ("CANCEL".equals(action)) {\n                if (mandatory) {\n                    throw new ExternalDecisionValidationException(\n                            ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED,\n                            "mandatory mana payment cannot cancel");\n                }\n                onCancel();\n                return;\n            }\n''',
        '''            final List<String> selectedActions = getController().chooseExternalUiOptions(\n                    actions, 1, 1, !mandatory, false, "MANA_PAYMENT", value -> value);\n            if (selectedActions.isEmpty()) {\n                if (mandatory) {\n                    throw new ExternalDecisionValidationException(\n                            ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED,\n                            "mandatory mana payment cannot cancel");\n                }\n                onCancel();\n                return;\n            }\n            final String action = selectedActions.get(0);\n''',
        "request-level cancellation",
    )

    require('actions.add("CANCEL")' not in src, "ordinary CANCEL payment option remains")
    require('"MANA_PAYMENT", value -> value' in src, "Forge-owned payment semantic mapper missing")
    require('actions, 1, 1, !mandatory, false, "MANA_PAYMENT"' in src,
            "request-level cancelAllowed mapping missing")
    require('if (selectedActions.isEmpty())' in src and 'onCancel();' in src,
            "response-cancel handling missing")
    require('isManaAbilityFor(saPaidFor, colorCanUse)' in src,
            "Forge payment transition filtering missing")
    require('tryPayCostWithMana(saPaidFor, manaCost, selectedMana, false)' in src,
            "Forge floating-mana revalidation missing")

    path.write_text(src, encoding="utf-8")
    print("WS33_MANA_CANCEL_BOUNDARY=PASS cancel_encoding=REQUEST_LEVEL ordinary_cancel_option=FALSE")
    print("WS33_MANA_CANCEL_RULES_MUTATION=0 payment_transition_filter=FORGE payment_revalidation=FORGE")


if __name__ == "__main__":
    main()
