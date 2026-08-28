#!/usr/bin/env python3
"""Static and contract smoke checks for the exact Forge Decision Export patch.

This is deliberately not a gameplay qualification.  It proves that the
research patch applies to the declared Forge pin, that the typed entity export
symbols are present, and that the complete controller/protocol census is
materialized with its remaining coverage explicitly fail-closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(forge: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(forge), *args], text=True).strip()


def source_assertions(forge: Path) -> dict[str, bool]:
    input_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSelectEntitiesFromList.java"
    proxy_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/InputProxy.java"
    controller_path = forge / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    request_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionRequest.java"
    response_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionResponse.java"
    validator_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionValidator.java"
    error_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionValidationException.java"
    synchronized_input_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSyncronizedBase.java"
    external_gui_path = forge / "forge-gui/src/main/java/forge/player/ExternalDecisionGuiAdapter.java"
    inp = input_path.read_text(encoding="utf-8")
    proxy = proxy_path.read_text(encoding="utf-8")
    controller = controller_path.read_text(encoding="utf-8")
    request = request_path.read_text(encoding="utf-8")
    response = response_path.read_text(encoding="utf-8")
    validator = validator_path.read_text(encoding="utf-8")
    error = error_path.read_text(encoding="utf-8")
    synchronized_input = synchronized_input_path.read_text(encoding="utf-8")
    external_gui = external_gui_path.read_text(encoding="utf-8")
    return {
        "typed_request_class": "class ExternalDecisionRequest" in request,
        "typed_response_class": "class ExternalDecisionResponse" in response,
        "typed_validator_class": "class ExternalDecisionValidator" in validator,
        "typed_provider_seam": "interface ExternalDecisionProvider" in (forge / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionProvider.java").read_text(encoding="utf-8"),
        "player_and_card_option_ids": 'kind + ":" + entity.getId()' in request,
        "discrete_response_schema": "DISCRETE_RESPONSE_SCHEMA" in request and "static Option discrete" in request,
        "server_mapped_discrete_options": "chooseExternalDiscrete" in controller and "requestExternalSelection" in controller,
        "authoritative_valid_choices_reapplied": "validChoices" in inp and "applyExternalSelection" in inp,
        "external_selection_is_atomic": "final List<T> resolved" in inp and "selected.addAll(resolved)" in inp,
        "gui_not_rendered_in_strict_input": "if (!getController().hasExternalDecisionProvider())" in inp,
        "gui_not_rendered_in_strict_proxy": "if (controller.hasExternalDecisionProvider())" in proxy and "return;" in proxy,
        "controller_routes_card_selection": '"ENTITY_CARD_SELECTION"' in controller,
        "controller_routes_single_selection": '"ENTITY_SINGLE_SELECTION"' in controller,
        "controller_routes_multi_selection": '"ENTITY_MULTI_SELECTION"' in controller,
        "monotonic_sequence": "AtomicLong externalDecisionSequence" in controller and "incrementAndGet" in controller,
        "timeout_is_explicit": "externalDecisionTimeoutMillis" in controller and "TimeoutException" in controller,
        "missing_response_error": "MISSING_RESPONSE" in error and "validateMissing" in validator,
        "legacy_show_and_wait_rejected": "legacy GUI input cannot block" in synchronized_input,
        "non_rendering_gui_facade": "ExternalDecisionGuiAdapter.create" in controller and "Proxy.newProxyInstance" in external_gui,
        "unmodelled_gui_paths_rejected": "unmodelled GUI operation is blocked" in external_gui,
        "unsupported_controller_paths_are_explicit": "rejectExternalDecision" in controller
        and "UNSUPPORTED_DECISION_PATH" in controller,
        "no_prompt_parser_added": "private final String prompt" not in request
        and "GameView gameView" not in request,
    }


def census(forge: Path) -> dict[str, Any]:
    controller = (forge / "forge-game/src/main/java/forge/game/player/PlayerController.java").read_text(encoding="utf-8")
    protocol = (forge / "forge-gui/src/main/java/forge/gamemodes/net/ProtocolMethod.java").read_text(encoding="utf-8")
    abstract_methods = sorted([
        match.group(1)
        for match in re.finditer(r"public\s+abstract\s+[^;{]+?\s+(\w+)\s*\((.*?)\)\s*;", controller, re.S)
    ])
    enum_block = protocol.split("public enum ProtocolMethod", 1)[1].split("private enum Mode", 1)[0]
    blocking = []
    for line in enum_block.splitlines():
        match = re.match(r"\s*(\w+)\s*\(Mode\.SERVER,\s*([^,\)]+)", line)
        if match and match.group(2).strip() != "Void.TYPE":
            blocking.append({"name": match.group(1), "return_type": match.group(2).strip()})
    return {
        "player_controller_abstract_method_count": len(abstract_methods),
        "player_controller_abstract_methods": abstract_methods,
        "remote_protocol_blocking_decision_count": len(blocking),
        "remote_protocol_blocking_decisions": blocking,
        "directly_externalized_controller_methods": [
            "chooseCardsForEffect", "chooseSingleEntityForEffect", "chooseEntitiesForEffect"
        ],
        "directly_externalized_method_count": 3,
        "remaining_controller_methods_not_externalized": max(0, len(abstract_methods) - 3),
        "full_decision_census_complete": False,
        "runtime_decision_tape_qualified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", required=True, type=Path)
    parser.add_argument("--patch", required=True, type=Path)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    actual_pin = git(args.forge_root, "rev-parse", "HEAD")
    actual_tree = git(args.forge_root, "rev-parse", "HEAD^{tree}")
    assertions = source_assertions(args.forge_root)
    count = census(args.forge_root)
    result: dict[str, Any] = {
        "schema": "commander-simulator-next.forge-decision-export-implementation.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "forge_pin": actual_pin,
        "forge_tree": actual_tree,
        "patch": {"path": str(args.patch), "sha256": sha256(args.patch)},
        "assertions": assertions,
        "census": count,
        "status": "PARTIAL",
        "gate": "FAIL",
        "runtime_qualification": "NOT_RUN",
        "failure": {
            "code": "FULL_DECISION_CENSUS_NOT_EXTERNALIZED",
            "message": "The typed entity-input boundary is implemented for three authoritative entity-selection entry points. A server-mapped discrete facade exists but remains runtime-unqualified; remaining controller and blocking GUI decisions are explicitly not admitted.",
        },
    }
    if actual_pin != FORGE_PIN:
        result["status"] = "FAIL"
        result["failure"] = {"code": "FORGE_PIN_MISMATCH", "expected": FORGE_PIN, "actual": actual_pin}
    elif not all(assertions.values()):
        result["status"] = "FAIL"
        result["failure"] = {"code": "IMPLEMENTATION_SYMBOL_MISSING", "assertions": assertions}
    elif count["player_controller_abstract_method_count"] != 109 or count["remote_protocol_blocking_decision_count"] != 15:
        result["status"] = "FAIL"
        result["failure"] = {"code": "CENSUS_PIN_ASSUMPTION_CHANGED", "census": count}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "gate": result["gate"], "forge_pin": actual_pin}, sort_keys=True))
    return 0 if result["status"] == "PARTIAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
