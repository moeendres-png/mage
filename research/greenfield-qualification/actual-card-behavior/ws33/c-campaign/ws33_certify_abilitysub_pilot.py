#!/usr/bin/env python3
"""Certify the WS33-C AbilitySub pilot campaign output (deterministic).

Checks, for every case in the pilot plan:
  - record.json present with record-success.marker;
  - schema id, witness/oracle/path identity match the plan + owned manifest;
  - execution boundary: actual_rules_core_path true, silent_fallbacks 0,
    direct_effect_resolution false, decision NOT_REQUIRED (STATE_ONLY pilot);
  - all state_assertions result PASS and match recomputed deltas;
  - trace.json shows >=1 child observation with production parent chain
    (parent_api/parent_host non-empty, matching plan parent_api/card) and
    forge_pin match; direct-child-only traces (null parent) FAIL;
  - claimed path is in the owned C manifest with STATE_ONLY dimensions.

Writes GATE json + sha256 file. Exit nonzero on any violation.
Self-test (--self-test) exercises the fail-closed negative without Forge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def fail(msg: str) -> int:
    print(f"WS33_C_ADJUDICATION=FAIL {msg}")
    return 1


def check_trace(trace: dict, case: dict) -> str | None:
    if trace.get("forge_pin") != FORGE_PIN:
        return "forge pin mismatch"
    if trace.get("path_id") != case["path_id"]:
        return "trace path mismatch"
    if trace.get("direct_effect_resolution") is not False:
        return "direct_effect_resolution not false"
    if trace.get("production_entrypoint") != "forge.game.ability.AbilityUtils.resolve":
        return "production entrypoint mismatch"
    obs = trace.get("child_observations") or []
    good = [o for o in obs
            if o.get("child_api") == case["child_api"]
            and o.get("parent_api") == case["parent_api"]
            and o.get("parent_host") == case["card_name"]
            and o.get("child_host") == case["card_name"]]
    if not good:
        return "no production-linked child observation (direct-child-only rejected)"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--campaign-root", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.self_test:
        # Positive: production-linked observation accepted.
        trace_ok = {
            "forge_pin": FORGE_PIN, "path_id": "P",
            "direct_effect_resolution": False,
            "production_entrypoint": "forge.game.ability.AbilityUtils.resolve",
            "child_observations": [
                {"seq": 0, "child_api": "GainLife", "child_host": "Cloudblazer",
                 "parent_api": "ChangesZone", "parent_host": "Cloudblazer"},
                {"seq": 1, "child_api": "Draw", "child_host": "Cloudblazer",
                 "parent_api": "GainLife", "parent_host": "Cloudblazer"},
            ],
        }
        case = {"path_id": "P", "child_api": "Draw", "parent_api": "GainLife",
                "card_name": "Cloudblazer"}
        assert check_trace(trace_ok, case) is None, "positive must pass"
        # Negative: direct-child-only trace (null parent chain) rejected.
        trace_bad = dict(trace_ok, child_observations=[
            {"seq": 0, "child_api": "Draw", "child_host": "Cloudblazer",
             "parent_api": None, "parent_host": None},
        ])
        err = check_trace(trace_bad, case)
        assert err is not None and "direct-child-only" in err, "negative must fail closed"
        print("WS33_C_ADJUDICATION_SELFTEST=PASS positive_accepted negative_rejected")
        return 0

    for req in ("campaign_root", "manifest", "plan", "out"):
        if getattr(args, req) is None:
            return fail(f"missing --{req.replace('_', '-')}")

    manifest = load(args.manifest)
    plan = load(args.plan)
    owned = {r["effective_v2_path_id"]: r for r in manifest["paths"]}
    assert manifest["forge_pin"] == FORGE_PIN and plan["forge_pin"] == FORGE_PIN

    passed = []
    for case in plan["cases"]:
        pid = case["path_id"]
        own = owned.get(pid)
        if own is None:
            return fail(f"case path not in owned C manifest: {pid}")
        if own["requires_decision"] or own["requires_hidden"] or own["requires_replay"] or own["requires_rng"]:
            return fail(f"pilot case requires beyond-STATE evidence: {pid}")
        d = args.campaign_root / "records" / pid.removeprefix("forge-behavior-v2:")
        rec_p, trace_p, mark_p = d / "record.json", d / "trace.json", d / "record-success.marker"
        if not (rec_p.is_file() and trace_p.is_file() and mark_p.is_file()):
            return fail(f"missing campaign evidence for {pid}")
        rec, trace = load(rec_p), load(trace_p)
        if rec.get("schema") != "commander-simulator-next.ws33-runtime-campaign-record.v1":
            return fail(f"record schema mismatch {pid}")
        if rec.get("v2_path_ids") != [pid]:
            return fail(f"record path identity mismatch {pid}")
        if rec.get("oracle_identities") != [case["oracle_identity"]]:
            return fail(f"record oracle mismatch {pid}")
        ex = rec.get("execution", {})
        if not (ex.get("actual_rules_core_path") is True and ex.get("silent_fallbacks") == 0
                and ex.get("direct_effect_resolution") is False):
            return fail(f"execution boundary violated {pid}")
        if ex.get("authoritative_decision_boundary") != "NOT_REQUIRED":
            return fail(f"unexpected decision boundary {pid}")
        for a in rec.get("state_assertions", []):
            if a.get("result") != "PASS":
                return fail(f"state assertion not PASS {pid}: {a.get('assertion_id')}")
        by_id = {a["assertion_id"]: a for a in rec["state_assertions"]}
        if by_id.get("life-delta", {}).get("actual") != case["life_delta"]:
            return fail(f"life delta mismatch {pid}")
        if by_id.get("hand-delta-net", {}).get("actual") != case["hand_delta_net"]:
            return fail(f"hand delta mismatch {pid}")
        err = check_trace(trace, case)
        if err is not None:
            return fail(f"{err} {pid}")
        if rec.get("evidence_class") != "TECHNICALLY_CONFORMANT":
            return fail(f"evidence class mismatch {pid}")
        passed.append(pid)

    gate = {
        "schema": "commander-simulator-next.ws33-c-abilitysub-pilot-gate.v1",
        "forge_pin": FORGE_PIN,
        "source_head": "895240f4058076764227a418ad28e84f61d3a7ed",
        "source_tree": "cec73ae51b0168280ea648892f3e9edd46dcd883",
        "pilot_path_count": len(passed),
        "pilot_paths": sorted(passed),
        "coverage_mutated": False,
        "coverage_promoted": False,
        "status": "PASS",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(gate, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    h = hashlib.sha256(args.out.read_bytes()).hexdigest()
    (args.out.parent / "WS33_C_PILOT_GATE.sha256").write_text(f"{h}  {args.out.name}\n", encoding="utf-8")
    print(f"WS33_C_ADJUDICATION=PASS pilot_paths={len(passed)} gate_sha256={h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
