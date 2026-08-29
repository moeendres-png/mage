import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("ws18_qualify.py")


class Ws18QualifierTest(unittest.TestCase):
    def test_all_and_only_combat_commander_primitives_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "status.json"
            subprocess.run([
                "python", str(SCRIPT), "--manifest", str(ROOT / "WS14_PRIMITIVE_MANIFEST.json"),
                "--source-head", "a" * 40, "--source-tree", "b" * 40, "--out", str(out),
            ], check=True)
            shard = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(shard["owner_family"], "COMBAT_COMMANDER")
        self.assertEqual(shard["counts"], {"PASS": 0, "PARTIAL": 10, "UNKNOWN": 0, "UNSUPPORTED": 0})
        self.assertEqual(len(shard["primitive_status"]), 10)
        self.assertTrue(all(row["status"] == "PARTIAL" for row in shard["primitive_status"]))
        self.assertTrue(all(not row["witness_ids"] and row["blocker"] for row in shard["primitive_status"]))


if __name__ == "__main__":
    unittest.main()
