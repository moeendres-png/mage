"""Counter contracts based on a retained full-pipeline positive witness."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUAL = ROOT / ".github/qualification"
spec = importlib.util.spec_from_file_location("qualify", QUAL / "qualify.py")
qualify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualify)
# Regenerated through the full pipeline once the corpus became method-bound; the
# earlier corpus-policy/1 witness stays in research/c12-independent-review-20261003.
FIXTURE = ROOT / "research/c12-method-binding-20261003"
LOCK = json.loads((FIXTURE / "counter-fixture-SOURCE_LOCK.json").read_text())
WITNESS = json.loads((FIXTURE / "counter-fixture-TRUSTED_WITNESS.json").read_text())
KEYS = ("tests_found", "tests_started", "tests_succeeded", "tests_failed",
        "tests_aborted", "tests_skipped", "containers_failed")


class CounterContract(unittest.TestCase):
    def test_actual_positive_witness_passes(self):
        self.assertEqual(qualify.decide(LOCK, copy.deepcopy(WITNESS)), ("PASS", []))

    def test_invalid_counts_never_receive_credit(self):
        for key in KEYS:
            for value in [-1, True, None, "0", 1.0]:
                with self.subTest(key=key, value=value):
                    witness = copy.deepcopy(WITNESS)
                    witness["trusted_execution_witness"][key] = value
                    status, reasons = qualify.decide(LOCK, witness)
                    self.assertEqual(status, "FAIL")
                    self.assertTrue(any("invalid_execution_counter" in r for r in reasons))
            with self.subTest(key=key, value="absent"):
                witness = copy.deepcopy(WITNESS)
                del witness["trusted_execution_witness"][key]
                self.assertEqual(qualify.decide(LOCK, witness)[0], "FAIL")

    def test_invalid_module_counts_cannot_be_coerced_to_zero(self):
        for key in KEYS:
            for value in [-1, True, None, "0", 1.0]:
                with self.subTest(key=key, value=value):
                    witness = copy.deepcopy(WITNESS)
                    witness["module_execution"][0]["witness"][key] = value
                    status, reasons = qualify.decide(LOCK, witness)
                    self.assertEqual(status, "FAIL")
                    self.assertTrue(any("invalid_module_counter" in r for r in reasons))

    def test_duplicate_totals_and_outcome_counts_are_checked(self):
        controls = [
            ("tests_succeeded", 0, "execution_outcomes_mismatch"),
            ("tests_skipped", 2, "execution_discovery_mismatch"),
        ]
        for key, value, reason in controls:
            witness = copy.deepcopy(WITNESS)
            execution = witness["trusted_execution_witness"]
            execution[key] = execution["totals"][key] = value
            status, reasons = qualify.decide(LOCK, witness)
            self.assertEqual(status, "FAIL")
            self.assertTrue(any(reason in r for r in reasons))
        witness = copy.deepcopy(WITNESS)
        witness["trusted_execution_witness"]["totals"]["tests_found"] = 2
        status, reasons = qualify.decide(LOCK, witness)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("execution_totals_mismatch" in r for r in reasons))


class MethodContract(unittest.TestCase):
    def test_the_positive_witness_binds_and_observes_its_method(self):
        corpus = WITNESS["corpus_policy"]
        observed = WITNESS["trusted_execution_witness"]["observed_methods"]
        self.assertEqual(corpus["required_methods"], [".::probe.ProbeTest#test0"])
        self.assertEqual(observed, [".::probe.ProbeTest#test0"])

    def test_a_required_method_that_never_started_is_fail(self):
        witness = copy.deepcopy(WITNESS)
        witness["trusted_execution_witness"]["observed_methods"] = []
        status, reasons = qualify.decide(LOCK, witness)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("required_test_methods_not_started" in r for r in reasons))

    def test_a_policy_without_methods_is_never_pass(self):
        for broken in (None, "x", [1]):
            witness = copy.deepcopy(WITNESS)
            witness["corpus_policy"]["required_methods"] = broken
            self.assertNotEqual(qualify.decide(LOCK, witness)[0], "PASS", broken)
        witness = copy.deepcopy(WITNESS)
        del witness["trusted_execution_witness"]["observed_methods"]
        self.assertEqual(qualify.decide(LOCK, witness)[0], "FAIL")


if __name__ == "__main__":
    unittest.main()
