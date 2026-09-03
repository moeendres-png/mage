#!/usr/bin/env python3
"""Strict source-profile adjudication for WS33 G principal observations.

This verifier does not infer Magic legality and does not select any action. It consumes
only already-materialized exact Forge cases plus runtime evidence. Positive temporary
identity observation is required when the pinned Forge consumer must expose hidden card
identity to a principal (a discretionary card decision or an explicit look/reveal family).
A Dig path that moves every examined card without a look/reveal consumer is classified as
NEGATIVE_OR_TRANSITION_ONLY: hidden-info evidence is still required, but manufacturing a
temporary identity grant would be incorrect. Unknown hidden consumer shapes fail closed.

Two exact case ABIs are supported:
- Direct-G v15: the executed consumer is columns 4/14 (dispatch/script).
- G SVar AF v19: the executed target-SVar consumer is columns 17/18
  (targetDispatch/targetScript), never the source-parent dispatch/script.

Any other, empty, or mixed case ABI fails closed. --expected-paths defaults to 28 to
preserve the immutable Direct-G contract; serial AF qualification passes 21 explicitly.
"""
from __future__ import annotations

import argparse
import base64
import json
from collections import Counter, defaultdict
from pathlib import Path


DIRECT_G_V15 = "DIRECT_G_V15"
G_SVAR_AF_V19 = "G_SVAR_AF_V19"


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def parse_script(script: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in script.split("|"):
        part = part.strip()
        if "$" not in part:
            continue
        key, value = part.split("$", 1)
        out[key.strip()] = value.strip()
    return out


def positive_profile(api: str, script: str, hidden: bool, decision: bool) -> tuple[str, str]:
    if not hidden:
        return "NONE_REQUIRED", "hidden=false"
    if decision:
        return "POSITIVE_TEMPORARY_REQUIRED", "authoritative hidden-card decision"

    params = parse_script(script)
    explicit = (
        params.get("Reveal", "").lower() == "true"
        or "RevealOptional" in params
        or "ForceReveal" in params
        or "ForceRevealToController" in params
        or "WithMayLook" in params
    )
    if explicit:
        return "POSITIVE_TEMPORARY_REQUIRED", "explicit pinned-Forge reveal/look parameter"

    always_observe_apis = {"PeekAndReveal", "RevealHand", "Scry", "Surveil", "Discover", "DigUntil"}
    if api in always_observe_apis:
        return "POSITIVE_TEMPORARY_REQUIRED", f"pinned-Forge {api} observation consumer"

    if api == "Dig":
        change_num = params.get("ChangeNum", "1").lower()
        # DigEffect's no-choice all-card path does not require a temporary look grant
        # unless one of the explicit reveal/may-look parameters above is present.
        if change_num == "all":
            return "NEGATIVE_OR_TRANSITION_ONLY", "Dig ChangeNum=All without reveal/may-look consumer"
        return "POSITIVE_TEMPORARY_REQUIRED", "Dig subset selection requires hidden-card identity"

    return "UNKNOWN_HIDDEN_CONSUMER", f"unadjudicated hidden API={api}"


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def decode_b64(field: str, label: str) -> str:
    try:
        return base64.b64decode(field, validate=True).decode("utf-8")
    except Exception as exc:
        raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL invalid {label}: {exc}") from exc


def load_cases(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    observed_abis: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) == 15:
            case_abi = DIRECT_G_V15
            api = f[4]
            script = decode_b64(f[14], f"Direct-G script line {line_number}")
        elif len(f) == 19:
            case_abi = G_SVAR_AF_V19
            api = f[17]
            script = decode_b64(f[18], f"AF targetScript line {line_number}")
            if not api or not script or not script.startswith("DB$"):
                raise SystemExit(
                    "WS33_G_PRINCIPAL_OBSERVATION=FAIL "
                    f"invalid AF target consumer line {line_number}: dispatch={api!r} script={script[:32]!r}"
                )
        else:
            raise SystemExit(
                "WS33_G_PRINCIPAL_OBSERVATION=FAIL "
                f"unknown case ABI line {line_number}: columns={len(f)}"
            )
        observed_abis.add(case_abi)
        if len(observed_abis) != 1:
            raise SystemExit(
                "WS33_G_PRINCIPAL_OBSERVATION=FAIL mixed/ambiguous case ABIs: "
                + ",".join(sorted(observed_abis))
            )

        hidden = f[10] == "1"
        decision = f[13] == "1"
        profile, reason = positive_profile(api, script, hidden, decision)
        pid = f[1]
        if not pid.startswith("forge-behavior-v2:"):
            raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL invalid path id line {line_number}: {pid!r}")
        if pid in out:
            raise SystemExit(f"WS33_G_PRINCIPAL_OBSERVATION=FAIL duplicate path id: {pid}")
        out[pid] = {
            "ordinal": int(f[0]),
            "oracle_id": f[2],
            "api": api,
            "implementation": f[5],
            "hidden": hidden,
            "rng": f[11] == "1",
            "replay": f[12] == "1",
            "decision": decision,
            "profile": profile,
            "profile_reason": reason,
            "script": script,
            "case_abi": case_abi,
        }
    if not out:
        raise SystemExit("WS33_G_PRINCIPAL_OBSERVATION=FAIL empty case file")
    return out


def load_summary(path: Path) -> dict[str, list[str]]:
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row[1]: row for row in rows}


