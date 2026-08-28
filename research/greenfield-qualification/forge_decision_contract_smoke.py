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
    java_contract_path = forge / "forge-gui/src/test/java/forge/gamemodes/match/input/ExternalDecisionValidatorContractTest.java"
    tape_path = forge / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionTape.java"
    inp = input_path.read_text(encoding="utf-8")
    proxy = proxy_path.read_text(encoding="utf-8")
    controller = controller_path.read_text(encoding="utf-8")
    request = request_path.read_text(encoding="utf-8")
    response = response_path.read_text(encoding="utf-8")
    validator = validator_path.read_text(encoding="utf-8")
    error = error_path.read_text(encoding="utf-8")
    synchronized_input = synchronized_input_path.read_text(encoding="utf-8")
    external_gui = external_gui_path.read_text(encoding="utf-8")
    java_contract = java_contract_path.read_text(encoding="utf-8")
    tape = tape_path.read_text(encoding="utf-8")
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
        "java_validator_contract_probe": all(marker in java_contract for marker in (
            "class ExternalDecisionValidatorContractTest",
            "JAVA_EXTERNAL_DECISION_CONTRACT=PASS",
            "ExternalDecisionTape",
            "STALE_RESPONSE",
            "WRONG_ACTOR",
            "WRONG_PRINCIPAL",
            "MALFORMED_RESPONSE",
            "NULL_RESPONSE",
            "MISSING_RESPONSE",
            "UNSUPPORTED_DECISION_PATH",
            "ILLEGAL_OPTION",
            "INVALID_SELECTION_COUNT",
            "CANCEL_NOT_ALLOWED",
            "DECISION_CONSUMED",
            "TIMEOUT",
        )),
        "server_side_decision_tape": all(marker in tape for marker in (
            "class ExternalDecisionTape",
            "validateAndRecord",
            "consumedTokens",
            "ResponseStatus",
            "getSelectedOptionIds",
            "appendFailure",
        )) and "externalDecisionTape.validateAndRecord" in controller,
        "decision_tape_excludes_hidden_payload": all(marker not in tape for marker in (
            "private final ExternalDecisionRequest",
            "getSemanticContext()",
            "getOptions()",
        )),
    }


def _split_java_parameters(parameters: str) -> list[str]:
    if not parameters.strip():
        return []
    result: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(parameters):
        if character in "<([{":
            depth += 1
        elif character in ">)]}":
            depth -= 1
        elif character == "," and depth == 0:
            result.append(parameters[start:index])
            start = index + 1
    result.append(parameters[start:])
    return result


