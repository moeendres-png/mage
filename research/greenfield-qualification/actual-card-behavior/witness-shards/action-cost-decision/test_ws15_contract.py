#!/usr/bin/env python3
"""Contract test for the WS15 fail-closed shard."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARD = Path(__file__).resolve().parent


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "primitive-status.json"
        subprocess.run([
            sys.executable, str(SHARD / "ws15_materialize.py"),
            "--manifest", str(ROOT / "WS14_PRIMITIVE_MANIFEST.json"),
            "--output", str(output),
            "--source-head", "d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5",
            "--source-tree", "5725f47951938bc71af181cf1617e6b3be158804",
        ], check=True)
        evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["assigned_primitive_count"] == 76
    assert evidence["pass_count"] == 0
    assert evidence["partial_count"] == 76
    assert evidence["unknown_count"] == 0
    assert evidence["unsupported_count"] == 0
    assert evidence["witness_count"] == 0
    assert evidence["card_name_production_hacks"] == 0
    assert all(row["classification"] == "PARTIAL" for row in evidence["rows"])
    assert all(row["witness_ids"] == [] for row in evidence["rows"])
    assert all("actual-card" in row["failure_reason"] for row in evidence["rows"])
    print("WS15 fail-closed primitive-status contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
