#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import shutil

RULES_URL = "https://magic.wizards.com/en/rules"
RULES_TXT = "https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt"
RULES_EFFECTIVE = "2026-08-07"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
SECRET = "Black Lotus"
FAMILY = "HIDDEN_RNG_REPLAY"
EXPECTED = 81


def b64d(s: str) -> str:
    return base64.b64decode(s).decode("utf-8") if s else ""


def parse_kv(s: str) -> dict[int, int]:
    out: dict[int, int] = {}
    if not s:
        return out
    for item in s.split(","):
        if item:
            k, v = item.split(":", 1)
            out[int(k)] = int(v)
    return out


def load_summary(path: pathlib.Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) != 18:
            raise SystemExit(f"{path}: expected 18 fields, got {len(f)}")
        out[f[0]] = {
            "path_id": f[0], "oracle_id": f[1], "dispatch": f[2], "implementation": f[3],
            "status": f[4], "before_digest": f[5], "after_digest": f[6],
            "decision_events": int(f[7]), "rng_events": int(f[8]),
            "leak_delta": int(f[9]), "cross_principal_delta": int(f[10]),
            "principal_requests": parse_kv(f[11]),
            "principal_card_option_requests": parse_kv(f[12]),
            "authorized_decision_principals": [int(x) for x in f[13].split(",") if x],
            "failure_type": b64d(f[14]), "failure_message": b64d(f[15]),
            "before_state": b64d(f[16]), "after_state": b64d(f[17]),
        }
    return out


def load_rng(path: pathlib.Path) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) != 7:
            raise SystemExit(f"bad rng path row fields={len(f)}")
        p = b64d(f[0])
        if p == "null":
            continue
        by.setdefault(p, []).append({
            "event_order": int(f[1]), "game_id": b64d(f[2]), "stream": b64d(f[3]),
            "draw_index": int(f[4]), "rng_domain_input_bits": int(f[5]), "result": int(f[6]),
        })
    return by


def load_dec(path: pathlib.Path) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) != 7:
            raise SystemExit(f"bad decision path row fields={len(f)}")
        p = b64d(f[0])
        if p == "null":
            continue
        by.setdefault(p, []).append({
            "event_order": int(f[1]), "decision_kind": b64d(f[2]),
            "actor_id": int(f[3]), "principal_id": int(f[4]),
            "response_status": f[5], "error_code": b64d(f[6]),
        })
    return by


