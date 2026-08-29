from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = ROOT / "WS14_PRIMITIVE_MANIFEST.json"
ABI = ROOT / "WS14_WITNESS_ABI.schema.json"
WS14_VALIDATOR = ROOT / "ws14" / "ws14_validate_witness.py"


class Ws19ShardTests(unittest.TestCase):
    def test_materializes_exact_owner_set_and_validates_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "coverage.json"
            subprocess.run([sys.executable, str(HERE / "ws19_materialize.py"), "--manifest", str(MANIFEST),
                            "--out", str(output), "--source-head", "d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5",
                            "--source-tree", "5725f47951938bc71af181cf1617e6b3be158804"], check=True)
            subprocess.run([sys.executable, str(HERE / "ws19_validate.py"), "--manifest", str(MANIFEST),
                            "--coverage", str(output), "--abi", str(ABI), "--ws14-validator", str(WS14_VALIDATOR),
                            "--witness-dir", str(HERE)], check=True)
            doc = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(doc["primitive_count"], 14)
            self.assertEqual(doc["coverage_counts"], {"PASS": 0, "PARTIAL": 14, "UNKNOWN": 0, "UNSUPPORTED": 0})
            self.assertEqual(doc["hard_gate"]["result"], "FAIL_CLOSED")

    def test_rejects_manifest_subset(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "coverage.json"
            subprocess.run([sys.executable, str(HERE / "ws19_materialize.py"), "--manifest", str(MANIFEST),
                            "--out", str(output), "--source-head", "d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5",
                            "--source-tree", "5725f47951938bc71af181cf1617e6b3be158804"], check=True)
            doc = json.loads(output.read_text(encoding="utf-8"))
            doc["primitive_coverage"].pop()
            output.write_text(json.dumps(doc), encoding="utf-8")
            result = subprocess.run([sys.executable, str(HERE / "ws19_validate.py"), "--manifest", str(MANIFEST),
                                     "--coverage", str(output), "--abi", str(ABI), "--ws14-validator", str(WS14_VALIDATOR),
                                     "--witness-dir", str(HERE)])
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
