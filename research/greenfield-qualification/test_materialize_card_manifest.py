from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from materialize_card_manifest import main


class MaterializeCardManifestTests(unittest.TestCase):
    def test_unknown_oracle_ids_are_not_promoted_to_card_rows(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "actual-card-manifest"
            source_dir.mkdir()
            manifest_path = root / "manifest.json"
            source_path = source_dir / "cards.json"
            index_path = root / "index.json"
            output_path = root / "union.json"
            source_path.write_text(
                json.dumps({"oracle_ids": ["known", "unknown"]}),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "oracle_union": {
                            "target_count": 2,
                            "source_files": ["actual-card-manifest/cards.json"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            index_path.write_text(
                json.dumps(
                    {
                        "source_head": "head",
                        "source_tree": "tree",
                        "oracle_identity_count": 1,
                        "cards": [{"oracle_id": "known", "name": "Known"}],
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "sys.argv",
                [
                    "materialize_card_manifest.py",
                    "--manifest",
                    str(manifest_path),
                    "--oracle-index",
                    str(index_path),
                    "--source-head",
                    "head",
                    "--source-tree",
                    "tree",
                    "--forge-pin",
                    "forge",
                    "--out",
                    str(output_path),
                ],
            ):
                self.assertEqual(main(), 1)

            output = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(output["unknown_oracle_ids_not_in_scryfall_index"], ["unknown"])
            self.assertEqual([row["oracle_id"] for row in output["cards"]], ["known"])


if __name__ == "__main__":
    unittest.main()
