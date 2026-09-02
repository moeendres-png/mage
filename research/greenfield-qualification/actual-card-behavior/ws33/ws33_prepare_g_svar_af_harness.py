#!/usr/bin/env python3
"""Adapt the already stack-qualified Direct-G harness for the 21 SVar AF parents.

The input must already have been produced by ws33_prepare_g_ability_harness.py.  This
adapter changes only campaign identity/cardinality; it does not reintroduce direct resolve,
manual targets, or any pilot/rules fallback.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_G_SVAR_AF_HARNESS=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    s = args.harness.read_text(encoding="utf-8")
    s = replace_once(
        s,
        'if(cases.size()!=28)throw new IllegalStateException("WS33 G-ABILITY expected 28 cases, got "+cases.size());',
        'if(cases.size()!=21)throw new IllegalStateException("WS33 G-SVAR-AF expected 21 cases, got "+cases.size());',
        "case cardinality",
    )
    s = s.replace("Ws33GAbilityQualificationTest", "Ws33GSVarAfQualificationTest")
    s = s.replace("WS33 G-ABILITY", "WS33 G-SVAR-AF")
    if "sa.resolve()" in s or "sa.getTargets().add(" in s:
        raise SystemExit("WS33_G_SVAR_AF_HARNESS=FAIL forbidden direct rules shortcut remains")
    for required in ("sa.setupTargets()", "getStack().addAndUnfreeze(sa)", "getStack().resolveStack()"):
        if required not in s:
            raise SystemExit(f"WS33_G_SVAR_AF_HARNESS=FAIL missing production route {required}")
    args.harness.write_text(s, encoding="utf-8")
    print("WS33_G_SVAR_AF_HARNESS=PASS paths=21 parent_entry=TRUE direct_target_svar=FALSE")


if __name__ == "__main__":
    main()
