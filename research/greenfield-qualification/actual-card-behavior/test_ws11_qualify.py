import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ws11", HERE / "ws11_qualify.py")
ws11 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ws11)


class Ws11PolicyTest(unittest.TestCase):
    def test_signature_is_content_bound(self):
        self.assertNotEqual(ws11.signature(["A:SP$ Draw | NumCards$ 1"]), ws11.signature(["A:SP$ Draw | NumCards$ 2"]))

    def test_invalid_stdout_only_witness_is_rejected(self):
        reg = {"witnesses": [{"scenario_id": "x", "execution": "PASS", "engine_state_assertions": "PASS",
                               "stdout_only": True, "trace_sha256": "0" * 64,
                               "official_rules_adjudication": "EXTERNALLY_RULE_VALIDATED",
                               "path_signature_ids": ["forge-path-v1:x"]}]}
        self.assertEqual({}, dict(ws11.validated_witnesses(reg)))

    def test_unwitnessed_executable_identity_is_partial_not_conditional_full(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            card = root / "s" / "sample.txt"
            card.parent.mkdir()
            card.write_text("Name:Sample\nManaCost:1 U\nA:SP$ Draw | NumCards$ 1\n", encoding="utf-8")
            base = {"oracle_id": "id", "oracle_name": "Sample", "source_mask": 1, "present": "PASS",
                    "exact_script_matches": [{"path": "forge-gui/res/cardsfolder/s/sample.txt", "sha256": "old"}]}
            load = {"loadable": True, "identity_match": True, "runtime_constructable": True}
            row = ws11.make_row(base, load, root, {}, {})
            self.assertEqual("PARTIAL", row["classification"])
            self.assertEqual("UNKNOWN", row["flags"]["BEHAVIOR_VERIFIED_WHERE_REQUIRED"])
            self.assertFalse(row["global_pass_inheritance_used"])

    def test_ambiguous_mapping_is_unknown(self):
        base = {"oracle_id": "id", "oracle_name": "Missing", "source_mask": 1, "present": "PASS", "exact_script_matches": []}
        load = {"loadable": True, "identity_match": True, "runtime_constructable": True}
        row = ws11.make_row(base, load, Path("missing"), {}, {})
        self.assertEqual("UNKNOWN", row["classification"])

    def test_per_identity_refs_are_concrete_and_immutable(self):
        refs = {"run_id": 33251282186, "job_id": 99097271546, "artifact_id": 9714450822,
                "artifact_digest": "sha256:a9505ece9e893a51c535a2674626a59d9c78be7a5cee3c31b4bd5239964f1f42"}
        base = {"oracle_id": "id", "oracle_name": "Missing", "source_mask": 1, "present": "PASS", "exact_script_matches": []}
        load = {"loadable": True, "identity_match": True, "runtime_constructable": True}
        row = ws11.make_row(base, load, Path("missing"), {}, refs)
        self.assertTrue(all(value is not None for value in row["run_job_artifact_refs"].values()))
        self.assertRegex(row["run_job_artifact_refs"]["artifact_digest"], r"^sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
