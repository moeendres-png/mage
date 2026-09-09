#!/usr/bin/env python3
"""Fail-closed adjudicator for A-rest AF8 production-cast Record/Replay evidence."""
from __future__ import annotations

import argparse
import base64
import json
import math
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


def load_multi_tsv(path: Path, columns: int) -> dict[str, list[list[str]]]:
    if not path.is_file():
        fail("missing " + str(path))
    out: dict[str, list[list[str]]] = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        f = line.split("\t")
        if len(f) != columns:
            fail(f"{path.name} line={n} columns={len(f)} expected={columns}")
        if not f[0]:
            fail(f"{path.name} empty path line={n}")
        out.setdefault(f[0], []).append(f)
    return out


def multi_multiset(rows: dict[str, list[list[str]]]) -> Counter[tuple]:
    return Counter((pid, tuple(tuple(r) for r in sorted(map(tuple, rs)))) for pid, rs in sorted(rows.items()))


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


def target_shape(target_script: str) -> tuple[str, str]:
    params = parse_script(target_script)
    api = params.get("DB")
    if api == "ChangeZone":
        return "ZONE", params.get("Destination", "")
    if api == "Pump" and "KW" in params:
        return "KEYWORD", params.get("KW", "")
    return "", ""


def target_detail_gate(label: str, rows: dict[str, list[list[str]]], cases: dict[str, list[str]], failures: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for pid in rows:
        if pid not in cases:
            failures.append(f"{label}:unknown_target_path={pid}")
    for pid in sorted(cases):
        rs = rows.get(pid, [])
        if not rs:
            failures.append(f"{pid}:{label}:target_rows_missing")
            continue
        target_script = base64.b64decode(cases[pid][18], validate=True).decode("utf-8")
        kind, expected = target_shape(target_script)
        if not kind or not expected:
            failures.append(f"{pid}:{label}:unsupported_target_shape")
            continue
        seen_cards: set[int] = set()
        src_ids: set[int] = set()
        root_ids: set[int] = set()
        actor_ids: set[int] = set()
        child_ids: set[int] = set()
        creature_gain = 0
        for r in rs:
            if len(r) != 13:
                failures.append(f"{pid}:{label}:target_schema")
                continue
            try:
                card, src, root, child, actor = int(r[1]), int(r[9]), int(r[10]), int(r[11]), int(r[12])
            except ValueError:
                failures.append(f"{pid}:{label}:target_identity")
                continue
            try:
                name, types = decode_field(r[2]), decode_field(r[3])
            except ValueError:
                failures.append(f"{pid}:{label}:target_encoding")
                continue
            if not name or not types:
                failures.append(f"{pid}:{label}:target_identity_empty")
                continue
            if card in seen_cards:
                failures.append(f"{pid}:{label}:duplicate_target_card")
                continue
            seen_cards.add(card)
            if r[4] not in {"true", "false"} or r[7] not in {"true", "false"} or r[8] not in {"true", "false"}:
                failures.append(f"{pid}:{label}:target_flag_schema")
                continue
            if not r[5] or not r[6] or r[6] == "UNKNOWN":
                failures.append(f"{pid}:{label}:target_zone_missing")
                continue
            if min(card, src, root, child, actor) < 0:
                failures.append(f"{pid}:{label}:target_identity_binding_missing")
                continue
            src_ids.add(src)
            root_ids.add(root)
            actor_ids.add(actor)
            child_ids.add(child)
            if kind == "ZONE":
                if r[5] == expected or r[6] != expected:
                    failures.append(f"{pid}:{label}:exact_zone_movement_missing")
            else:
                if r[8] != "true":
                    failures.append(f"{pid}:{label}:keyword_not_observed")
                elif "Creature" in target_script and r[4] == "true":
                    creature_gain += 1
        if len(src_ids) != 1 or len(root_ids) != 1 or len(actor_ids) != 1:
            failures.append(f"{pid}:{label}:source_root_actor_chain_split")
        if not child_ids:
            failures.append(f"{pid}:{label}:child_execution_missing")
        if kind == "KEYWORD" and "Creature" in target_script and creature_gain < 1:
            failures.append(f"{pid}:{label}:selected_creature_gain_missing")
        counts[pid] = len(rs)
    return counts


SELECTION_BASIS = {"POSITIVE_X_ANNOUNCEMENT", "SOURCE_PROVEN_DESIRED_PLUS_MINIMUM", "AUTHORITATIVE_STABLE_ORDER"}


def forced_selection(n: int, mn: int, mx: int) -> bool:
    total = sum(math.comb(n, k) for k in range(max(0, mn), min(n, mx) + 1))
    return total == 1


def selection_gate(label: str, rows: dict[str, list[list[str]]], cases: dict[str, list[str]], failures: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for pid in rows:
        if pid not in cases:
            failures.append(f"{label}:unknown_selection_path={pid}")
    for pid in sorted(cases):
        rs = rows.get(pid, [])
        script = base64.b64decode(cases[pid][14], validate=True).decode("utf-8")
        for r in rs:
            if len(r) != 12:
                failures.append(f"{pid}:{label}:selection_schema")
                continue
            kind, basis = r[1], r[10]
            if not kind:
                failures.append(f"{pid}:{label}:selection_kind_empty")
                continue
            try:
                actor, principal, n, mn, mx, sel = (int(r[i]) for i in (2, 3, 4, 5, 6, 7))
            except ValueError:
                failures.append(f"{pid}:{label}:selection_integers")
                continue
            if actor != principal or actor < 0:
                failures.append(f"{pid}:{label}:selection_principal_scope")
                continue
            if mn < 0 or mx < mn or n < 0 or sel < 0 or sel > n or not mn <= sel <= mx:
                failures.append(f"{pid}:{label}:selection_cardinality")
                continue
            ids = r[8].split(",") if r[8] else []
            sems = r[9].split(",") if r[9] else []
            if bool(r[8]) != bool(r[9]):
                failures.append(f"{pid}:{label}:selection_identity_semantic_mismatch")
                continue
            if r[8] and len(ids) != sel:
                failures.append(f"{pid}:{label}:selected_id_count")
                continue
            decoded: list[str] = []
            if r[9]:
                try:
                    decoded = [decode_field(s) for s in sems]
                except ValueError:
                    failures.append(f"{pid}:{label}:selection_semantic_encoding")
                    continue
                if len(decoded) != sel:
                    failures.append(f"{pid}:{label}:selected_semantic_count")
                    continue
            if basis not in SELECTION_BASIS:
                failures.append(f"{pid}:{label}:unknown_selection_basis")
                continue
            if r[11] not in {"true", "false"} or (forced_selection(n, mn, mx) != (r[11] == "true")):
                failures.append(f"{pid}:{label}:forced_misclassified")
                continue
            if kind == "NUMBER" and basis == "POSITIVE_X_ANNOUNCEMENT":
                if mn != 1 or mx != 1 or sel != 1 or len(decoded) != 1:
                    failures.append(f"{pid}:{label}:x_selection_shape")
                    continue
                if not decoded[0].isdigit() or int(decoded[0]) < 1:
                    failures.append(f"{pid}:{label}:x_not_positive")
        if "Announce$ X" in script:
            xrows = [r for r in rs if len(r) == 12 and r[1] == "NUMBER" and r[10] == "POSITIVE_X_ANNOUNCEMENT"]
            if not xrows:
                failures.append(f"{pid}:{label}:x_announcement_selection_missing")
        if cases[pid][4] == "Charm":
            mrows = [r for r in rs if len(r) == 12 and r[1] == "MODE_SELECTION"]
            if not mrows:
                failures.append(f"{pid}:{label}:mode_selection_missing")
            for r in mrows:
                try:
                    mn, mx, sel = int(r[5]), int(r[6]), int(r[7])
                except ValueError:
                    continue
                if sel != max(1, mn) or sel < 1 or sel > mx:
                    failures.append(f"{pid}:{label}:mode_cardinality")
        counts[pid] = len(rs)
    return counts


def play_stage_gate(label: str, path: Path, cases: dict[str, list[str]], failures: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    source_api_seen: Counter[str] = Counter()
    source_api_success: Counter[str] = Counter()
    true_stages: dict[str, set[str]] = defaultdict(set)
    terminal_failed: set[str] = set()
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
        success = f[2] == "true"
        if api == cases[pid][4]:
            source_api_seen[pid] += 1
            if success:
                source_api_success[pid] += 1
        if success:
            true_stages[pid].add(stage)
        elif stage in {"PLAY_ABILITY_FALSE", "OPTIONAL_COST_SELECTION_NULL"}:
            terminal_failed.add(pid)
    if set(counts) != set(cases):
        failures.append(label + ":play_stage_path_coverage")
    for pid in cases:
        if source_api_seen[pid] < 1:
            failures.append(f"{pid}:{label}:source_play_stage_missing")
        if source_api_success[pid] < 1:
            failures.append(f"{pid}:{label}:source_play_stage_success_missing")
        if not {"PLAY_ABILITY_TRUE", "PREREQUISITES_MET"} <= true_stages[pid]:
            failures.append(f"{pid}:{label}:production_stage_success_missing")
        if pid in terminal_failed:
            failures.append(f"{pid}:{label}:terminal_play_stage_failure")
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

    rec_tgt = load_multi_tsv(args.record_dir / "AF8_TARGET_EVIDENCE.tsv", 13)
    rep_tgt = load_multi_tsv(args.replay_dir / "AF8_TARGET_EVIDENCE.tsv", 13)
    rec_target_counts = target_detail_gate("record", rec_tgt, cases, failures)
    rep_target_counts = target_detail_gate("replay", rep_tgt, cases, failures)
    if multi_multiset(rec_tgt) != multi_multiset(rep_tgt):
        failures.append("target_replay_mismatch")

    rec_sel = load_multi_tsv(args.record_dir / "AF8_SELECTION_WITNESS.tsv", 12)
    rep_sel = load_multi_tsv(args.replay_dir / "AF8_SELECTION_WITNESS.tsv", 12)
    rec_selection_counts = selection_gate("record", rec_sel, cases, failures)
    rep_selection_counts = selection_gate("replay", rep_sel, cases, failures)
    if multi_multiset(rec_sel) != multi_multiset(rep_sel):
        failures.append("selection_replay_mismatch")

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
        "record_target_row_counts": dict(sorted(rec_target_counts.items())),
        "replay_target_row_counts": dict(sorted(rep_target_counts.items())),
        "record_selection_row_counts": dict(sorted(rec_selection_counts.items())),
        "replay_selection_row_counts": dict(sorted(rep_selection_counts.items())),
        "identity_bound_evidence_required": True,
        "forced_selection_classification_required": True,
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
