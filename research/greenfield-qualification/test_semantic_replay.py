#!/usr/bin/env python3
"""Unit tests for the semantic-only replay adjudicator."""

from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from semantic_replay import compare


def evidence(turn: int, *, noise: int) -> dict[str, object]:
    return {
        "source_head": "head-a",
        "source_tree": "tree-a",
        "external_pins": {"forge": "forge-a"},
        "scenario": "REPLAY_TEST",
        "seed": 7,
        "players": 4,
        "semantic_states": [{"turn": turn, "timestamp": noise, "process_id": noise}],
        "rng_events": [{"event_id": 1, "stream": "library", "value": 3, "timestamp": noise}],
        "decision_tape": [{"event_id": 1, "decision_id": 1, "token": 1, "selected": ["player:2"], "wall_seconds": noise}],
    }


class SemanticReplayTests(unittest.TestCase):
    def write_inputs(self, values: list[dict[str, object]]) -> list[Path]:
        directory = Path(tempfile.mkdtemp(prefix="semantic-replay-"))
        paths: list[Path] = []
        for index, value in enumerate(values):
            path = directory / f"process-{index}.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            paths.append(path)
        return paths

    def test_volatile_process_noise_is_ignored(self) -> None:
        result = compare(self.write_inputs([evidence(2, noise=noise) for noise in (1, 2, 3)]))
        self.assertEqual(result["status"], "PASS")

    def test_semantic_divergence_fails(self) -> None:
        result = compare(self.write_inputs([evidence(2, noise=1), evidence(2, noise=2), evidence(3, noise=3)]))
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["divergences"])

    def test_missing_stream_is_not_run(self) -> None:
        values = [evidence(2, noise=noise) for noise in (1, 2, 3)]
        for value in values:
            del value["decision_tape"]
        result = compare(self.write_inputs(values))
        self.assertEqual(result["status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
