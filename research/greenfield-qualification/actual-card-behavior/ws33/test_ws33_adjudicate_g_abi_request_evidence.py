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
    def row(*, principal: int, event_id: int) -> str:
        return "\t".join(
            [
                enc("path:one"),
                str(event_id),
                enc("BINARY_CHOICE"),
                str(principal),
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


if __name__ == "__main__":
    unittest.main()
