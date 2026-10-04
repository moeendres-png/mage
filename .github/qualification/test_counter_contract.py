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
RETAINED_WITNESS = json.loads((FIXTURE / "counter-fixture-TRUSTED_WITNESS.json").read_text())


def current_schema(witness: dict) -> dict:
    """The retained witness with the selection fields later witnesses carry.

    It predates ``selected_test_classes`` and ``required_inheriting_classes``.
    Its one class owns its one method and inherits nothing, so both fields are
    derived, not chosen: the selection is the whole required set and no class
    inherits. ``RetainedSchema`` shows the unmodified witness is never PASS.
    """
    upgraded = copy.deepcopy(witness)
    upgraded["corpus_policy"]["required_inheriting_classes"] = []
    upgraded["selected_test_classes"] = copy.deepcopy(upgraded["required_test_classes"])
    return upgraded


WITNESS = current_schema(RETAINED_WITNESS)
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


class RetainedSchema(unittest.TestCase):
    def test_a_witness_without_selection_fields_is_never_pass(self):
        status, reasons = qualify.decide(LOCK, RETAINED_WITNESS)
        self.assertNotEqual(status, "PASS")
        self.assertTrue(any("required_inheriting_classes_missing" in r for r in reasons))
        self.assertTrue(any("selected_set_not_policy_derived" in r for r in reasons))

    def test_a_selection_that_drops_or_adds_a_class_is_fail(self):
        for selected in ([], [{"module": ".", "class_name": "probe.ProbeTest"},
                              {"module": ".", "class_name": "probe.OtherTest"}]):
            witness = copy.deepcopy(WITNESS)
            witness["selected_test_classes"] = selected
            status, reasons = qualify.decide(LOCK, witness)
            self.assertEqual(status, "FAIL", selected)
            self.assertTrue(any("selected_set_not_policy_derived" in r for r in reasons))

    def test_an_owed_inheriting_class_must_be_selected_and_entered(self):
        witness = copy.deepcopy(WITNESS)
        witness["corpus_policy"]["required_pairs"].append(".::probe.SubProbeTest")
        witness["corpus_policy"]["required_inheriting_classes"] = [".::probe.SubProbeTest"]
        witness["required_test_classes"].append({"module": ".", "class_name": "probe.SubProbeTest"})
        status, reasons = qualify.decide(LOCK, witness)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("selected_set_not_policy_derived" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
