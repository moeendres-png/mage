#!/usr/bin/env python3
"""WS22 bindings from qualified Q2/Q3 detectors to the WS12 public outcome contract.

This module deliberately does not implement replay comparison or hidden-information
rules. It accepts only evidence emitted by the qualified WS06 comparator or the
WS05 principal-visibility detector and fails closed for any other shape.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

OUTCOME_SCHEMA = "commander-simulator-next.failure-outcome.v1"
TRACE_SCHEMA = "commander-simulator-next.ws22-failure-adapter-trace.v1"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("$id") != OUTCOME_SCHEMA:
        raise ValueError("unexpected WS12 outcome contract")
    return contract


def public_failure(contract: dict[str, Any], category: str, *, correlation_id: str,
                   game_id: str, decision_id: int | None = None,
                   principal_id: int | None = None) -> dict[str, Any]:
    definitions = contract.get("x-categories", {})
    if category not in definitions:
        raise ValueError(f"category absent from WS12 contract: {category}")
    definition = definitions[category]
    if definition.get("state_commit") == "REQUIRED":
        raise ValueError(f"failure category unexpectedly requires state commit: {category}")
    return {
        "schema": OUTCOME_SCHEMA,
        "category": category,
        "correlation_id": correlation_id,
        "game_id": game_id,
        "decision_id": decision_id,
        "principal_id": principal_id,
        "public_message": definition["public_message"],
        "state_committed": False,
    }


def bind_replay_divergence(contract: dict[str, Any], comparator: dict[str, Any]) -> dict[str, Any]:
    failure_codes = [item.get("code") for item in comparator.get("failures", [])]
    counts = {
        "semantic_state": comparator.get("semantic_state_divergences"),
        "rng_event": comparator.get("rng_event_divergences"),
        "decision_event": comparator.get("decision_event_divergences"),
    }
    actual_divergence = any(isinstance(value, int) and value > 0 for value in counts.values())
    first = comparator.get("first_divergence") or {}
    checks = {
        "actual_ws06_comparator_schema": comparator.get("schema") == "commander-simulator-next.semantic-replay.v2",
        "comparator_rejected_replay": comparator.get("status") == "FAIL",
        "typed_semantic_divergence_detected": "E_SEMANTIC_DIVERGENCE" in failure_codes and actual_divergence,
        "semantic_criteria_only": comparator.get("stdout_used_as_replay_criterion") is False,
        "first_divergence_structural": first.get("stream") in {"states", "rng_events", "decision_tape"}
            and isinstance(first.get("index"), int) and isinstance(first.get("path"), str),
    }
    if not all(checks.values()):
        raise ValueError(f"WS06 comparator evidence does not establish replay divergence: {checks}")

    outcome = public_failure(
        contract,
        "REPLAY_DIVERGENCE",
        correlation_id="corr:ws22:replay-divergence",
        game_id="ws06-4p-commander-game",
    )
    trace = {
        "schema": TRACE_SCHEMA,
        "category": "REPLAY_DIVERGENCE",
        "production_binding": "WS06_SEMANTIC_REPLAY_COMPARATOR_E_SEMANTIC_DIVERGENCE",
        "evidence_class": "TECHNICALLY_CONFORMANT",
        "detector": {
            "schema": comparator.get("schema"),
            "failure_codes": failure_codes,
            "divergence_counts": counts,
            "first_divergence": {
                "stream": first.get("stream"),
                "index": first.get("index"),
                "path": first.get("path"),
            },
            "stdout_used_as_replay_criterion": comparator.get("stdout_used_as_replay_criterion"),
        },
        "outcome": outcome,
        "checks": {
            **checks,
            "state_committed": outcome["state_committed"] is False,
            "no_fallback": True,
        },
        "status": "PASS",
    }
    trace["trace_sha256"] = canonical_hash(trace)
    return trace


def bind_hidden_info_violation(contract: dict[str, Any], detector: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "actual_ws05_principal_detector": detector.get("detector_boundary") == "WS05_CARDVIEW_PLAYERVIEW_AUTHORIZATION",
        "actual_identity_bearing_cardview": detector.get("actual_cardview_identity_bearing") is True,
        "cross_principal_datum_forbidden": detector.get("authorized_for_target_principal") is False,
        "detector_caught_leak": detector.get("detected") is True
            and detector.get("leaks_before") == 0 and detector.get("leaks_after") == 1,
        "public_envelope_secret_safe": detector.get("public_envelope_secret_safe") is True,
        "state_unchanged": detector.get("state_witness_unchanged") is True,
        "fail_closed": detector.get("fail_closed") is True,
    }
    if not all(checks.values()):
        raise ValueError(f"WS05 detector evidence does not establish hidden-info violation: {checks}")

    outcome = detector.get("outcome")
    if not isinstance(outcome, dict):
        raise ValueError("hidden-info detector omitted public outcome")
    expected = public_failure(
        contract,
        "HIDDEN_INFO_VIOLATION",
        correlation_id="corr:ws22:hidden-info-violation",
        game_id="ws22-4p-hidden-info-game",
        decision_id=outcome.get("decision_id"),
        principal_id=outcome.get("principal_id"),
    )
    for key in ("schema", "category", "correlation_id", "game_id", "public_message", "state_committed"):
        if outcome.get(key) != expected.get(key):
            raise ValueError(f"hidden-info public outcome mismatch at {key}")

    trace = {
        "schema": TRACE_SCHEMA,
        "category": "HIDDEN_INFO_VIOLATION",
        "production_binding": "WS05_PRINCIPAL_CARDVIEW_AUTHORIZATION_REDTEAM",
        "evidence_class": "TECHNICALLY_CONFORMANT",
        "detector": {
            "boundary": detector.get("detector_boundary"),
            "actual_cardview_identity_bearing": True,
            "authorized_for_target_principal": False,
            "leaks_before": 0,
            "leaks_after": 1,
        },
        "outcome": outcome,
        "checks": {
            **checks,
            "state_committed": outcome.get("state_committed") is False,
            "no_fallback": True,
        },
        "status": "PASS",
    }
    if not all(trace["checks"].values()):
        raise ValueError("hidden-info outcome violates fail-closed contract")
    trace["trace_sha256"] = canonical_hash(trace)
    return trace
