#!/usr/bin/env python3
import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("ws10_qualify", HERE / "qualify.py")
q = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(q)


class Ws10HarnessTests(unittest.TestCase):
    def test_decode_union_exact_uuid_mask_rows(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            qdir = root / "research/greenfield-qualification/actual-card-manifest"
            qdir.mkdir(parents=True)
            ids = sorted([str(uuid.uuid4()), str(uuid.uuid4())])
            raw = b"".join(uuid.UUID(x).bytes + bytes([1 << i]) for i, x in enumerate(ids))
            chunk = qdir / "UNION_MEMBERS_01.b64"
            chunk.write_text(base64.b64encode(raw).decode() + "\n")
            union = {
                "schema": "commander-simulator-next.actual-card-requirement-union.v2",
                "status": "PASS", "complete": True,
                "target_count": 2, "computed_oracle_id_count": 2,
                "member_chunks": [{
                    "path": "actual-card-manifest/UNION_MEMBERS_01.b64",
                    "sha256": hashlib.sha256(chunk.read_bytes()).hexdigest(),
                    "encoding": "uuid16-mask8-base64-v1", "count": 2,
                }],
            }
            self.assertEqual([(ids[0], 1), (ids[1], 2)], q.decode_union(root, union))

    def test_reachability_patterns_are_conservative(self):
        self.assertTrue(q.DECISION_RE.search("AB$ ChooseCard | Choices$ Card.YouCtrl"))
        self.assertTrue(q.HIDDEN_RE.search("Origin$ Library | Destination$ Hand"))
        self.assertTrue(q.RNG_RE.search("DB$ RollDice"))
        self.assertTrue(q.BEHAVIOR_RE.search("Name:X\nA:SP$ Draw | NumCards$ 1\n"))

    def test_classification_vocabulary_is_fail_closed(self):
        self.assertEqual({"FULL", "CONDITIONAL_FULL", "PARTIAL", "UNKNOWN", "UNSUPPORTED"}, q.CLASSIFICATIONS)


if __name__ == "__main__":
    unittest.main()
