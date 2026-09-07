import base64
import unittest

from ws33_decision_path_evidence import decision_path_counts, decode_field


def encoded(s):
    return base64.b64encode(s.encode()).decode()


def row(path='path-a', event=1, actor=1, principal=1, kind='TARGET_SELECTION', status='ACCEPTED'):
    return '\t'.join(map(str, (encoded(path), event, encoded(kind), actor, principal, status, encoded('null'))))


class DecisionPathEvidenceTest(unittest.TestCase):
    def test_encoded_path_recognized(self):
        self.assertEqual(decision_path_counts(row(), {'path-a'}), {'path-a': 1})

    def test_explicit_setup_not_coverage(self):
        self.assertEqual(decision_path_counts(row('null', actor=0, principal=0, kind='MULLIGAN')+'\n'+row(), {'path-a'}), {'path-a': 1})

    def test_same_event_number_distinct_principals(self):
        self.assertEqual(decision_path_counts(row()+'\n'+row(actor=2, principal=2), {'path-a'}), {'path-a': 2})

    def test_duplicate_principal_event_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            decision_path_counts(row()+'\n'+row(), {'path-a'})

    def test_missing_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'coverage'):
            decision_path_counts(row(), {'path-a', 'path-b'})

    def test_foreign_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'foreign'):
            decision_path_counts(row('foreign'), {'path-a'})

    def test_raw_path_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            decision_path_counts(row().replace(encoded('path-a'), 'path-a'), {'path-a'})

    def test_invalid_and_noncanonical_encoding_rejected(self):
        for value in ('!!!', 'Zh==', '/w=='):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_field(value)

    def test_actor_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'actor'):
            decision_path_counts(row(actor=2), {'path-a'})

    def test_rejected_decision_not_coverage(self):
        with self.assertRaisesRegex(ValueError, 'unsuccessful'):
            decision_path_counts(row(status='REJECTED'), {'path-a'})

    def test_unattributed_target_not_setup(self):
        with self.assertRaisesRegex(ValueError, 'non-setup'):
            decision_path_counts(row('null'), {'path-a'})

    def test_schema_error_rejected(self):
        with self.assertRaisesRegex(ValueError, 'columns'):
            decision_path_counts(row()+'\textra', {'path-a'})


if __name__ == '__main__':
    unittest.main()