def _java_parameter_types(parameters: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for parameter in _split_java_parameters(parameters):
        value = re.sub(r"@\w+(?:\([^)]*\))?\s*", "", parameter)
        value = re.sub(r"\bfinal\s+", "", value).strip()
        value = re.sub(r"\s+", " ", value)
        value = re.sub(r"\s+[A-Za-z_$][\w$]*$", "", value)
        normalized.append(value)
    return tuple(normalized)


def _java_block(source: str, opening_brace: int) -> str | None:
    depth = 0
    for index in range(opening_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening_brace:index + 1]
    return None


def _java_public_method_bodies(source: str) -> dict[tuple[str, tuple[str, ...]], str]:
    result: dict[tuple[str, tuple[str, ...]], str] = {}
    pattern = re.compile(
        r"\bpublic\s+(?!class\b)[^;{}]+?\s+(\w+)\s*\((.*?)\)\s*(?:throws\s+[^\{]+)?\{",
        re.S,
    )
    for match in pattern.finditer(source):
        body = _java_block(source, match.end() - 1)
        if body is not None:
            result[(match.group(1), _java_parameter_types(match.group(2)))] = body
    return result


def _controller_static_status(body: str | None) -> str:
    if body is None:
        return "MISSING_OVERRIDE"
    if "rejectExternalDecision(" in body:
        return "EXPLICITLY_REJECTED_STATIC"
    if "hasExternalDecisionProvider()" in body and (
        "chooseExternal" in body or "requestExternalSelection" in body
    ):
        return "TYPED_EXTERNALIZED_STATIC"
    if any(re.search(rf"\b{name}\s*\(", body) for name in (
        "chooseCardsForEffect", "chooseSingleEntityForEffect", "chooseEntitiesForEffect",
    )):
        return "DELEGATES_TO_TYPED_EXTERNAL_STATIC"
    if "hasExternalDecisionProvider()" in body:
        return "STRICT_GUARD_UNCLASSIFIED"
    if "getGui()" in body:
        return "GUI_ADAPTER_DEPENDENT_STATIC"
    return "LEGACY_PATH_UNCLASSIFIED"


def census(forge: Path) -> dict[str, Any]:
    controller = (forge / "forge-game/src/main/java/forge/game/player/PlayerController.java").read_text(encoding="utf-8")
    protocol = (forge / "forge-gui/src/main/java/forge/gamemodes/net/ProtocolMethod.java").read_text(encoding="utf-8")
    human_controller = (forge / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java").read_text(encoding="utf-8")
    external_gui = (forge / "forge-gui/src/main/java/forge/player/ExternalDecisionGuiAdapter.java").read_text(encoding="utf-8")
    abstract_declarations = [
        (match.group(1), _java_parameter_types(match.group(2)))
        for match in re.finditer(r"public\s+abstract\s+[^;{]+?\s+(\w+)\s*\((.*?)\)\s*;", controller, re.S)
    ]
    human_methods = _java_public_method_bodies(human_controller)
    callback_census = []
    for callback_index, (name, parameter_types) in enumerate(abstract_declarations, 1):
        body = human_methods.get((name, parameter_types))
        callback_census.append({
            "callback_index": callback_index,
            "callback_id": f"{name}({', '.join(parameter_types)})",
            "name": name,
            "parameter_types": list(parameter_types),
            "static_status": _controller_static_status(body),
            "runtime_evidence": "NOT_RUN",
        })
    enum_block = protocol.split("public enum ProtocolMethod", 1)[1].split("private enum Mode", 1)[0]
    blocking = []
    for line in enum_block.splitlines():
        match = re.match(r"\s*(\w+)\s*\(Mode\.SERVER,\s*([^,\)]+)", line)
        if match and match.group(2).strip() != "Void.TYPE":
            blocking.append({"name": match.group(1), "return_type": match.group(2).strip()})
    typed_gui_handlers = {
        "showConfirmDialog", "confirm", "showOptionDialog", "showInputDialog", "getChoices",
        "order", "chooseSingleEntityForEffect", "chooseEntitiesForEffect",
    }
    explicit_gui_rejections = {
        "getAbilityToPlay", "assignCombatDamage", "assignGenericAmount", "sideboard",
        "manipulateCardList", "openZones",
    }
    gui_callback_census = []
    for decision in blocking:
        name = decision["name"]
        if name in typed_gui_handlers and f'case "{name}"' in external_gui:
            static_status = "TYPED_EXTERNALIZED_STATIC"
        elif name in explicit_gui_rejections and f'case "{name}"' in external_gui:
            static_status = "EXPLICITLY_REJECTED_STATIC"
        else:
            static_status = "FAIL_CLOSED_DEFAULT_STATIC"
        gui_callback_census.append({
            **decision,
            "static_status": static_status,
            "runtime_evidence": "NOT_RUN",
        })
    controller_status_counts: dict[str, int] = {}
    for item in callback_census:
        status = item["static_status"]
        controller_status_counts[status] = controller_status_counts.get(status, 0) + 1
    gui_status_counts: dict[str, int] = {}
    for item in gui_callback_census:
        status = item["static_status"]
        gui_status_counts[status] = gui_status_counts.get(status, 0) + 1
    return {
        "player_controller_abstract_method_count": len(abstract_declarations),
        "player_controller_abstract_methods": sorted(name for name, _ in abstract_declarations),
        "player_controller_callback_census": callback_census,
        "controller_static_classification_counts": dict(sorted(controller_status_counts.items())),
        "controller_static_census_complete": len(callback_census) == len(abstract_declarations)
        and all(item["static_status"] != "MISSING_OVERRIDE" for item in callback_census),
        "remote_protocol_blocking_decision_count": len(blocking),
        "remote_protocol_blocking_decisions": blocking,
        "remote_protocol_blocking_decision_census": gui_callback_census,
        "blocking_gui_static_classification_counts": dict(sorted(gui_status_counts.items())),
        "blocking_gui_static_census_complete": len(gui_callback_census) == len(blocking),
        "directly_externalized_controller_methods": [
            "chooseCardsForEffect", "chooseSingleEntityForEffect", "chooseEntitiesForEffect"
        ],
        "directly_externalized_method_count": 3,
        "remaining_controller_methods_not_externalized": max(0, len(abstract_declarations) - 3),
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
        "decision_tape_contract": "PASS" if assertions["server_side_decision_tape"]
        and assertions["decision_tape_excludes_hidden_payload"] else "FAIL",
        "failure": {
            "code": "FULL_DECISION_CENSUS_NOT_EXTERNALIZED",
            "message": "The typed entity-input boundary and a server-side metadata-only DecisionTape contract are implemented, but the tape has not yet been exercised through a complete game. Remaining controller and blocking GUI decisions are explicitly not admitted.",
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
