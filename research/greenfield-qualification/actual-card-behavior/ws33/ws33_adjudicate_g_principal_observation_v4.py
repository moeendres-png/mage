#!/usr/bin/env python3
"""WS33 G observation v4: preserve v3 semantics, fix summary row identity.

case-summary.tsv column 0 is the effective V2 path id and column 1 is Oracle identity.
The v3 verifier accidentally keyed summaries by column 1. This wrapper replaces only
that parser function and then executes the otherwise unchanged source-profile/lifecycle
adjudicator.
"""
from pathlib import Path
import ws33_adjudicate_g_principal_observation as base


def load_summary_by_path(path: Path) -> dict[str, list[str]]:
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    out: dict[str, list[str]] = {}
    for row in rows:
        if len(row) < 2 or not row[0].startswith("forge-behavior-v2:"):
            raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL bad summary row: {row[:2]}")
        if row[0] in out:
            raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL duplicate summary path: {row[0]}")
        out[row[0]] = row
    return out


if __name__ == "__main__":
    base.load_summary = load_summary_by_path
    base.main()