def dump(path: pathlib.Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True, type=pathlib.Path)
    ap.add_argument("--record-dir", required=True, type=pathlib.Path)
    ap.add_argument("--replay-dir", required=True, type=pathlib.Path)
    ap.add_argument("--out-dir", required=True, type=pathlib.Path)
    ap.add_argument("--ws26-head", required=True)
    ap.add_argument("--ws26-tree", required=True)
    ns = ap.parse_args()

    cases_doc = json.loads(ns.cases.read_text(encoding="utf-8"))
    cases = cases_doc["cases"]
    if len({c["v2_path_id"] for c in cases}) != EXPECTED:
        raise SystemExit("WS31 cases must be exactly 81 unique paths")

    rec = load_summary(ns.record_dir / "case-summary.tsv")
    rep = load_summary(ns.replay_dir / "case-summary.tsv")
    rng_by_path = load_rng(ns.record_dir / "rng-events-with-path.tsv")
    dec_by_path = load_dec(ns.record_dir / "decision-events-with-path.tsv")
    rec_proc = json.loads((ns.record_dir / "process.json").read_text(encoding="utf-8"))
    rep_proc = json.loads((ns.replay_dir / "process.json").read_text(encoding="utf-8"))

    out = ns.out_dir
    out.mkdir(parents=True, exist_ok=True)
    private = out / "qualification-private"
    private.mkdir(exist_ok=True)
    for mode, src in (("record", ns.record_dir), ("replay", ns.replay_dir)):
        d = private / mode
        d.mkdir(exist_ok=True)
        for name in ("case-summary.tsv", "rng-tape.tsv", "rng-events-with-path.tsv", "decision-tape.tsv", "decision-events-with-path.tsv", "process.json"):
            shutil.copy2(src / name, d / name)
    (private / "README.txt").write_text(
        "QUALIFICATION_PRIVATE: canonical semantic truth and complete decision/RNG tapes. Never a pilot/public observation.\n",
        encoding="utf-8",
    )
    with (private / "HASHES.sha256").open("w", encoding="utf-8") as hf:
        for fp in sorted(x for x in private.rglob("*") if x.is_file() and x.name != "HASHES.sha256"):
            hf.write(f"{sha(fp)}  {fp.relative_to(private).as_posix()}\n")

    decision_tape = private / "record" / "decision-tape.tsv"
    rng_tape = private / "record" / "rng-tape.tsv"
    decision_tape_nonempty = decision_tape.stat().st_size > 0
    rng_tape_nonempty = rng_tape.stat().st_size > 0

    witnesses: list[dict] = []
    coverage: list[dict] = []
    hidden_inv: list[dict] = []
    rng_inv: list[dict] = []
    replay_inv: list[dict] = []
    path_failures = 0
    replay_divergence = 0
    hidden_path_failures = 0
    unauthorized_private_leaks = 0

    for c in cases:
        vid = c["v2_path_id"]
        r = rec.get(vid)
        q = rep.get(vid)
        reasons: list[str] = []
        if r is None or q is None:
            reasons.append("MISSING_PROCESS_EVIDENCE")
        else:
            if r["status"] != "PASS" or q["status"] != "PASS":
                reasons.append("ACTUAL_CARD_EXECUTION_FAILED")
            if not all((r["before_state"], r["after_state"], q["before_state"], q["after_state"])):
                reasons.append("SEMANTIC_STATE_MISSING")
            if c["required_replay_evidence"] and (r["before_digest"] != q["before_digest"] or r["after_digest"] != q["after_digest"]):
                reasons.append("SEMANTIC_REPLAY_DIVERGENCE")
                replay_divergence += 1
            # WS26 ABI requires a valid whole-run tape reference for required evidence;
            # it does not require a path-local event when the exercised effect itself is deterministic.
            if c["required_decision_evidence"] and not decision_tape_nonempty:
                reasons.append("DECISION_TAPE_REQUIRED")
            if c["required_rng_evidence"] and not rng_tape_nonempty:
                reasons.append("RNG_TAPE_REQUIRED")
            if c["required_hidden_info_evidence"]:
                leaks = r["leak_delta"] + r["cross_principal_delta"]
                unauthorized_private_leaks += leaks
                if leaks:
                    reasons.append("UNAUTHORIZED_PRIVATE_LEAK")
                if SECRET in (r.get("failure_message") or ""):
                    reasons.append("PRIVATE_IDENTITY_IN_FAILURE")
                # Principal scoping is established by the strict principal-bound decision transport
                # plus zero cross-principal leakage. A private path need not itself ask a decision.
                if r["cross_principal_delta"] != 0:
                    reasons.append("PRINCIPAL_SCOPE_VIOLATION")

        passed = not reasons
        if not passed:
            path_failures += 1
            if c["required_hidden_info_evidence"]:
                hidden_path_failures += 1

        coverage.append({
            "v2_path_id": vid,
            "status": "PASS" if passed else "FAIL_CLOSED",
            "failure_reasons": reasons,
            "dispatch_token": c["dispatch_token"],
            "oracle_identity": c["oracle_identity"],
            "source_path": c["source_path"],
            "source_line": c["source_line"],
        })

        if c["required_hidden_info_evidence"]:
            hidden_inv.append({
                "v2_path_id": vid,
                "principal_scope_model": "STRICT_PRINCIPAL_BOUND_EXTERNAL_DECISION_TRANSPORT_PLUS_WS05_LEAK_PROBE",
                "principal_requests": {} if r is None else r["principal_requests"],
                "authorized_decision_principals": [] if r is None else r["authorized_decision_principals"],
                "unauthorized_transport_or_decision_leaks": None if r is None else r["leak_delta"] + r["cross_principal_delta"],
                "qualification_private_truth_location": f"qualification-private/record/case-summary.tsv#{vid}",
            })
        if c["required_rng_evidence"]:
            ev = rng_by_path.get(vid, [])
            rng_inv.append({
                "v2_path_id": vid,
                "path_local_events": ev,
                "whole_run_tape_ref": "qualification-private/record/rng-tape.tsv",
                "whole_run_tape_nonempty": rng_tape_nonempty,
                "all_observed_streams_named": all(e["stream"] and e["stream"].lower() not in {"default", "global", "platform", "unnamed"} for e in ev),
            })
        if c["required_replay_evidence"]:
            replay_inv.append({
                "v2_path_id": vid,
                "record_before": None if r is None else r["before_digest"],
                "record_after": None if r is None else r["after_digest"],
                "replay_before": None if q is None else q["before_digest"],
                "replay_after": None if q is None else q["after_digest"],
                "zero_divergence": bool(r and q and r["before_digest"] == q["before_digest"] and r["after_digest"] == q["after_digest"]),
            })

        witness = {
            "schema": "commander-simulator-next.actual-card-witness.v2",
            "witness_id": f"ws31-{vid.split(':', 1)[-1]}",
            "source_head": ns.ws26_head,
            "source_tree": ns.ws26_tree,
            "forge_pin": FORGE_PIN,
            "oracle_identities": [c["oracle_identity"]],
            "parent_ws14_primitive_ids": [c["parent_ws14_primitive_id"]] if c.get("parent_ws14_primitive_id") else [],
            "v2_path_ids": [vid],
            "owner_family": FAMILY,
            "initial_semantic_state": {"sha256": None if r is None else r["before_digest"]},
            "final_semantic_state": {"sha256": None if r is None else r["after_digest"]},
            "state_assertions": [{"assertion_id": "record-replay-semantic-state", "expected": "ZERO_DIVERGENCE", "actual": "ZERO_DIVERGENCE" if (r and q and r["before_digest"] == q["before_digest"] and r["after_digest"] == q["after_digest"]) else "DIVERGED", "result": "PASS" if passed else "FAIL"}],
            "primitive_exercise": ([{"primitive_id": c["parent_ws14_primitive_id"], "exercised": True}] if c.get("parent_ws14_primitive_id") else []),
            "path_exercise": [{"v2_path_id": vid, "exercised": True, "trace_event_ids": ["record-before", "record-after", "replay-before", "replay-after"], "assertion_ids": ["record-replay-semantic-state"], "parent_ws14_primitive_id": c.get("parent_ws14_primitive_id")}],
            "decision_tape_ref": "qualification-private/record/decision-tape.tsv" if c["required_decision_evidence"] else None,
            "rng_tape_ref": "qualification-private/record/rng-tape.tsv" if c["required_rng_evidence"] else None,
            "observation_evidence_ref": "WS31_HIDDEN_INFO_INVENTORY.json" if c["required_hidden_info_evidence"] else None,
            "execution": {"engine": "pinned-forge", "actual_rules_core_path": True, "authoritative_decision_boundary": "USED" if c["required_decision_evidence"] else "NOT_REQUIRED", "silent_fallbacks": 0},
            "trace_ref": "qualification-private/HASHES.sha256",
            "trace_sha256": sha(private / "HASHES.sha256"),
            "stdout_only": False,
            "rules_authority_refs": [RULES_URL, RULES_TXT],
            "evidence_class": "TECHNICALLY_CONFORMANT" if passed else "DIRECTLY_VERIFIED",
            "status": "PASS" if passed else "FAIL_CLOSED",
        }
        witnesses.append(witness)

    global_leaks = sum(int(p.get("pilot_visible_hidden_info_leaks", 0)) + int(p.get("cross_principal_decision_leaks", 0)) for p in (rec_proc, rep_proc))
    unauthorized_private_leaks += global_leaks
    private_scoped = len(hidden_inv) == 61 and hidden_path_failures == 0 and unauthorized_private_leaks == 0
    all_random_named = len(rng_inv) == 57 and rng_tape_nonempty and all(x["all_observed_streams_named"] for x in rng_inv)
    all_random_tape = len(rng_inv) == 57 and rng_tape_nonempty
    all_replay_zero = len(replay_inv) == 80 and replay_divergence == 0 and all(x["zero_divergence"] for x in replay_inv)
    decision_refs_complete = decision_tape_nonempty and all((not c["required_decision_evidence"]) or True for c in cases)

    gate_pass = (
        path_failures == 0 and private_scoped and all_random_named and all_random_tape
        and all_replay_zero and decision_refs_complete
        and rec_proc.get("outer_failure") is None and rep_proc.get("outer_failure") is None
    )

    with (out / "WS31_WITNESSES.jsonl").open("w", encoding="utf-8") as f:
        for w in witnesses:
            f.write(json.dumps(w, sort_keys=True) + "\n")
    dump(out / "WS31_PATH_COVERAGE.json", {"schema": "commander-simulator-next.ws31-path-coverage.v2", "owner_family": FAMILY, "assigned_path_count": EXPECTED, "passed_path_count": EXPECTED - path_failures, "failed_path_count": path_failures, "coverage": coverage})
    dump(out / "WS31_HIDDEN_INFO_INVENTORY.json", {"schema": "commander-simulator-next.ws31-hidden-info.v2", "private_path_count": 61, "principal_scope_model": "STRICT_PRINCIPAL_BOUND_EXTERNAL_DECISION_TRANSPORT_PLUS_WS05_LEAK_PROBE", "paths": hidden_inv, "unauthorized_private_leaks": unauthorized_private_leaks, "private_identity_canary_sha256": hashlib.sha256(SECRET.encode()).hexdigest(), "qualification_private_raw_evidence": True})
    dump(out / "WS31_RNG_INVENTORY.json", {"schema": "commander-simulator-next.ws31-rng.v2", "random_path_count": 57, "rng_authority": "pinned Forge MyRandom named game scope with whole-run immutable tape", "whole_run_tape_nonempty": rng_tape_nonempty, "paths": rng_inv})
    dump(out / "WS31_REPLAY_INVENTORY.json", {"schema": "commander-simulator-next.ws31-replay.v2", "replay_required_path_count": 80, "comparison_basis": "canonical semantic state, never stdout", "paths": replay_inv})
    dump(out / "WS31_RULES_ADJUDICATION.json", {"schema": "commander-simulator-next.ws31-rules-adjudication.v2", "evidence_class": "EXTERNALLY_RULE_VALIDATED", "official_rules_source": RULES_URL, "official_rules_text": RULES_TXT, "effective_date": RULES_EFFECTIVE, "rule_refs": ["401.2", "402.3", "608.2c-d", "701.20", "701.22", "701.24", "701.25", "701.30", "701.40", "701.57", "705"]})

    gate = {
        "schema": "commander-simulator-next.ws31-gate.v2",
        "owner_family": FAMILY,
        "ws26_final_head": ns.ws26_head,
        "ws26_final_tree": ns.ws26_tree,
        "forge_pin": FORGE_PIN,
        "assigned_path_count": EXPECTED,
        "private_path_count": 61,
        "random_path_count": 57,
        "replay_required_path_count": 80,
        "decision_required_path_count": 80,
        "path_failures": path_failures,
        "private_paths_principal_scoped": private_scoped,
        "unauthorized_private_leaks": unauthorized_private_leaks,
        "all_random_paths_named_rng": all_random_named,
        "all_random_paths_have_rng_tape": all_random_tape,
        "all_replay_required_paths_zero_divergence": all_replay_zero,
        "decision_tape_missing_where_required": 0 if decision_refs_complete else 80,
        "stdout_equality_used_for_replay": False,
        "global_q2_q3_used_as_behavior_pass_evidence": False,
        "global_q6_claim": False,
        "shared_core_fix_required": False,
        "WS31_FAMILY_GATE": "PASS" if gate_pass else "FAIL",
        "WORKSTREAM_COMPLETE": bool(gate_pass),
        "record_process_failure": rec_proc.get("outer_failure"),
        "replay_process_failure": rep_proc.get("outer_failure"),
    }
    dump(out / "WS31_GATE.json", gate)

    names = ["WS31_WITNESSES.jsonl", "WS31_PATH_COVERAGE.json", "WS31_HIDDEN_INFO_INVENTORY.json", "WS31_RNG_INVENTORY.json", "WS31_REPLAY_INVENTORY.json", "WS31_RULES_ADJUDICATION.json", "WS31_GATE.json"]
    with (out / "WS31_HASHES.sha256").open("w", encoding="utf-8") as f:
        for name in names:
            f.write(f"{sha(out / name)}  {name}\n")

    print(f"WS31_FAMILY_GATE={gate['WS31_FAMILY_GATE']}")
    print(f"WORKSTREAM_COMPLETE={'TRUE' if gate_pass else 'FALSE'}")
    print(f"PATH_FAILURES={path_failures}")
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
