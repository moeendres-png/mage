#!/usr/bin/env python3
"""Validate the WS14 witness ABI, including cross-field exercise semantics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_witness(schema: dict[str, Any], witness: dict[str, Any]) -> None:
    Draft202012Validator(schema).validate(witness)

    primitive_ids = witness["primitive_ids"]
    exercise = witness["primitive_exercise"]
    exercise_ids = [item["primitive_id"] for item in exercise]
    if len(exercise_ids) != len(set(exercise_ids)):
        raise ValueError("duplicate primitive_exercise entries are not allowed")
    if set(exercise_ids) != set(primitive_ids):
        missing = sorted(set(primitive_ids) - set(exercise_ids))
        extra = sorted(set(exercise_ids) - set(primitive_ids))
        raise ValueError(
            f"primitive_exercise must cover primitive_ids exactly; missing={missing}, extra={extra}"
        )

    assertions = witness["state_assertions"]
    assertion_ids = [item["assertion_id"] for item in assertions]
    if len(assertion_ids) != len(set(assertion_ids)):
        raise ValueError("duplicate state assertion ids are not allowed")
    assertion_id_set = set(assertion_ids)
    for item in exercise:
        unknown_assertions = sorted(set(item["assertion_ids"]) - assertion_id_set)
        if unknown_assertions:
            raise ValueError(
                f"primitive {item['primitive_id']} references unknown assertions: {unknown_assertions}"
            )
        if not item["trace_event_ids"] or not item["assertion_ids"]:
            raise ValueError(
                f"primitive {item['primitive_id']} lacks trace/assertion proof"
            )

    adjudication = witness["official_rules_adjudication"]
    if adjudication["status"] == "EXTERNALLY_RULE_VALIDATED":
        if not adjudication["rules_refs"] or not adjudication["adjudication"]:
            raise ValueError(
                "EXTERNALLY_RULE_VALIDATED requires rules_refs and adjudication"
            )
    if witness["evidence_class"] == "EXTERNALLY_RULE_VALIDATED" and (
        adjudication["status"] != "EXTERNALLY_RULE_VALIDATED"
    ):
        raise ValueError(
            "EXTERNALLY_RULE_VALIDATED evidence requires matching official-rules adjudication"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--witness", type=Path, required=True)
    args = parser.parse_args()
    validate_witness(load_json(args.schema), load_json(args.witness))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
