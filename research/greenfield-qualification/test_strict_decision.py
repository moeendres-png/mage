#!/usr/bin/env python3
"""Executable fail-closed contract tests for the external decision boundary."""

from __future__ import annotations

import unittest

from strict_decision import (
    DecisionErrorCode,
    DecisionOption,
    DecisionRequest,
    DecisionResponse,
    DecisionValidationError,
    canonical_option_id,
    canonical_semantic_state,
    validate_response,
)


def request(*, cancel_allowed: bool = False) -> DecisionRequest:
    options = (
        DecisionOption(canonical_option_id("player", 1), "player", "1"),
        DecisionOption(canonical_option_id("player", 2), "player", "2"),
        DecisionOption(canonical_option_id("card", 7), "card", "7"),
    )
    return DecisionRequest(
        decision_id=17,
        token=91,
        decision_kind="ENTITY_SELECTION",
        actor="player:1",
        principal="player:1",
        visibility_scope="PRINCIPAL_ONLY",
        options=options,
        minimum_selection=1,
        maximum_selection=2,
        constraints={"ordered": "false"},
        response_schema="entity-selection.v1",
        semantic_context={"source": "InputSelectEntitiesFromList"},
        cancel_allowed=cancel_allowed,
    )


def response(req: DecisionRequest, **overrides: object) -> DecisionResponse:
    values = {
        "decision_id": req.decision_id,
        "token": req.token,
        "actor": req.actor,
        "principal": req.principal,
        "response_schema": req.response_schema,
        "selected_option_ids": ("player:2",),
        "cancel": False,
    }
    values.update(overrides)
    return DecisionResponse(**values)  # type: ignore[arg-type]


class StrictDecisionTests(unittest.TestCase):
    def assert_code(self, code: DecisionErrorCode, call: object) -> None:
        with self.assertRaises(DecisionValidationError) as ctx:
            call()  # type: ignore[operator]
        self.assertEqual(ctx.exception.code, code)

    def test_valid_player_round_trip(self) -> None:
        result = validate_response(request(), response(request()), current_token=91, current_actor="player:1", current_principal="player:1")
        self.assertEqual(result.selected_options[0].option_id, "player:2")

    def test_invalid_player_rejected(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.ILLEGAL_OPTION, lambda: validate_response(req, response(req, selected_option_ids=("player:99",))))

    def test_option_id_must_match_entity_identity(self) -> None:
        with self.assertRaises(ValueError):
            DecisionOption("card:7", "player", "7")

    def test_wrong_actor_rejected(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.WRONG_ACTOR, lambda: validate_response(req, response(req, actor="player:2")))

    def test_wrong_principal_rejected(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.WRONG_PRINCIPAL, lambda: validate_response(req, response(req, principal="player:2")))

    def test_stale_token_rejected(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.STALE_RESPONSE, lambda: validate_response(req, response(req, token=90)))

    def test_malformed_and_missing_rejected(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.MISSING_RESPONSE, lambda: validate_response(req, None, missing=True))
        self.assert_code(DecisionErrorCode.NULL_RESPONSE, lambda: validate_response(req, None))
        self.assert_code(DecisionErrorCode.MALFORMED_RESPONSE, lambda: validate_response(req, object()))

    def test_timeout_and_consumed_rejected(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.TIMEOUT, lambda: validate_response(req, response(req), timed_out=True))
        self.assert_code(DecisionErrorCode.DECISION_CONSUMED, lambda: validate_response(req, response(req), consumed=True))

    def test_count_and_cancel_constraints_are_fail_closed(self) -> None:
        req = request()
        self.assert_code(DecisionErrorCode.INVALID_SELECTION_COUNT, lambda: validate_response(req, response(req, selected_option_ids=())))
        self.assert_code(DecisionErrorCode.CANCEL_NOT_ALLOWED, lambda: validate_response(req, response(req, selected_option_ids=(), cancel=True)))
        optional = request(cancel_allowed=True)
        result = validate_response(optional, response(optional, selected_option_ids=(), cancel=True))
        self.assertTrue(result.response.cancel)

    def test_semantic_normalization_ignores_runtime_noise_only(self) -> None:
        left = canonical_semantic_state({"state": {"turn": 1}, "timestamp": 1, "process_id": 2})
        right = canonical_semantic_state({"state": {"turn": 1}, "timestamp": 999, "process_id": 3})
        self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
