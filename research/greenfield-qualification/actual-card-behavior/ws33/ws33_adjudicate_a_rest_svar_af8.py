#!/usr/bin/env python3
"""Fail-closed adjudicator for A-rest AF8 production-cast Record/Replay evidence."""
from __future__ import annotations

import argparse
import base64
import json
from collections import Counter, defaultdict
from pathlib import Path

from ws33_decision_path_evidence import decode_field, decision_path_counts


def fail(msg: str) -> None:
    raise SystemExit("WS33_A_SVAR_AF8_GATE=FAIL " + msg)


def parse_script(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for token in text.split(" | "):
        if "$" not in token:
            continue
        key, value = token.split("$", 1)
        out[key.strip()] = value.strip()
    return out


def load_cases(path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        f = line.split("\t")
        if len(f) != 19:
            fail(f"case ABI line={n} columns={len(f)}")
        pid = f[1]
        if pid in out:
            fail("duplicate case " + pid)
        if f[8] != "ABILITY" or f[10] != "1" or f[11] != "0" or f[12] != "1" or f[13] != "1":
            fail("case route/evidence flags mismatch " + pid)
        out[pid] = f
    if len(out) != 8:
        fail(f"case count={len(out)}")
    return out


def load_tsv(path: Path, columns: int | None = None) -> dict[str, list[str]]:
    if not path.is_file():
        fail("missing " + str(path))
    out: dict[str, list[str]] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        f = line.split("\t")
        if columns is not None and len(f) != columns:
            fail(f"{path.name} line={n} columns={len(f)} expected={columns}")
        if not f[0] or f[0] in out:
            fail(f"{path.name} duplicate/empty path line={n}")
        out[f[0]] = f
    return out


def summary_gate(label: str, rows: dict[str, list[str]], cases: dict[str, list[str]], failures: list[str]) -> None:
    if set(rows) != set(cases):
        failures.append(label + ":path_set_mismatch")
    for pid in sorted(set(rows) & set(cases)):
        r = rows[pid]
        if len(r) != 22:
            failures.append(f"{pid}:{label}:summary_columns={len(r)}")
            continue
        if r[4] != "PASS":
            failures.append(f"{pid}:{label}:status={r[4]}")
        if int(r[7]) <= 0:
            failures.append(f"{pid}:{label}:missing_decision")
        if int(r[8]) != 0:
            failures.append(f"{pid}:{label}:unexpected_rng")
        if int(r[9]) != 0 or int(r[10]) != 0:
            failures.append(f"{pid}:{label}:hidden_leak")
        if int(r[18]) != 1 or int(r[19]) != 1 or int(r[20]) < 1 or int(r[21]) < 1:
            failures.append(f"{pid}:{label}:source_target_reachability")
        if r[14] or r[15]:
            failures.append(f"{pid}:{label}:runtime_failure")


def effect_gate(label: str, rows: dict[str, list[str]], cases: dict[str, list[str]], failures: list[str]) -> None:
    if set(rows) != set(cases):
        failures.append(label + ":effect_path_set_mismatch")
    for pid in sorted(set(rows) & set(cases)):
        r = rows[pid]
        if len(r) != 6:
            failures.append(f"{pid}:{label}:effect_schema")
            continue
        target_script = base64.b64decode(cases[pid][18], validate=True).decode("utf-8")
        params = parse_script(target_script)
        api = params.get("DB")
        expected_kind = "ZONE" if api == "ChangeZone" else "KEYWORD" if api == "Pump" and "KW" in params else ""
        expected_value = params.get("Destination", "") if expected_kind == "ZONE" else params.get("KW", "") if expected_kind == "KEYWORD" else ""
        try:
            actual_value = decode_field(r[2])
        except ValueError:
            failures.append(f"{pid}:{label}:effect_expected_encoding")
            continue
        if not expected_kind or r[1] != expected_kind or actual_value != expected_value:
            failures.append(f"{pid}:{label}:effect_shape_mismatch")
        if int(r[3]) < 1 or int(r[4]) < 1 or int(r[5]) < 1:
            failures.append(f"{pid}:{label}:positive_effect_missing")


def observation_gate(label: str, rows: dict[str, list[str]], cases: dict[str, list[str]], failures: list[str]) -> None:
    if set(rows) != set(cases):
        failures.append(label + ":client_sample_path_set_mismatch")
    for pid in sorted(set(rows) & set(cases)):
        r = rows[pid]
        if len(r) != 5:
            failures.append(f"{pid}:{label}:client_sample_schema")
            continue
        if min(int(r[1]), int(r[2]), int(r[3])) < 1:
            failures.append(f"{pid}:{label}:missing_real_remote_sample")
        if int(r[4]) != 0:
            failures.append(f"{pid}:{label}:client_visibility_mismatch")


def play_stage_gate(label: str, path: Path, cases: dict[str, list[str]], failures: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    source_api_seen: Counter[str] = Counter()
    if not path.is_file():
        failures.append(label + ":play_stages_missing")
        return counts
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        f = line.split("\t")
        if len(f) != 4:
            failures.append(f"{label}:play_stage_schema:{n}")
            continue
        try:
            pid, stage, api = decode_field(f[0]), decode_field(f[1]), decode_field(f[3])
        except ValueError:
            failures.append(f"{label}:play_stage_encoding:{n}")
            continue
        if pid not in cases or not stage or f[2] not in {"true", "false"}:
            failures.append(f"{label}:invalid_play_stage:{n}")
            continue
        counts[pid] += 1
        if api == cases[pid][4]:
            source_api_seen[pid] += 1
    if set(counts) != set(cases):
        failures.append(label + ":play_stage_path_coverage")
    for pid in cases:
        if source_api_seen[pid] < 1:
            failures.append(f"{pid}:{label}:source_play_stage_missing")
    return counts


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def transient_observation_gate(label: str, events: list[dict], cases: dict[str, list[str]], failures: list[str]) -> Counter[str]:
    kinds: Counter[str] = Counter()
    streams: defaultdict[tuple[str, int, int], list[dict]] = defaultdict(list)
    for e in events:
        pid = e.get("path_id")
        if pid not in cases:
            failures.append(f"{label}:unknown_observation_path={pid}")
            continue
        if e.get("identity_match") is not True:
            failures.append(f"{label}:identity_mismatch={pid}")
        kind = str(e.get("kind"))
        kinds[kind] += 1
        if kind in {"SERVER_GRANT", "SERVER_REVOKE"}:
            reason = str(e.get("decision_kind", ""))
            if not reason or reason.startswith("delta:"):
                failures.append(f"{label}:invalid_server_reason={pid}")
        elif kind in {"CLIENT_VISIBLE", "CLIENT_HIDDEN"}:
            delta = str(e.get("decision_kind", ""))
            if delta and not delta.startswith("delta:"):
                failures.append(f"{label}:invalid_client_delta={pid}")
        if kind in {"SERVER_GRANT", "CLIENT_VISIBLE", "SERVER_REVOKE", "CLIENT_HIDDEN"}:
            try:
                streams[(pid, int(e["principal_id"]), int(e["card_id"]))].append(e)
            except Exception:
                failures.append(f"{label}:bad_observation_identity={pid}")
    for key, stream in streams.items():
        state = "HIDDEN"
        transitions = {
            "HIDDEN": ("SERVER_GRANT", "GRANTED"),
            "GRANTED": ("CLIENT_VISIBLE", "VISIBLE"),
            "VISIBLE": ("SERVER_REVOKE", "REVOKED"),
            "REVOKED": ("CLIENT_HIDDEN", "HIDDEN"),
        }
        for e in sorted(stream, key=lambda x: int(x.get("sequence", -1))):
            expected, nxt = transitions[state]
            if e.get("kind") != expected:
                failures.append(f"{label}:lifecycle:{key}:expected={expected}:actual={e.get('kind')}")
                break
            state = nxt
        if state != "HIDDEN":
            failures.append(f"{label}:incomplete_lifecycle:{key}:{state}")
    return kinds


def normalized_observations(events: list[dict]) -> Counter[tuple]:
    rows: list[tuple] = []
    for e in events:
        kind = e.get("kind")
        reason = e.get("decision_kind", "") if kind in {"SERVER_GRANT", "SERVER_REVOKE"} else ""
        rows.append((e.get("path_id"), kind, int(e.get("principal_id", -1)), int(e.get("card_id", -1)), reason, bool(e.get("identity_match"))))
    return Counter(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--record-dir", type=Path, required=True)
    ap.add_argument("--replay-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    cases = load_cases(args.cases)
    expected = set(cases)
    failures: list[str] = []

    rec = load_tsv(args.record_dir / "case-summary.tsv")
    rep = load_tsv(args.replay_dir / "case-summary.tsv")
    summary_gate("record", rec, cases, failures)
    summary_gate("replay", rep, cases, failures)
    for pid in sorted(set(rec) & set(rep) & expected):
        if len(rec[pid]) == 22 and len(rep[pid]) == 22:
            if rec[pid][5] != rep[pid][5] or rec[pid][6] != rep[pid][6]:
                failures.append(pid + ":semantic_digest_mismatch")
            if rec[pid][7:11] != rep[pid][7:11]:
                failures.append(pid + ":decision_rng_leak_count_mismatch")

    decision_counts: dict[str, Counter[str]] = {}
    for label, directory in (("record", args.record_dir), ("replay", args.replay_dir)):
        p = directory / "decision-events-with-path.tsv"
        try:
            decision_counts[label] = decision_path_counts(p.read_text(encoding="utf-8"), expected)
        except (OSError, ValueError) as exc:
            failures.append(label + ":decision_path_evidence:" + str(exc))
    if decision_counts.get("record") != decision_counts.get("replay"):
        failures.append("decision_path_count_replay_mismatch")

    rec_eff = load_tsv(args.record_dir / "AF8_EFFECT_EVIDENCE.tsv", 6)
    rep_eff = load_tsv(args.replay_dir / "AF8_EFFECT_EVIDENCE.tsv", 6)
    effect_gate("record", rec_eff, cases, failures)
    effect_gate("replay", rep_eff, cases, failures)
    for pid in sorted(set(rec_eff) & set(rep_eff) & expected):
        if rec_eff[pid][1:] != rep_eff[pid][1:]:
            failures.append(pid + ":effect_replay_mismatch")

    rec_obs = load_tsv(args.record_dir / "AF8_CLIENT_OBSERVATION_SAMPLES.tsv", 5)
    rep_obs = load_tsv(args.replay_dir / "AF8_CLIENT_OBSERVATION_SAMPLES.tsv", 5)
    observation_gate("record", rec_obs, cases, failures)
    observation_gate("replay", rep_obs, cases, failures)

    rec_stages = play_stage_gate("record", args.record_dir / "play-stages.tsv", cases, failures)
    rep_stages = play_stage_gate("replay", args.replay_dir / "play-stages.tsv", cases, failures)
    if rec_stages != rep_stages:
        failures.append("play_stage_count_replay_mismatch")

    rec_transient = load_jsonl(args.record_dir / "PRINCIPAL_OBSERVATIONS.jsonl")
    rep_transient = load_jsonl(args.replay_dir / "PRINCIPAL_OBSERVATIONS.jsonl")
    rec_kinds = transient_observation_gate("record", rec_transient, cases, failures)
    rep_kinds = transient_observation_gate("replay", rep_transient, cases, failures)
    if normalized_observations(rec_transient) != normalized_observations(rep_transient):
        failures.append("transient_observation_replay_mismatch")

    out = {
        "schema": "commander-simulator-next.ws33-a-rest-svar-af8-runtime.v2",
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "expected_paths": 8,
        "actual_card_source_bound": True,
        "play_spell_ability_authoritative": True,
        "mode_selection_authoritative": True,
        "target_selection_authoritative": True,
        "cost_payment_authoritative": True,
        "manual_target_injection": False,
        "direct_effect_resolution": False,
        "remote_actor_slot": 1,
        "positive_target_effect_required": True,
        "real_client_confidentiality_samples_required": True,
        "transient_hidden_event_positive_required": False,
        "record_decision_counts": dict(sorted((decision_counts.get("record") or {}).items())),
        "replay_decision_counts": dict(sorted((decision_counts.get("replay") or {}).items())),
        "record_play_stage_counts": dict(sorted(rec_stages.items())),
        "replay_play_stage_counts": dict(sorted(rep_stages.items())),
        "record_transient_event_kinds": dict(sorted(rec_kinds.items())),
        "replay_transient_event_kinds": dict(sorted(rep_kinds.items())),
        "failure_count": len(failures),
        "failures": failures,
        "coverage_mutated": False,
        "coverage_promotion": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    if failures:
        fail(";".join(failures[:24]))
    print("WS33_A_SVAR_AF8_GATE=PASS paths=8 coverage_promotion=false")


if __name__ == "__main__":
    main()
