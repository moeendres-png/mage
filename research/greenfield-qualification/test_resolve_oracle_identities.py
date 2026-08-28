import json
import tempfile
import unittest
from pathlib import Path

from resolve_oracle_identities import resolve


class ResolveOracleIdentitiesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.index = self.root / "index.json"
        self.index.write_text(json.dumps({
            "source_head": "head",
            "source_tree": "tree",
            "oracle_identity_count": 2,
            "cards": [
                {"name": "Alpha", "oracle_id": "oid-a", "commander_legality": "legal"},
                {"name": "Beta // Back", "face_names": ["Beta", "Back"], "oracle_id": "oid-b", "commander_legality": "legal"},
            ],
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def source(self, records):
        path = self.root / "source.jsonl"
        path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
        return path

    def test_exact_unique_join_passes(self):
        result = resolve(self.source([
            {"card_id": "card-1", "oracle_name": "Alpha"},
            {"card_id": "card-2", "oracle_name": "Beta"},
        ]), self.index, 2)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(2, result["counts"]["distinct_oracle_ids"])
        self.assertFalse(result["resolution_policy"]["fuzzy_matching"])

    def test_missing_name_fails_closed(self):
        result = resolve(self.source([{"card_id": "card-1", "oracle_name": "Unknown"}]), self.index, 1)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(1, result["counts"]["missing"])

    def test_ambiguous_name_fails_closed(self):
        payload = json.loads(self.index.read_text(encoding="utf-8"))
        payload["cards"].append({"name": "Alpha", "oracle_id": "oid-other"})
        self.index.write_text(json.dumps(payload), encoding="utf-8")
        result = resolve(self.source([{"card_id": "card-1", "oracle_name": "Alpha"}]), self.index, 1)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(1, result["counts"]["ambiguous"])

    def test_exact_type_line_disambiguates_token_name(self):
        payload = json.loads(self.index.read_text(encoding="utf-8"))
        payload["cards"][0]["type_line"] = "Creature — Cat"
        payload["cards"].append({"name": "Alpha", "oracle_id": "oid-token", "type_line": "Token Creature — Cat"})
        self.index.write_text(json.dumps(payload), encoding="utf-8")
        result = resolve(self.source([{
            "card_id": "card-1", "oracle_name": "Alpha", "type_line": "Creature — Cat"
        }]), self.index, 1)
        self.assertEqual("PASS", result["status"])
        self.assertEqual("oid-a", result["resolved"][0]["oracle_id"])
        self.assertEqual(
            "EXACT_NFC_ORACLE_NAME_AND_TYPE_LINE_UNIQUE_IN_PINNED_BULK",
            result["resolved"][0]["resolution"],
        )

    def test_exact_face_name_resolves_multiface_card(self):
        result = resolve(self.source([{"card_id": "card-1", "oracle_name": "Beta"}]), self.index, 1)
        self.assertEqual("PASS", result["status"])
        self.assertEqual("oid-b", result["resolved"][0]["oracle_id"])
        self.assertEqual("EXACT_NFC_CARD_FACE_NAME_UNIQUE_IN_PINNED_BULK", result["resolved"][0]["resolution"])

    def test_physical_deck_card_excludes_same_name_token(self):
        payload = json.loads(self.index.read_text(encoding="utf-8"))
        payload["cards"][0]["type_line"] = "Land"
        payload["cards"].append({"name": "Alpha", "oracle_id": "oid-token", "type_line": "Token Land"})
        self.index.write_text(json.dumps(payload), encoding="utf-8")
        result = resolve(self.source([{
            "card_id": "card-1", "oracle_name": "Alpha", "admission_kind": "PHYSICAL_DECK_CARD"
        }]), self.index, 1)
        self.assertEqual("PASS", result["status"])
        self.assertEqual("oid-a", result["resolved"][0]["oracle_id"])

    def test_count_mismatch_fails_closed(self):
        result = resolve(self.source([{"card_id": "card-1", "oracle_name": "Alpha"}]), self.index, 2)
        self.assertEqual("FAIL", result["status"])
        self.assertFalse(result["source"]["expected_count_matches"])


if __name__ == "__main__":
    unittest.main()
