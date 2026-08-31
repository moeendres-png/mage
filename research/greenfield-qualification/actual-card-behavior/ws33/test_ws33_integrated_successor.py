#!/usr/bin/env python3
"""Regression for Generation-2 descendant qualification-source authorization."""
from __future__ import annotations
from pathlib import Path

source = Path(__file__).with_name("ws33_authorize_integrated_successor.py").read_text(encoding="utf-8")
required = [
    '"merge-base", "--is-ancestor"',
    'f"{args.source_head}^{{tree}}"',
    'scoped_integrated_ownership_verified',
    'GENERATION2_DESCENDANT_INTEGRATED_QUALIFICATION',
]
for marker in required:
    if marker not in source:
        raise SystemExit("WS33_INTEGRATED_SUCCESSOR_REGRESSION=FAIL missing " + marker)
if 'approvals[key] = {' in source and 'args.source_head' not in source:
    raise SystemExit("WS33_INTEGRATED_SUCCESSOR_REGRESSION=FAIL non-derived approval")
print("WS33_INTEGRATED_SUCCESSOR_REGRESSION=PASS")
