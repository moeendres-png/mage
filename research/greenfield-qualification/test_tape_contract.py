import unittest

from tape_contract import CanonicalStateDigest, RngEvent, canonical_state_digest, validate_monotonic_event_ids


class TapeContractTests(unittest.TestCase):
    def test_rng_event_requires_named_bounded_stream(self) -> None:
        self.assertEqual(RngEvent(1, "library_shuffle", 0, 10, 9).value, 9)
        with self.assertRaises(ValueError):
            RngEvent(1, "", 0, 10, 1)
        with self.assertRaises(ValueError):
            RngEvent(1, "library_shuffle", 0, 10, 10)

    def test_canonical_state_digest_ignores_runtime_noise(self) -> None:
        left = canonical_state_digest({"turn": 2, "timestamp": 1}, sequence=0, scope="PUBLIC")
        right = canonical_state_digest({"turn": 2, "timestamp": 999}, sequence=0, scope="PUBLIC")
        self.assertEqual(left, right)
        self.assertIsInstance(left, CanonicalStateDigest)

    def test_principal_digest_requires_principal(self) -> None:
        with self.assertRaises(ValueError):
            CanonicalStateDigest(0, "0" * 64, "PRINCIPAL")

    def test_event_ids_are_strictly_monotonic(self) -> None:
        validate_monotonic_event_ids([{"event_id": 1}, {"event_id": 2}])
        with self.assertRaises(ValueError):
            validate_monotonic_event_ids([{"event_id": 1}, {"event_id": 1}])


if __name__ == "__main__":
    unittest.main()
