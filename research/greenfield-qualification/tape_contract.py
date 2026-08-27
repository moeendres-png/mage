"""Engine-neutral validation for RNG, decision, and canonical-state tapes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from strict_decision import canonical_json_hash, canonical_semantic_state


@dataclass(frozen=True)
class RngEvent:
    event_id: int
    stream: str
    draw_index: int
    bound: int
    value: int
    semantic_context: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.event_id < 1 or self.draw_index < 0 or self.bound < 1:
            raise ValueError("RNG event identifiers and bound are invalid")
        if not self.stream or not 0 <= self.value < self.bound:
            raise ValueError("RNG event must use a named stream and an in-bound value")


@dataclass(frozen=True)
class DecisionEvent:
    event_id: int
    decision_id: int
    token: int
    decision_kind: str
    actor: str
    principal: str
    response_status: str
    selected_option_ids: tuple[str, ...] = ()
    error_code: str | None = None

    def __post_init__(self) -> None:
        if min(self.event_id, self.decision_id, self.token) < 1:
            raise ValueError("decision event identifiers must be positive")
        if not self.decision_kind or not self.actor or not self.principal:
            raise ValueError("decision event identity is required")
        if self.response_status not in {"ACCEPTED", "REJECTED", "TIMEOUT", "UNSUPPORTED"}:
            raise ValueError("unknown decision event response status")
        if len(self.selected_option_ids) != len(set(self.selected_option_ids)):
            raise ValueError("decision event selections must be unique")


@dataclass(frozen=True)
class CanonicalStateDigest:
    sequence: int
    sha256: str
    scope: str
    principal: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0 or len(self.sha256) != 64:
            raise ValueError("canonical state digest is malformed")
        if any(character not in "0123456789abcdef" for character in self.sha256):
            raise ValueError("canonical state digest must use lowercase SHA-256")
        if self.scope not in {"PUBLIC", "PRINCIPAL"}:
            raise ValueError("unknown canonical digest scope")
        if self.scope == "PRINCIPAL" and not self.principal:
            raise ValueError("principal-scoped digest requires a principal")
        if self.scope == "PUBLIC" and self.principal is not None:
            raise ValueError("public digest must not carry a principal")


def canonical_state_digest(value: Any, *, sequence: int, scope: str, principal: str | None = None) -> CanonicalStateDigest:
    """Create a digest from semantic state only; runtime noise is excluded."""

    return CanonicalStateDigest(
        sequence=sequence,
        sha256=canonical_json_hash(canonical_semantic_state(value)),
        scope=scope,
        principal=principal,
    )


def validate_monotonic_event_ids(events: Sequence[Mapping[str, Any]], *, field: str = "event_id") -> None:
    """Reject duplicate or backward event identifiers before replay."""

    previous = 0
    for event in events:
        identifier = event.get(field)
        if not isinstance(identifier, int) or identifier <= previous:
            raise ValueError(f"{field} must be strictly increasing")
        previous = identifier


__all__ = ["CanonicalStateDigest", "DecisionEvent", "RngEvent", "canonical_state_digest", "validate_monotonic_event_ids"]
