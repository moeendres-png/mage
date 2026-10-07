"""Scorer counter contracts.

Historical execution fixtures remain immutable evidence for their own schema epoch.
Current-shape mutations below are explicitly SYNTHETIC scorer-unit inputs only; they
carry no runtime or qualification credit. Production-path counter controls live in
qualification_selftest.py (CTRL-54/55).
"""
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


# This second retained fixture was a real positive under the predecessor direct-driver
# epoch. It is deliberately NOT upgraded on disk: the current observer epoch must reject it.
PRE_OBSERVER = ROOT / "research/c12-qualified-signatures-20261004"
LOCK = json.loads((PRE_OBSERVER / "counter-fixture-SOURCE_LOCK.json").read_text())
PRE_OBSERVER_WITNESS = json.loads((PRE_OBSERVER / "counter-fixture-TRUSTED_WITNESS.json").read_text())

KEYS = ("tests_found", "tests_started", "tests_succeeded", "tests_failed",
        "tests_aborted", "tests_skipped", "containers_failed")


def synthetic_current_witness():
    """Adapt retained values to the current scorer shape for unit mutation tests only.

    This is SYNTHETIC and must never be cited as runtime evidence. The full production
    pipeline controls independently exercise real parent-observer receipts.
    """
    witness = copy.deepcopy(PRE_OBSERVER_WITNESS)
    witness["schema"] = "mage.candidate-qualification.witness/7"
    witness["test_bytecode_origin"] = "trusted_compile_of_trusted_validator_export"
    witness["candidate_witness_authority"] = False
    witness["execution_mode"] = "per_module_external_observer"

    corpus = witness["corpus_policy"]
    corpus["trusted_required_pairs"] = list(corpus.get("required_pairs") or [])
    corpus["trusted_required_methods"] = list(corpus.get("required_methods") or [])
    corpus["trusted_required_inheriting_classes"] = list(
        corpus.get("required_inheriting_classes") or []
    )

    execution = witness["trusted_execution_witness"]
    execution["schema"] = "mage.candidate-qualification.trusted-execution-witness/6"
    execution["evidence_origin"] = "trusted_parent_jdi_observation"
    execution["candidate_witness_authority"] = False
    execution["execution_mode"] = "per_module_external_observer"
    execution["receipt_authentication"] = "trusted_parent_hmac_sha256"
    execution["all_receipts_hmac_verified"] = True
    execution["receipt_key_in_candidate_jvm"] = False
    execution["body_entered_methods"] = list(execution.get("observed_methods") or [])
    execution["body_completed_methods"] = list(execution.get("observed_methods") or [])
    execution["methods_never_body_completed"] = []
    execution["control_violations"] = []

    for entry in witness.get("module_execution") or []:
        record = entry.get("witness") or {}
        record["schema"] = "mage.candidate-qualification.trusted-execution-witness/6"
        record["evidence_origin"] = "trusted_parent_jdi_observation"
        record["candidate_witness_authority"] = False
        record["observer_status"] = "COMPLETE"
        record["protocol_violations"] = []
        record["control_violations"] = []
        record["receipt_authentication"] = "trusted_parent_hmac_sha256"
        record["receipt_hmac_verified"] = True
        record["receipt_key_in_candidate_jvm"] = False
        record["body_entered_methods"] = list(record.get("observed_methods") or [])
        record["body_completed_methods"] = list(record.get("observed_methods") or [])
        record["methods_never_body_completed"] = []
        entry["observer_exit_code"] = 0

    return witness


WITNESS = synthetic_current_witness()


class CounterContract(unittest.TestCase):
    def test_historical_pre_observer_positive_is_refused(self):
        status, reasons = qualify.decide(LOCK, copy.deepcopy(PRE_OBSERVER_WITNESS))
        self.assertNotEqual(status, "PASS")
        self.assertTrue(any("trusted_witness_schema_unexpected" in r for r in reasons))

    def test_synthetic_current_shape_exercises_the_scorer_only(self):
        # SYNTHETIC unit contract, not runtime evidence or qualification credit.
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
        self.assertEqual(corpus["required_methods"], [".::probe.ProbeTest#test0()"])
        self.assertEqual(observed, [".::probe.ProbeTest#test0()"])

    def test_a_required_method_that_never_started_is_fail(self):
        witness = copy.deepcopy(WITNESS)
        witness["trusted_execution_witness"]["observed_methods"] = []
        status, reasons = qualify.decide(LOCK, witness)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("required_test_methods_not_started" in r for r in reasons))

    def test_a_policy_without_methods_is_never_pass(self):
        for broken in (None, "x", [1]):
            witness = copy.deepcopy(WITNESS)
            witness["corpus_policy"]["trusted_required_methods"] = broken
            self.assertNotEqual(qualify.decide(LOCK, witness)[0], "PASS", broken)
        witness = copy.deepcopy(WITNESS)
        del witness["trusted_execution_witness"]["observed_methods"]
        self.assertEqual(qualify.decide(LOCK, witness)[0], "FAIL")


class RetainedSchema(unittest.TestCase):
    """Historical-schema refusal contracts; never positive runtime evidence."""

    def test_a_witness_without_selection_fields_is_never_pass(self):
        status, reasons = qualify.decide(LOCK, RETAINED_WITNESS)
        self.assertNotEqual(status, "PASS")
        self.assertTrue(any("trusted_witness_schema_unexpected" in r for r in reasons))

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
        witness["corpus_policy"]["trusted_required_pairs"].append(".::probe.SubProbeTest")
        witness["corpus_policy"]["trusted_required_inheriting_classes"] = [".::probe.SubProbeTest"]
        witness["required_test_classes"].append({"module": ".", "class_name": "probe.SubProbeTest"})
        status, reasons = qualify.decide(LOCK, witness)
        self.assertEqual(status, "FAIL")
        self.assertTrue(any("selected_set_not_policy_derived" in r for r in reasons))


class RecordIdentifier(unittest.TestCase):
    """Review P3 on 02c8af1a: `record` as an ordinary identifier must not make the corpus UNKNOWN."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("corpus_policy", QUAL / "corpus_policy.py")
        self.policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.policy)

    def test_record_as_identifier_is_not_a_declaration(self):
        source = """package p;
import org.junit.Test;
public class ATest {
    @Test public void reads() { Object record = null; record.hashCode(); for (Object record : java.util.List.of()) { } }
    @Test public void writes() { }
}
"""
        enabled, disabled = self.policy.java_test_methods(source)
        self.assertEqual(sorted(enabled), ["ATest#reads()", "ATest#writes()"])

    def test_a_real_record_still_scopes_its_tests(self):
        source = """package p;
import org.junit.jupiter.api.Test;
public class BTest {
    record Pair<T>(T a, T b) { }
    @Test void outer() { }
}
"""
        enabled, _ = self.policy.java_test_methods(source)
        self.assertEqual(sorted(enabled), ["BTest#outer()"])


if __name__ == "__main__":
    unittest.main()
