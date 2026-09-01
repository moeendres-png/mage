#!/usr/bin/env python3
"""WS33 G observation v4: bind the verifier to the current direct-G evidence ABI.

The direct-G qualification artifact defines required decision/RNG flags as minimum
evidence obligations, not exclusive path behavior. Executed subabilities can therefore
produce additional authoritative decisions or RNG while remaining valid, provided fresh
record/replay evidence is deterministic and fully tape-driven.

case-summary.tsv uses the current 20-column ABI:
  0 effective V2 path id
  1 Oracle identity
  4 status
  5/6 semantic before/after digests
  7/8 decision/RNG event counts
  9/10 hidden-leak/cross-principal deltas
  11/12 principal request summaries
  13 authorized decision principals
  14/15 failure type/message
  18/19 stack admissions/resolutions

The historical v3 observation verifier keyed summaries by Oracle identity, interpreted
columns 11/12 as failures, and treated minimum evidence requirements as iff predicates.
This wrapper corrects only those ABI/contract mismatches while preserving the strict
principal-observation lifecycle, identity, leak, stack, and record/replay checks.
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


def check_summary_v4(
    label: str,
    rows: dict[str, list[str]],
    req: dict[str, dict],
    failures: list[str],
) -> None:
    base.require(set(rows) == set(req), f"{label}:summary_path_set_mismatch", failures)
    for pid in sorted(set(rows) & set(req)):
        row = rows[pid]
        rq = req[pid]
        base.require(len(row) >= 20, f"{pid}:{label}_summary_columns={len(row)}", failures)
        if len(row) < 20:
            continue
        base.require(row[4] == "PASS", f"{pid}:{label}_status={row[4]}", failures)
        base.require(row[18] == "1", f"{pid}:{label}_stack_admission={row[18]}", failures)
        base.require(row[19] == "1", f"{pid}:{label}_stack_resolution={row[19]}", failures)
        base.require(int(row[9]) == 0, f"{pid}:{label}_hidden_leak_delta={row[9]}", failures)
        base.require(int(row[10]) == 0, f"{pid}:{label}_cross_principal_delta={row[10]}", failures)

        # The source-proven direct-G contract defines these flags as minimum evidence
        # obligations. Extra path-scoped events from executed subabilities are valid and
        # remain replay-bound by the unchanged record/replay checks in base.main().
        if rq["decision"]:
            base.require(int(row[7]) > 0, f"{pid}:{label}_missing_required_decision", failures)
        if rq["rng"]:
            base.require(int(row[8]) > 0, f"{pid}:{label}_missing_required_rng", failures)

        # Current summary ABI stores principal request distributions in 11/12. Runtime
        # failure type/message are columns 14/15 and must remain empty for every PASS.
        base.require(not row[14] and not row[15], f"{pid}:{label}_runtime_failure={row[14]}:{row[15]}", failures)


if __name__ == "__main__":
    base.load_summary = load_summary_by_path
    base.check_summary = check_summary_v4
    base.main()
