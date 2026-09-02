#!/usr/bin/env python3
"""Focused negative and identity-scope tests for the G ABI adjudicator."""

from __future__ import annotations

import base64
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ws33_adjudicate_g_abi_request_evidence import (
    EvidenceError,
    correlate_tape,
    parse_event_paths,
    parse_requests,
)


def enc(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def request_row(*, principal: int, token: int, option_id: str = "choice:0") -> str:
    return "\t".join(
        [
            enc("path:one"),
            str(token),
            str(token),
            enc("BINARY_CHOICE"),
            "1",
            str(principal),
            enc("PRINCIPAL_ONLY"),
            "1",
            "1",
            "false",
            enc("schema:v1"),
            "1",
            enc(option_id),
        ]
    )


class RequestIdentityScopeTest(unittest.TestCase):
    def parse(self, rows: list[str]):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.tsv"
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            return parse_requests(path, {"path:one": {"rng": False, "decision": True}})

    def test_same_token_is_allowed_for_distinct_principals(self) -> None:
        identities, by_path = self.parse(
            [request_row(principal=10, token=1), request_row(principal=11, token=1)]
        )
        self.assertEqual(set(identities), {(10, 1), (11, 1)})
        self.assertEqual(len(by_path["path:one"]), 2)

    def test_duplicate_principal_scoped_token_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "duplicate principal-scoped token"):
            self.parse(
                [request_row(principal=10, token=1), request_row(principal=10, token=1)]
            )

    def test_semantic_pseudo_option_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "non-opaque option id"):
            self.parse([request_row(principal=10, token=1, option_id="target-action:cancel")])


class EventIdentityScopeTest(unittest.TestCase):
    @staticmethod
    def row(*, principal: int, event_id: int, actor: int | None = None,
            kind: str = "BINARY_CHOICE", path: str = "path:one") -> str:
        actor = principal if actor is None else actor
        return "\t".join(
            [
                enc(path),
                str(event_id),
                enc(kind),
                str(actor),
                str(principal),
                "ACCEPTED",
                enc("null"),
            ]
        )

    def parse(self, rows: list[str]):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.tsv"
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            return parse_event_paths(path)

    def test_same_event_id_is_allowed_for_distinct_principals(self) -> None:
        events = self.parse(
            [self.row(principal=10, event_id=1), self.row(principal=11, event_id=1)]
        )
        self.assertEqual(set(events), {(10, 1), (11, 1)})

    def test_duplicate_principal_scoped_event_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "principal-scoped event id"):
            self.parse(
                [self.row(principal=10, event_id=1), self.row(principal=10, event_id=1)]
            )

    def test_ambiguous_matching_event_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "principal-scoped event id"):
            self.parse(
                [
                    self.row(principal=10, event_id=7, actor=10, kind="BINARY_CHOICE"),
                    self.row(principal=10, event_id=7, actor=11, kind="PILE_SELECTION"),
                ]
            )


class EventTapeCorrelationTest(unittest.TestCase):
    cases = {"path:one": {"rng": False, "decision": True}}

    @staticmethod
    def request(*, principal: int = 10, token: int = 1, actor: int = 10,
                kind: str = "BINARY_CHOICE") -> dict:
        return {
            "path_id": "path:one",
            "decision_id": token,
            "token": token,
            "decision_kind": kind,
            "actor": actor,
            "principal": principal,
            "visibility_scope": "PRINCIPAL_ONLY",
            "minimum_selection": 1,
            "maximum_selection": 1,
            "cancel_allowed": False,
            "response_schema": "schema:v1",
            "authoritative_legal_options": ["choice:0"],
        }

    @staticmethod
    def tape_row(*, event_id: int = 1, decision_id: int = 1, token: int = 1,
                 kind: str = "BINARY_CHOICE", actor: int = 10,
                 principal: int = 10, selected: str = "choice:0") -> str:
        return "\t".join(
            [
                str(event_id),
                str(decision_id),
                str(token),
                enc(kind),
                str(actor),
                str(principal),
                "1",
                enc(selected),
            ]
        )

    def correlate(self, *, event_rows: list[str], tape_rows: list[str], requests: dict | None = None):
        event_paths = EventIdentityScopeTest().parse(event_rows)
        if requests is None:
            requests = {(10, 1): self.request()}
        with tempfile.TemporaryDirectory() as directory:
            tape = Path(directory) / "decision-tape.tsv"
            tape.write_text("\n".join(tape_rows) + "\n", encoding="utf-8")
            return correlate_tape(tape, event_paths, requests, self.cases)

    def test_wrong_principal_event_correlation_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "principal-scoped event .* missing path metadata"):
            self.correlate(
                event_rows=[EventIdentityScopeTest.row(principal=10, event_id=1)],
                tape_rows=[self.tape_row(principal=11, actor=11)],
                requests={(11, 1): self.request(principal=11, actor=11)},
            )

    def test_wrong_actor_event_correlation_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "event metadata mismatch"):
            self.correlate(
                event_rows=[EventIdentityScopeTest.row(principal=10, event_id=1, actor=10)],
                tape_rows=[self.tape_row(actor=11)],
            )

    def test_wrong_kind_event_correlation_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "event metadata mismatch"):
            self.correlate(
                event_rows=[EventIdentityScopeTest.row(principal=10, event_id=1, kind="BINARY_CHOICE")],
                tape_rows=[self.tape_row(kind="PILE_SELECTION")],
            )

    def test_missing_matching_event_is_rejected(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "principal-scoped event .* missing path metadata"):
            self.correlate(
                event_rows=[EventIdentityScopeTest.row(principal=10, event_id=2)],
                tape_rows=[self.tape_row(event_id=1)],
            )


if __name__ == "__main__":
    unittest.main()
