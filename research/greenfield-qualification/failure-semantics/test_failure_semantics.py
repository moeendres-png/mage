import json
import unittest

from qualify import SECRET_MARKERS, execute_witness, load_contract, qualify


class FailureSemanticsContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()

    def test_exact_authoritative_categories(self):
        categories = self.contract["properties"]["category"]["enum"]
        self.assertEqual(16, len(categories))
        self.assertEqual(set(categories), set(self.contract["x-categories"]))

    def test_every_category_has_executable_no_fallback_witness(self):
        for category in self.contract["properties"]["category"]["enum"]:
            with self.subTest(category=category):
                witness = execute_witness(self.contract, category)
                self.assertEqual("PASS", witness["status"])
                self.assertTrue(witness["checks"]["no_pass_cancel_default_random_first_or_skip_fallback"])

    def test_failure_payloads_never_contain_private_markers(self):
        for category in self.contract["properties"]["category"]["enum"]:
            serialized = json.dumps(execute_witness(self.contract, category)["outcome"])
            self.assertFalse(any(marker in serialized for marker in SECRET_MARKERS))

    def test_only_success_commits(self):
        for category in self.contract["properties"]["category"]["enum"]:
            witness = execute_witness(self.contract, category)
            self.assertEqual(category == "SUCCESS", witness["before_state_sha256"] != witness["after_state_sha256"])

    def test_integrated_gate_is_fail_closed(self):
        gate = qualify("test-head", "test-tree", java_contract_pass=True, q1_validator_pass=True)
        self.assertEqual("PASS", gate["FAILURE_SEMANTICS"])
        self.assertEqual(0, gate["production_reachable_untyped_failure_outcomes"])
        self.assertEqual(0, gate["production_reachable_fallback_failure_handling"])
        self.assertTrue(all(gate["hard_gate_values"].values()))


if __name__ == "__main__":
    unittest.main()
