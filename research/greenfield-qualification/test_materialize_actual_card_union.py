import json
import tempfile
import unittest
from pathlib import Path

from materialize_actual_card_union import materialize


class MaterializeActualCardUnionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index = self.root / "index.json"
        self.index.write_text(json.dumps({
            "source_head": "head",
            "source_tree": "tree",
            "oracle_identity_count": 3,
            "cards": [
                {"oracle_id": "oid-a", "name": "A"},
                {"oracle_id": "oid-b", "name": "B"},
                {"oracle_id": "oid-c", "name": "C"},
            ],
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def manifest(self, target=2, classes=None):
        path = self.root / "manifest.json"
        path.write_text(json.dumps({
            "qualification_input": {"forge_pin": "forge"},
            "oracle_union": {"target_count": target, "source_classes": classes or ["one", "two"]},
        }), encoding="utf-8")
        return path

    def resolution(self, name, rows, status="PASS"):
        import hashlib
        index_sha = hashlib.sha256(self.index.read_bytes()).hexdigest()
        path = self.root / f"{name}.json"
        path.write_text(json.dumps({
            "status": status,
            "scryfall_index": {"sha256": index_sha},
            "resolved": [{"oracle_id": oracle_id, "oracle_name": oracle_name} for oracle_id, oracle_name in rows],
        }), encoding="utf-8")
        return path

    def test_deduplicates_and_reads_target_from_manifest(self):
        result = materialize(self.manifest(), self.index, [
            ("one", self.resolution("one", [("oid-a", "A"), ("oid-b", "B")])),
            ("two", self.resolution("two", [("oid-b", "B")])),
        ])
        self.assertEqual("PASS", result["status"])
        self.assertEqual(2, result["computed_oracle_id_count"])
        self.assertEqual(["one", "two"], next(x for x in result["cards"] if x["oracle_id"] == "oid-b")["source_classes"])
        self.assertFalse(result["gate"]["synthetic_promotion"])

    def test_target_mismatch_fails_closed(self):
        result = materialize(self.manifest(target=3), self.index, [
            ("one", self.resolution("one", [("oid-a", "A")])),
            ("two", self.resolution("two", [("oid-b", "B")])),
        ])
        self.assertEqual("FAIL", result["status"])
        self.assertFalse(result["gate"]["target_count_equal"])

    def test_missing_source_class_fails_closed(self):
        result = materialize(self.manifest(), self.index, [
            ("one", self.resolution("one", [("oid-a", "A"), ("oid-b", "B")])),
        ])
        self.assertEqual("FAIL", result["status"])
        self.assertIn("two", {row["source_class"] for row in result["errors"]})

    def test_nonpassing_resolution_fails_closed(self):
        result = materialize(self.manifest(), self.index, [
            ("one", self.resolution("one", [("oid-a", "A")], status="FAIL")),
            ("two", self.resolution("two", [("oid-b", "B")])),
        ])
        self.assertEqual("FAIL", result["status"])
        self.assertFalse(result["gate"]["all_resolution_artifacts_pass"])


if __name__ == "__main__":
    unittest.main()
