"""Engine-neutral validation for RNG, decision, and canonical-state tapes.

The contracts in this module describe semantic evidence only. They deliberately
exclude process ids, timestamps, wall-clock measurements, log text, and stdout
from replay identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from strict_decision import canonical_json_hash, canonical_semantic_state


@dataclass(frozen=True)
class RngEvent:
    event_id: int
    game_id: str
    stream: str
    draw_index: int
    bits: int
    value: int

    def __post_init__(self) -> None:
        if self.event_id < 1:
            raise ValueError("RNG event_id must be positive")
        if not self.game_id or not self.stream:
            raise ValueError("RNG event requires explicit game_id and named stream")
        if self.draw_index < 0:
            raise ValueError("RNG draw_index must be non-negative")
        if not 1 <= self.bits <= 32:
            raise ValueError("RNG bits must be in 1..32")
        if self.bits < 32 and not 0 <= self.value < (1 << self.bits):
            raise ValueError("RNG value is outside the emitted bit width")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RngEvent":
        return cls(
            event_id=int(value["event_id"]),
            game_id=str(value["game_id"]),
            stream=str(value["stream"]),
            draw_index=int(value["draw_index"]),
            bits=int(value["bits"]),
            value=int(value["value"]),
        )


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

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DecisionEvent":
        actor = value.get("actor_id", value.get("actor"))
        principal = value.get("principal_id", value.get("principal"))
        if actor is None or principal is None:
            raise ValueError("decision event requires actor and principal identity")
        return cls(
            event_id=int(value["event_id"]),
            decision_id=int(value["decision_id"]),
            token=int(value["token"]),
            decision_kind=str(value["decision_kind"]),
            actor=str(actor),
            principal=str(principal),
            response_status=str(value["response_status"]),
            selected_option_ids=tuple(str(item) for item in value.get("selected_option_ids", ())),
            error_code=None if value.get("error_code") is None else str(value["error_code"]),
        )


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
        if self.scope not in {"PUBLIC", "PRINCIPAL", "ENGINE"}:
            raise ValueError("unknown canonical digest scope")
        if self.scope == "PRINCIPAL" and not self.principal:
            raise ValueError("principal-scoped digest requires a principal")
        if self.scope != "PRINCIPAL" and self.principal is not None:
            raise ValueError("non-principal digest must not carry a principal")


def canonical_state_digest(
    value: Any,
    *,
    sequence: int,
    scope: str = "ENGINE",
    principal: str | None = None,
) -> CanonicalStateDigest:
    """Create a digest from semantic state only; runtime noise is excluded."""

    return CanonicalStateDigest(
        sequence=sequence,
        sha256=canonical_json_hash(canonical_semantic_state(value)),
        scope=scope,
        principal=principal,
    )


def validate_monotonic_event_ids(
    events: Sequence[Mapping[str, Any]],
    *,
    field: str = "event_id",
    start: int = 1,
) -> None:
    """Reject duplicate, missing, or backward event identifiers before replay."""

    expected = start
    for event in events:
        identifier = event.get(field)
        if not isinstance(identifier, int) or identifier != expected:
            raise ValueError(f"{field} must be contiguous from {start}; expected {expected}, got {identifier!r}")
        expected += 1


def validate_rng_tape(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate game identity, named streams, per-stream ordering, and results."""

    validate_monotonic_event_ids(events)
    game_ids: set[str] = set()
    stream_draws: dict[tuple[str, str], int] = {}
    streams: set[str] = set()
    for raw in events:
        event = RngEvent.from_mapping(raw)
        game_ids.add(event.game_id)
        streams.add(event.stream)
        key = (event.game_id, event.stream)
        expected_draw = stream_draws.get(key, 0)
        if event.draw_index != expected_draw:
            raise ValueError(
                f"draw_index for {event.game_id}/{event.stream} must be contiguous; "
                f"expected {expected_draw}, got {event.draw_index}"
            )
        stream_draws[key] = expected_draw + 1
    if not events:
        raise ValueError("RNG tape is empty")
    if len(game_ids) != 1:
        raise ValueError(f"RNG tape must belong to exactly one game identity, found {sorted(game_ids)!r}")
    return {
        "event_count": len(events),
        "game_id": next(iter(game_ids)),
        "streams": sorted(streams),
        "sha256": canonical_json_hash(canonical_semantic_state(list(events))),
    }


def validate_decision_tape(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate the accepted full-game Decision Tape without inventing choices.

    WS01 owns one ExternalDecisionTape sequence per principal/controller. Its
    event_id, decision_id, and token therefore restart at 1 for each principal.
    Cross-principal observer arrival order is not an identifier sequence and is
    intentionally not treated as one here. Every principal sequence remains
    strict, contiguous, and gap-free in the order actually observed.
    """

    if not events:
        raise ValueError("Decision Tape is empty")

    parsed = [DecisionEvent.from_mapping(item) for item in events]
    nonaccepted = [event.event_id for event in parsed if event.response_status != "ACCEPTED"]
    if nonaccepted:
        raise ValueError(f"Decision Tape contains non-accepted events: {nonaccepted!r}")

    expected_by_principal: dict[str, int] = {}
    decision_expected_by_principal: dict[str, int] = {}
    token_expected_by_principal: dict[str, int] = {}
    principals: set[str] = set()
    for event in parsed:
        principal = event.principal
        principals.add(principal)

        expected_event = expected_by_principal.get(principal, 1)
        if event.event_id != expected_event:
            raise ValueError(
                f"Decision Tape event_id for principal {principal} must be contiguous from 1; "
                f"expected {expected_event}, got {event.event_id}"
            )
        expected_by_principal[principal] = expected_event + 1

        expected_decision = decision_expected_by_principal.get(principal, 1)
        if event.decision_id != expected_decision:
            raise ValueError(
                f"Decision Tape decision_id for principal {principal} must be contiguous from 1; "
                f"expected {expected_decision}, got {event.decision_id}"
            )
        decision_expected_by_principal[principal] = expected_decision + 1

        expected_token = token_expected_by_principal.get(principal, 1)
        if event.token != expected_token:
            raise ValueError(
                f"Decision Tape token for principal {principal} must be contiguous from 1; "
                f"expected {expected_token}, got {event.token}"
            )
        token_expected_by_principal[principal] = expected_token + 1

    return {
        "event_count": len(parsed),
        "principal_count": len(principals),
        "principals": sorted(principals),
        "decision_kinds": sorted({event.decision_kind for event in parsed}),
        "sha256": canonical_json_hash(canonical_semantic_state(list(events))),
    }


def validate_state_stream(states: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate canonical engine-state checkpoints."""

    if not states:
        raise ValueError("canonical state stream is empty")
    validate_monotonic_event_ids(states, field="sequence", start=0)
    return {
        "state_count": len(states),
        "sha256": canonical_json_hash(canonical_semantic_state(list(states))),
    }


__all__ = [
    "CanonicalStateDigest",
    "DecisionEvent",
    "RngEvent",
    "canonical_state_digest",
    "validate_decision_tape",
    "validate_monotonic_event_ids",
    "validate_rng_tape",
    "validate_state_stream",
]
