"""Focused AF8 regression for non-semantic remote-observation sample counts."""

from __future__ import annotations

import unittest
from pathlib import Path

from ws33_adjudicate_a_rest_svar_af8 import observation_gate


class Af8ObservationReplayContractTest(unittest.TestCase):
    path_id = "forge-behavior-v2:qualified-path"

    def test_positive_client_samples_need_not_have_equal_transport_counts(self) -> None:
        cases = {self.path_id: [""] * 19}
        failures: list[str] = []
        observation_gate("record", {self.path_id: [self.path_id, "2", "1", "1", "0"]}, cases, failures)
        observation_gate("replay", {self.path_id: [self.path_id, "2", "2", "1", "0"]}, cases, failures)
        self.assertEqual([], failures)

    def test_workflow_compares_semantic_replay_artifacts_not_sample_multiplicity(self) -> None:
        workflow = Path(__file__).resolve().parents[4] / ".github" / "workflows" / "ws33-abc-a-rest-svar-af8-runtime.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("cmp generated/record/decision-tape.tsv generated/replay/decision-tape.tsv", text)
        self.assertIn("cmp generated/record/play-stages.tsv generated/replay/play-stages.tsv", text)
        self.assertNotIn("cmp generated/record/AF8_CLIENT_OBSERVATION_SAMPLES.tsv", text)


if __name__ == "__main__":
    unittest.main()
