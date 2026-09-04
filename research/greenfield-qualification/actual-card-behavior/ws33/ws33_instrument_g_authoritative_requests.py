#!/usr/bin/env python3
"""Run the frozen WS33 request instrumenter, then apply the generic obligation fixture overlay."""
from __future__ import annotations
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "ws33_instrument_g_authoritative_requests_base_33858197355.py"
FIXTURE = ROOT / "ws33_patch_g_svar_obligation_fixture.py"
FIXTURE_CONTRACT = "diguntil_random_order=NONDEGENERATE_FAIL_CLOSED"


def main() -> None:
    fixture_source = FIXTURE.read_text(encoding="utf-8")
    if FIXTURE_CONTRACT not in fixture_source:
        raise SystemExit("WS33_G_SVAR_OBLIGATION_FIXTURE=FAIL non-degenerate random-order contract marker missing")
    original = list(sys.argv)
    runpy.run_path(str(BASE), run_name="__main__")
    try:
        i = original.index("--harness")
        harness = original[i + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit("WS33_G_SVAR_OBLIGATION_FIXTURE=FAIL missing --harness") from exc
    subprocess.check_call([sys.executable, str(FIXTURE), "--harness", harness])


if __name__ == "__main__":
    main()
