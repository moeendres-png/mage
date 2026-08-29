#!/usr/bin/env python3
"""Apply the WS12 outcome overlay after the retained WS01 strict patch."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def java_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def generate_enum(contract: dict) -> str:
    categories = contract["properties"]["category"]["enum"]
    definitions = contract["x-categories"]
    constants = []
    for category in categories:
        item = definitions[category]
        constants.append(
            f'    {category}("{java_string(item["public_message"])}", '
            f'{str(item["state_commit"] == "REQUIRED").lower()})'
        )
    return """package forge.gamemodes.match.input;

/** Generated exclusively from outcome-contract.schema.json. Do not hand edit. */
public enum UnifiedOutcomeCategory {
%s;

    private final String publicMessage;
    private final boolean commitRequired;

    UnifiedOutcomeCategory(final String publicMessage, final boolean commitRequired) {
        this.publicMessage = publicMessage;
        this.commitRequired = commitRequired;
    }

    public String getPublicMessage() { return publicMessage; }
    public boolean isCommitRequired() { return commitRequired; }
}
""" % ",\n".join(constants)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.forge_root.resolve()
    here = Path(__file__).resolve().parent
    contract = json.loads((here / "outcome-contract.schema.json").read_text(encoding="utf-8"))
    main_dir = root / "forge-gui/src/main/java/forge/gamemodes/match/input"
    test_dir = root / "forge-gui/src/test/java/forge/gamemodes/match/input"
    if not (main_dir / "ExternalDecisionTape.java").exists():
        raise SystemExit("WS01 strict decision overlay must be applied before WS12")
    main_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    (main_dir / "UnifiedOutcomeCategory.java").write_text(generate_enum(contract), encoding="utf-8")
    shutil.copy2(here / "forge-overlay/UnifiedOutcome.java", main_dir / "UnifiedOutcome.java")
    shutil.copy2(here / "forge-overlay/UnifiedOutcomeMapper.java", main_dir / "UnifiedOutcomeMapper.java")
    shutil.copy2(here / "forge-overlay/Ws12FailureSemanticsContractTest.java",
                 test_dir / "Ws12FailureSemanticsContractTest.java")

    tape_path = main_dir / "ExternalDecisionTape.java"
    tape = tape_path.read_text(encoding="utf-8")
    old_field = "        private final String errorCode;\n"
    new_field = old_field + "        private final UnifiedOutcomeCategory outcomeCategory;\n"
    old_init = "            this.errorCode = errorCode;\n"
    new_init = old_init + ("            this.outcomeCategory = UnifiedOutcomeMapper.fromTape("
                           "responseStatus, errorCode, response != null && response.isCancel());\n")
    old_getter = "        public String getErrorCode() { return errorCode; }\n"
    new_getter = old_getter + "        public UnifiedOutcomeCategory getOutcomeCategory() { return outcomeCategory; }\n"
    for old in (old_field, old_init, old_getter):
        if tape.count(old) != 1:
            raise SystemExit(f"unexpected exact-pin ExternalDecisionTape structure: {old!r}")
    tape = tape.replace(old_field, new_field).replace(old_init, new_init).replace(old_getter, new_getter)
    tape_path.write_text(tape, encoding="utf-8")
    print("WS12_FORGE_OVERLAY=APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