def check_summary(label: str, rows: dict[str, list[str]], req: dict[str, dict], failures: list[str]) -> None:
    require(set(rows) == set(req), f"{label}:summary_path_set_mismatch", failures)
    for pid in sorted(set(rows) & set(req)):
        row = rows[pid]
        rq = req[pid]
        require(len(row) >= 20, f"{pid}:{label}_summary_columns={len(row)}", failures)
        if len(row) < 20:
            continue
        require(row[4] == "PASS", f"{pid}:{label}_status={row[4]}", failures)
        require(row[18] == "1", f"{pid}:{label}_stack_admission={row[18]}", failures)
        require(row[19] == "1", f"{pid}:{label}_stack_resolution={row[19]}", failures)
        require(int(row[9]) == 0, f"{pid}:{label}_hidden_leak_delta={row[9]}", failures)
        require(int(row[10]) == 0, f"{pid}:{label}_cross_principal_delta={row[10]}", failures)
        require((int(row[7]) > 0) == rq["decision"], f"{pid}:{label}_decision_requirement_mismatch={row[7]}", failures)
        require((int(row[8]) > 0) == rq["rng"], f"{pid}:{label}_rng_requirement_mismatch={row[8]}", failures)
        require(not row[11] and not row[12], f"{pid}:{label}_runtime_failure={row[11]}:{row[12]}", failures)


def check_events(label: str, events: list[dict], req: dict[str, dict], failures: list[str]) -> dict[str, Counter]:
    by_path: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        pid = event.get("path_id")
        require(pid in req, f"{label}:unknown_path={pid}", failures)
        require(event.get("identity_match") is True, f"{label}:identity_mismatch={pid}:{event.get('principal_id')}:{event.get('card_id')}", failures)
        if pid in req:
            by_path[pid].append(event)

    counts: dict[str, Counter] = {}
    for pid, rq in req.items():
        ordered = sorted(by_path.get(pid, []), key=lambda e: e.get("sequence", -1))
        kinds = Counter(e.get("kind") for e in ordered)
        counts[pid] = kinds
        grants = [e for e in ordered if e.get("kind") == "SERVER_GRANT"]
        if rq["profile"] == "UNKNOWN_HIDDEN_CONSUMER":
            failures.append(f"{pid}:{label}_unknown_hidden_consumer_profile")
        elif rq["profile"] == "POSITIVE_TEMPORARY_REQUIRED" and not grants:
            failures.append(f"{pid}:{label}_missing_positive_observation")
        elif rq["profile"] == "NEGATIVE_OR_TRANSITION_ONLY":
            # No positive grant is required. Existing grants are allowed only if they
            # complete the same strict lifecycle; this protects future pinned-Forge
            # changes without forcing an artificial observation today.
            pass

        # Strict per-card lifecycle. Multiple cards can be granted in one batch, so
        # validate each (principal,card) stream independently rather than global order.
        streams: dict[tuple[int, int], list[dict]] = defaultdict(list)
        for event in ordered:
            if event.get("kind") in {"SERVER_GRANT", "CLIENT_VISIBLE", "SERVER_REVOKE", "CLIENT_HIDDEN"}:
                streams[(int(event["principal_id"]), int(event["card_id"]))].append(event)
        for (principal, card), stream in streams.items():
            state = "HIDDEN"
            for event in stream:
                kind = event["kind"]
                if state == "HIDDEN":
                    require(kind == "SERVER_GRANT", f"{pid}:{label}_lifecycle_expected_grant:{principal}:{card}:{kind}", failures)
                    if kind == "SERVER_GRANT":
                        state = "GRANTED"
                elif state == "GRANTED":
                    require(kind == "CLIENT_VISIBLE", f"{pid}:{label}_lifecycle_expected_visible:{principal}:{card}:{kind}", failures)
                    if kind == "CLIENT_VISIBLE":
                        state = "VISIBLE"
                elif state == "VISIBLE":
                    require(kind == "SERVER_REVOKE", f"{pid}:{label}_lifecycle_expected_revoke:{principal}:{card}:{kind}", failures)
                    if kind == "SERVER_REVOKE":
                        state = "REVOKED"
                elif state == "REVOKED":
                    require(kind == "CLIENT_HIDDEN", f"{pid}:{label}_lifecycle_expected_hidden:{principal}:{card}:{kind}", failures)
                    if kind == "CLIENT_HIDDEN":
                        state = "HIDDEN"
            require(state == "HIDDEN", f"{pid}:{label}_incomplete_lifecycle:{principal}:{card}:{state}", failures)
    return counts


