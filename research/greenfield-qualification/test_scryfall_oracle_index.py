import gzip
import json
import tempfile
import unittest
from pathlib import Path

from scryfall_oracle_index import index_rows, payload_text, rows_from_text


class ScryfallOracleIndexTests(unittest.TestCase):
    def test_gzip_jsonl_and_deterministic_deduplication(self) -> None:
        rows = [
            {"id": "z", "oracle_id": "oracle-b", "name": "B", "legalities": {}},
            {"id": "a", "oracle_id": "oracle-a", "name": "A", "legalities": {}},
            {"id": "y", "oracle_id": "oracle-b", "name": "B newer", "legalities": {}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oracle.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")
            indexed = index_rows(rows_from_text(payload_text(path)))
        self.assertEqual([row["oracle_id"] for row in indexed], ["oracle-a", "oracle-b"])
        self.assertEqual(indexed[1]["scryfall_id"], "y")

    def test_plain_json_array_is_supported(self) -> None:
        text = json.dumps([{"id": "a", "oracle_id": "oracle-a", "name": "A"}])
        self.assertEqual(len(list(rows_from_text(text))), 1)

    def test_invalid_magic_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.bin"
            path.write_bytes(b"not-json")
            with self.assertRaises(SystemExit):
                payload_text(path)


if __name__ == "__main__":
    unittest.main()
