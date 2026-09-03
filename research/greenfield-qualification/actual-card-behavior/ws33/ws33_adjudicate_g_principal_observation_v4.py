#!/usr/bin/env python3
"""WS33 G observation v4: bind the verifier to the current AF evidence ABI.

The AF qualification artifact defines required decision/RNG flags as minimum evidence
obligations, not exclusive path behavior. Executed subabilities can therefore produce
additional authoritative decisions or RNG while remaining valid, provided fresh
record/replay evidence is deterministic and fully tape-driven.

case-summary.tsv uses the current 21-column AF ABI:
  0 effective V2 path id
  1 Oracle identity
  4 status
  5/6 semantic before/after digests
  7/8 decision/RNG event counts
  9/10 historical coarse hidden-visibility / cross-principal deltas
  11/12 principal request summaries
  13 authorized decision principals
  14/15 failure type/message
  18/19 stack admissions/resolutions
  20 target-SVar reachability count

Column 9 is retained raw evidence. A positive value is not silently waived: v4 may
classify it as an attested temporary-observation signal only for a source profile that
requires positive temporary observation, and only when the exact same path/run side has
strict principal lifecycle evidence. All other positive values fail closed. Direct-G's
base verifier keeps its existing strict all-zero default.
"""
from collections import Counter
import json
from pathlib import Path
import sys

import ws33_adjudicate_g_principal_observation as base


_BASE_CHECK_EVENTS = base.check_events
_COARSE_SIGNALS: dict[str, dict[str, int]] = {"record": {}, "replay": {}}


def reset_contract_state() -> None:
    _COARSE_SIGNALS["record"].clear()
    _COARSE_SIGNALS["replay"].clear()


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
    base.require(label in _COARSE_SIGNALS, f"{label}:unsupported_summary_label", failures)
    if label in _COARSE_SIGNALS:
        _COARSE_SIGNALS[label].clear()
    base.require(set(rows) == set(req), f"{label}:summary_path_set_mismatch", failures)
    for pid in sorted(set(rows) & set(req)):
        row = rows[pid]
        rq = req[pid]
        base.require(len(row) >= 21, f"{pid}:{label}_summary_columns={len(row)}", failures)
        if len(row) < 21:
            continue
        base.require(row[4] == "PASS", f"{pid}:{label}_status={row[4]}", failures)
        base.require(row[18] == "1", f"{pid}:{label}_stack_admission={row[18]}", failures)
        base.require(row[19] == "1", f"{pid}:{label}_stack_resolution={row[19]}", failures)
        base.require(int(row[20]) >= 1, f"{pid}:{label}_target_reachability={row[20]}", failures)

        coarse = int(row[9])
        base.require(coarse >= 0, f"{pid}:{label}_negative_coarse_hidden_signal={coarse}", failures)
        if coarse > 0:
            base.require(
                rq["profile"] == "POSITIVE_TEMPORARY_REQUIRED",
                f"{pid}:{label}_coarse_hidden_signal_without_positive_profile={coarse}:{rq['profile']}",
                failures,
            )
            if label in _COARSE_SIGNALS:
                _COARSE_SIGNALS[label][pid] = coarse
        base.require(int(row[10]) == 0, f"{pid}:{label}_cross_principal_delta={row[10]}", failures)

        # Source-proven requirements are minima, not iff predicates. Additional events
        # created by executed subabilities remain legal only when replay is identical.
        if rq["decision"]:
            base.require(int(row[7]) > 0, f"{pid}:{label}_missing_required_decision", failures)
        if rq["rng"]:
            base.require(int(row[8]) > 0, f"{pid}:{label}_missing_required_rng", failures)

        base.require(not row[14] and not row[15], f"{pid}:{label}_runtime_failure={row[14]}:{row[15]}", failures)

    if label == "replay":
        base.require(
            _COARSE_SIGNALS["record"] == _COARSE_SIGNALS["replay"],
            "record_replay_coarse_hidden_signal_mismatch="
            + repr((_COARSE_SIGNALS["record"], _COARSE_SIGNALS["replay"])),
            failures,
        )


def check_events_v4(
    label: str,
    events: list[dict],
    req: dict[str, dict],
    failures: list[str],
) -> dict[str, Counter]:
    counts = _BASE_CHECK_EVENTS(label, events, req, failures)
    coarse_paths = _COARSE_SIGNALS.get(label, {})
    for pid, raw_signal in sorted(coarse_paths.items()):
        scoped = [e for e in events if e.get("path_id") == pid]
        kinds = Counter(e.get("kind") for e in scoped)
        grants = kinds.get("SERVER_GRANT", 0)
        visible = kinds.get("CLIENT_VISIBLE", 0)
        revokes = kinds.get("SERVER_REVOKE", 0)
        hidden = kinds.get("CLIENT_HIDDEN", 0)
        base.require(bool(scoped), f"{pid}:{label}_coarse_signal_without_observation_events={raw_signal}", failures)
        base.require(grants > 0, f"{pid}:{label}_coarse_signal_without_grant={raw_signal}", failures)
        base.require(
            grants == visible == revokes == hidden,
            f"{pid}:{label}_coarse_signal_unbalanced_lifecycle={raw_signal}:"
            f"grant={grants}:visible={visible}:revoke={revokes}:hidden={hidden}",
            failures,
        )
        base.require(
            all(e.get("identity_match") is True for e in scoped),
            f"{pid}:{label}_coarse_signal_identity_mismatch={raw_signal}",
            failures,
        )
    return counts


def _output_path() -> Path | None:
    try:
        i = sys.argv.index("--out")
        return Path(sys.argv[i + 1])
    except (ValueError, IndexError):
        return None


def _augment_success_output() -> None:
    out_path = _output_path()
    if out_path is None or not out_path.is_file():
        return
    data = json.loads(out_path.read_text(encoding="utf-8"))
    data["coarse_hidden_signal_policy"] = "PRINCIPAL_ATTESTED_TEMPORARY_OBSERVATION"
    data["coarse_hidden_signal_raw_retained"] = True
    data["coarse_hidden_signal_record_paths"] = dict(sorted(_COARSE_SIGNALS["record"].items()))
    data["coarse_hidden_signal_replay_paths"] = dict(sorted(_COARSE_SIGNALS["replay"].items()))
    data["coarse_hidden_signal_record_total"] = sum(_COARSE_SIGNALS["record"].values())
    data["coarse_hidden_signal_replay_total"] = sum(_COARSE_SIGNALS["replay"].values())
    data["unauthorized_hidden_leak_delta_required"] = 0
    # Preserve the historical field for compatibility. In v4 it refers to unauthorized
    # leakage after principal attestation, not to the raw coarse summary column.
    data["hidden_leak_delta_required"] = 0
    out_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    reset_contract_state()
    base.load_summary = load_summary_by_path
    base.check_summary = check_summary_v4
    base.check_events = check_events_v4
    base.main()
    _augment_success_output()


if __name__ == "__main__":
    main()