def normalized(events: list[dict]) -> Counter:
    return Counter(
        (
            e["path_id"], e["kind"], int(e["principal_id"]), int(e["card_id"]),
            e.get("decision_kind", "") if str(e["kind"]).startswith("SERVER_") else "",
            bool(e["identity_match"]),
        )
        for e in events
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--record-dir", type=Path, required=True)
    ap.add_argument("--replay-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--source-case-artifact-id", type=int, required=True)
    ap.add_argument("--expected-paths", type=int, default=28)
    args = ap.parse_args()

    if args.expected_paths <= 0:
        raise SystemExit("WS33_G_PRINCIPAL_OBSERVATION=FAIL expected-paths must be positive")

    failures: list[str] = []
    req = load_cases(args.cases)
    require(len(req) == args.expected_paths, f"requirement_rows={len(req)} expected={args.expected_paths}", failures)

    record_summary = load_summary(args.record_dir / "case-summary.tsv")
    replay_summary = load_summary(args.replay_dir / "case-summary.tsv")
    check_summary("record", record_summary, req, failures)
    check_summary("replay", replay_summary, req, failures)
    for pid in sorted(set(record_summary) & set(replay_summary) & set(req)):
        a, b = record_summary[pid], replay_summary[pid]
        if len(a) >= 20 and len(b) >= 20:
            require(a[5] == b[5], f"{pid}:semantic_before_digest_mismatch", failures)
            require(a[6] == b[6], f"{pid}:semantic_after_digest_mismatch", failures)
            require(a[7] == b[7], f"{pid}:decision_count_replay_mismatch", failures)
            require(a[8] == b[8], f"{pid}:rng_count_replay_mismatch", failures)

    rec = load_jsonl(args.record_dir / "PRINCIPAL_OBSERVATIONS.jsonl")
    rep = load_jsonl(args.replay_dir / "PRINCIPAL_OBSERVATIONS.jsonl")
    require(bool(rec), "record_observations_empty", failures)
    require(bool(rep), "replay_observations_empty", failures)
    record_counts = check_events("record", rec, req, failures)
    replay_counts = check_events("replay", rep, req, failures)
    require(normalized(rec) == normalized(rep), "record_replay_observation_multiset_mismatch", failures)

    profiles = Counter(rq["profile"] for rq in req.values())
    case_abis = sorted({rq["case_abi"] for rq in req.values()})
    profile_rows = [
        {
            "path_id": pid,
            "api": rq["api"],
            "profile": rq["profile"],
            "reason": rq["profile_reason"],
            "record_grants": record_counts.get(pid, Counter()).get("SERVER_GRANT", 0),
            "replay_grants": replay_counts.get(pid, Counter()).get("SERVER_GRANT", 0),
        }
        for pid, rq in sorted(req.items()) if rq["hidden"]
    ]

    out = {
        "schema": "commander-simulator-next.ws33-g-principal-observation.v3",
        "source_case_artifact_id": args.source_case_artifact_id,
        "case_abi": case_abis[0] if len(case_abis) == 1 else "AMBIGUOUS",
        "expected_paths": args.expected_paths,
        "hidden_required_paths": sum(rq["hidden"] for rq in req.values()),
        "record_path_coverage": len(set(record_summary) & set(req)),
        "replay_path_coverage": len(set(replay_summary) & set(req)),
        "record_observation_event_path_count": len({e.get("path_id") for e in rec if e.get("path_id") in req}),
        "replay_observation_event_path_count": len({e.get("path_id") for e in rep if e.get("path_id") in req}),
        "observation_profile_counts": dict(sorted(profiles.items())),
        "observation_profiles": profile_rows,
        "record_event_count": len(rec),
        "replay_event_count": len(rep),
        "retained_hidden_identity_payload": False,
        "client_identity_compared_to_authoritative_card_in_memory": True,
        "principal_transport": "REMOTE_CLIENT_DELTA",
        "local_host_public_reveal_remote_evidence_claimed": False,
        "hidden_discretionary_choice_without_remote_observation_allowed": False,
        "temporary_observation_revocation_required": True,
        "negative_hidden_paths_require_positive_observation": False,
        "hidden_leak_delta_required": 0,
        "cross_principal_delta_required": 0,
        "coverage_mutated": False,
        "failure_count": len(failures),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL_CLOSED",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    if failures:
        raise SystemExit("WS33_G_PRINCIPAL_OBSERVATION=FAIL " + repr(failures[:30]))
    print("WS33_G_PRINCIPAL_OBSERVATION=PASS")


if __name__ == "__main__":
    main()
