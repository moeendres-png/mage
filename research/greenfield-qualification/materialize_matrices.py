#!/usr/bin/env python3
"""Materialize the complete A-T and C01-C22 requirement matrices.

Definitions are copied from the versioned scenario manifest; qualification
status is never inferred from a definition or from a historical candidate
run. The current production-boundary status remains NOT_RUN until a compatible
runtime evidence bundle exists.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", required=True, type=Path)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--forge-pin", required=True)
    parser.add_argument("--out-at", required=True, type=Path)
    parser.add_argument("--out-commander", required=True, type=Path)
    args = parser.parse_args()

    scenarios: dict[str, Any] = json.loads(args.scenarios.read_text(encoding="utf-8"))
    classes = scenarios.get("classes", {})
    commander = scenarios.get("commander", {})
    if len(classes) != 20 or set(classes) != set("ABCDEFGHIJKLMNOPQRST"):
        raise SystemExit("scenario manifest must contain exactly A-T")
    if len(commander) != 22 or set(commander) != {f"C{index:02d}" for index in range(1, 23)}:
        raise SystemExit("scenario manifest must contain exactly C01-C22")

    common = {
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "external_pins": {"forge": args.forge_pin},
        "qualification_boundary": "strict_typed_decision_export_and_principal_scoped_observation",
        "qualification_status": "NOT_RUN",
        "evidence_class": "REQUIREMENT_DEFINITION_ONLY",
        "production_qualified": False,
    }
    at = {
        "schema": "commander-simulator-next.rules-matrix-a-t.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "external_pins": {"forge": args.forge_pin},
        "complete": False,
        "classes": [{"id": key, "definition": value, **common} for key, value in classes.items()],
        "reason": "The complete production-boundary runtime matrix is downstream of decision externalization, hidden-information, RNG/replay, and card-coverage gates.",
    }
    c = {
        "schema": "commander-simulator-next.rules-matrix-c01-c22.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "external_pins": {"forge": args.forge_pin},
        "complete": False,
        "definitions": [
            {"id": key, "definition": value, "source_definition_status": "AVAILABLE_IN_SCENARIO_MANIFEST", **common}
            for key, value in commander.items()
        ],
        "reason": "Definitions are materialized without promoting any historical targeted run to current production-boundary evidence.",
    }
    for target, value in ((args.out_at, at), (args.out_commander, c)):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("A_T_COUNT=", len(at["classes"]))
    print("C01_C22_COUNT=", len(c["definitions"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
