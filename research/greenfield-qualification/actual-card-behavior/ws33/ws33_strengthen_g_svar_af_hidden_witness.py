#!/usr/bin/env python3
"""Strengthen AF witnesses whose hidden consumer is gated by a source Count$Valid ...+tapped SVar.

This transform is qualification-only. It does not choose a Magic action, derive legality,
or alter production rules code. It consumes the actual target-SVar script and the actual
source card's SVar at runtime. If the target script references a simple source SVar whose
expression is `Count$Valid <predicate>` and that exact predicate requires `+tapped`, the
witness establishes a positive precondition by tapping one battlefield card that Forge's
own `Card.isValid` accepts for the exact predicate. No card name or path id is used.

The purpose is to prevent a source-proven hidden consumer such as `ScryNum$ X` from being
qualified only through its zero/no-op branch when X is defined by a tapped-card count.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_G_SVAR_AF_HIDDEN_WITNESS=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    args = ap.parse_args()
    text = args.harness.read_text(encoding="utf-8")

    helper_anchor = "private static boolean matchesTarget(CaseSpec spec,AbilitySub sub){"
    helper = (
        'private static void prepareSourceDependentPositiveWitness(CaseSpec spec,SpellAbility sa,Card source,Player actor){'
        'Map<String,String>target=AbilityFactory.getMapParams(spec.targetScript);'
        'Set<String>refs=new LinkedHashSet<>(target.values());'
        'for(String ref:refs){if(ref==null||!ref.matches("[A-Za-z][A-Za-z0-9_]*")||!source.getCurrentState().hasSVar(ref))continue;'
        'String expr=source.getCurrentState().getSVar(ref);String prefix="Count$Valid ";if(!expr.startsWith(prefix))continue;'
        'String valid=expr.substring(prefix.length()).trim();if(valid.isEmpty()||!valid.contains("+tapped"))continue;'
        'for(Card candidate:actor.getCardsIn(ZoneType.Battlefield)){boolean wasTapped=candidate.isTapped();candidate.setTapped(true);'
        'if(candidate.isValid(valid.split(","),actor,source,sa))return;candidate.setTapped(wasTapped);}'
        'throw new IllegalStateException("no Forge-valid battlefield candidate for source Count$Valid tapped witness "+ref+"="+expr+" path="+spec.pathId);'
        '}}\n    '
    )
    text = replace_once(text, helper_anchor, helper + helper_anchor, "source-SVar positive precondition helper")

    call_anchor = "SpellAbility sa=resolveSourceParent(spec,source);sa.setActivatingPlayer(actor);"
    call = call_anchor + "prepareSourceDependentPositiveWitness(spec,sa,source,actor);"
    text = replace_once(text, call_anchor, call, "source-SVar precondition call")

    required = (
        "prepareSourceDependentPositiveWitness(spec,sa,source,actor)",
        'expr.startsWith(prefix)',
        'valid.contains("+tapped")',
        'candidate.isValid(valid.split(","),actor,source,sa)',
        "candidate.setTapped(true)",
        "candidate.setTapped(wasTapped)",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise SystemExit("WS33_G_SVAR_AF_HIDDEN_WITNESS=FAIL missing=" + repr(missing))
    if "Alibou" in text or "a817142" in text:
        raise SystemExit("WS33_G_SVAR_AF_HIDDEN_WITNESS=FAIL card/path-specific branch forbidden")

    args.harness.write_text(text, encoding="utf-8")
    print("WS33_G_SVAR_AF_HIDDEN_WITNESS=PASS")
    print("WS33_G_SVAR_AF_HIDDEN_WITNESS_SOURCE=ACTUAL_TARGET_SCRIPT_PLUS_SOURCE_SVAR")
    print("WS33_G_SVAR_AF_HIDDEN_WITNESS_VALIDITY=FORGE_CARD_ISVALID")
    print("WS33_G_SVAR_AF_HIDDEN_WITNESS_CARD_NAME_BRANCH=0")
    print("WS33_G_SVAR_AF_HIDDEN_WITNESS_PATH_ID_BRANCH=0")


if __name__ == "__main__":
    main()
