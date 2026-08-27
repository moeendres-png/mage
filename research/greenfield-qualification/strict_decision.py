"""Fail-closed decision-boundary contract used by qualification probes.

The module is deliberately engine-neutral.  It does not calculate Magic rules;
the engine supplies the authoritative option set and this module verifies that
an external response is for the current decision and is a legal selection from
that set.  Keeping this validator independent makes the negative-path tests
executable without a GUI or a live engine process.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping, Sequence


class DecisionErrorCode(str, Enum):
    MISSING_RESPONSE = "MISSING_RESPONSE"
    NULL_RESPONSE = "NULL_RESPONSE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    STALE_RESPONSE = "STALE_RESPONSE"
    WRONG_ACTOR = "WRONG_ACTOR"
    WRONG_PRINCIPAL = "WRONG_PRINCIPAL"
    ILLEGAL_OPTION = "ILLEGAL_OPTION"
    INVALID_SELECTION_COUNT = "INVALID_SELECTION_COUNT"
    CANCEL_NOT_ALLOWED = "CANCEL_NOT_ALLOWED"
    DECISION_CONSUMED = "DECISION_CONSUMED"
    TIMEOUT = "TIMEOUT"
    UNSUPPORTED_DECISION_PATH = "UNSUPPORTED_DECISION_PATH"


class DecisionValidationError(ValueError):
    """A response was rejected without changing engine state."""

    def __init__(self, code: DecisionErrorCode, message: str) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.message = message


def canonical_option_id(entity_kind: str, entity_id: int | str) -> str:
    """Return a token-scoped, type-qualified identifier for an engine entity."""

    kind = str(entity_kind).strip().lower()
    identifier = str(entity_id).strip()
    if not kind or not identifier or ":" in kind or ":" in identifier:
        raise ValueError("entity kind and id must be non-empty and colon-free")
    return f"{kind}:{identifier}"


@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    entity_kind: str
    entity_id: str
    label: str | None = None

    def __post_init__(self) -> None:
        if not self.option_id or not self.entity_kind or not self.entity_id:
            raise ValueError("decision options require an id, kind, and entity id")
        if self.option_id != canonical_option_id(self.entity_kind, self.entity_id):
            raise ValueError("option id must be type-qualified by entity kind and id")
        if self.label is not None and "\n" in self.label:
            raise ValueError("decision option labels must be single-line")


@dataclass(frozen=True)
class DecisionRequest:
    decision_id: int
    token: int
    decision_kind: str
    actor: str
    principal: str
    visibility_scope: str
    options: tuple[DecisionOption, ...]
    minimum_selection: int
    maximum_selection: int
    constraints: Mapping[str, str]
    response_schema: str
    semantic_context: Mapping[str, str]
    cancel_allowed: bool = False

    def __post_init__(self) -> None:
        if self.decision_id < 1 or self.token < 1:
            raise ValueError("decision id and token must be positive")
        if not self.decision_kind or not self.actor or not self.principal:
            raise ValueError("decision kind, actor, and principal are required")
        if not self.visibility_scope or not self.response_schema:
            raise ValueError("visibility scope and response schema are required")
        if self.minimum_selection < 0 or self.maximum_selection < self.minimum_selection:
            raise ValueError("invalid selection bounds")
        if self.maximum_selection > len(self.options):
            raise ValueError("maximum selection exceeds exact option set")
        option_ids = [option.option_id for option in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("decision option ids must be unique")
        object.__setattr__(self, "constraints", MappingProxyType(dict(self.constraints)))
        object.__setattr__(self, "semantic_context", MappingProxyType(dict(self.semantic_context)))


@dataclass(frozen=True)
class DecisionResponse:
    decision_id: int
    token: int
    actor: str
    principal: str
    response_schema: str
    selected_option_ids: tuple[str, ...] = ()
    cancel: bool = False


@dataclass(frozen=True)
class ValidatedDecision:
    request: DecisionRequest
    response: DecisionResponse
    selected_options: tuple[DecisionOption, ...]


def validate_response(
    request: DecisionRequest | None,
    response: DecisionResponse | None,
    *,
    current_token: int | None = None,
    current_actor: str | None = None,
    current_principal: str | None = None,
    consumed: bool = False,
    timed_out: bool = False,
    missing: bool = False,
) -> ValidatedDecision:
    """Validate a response against the current authoritative request.

    The function intentionally raises for every invalid path.  Callers must
    catch the typed exception and terminate the current input or game; they may
    not substitute pass, cancel, first, random, or AI behavior.
    """

    if request is None:
        raise DecisionValidationError(
            DecisionErrorCode.UNSUPPORTED_DECISION_PATH,
            "no authoritative decision request is open",
        )
    if timed_out:
        raise DecisionValidationError(DecisionErrorCode.TIMEOUT, "decision deadline elapsed")
    if consumed:
        raise DecisionValidationError(DecisionErrorCode.DECISION_CONSUMED, "decision was already consumed")
    if missing:
        raise DecisionValidationError(DecisionErrorCode.MISSING_RESPONSE, "response envelope is missing")
    if response is None:
        raise DecisionValidationError(DecisionErrorCode.NULL_RESPONSE, "response is null")
    if not isinstance(response, DecisionResponse):
        raise DecisionValidationError(DecisionErrorCode.MALFORMED_RESPONSE, "response has an unknown type")
    if current_token is not None and response.token != current_token:
        raise DecisionValidationError(DecisionErrorCode.STALE_RESPONSE, "response token is not current")
    if response.token != request.token or response.decision_id != request.decision_id:
        raise DecisionValidationError(DecisionErrorCode.STALE_RESPONSE, "response does not match request")
    if current_actor is not None and response.actor != current_actor:
        raise DecisionValidationError(DecisionErrorCode.WRONG_ACTOR, "response actor is not current")
    if response.actor != request.actor:
        raise DecisionValidationError(DecisionErrorCode.WRONG_ACTOR, "response actor does not match request")
    if current_principal is not None and response.principal != current_principal:
        raise DecisionValidationError(DecisionErrorCode.WRONG_PRINCIPAL, "response principal is not current")
    if response.principal != request.principal:
        raise DecisionValidationError(DecisionErrorCode.WRONG_PRINCIPAL, "response principal does not match request")
    if response.response_schema != request.response_schema:
        raise DecisionValidationError(DecisionErrorCode.MALFORMED_RESPONSE, "response schema does not match request")

    selected_ids = response.selected_option_ids
    if not isinstance(selected_ids, tuple) or any(not isinstance(item, str) or not item for item in selected_ids):
        raise DecisionValidationError(DecisionErrorCode.MALFORMED_RESPONSE, "selected options must be non-empty strings")
    if len(selected_ids) != len(set(selected_ids)):
        raise DecisionValidationError(DecisionErrorCode.ILLEGAL_OPTION, "duplicate option selection")
    option_by_id = {option.option_id: option for option in request.options}
    unknown = [option_id for option_id in selected_ids if option_id not in option_by_id]
    if unknown:
        raise DecisionValidationError(DecisionErrorCode.ILLEGAL_OPTION, f"unknown options: {unknown!r}")
    if response.cancel:
        if selected_ids:
            raise DecisionValidationError(DecisionErrorCode.MALFORMED_RESPONSE, "cancel cannot include selections")
        if not request.cancel_allowed:
            raise DecisionValidationError(DecisionErrorCode.CANCEL_NOT_ALLOWED, "cancel is not legal")
    elif not request.minimum_selection <= len(selected_ids) <= request.maximum_selection:
        raise DecisionValidationError(
            DecisionErrorCode.INVALID_SELECTION_COUNT,
            f"selected {len(selected_ids)} options, expected {request.minimum_selection}..{request.maximum_selection}",
        )
    selected = tuple(option_by_id[option_id] for option_id in selected_ids)
    return ValidatedDecision(request=request, response=response, selected_options=selected)


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload).hexdigest()


def canonical_semantic_state(value: Any) -> Any:
    """Drop known volatile fields before cross-process state comparison."""

    volatile = {
        "timestamp",
        "started_epoch",
        "wall_seconds",
        "duration_ms",
        "process_id",
        "thread_id",
        "jvm_id",
        "host",
    }

    def clean(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(k): clean(v) for k, v in sorted(item.items()) if str(k) not in volatile}
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            return [clean(v) for v in item]
        return item

    return clean(value)


__all__ = [
    "DecisionErrorCode",
    "DecisionOption",
    "DecisionRequest",
    "DecisionResponse",
    "DecisionValidationError",
    "ValidatedDecision",
    "canonical_json_hash",
    "canonical_option_id",
    "canonical_semantic_state",
    "validate_response",
]
