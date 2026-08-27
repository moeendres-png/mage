#!/usr/bin/env python3
"""Small schema/provenance tests for the neutral run harness."""

from __future__ import annotations

import argparse
import unittest

from harness import base_result, parse_external_pins


class HarnessTests(unittest.TestCase):
    def namespace(self, *, head: str = "head", tree: str = "tree") -> argparse.Namespace:
        return argparse.Namespace(
            candidate="test", commit="candidate", source_head=head, source_tree=tree,
            external_pin=["forge=forge-pin"], scenario="TEST", seed=1, players=4,
            evidence_level="L3_LOCALLY_EXECUTED",
        )

    def test_base_result_contains_current_provenance_and_tapes(self) -> None:
        record = base_result(self.namespace())
        self.assertEqual(record["schema"], "commander-simulator-next.game-run-evidence.v2")
        self.assertEqual(record["source_head"], "head")
        self.assertEqual(record["source_tree"], "tree")
        self.assertEqual(record["external_pins"], {"forge": "forge-pin"})
        for key in ("semantic_state_hashes", "rng_events", "decision_tape"):
            self.assertEqual(record[key], [])

    def test_duplicate_external_pins_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_external_pins(["forge=a", "forge=b"])


if __name__ == "__main__":
    unittest.main()
