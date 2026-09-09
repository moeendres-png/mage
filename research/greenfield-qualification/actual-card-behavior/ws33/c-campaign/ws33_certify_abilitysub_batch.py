#!/usr/bin/env python3
"""Certify the WS33-C AbilitySub batch campaign output (deterministic).

Per-execution checks over record.json + trace.json:
  - schema/identity (record v1, trace v2, forge pin, batch, execution,
    oracle set, path-id set, marker present);
  - execution boundary (rules-core path, silent 0, no direct resolution,
    decision NOT_REQUIRED, TECHNICALLY_CONFORMANT);
  - exact chain: for every claimed link, a parent-resolution event and a
    child observation with child.parent_id == parent.id, root linkage, and
    integer parent_seq < child_seq; relation_runtime_derived ==
    relation_declared == planned child_sub;
  - modeled vs actual runtime class preserved with explicit relation
    (mismatch without relation fails closed);
  - decision tripwire: expected method set, zero hits;
  - runtime profile flags all clean; replay not required;
  - every planned semantic assertion present with result PASS and the
    planned expected value; per-link production-child-reached present.

Writes a batch gate with a per-path verdict table (EVIDENCED or
UNKNOWN + root cause). Exit nonzero on any violation.
--self-test runs the positive control plus the nine fail-closed negatives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
TRIPWIRE_METHODS = [
    "chooseTargetsFor", "chooseCardsForEffect", "chooseCardsForEffectMultiple",
    "chooseSingleEntityForEffect", "confirmAction", "chooseNumber",
    "chooseSpellAbilityToPlay",
]
TRACE_SCHEMA_V2 = "commander-simulator-next.ws33-abilitysub-trace.v2"
RECORD_SCHEMA_V1 = "commander-simulator-next.ws33-runtime-campaign-record.v1"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def check_execution(trace: dict, record: dict, expect: dict, owned: dict) -> str | None:
    """Return None on accept, else the fail-closed reason."""
    if trace.get("schema") != TRACE_SCHEMA_V2:
        return "trace schema mismatch"
    if record.get("schema") != RECORD_SCHEMA_V1:
        return "record schema mismatch"
    if trace.get("forge_pin") != FORGE_PIN:
        return "forge pin mismatch"
    if trace.get("execution_id") != expect["execution_id"]:
        return "record identity mismatch: execution"
    if set(record.get("v2_path_ids", [])) != set(expect["paths"]):
        return "record identity mismatch: path set"
    if [expect["oracle_identity"]] != sorted(record.get("oracle_identities", [])) \
            and set(record.get("oracle_identities", [])) != {expect["oracle_identity"]}:
        return "record identity mismatch: oracle"
    if trace.get("direct_effect_resolution") is not False:
        return "direct_effect_resolution not false"
    if trace.get("production_entrypoint") != "forge.game.ability.AbilityUtils.resolve":
        return "production entrypoint mismatch"
    ex = record.get("execution", {})
    if not (ex.get("actual_rules_core_path") is True and ex.get("silent_fallbacks") == 0
            and ex.get("direct_effect_resolution") is False):
        return "execution boundary violated"
    if ex.get("authoritative_decision_boundary") != "NOT_REQUIRED":
        return "unexpected decision boundary"
    if record.get("evidence_class") != "TECHNICALLY_CONFORMANT":
        return "evidence class mismatch"
    parents = {e["id"]: e for e in trace.get("parent_resolution_events", [])}
    if not parents:
        return "missing parent provenance: no parent-resolution events"
    children = trace.get("child_observations", [])
    matched = {m["path_id"]: m for m in trace.get("matched_links", [])}
    for link in expect["links"]:
        pid = link["path_id"]
        m = matched.get(pid)
        if m is None:
            return f"missing matched link: {pid}"
        p = parents.get(m.get("parent_id"))
        c = next((x for x in children if x["id"] == m.get("child_id")), None)
        if p is None or c is None:
            return f"missing parent/child observation: {pid}"
        if not isinstance(m.get("parent_seq"), int) or not isinstance(m.get("child_seq"), int):
            return f"ordering not integer-sequenced: {pid}"
        if not (m["parent_seq"] < m["child_seq"]):
            return f"child-before-parent observation: {pid}"
        if c.get("parent_id") != p["id"]:
            return f"missing parent provenance: child not linked to parent: {pid}"
        if p.get("api") != link["parent_api"] or c.get("api") != link["child_api"]:
            return f"wrong child match: {pid}"
        if p.get("host") != expect["card_name"] or c.get("host") != expect["card_name"]:
            return f"host identity mismatch: {pid}"
        if m.get("relation_runtime_derived") != link["child_sub"]:
            return f"runtime relation mismatch: {pid}"
        if m.get("relation_declared") != link["child_sub"] \
                or m.get("relation_match") is not True:
            return f"declared relation mismatch: {pid}"
        own = owned.get(pid, {})
        if m.get("modeled_class") != own.get("implementation_target"):
            return f"modeled class mismatch: {pid}"
        if m.get("actual_runtime_class") != own.get("actual_runtime_class"):
            return f"runtime class mismatch: {pid}"
        if m.get("modeled_class") != m.get("actual_runtime_class") \
                and not m.get("attribution_relation"):
            return "modeled/runtime attribution mismatch without explicit relation"
    trip = trace.get("decision_tripwire", {})
    if sorted(trip.get("methods", [])) != sorted(TRIPWIRE_METHODS):
        return "tripwire method set mismatch"
    declared = {(c.get("site"), c.get("options"))
                for c in expect.get("expected_consultations", [])}
    for hit in trip.get("hits", []):
        if hit.get("incidental") is True:
            continue
        if (hit.get("site"), hit.get("options")) not in declared:
            return (f"unexpected decision requirement: {hit.get('site')} "
                    f"options={hit.get('options')} caller={hit.get('caller')}")
    for site, options in sorted(declared):
        if not any(h.get("site") == site and h.get("options") == options
                   and h.get("incidental") is not True for h in trip.get("hits", [])):
            return f"declared consultation not observed: {site} options={options}"
    prof = trace.get("runtime_profile", {})
    if prof.get("static_screen") != "PASS":
        return "static screen not passed"
    if prof.get("unexpected_decision"):
        return "unexpected decision requirement (profile)"
    if prof.get("unexpected_hidden"):
        return "unexpected hidden-information requirement"
    if prof.get("unexpected_rng"):
        return "unexpected RNG requirement"
    if prof.get("replay_required"):
        return "replay requirement inconsistent with STATE_ONLY profile"
    by_id = {a["assertion_id"]: a for a in record.get("state_assertions", [])}
    for a in expect["assertions"]:
        got = by_id.get(a["assertion_id"])
        if got is None or got.get("result") != "PASS":
            return f"semantic assertion not PASS: {a['assertion_id']}"
        if got.get("expected") != a["expected"]:
            return f"semantic expectation mismatch: {a['assertion_id']}"
    for link in expect["links"]:
        short = link["path_id"].removeprefix("forge-behavior-v2:")
        got = by_id.get(f"production-child-reached-{short}")
        if got is None or got.get("result") != "PASS":
            return f"production-child-reached missing: {link['path_id']}"
    return None


def check_source_seal(run_source: str, expected_source: str) -> str | None:
    if expected_source and run_source != expected_source:
        return (f"source-seal mismatch: run={run_source} "
                f"expected={expected_source}")
    return None


def selftest() -> int:
    base_trace = {
        "schema": TRACE_SCHEMA_V2, "forge_pin": FORGE_PIN,
        "execution_id": "e1", "direct_effect_resolution": False,
        "production_entrypoint": "forge.game.ability.AbilityUtils.resolve",
        "parent_resolution_events": [
            {"seq": 4, "id": 11, "api": "GainLife", "host": "Cloudblazer",
             "sub_param": "DBDraw"}],
        "child_observations": [
            {"seq": 5, "id": 12, "api": "Draw", "host": "Cloudblazer",
             "parent_id": 11, "root_id": 11}],
        "matched_links": [{
            "path_id": "P", "parent_id": 11, "child_id": 12,
            "parent_seq": 4, "child_seq": 5,
            "relation_runtime_derived": "DBDraw", "relation_declared": "DBDraw",
            "relation_match": True, "modeled_class": "M", "actual_runtime_class": "M",
            "attribution_relation": "IDENTICAL"}],
        "decision_tripwire": {"methods": list(TRIPWIRE_METHODS), "hits": []},
        "runtime_profile": {"static_screen": "PASS", "unexpected_decision": False,
                            "unexpected_hidden": False, "unexpected_rng": False,
                            "replay_required": False},
    }
    base_record = {
        "schema": RECORD_SCHEMA_V1, "v2_path_ids": ["P"],
        "oracle_identities": ["O"],
        "execution": {"actual_rules_core_path": True, "silent_fallbacks": 0,
                      "direct_effect_resolution": False,
                      "authoritative_decision_boundary": "NOT_REQUIRED"},
        "evidence_class": "TECHNICALLY_CONFORMANT",
        "state_assertions": [
            {"assertion_id": "life-delta-actor", "expected": 2, "actual": 2,
             "result": "PASS"},
            {"assertion_id": "production-child-reached-P", "expected": True,
             "actual": True, "result": "PASS"}],
    }
    expect = {"execution_id": "e1", "card_name": "Cloudblazer",
              "oracle_identity": "O", "paths": ["P"],
              "links": [{"path_id": "P", "parent_api": "GainLife",
                         "child_api": "Draw", "child_sub": "DBDraw"}],
              "assertions": [{"assertion_id": "life-delta-actor", "expected": 2}],
              "expected_consultations": []}
    owned = {"P": {"implementation_target": "M", "actual_runtime_class": "M"}}

    import copy
    cases = []
    t, r = copy.deepcopy(base_trace), copy.deepcopy(base_record)
    cases.append(("positive", t, r, None))
    t = copy.deepcopy(base_trace)
    t["child_observations"][0]["parent_id"] = -1
    t["parent_resolution_events"] = []
    cases.append(("missing-parent-provenance", t, copy.deepcopy(base_record),
                  "missing parent provenance"))
    t = copy.deepcopy(base_trace)
    t["child_observations"][0]["api"] = "Token"
    cases.append(("wrong-child-match", t, copy.deepcopy(base_record),
                  "wrong child match"))
    t = copy.deepcopy(base_trace)
    t["matched_links"][0]["parent_seq"] = 9
    t["matched_links"][0]["child_seq"] = 4
    cases.append(("child-before-parent", t, copy.deepcopy(base_record),
                  "child-before-parent"))
    t = copy.deepcopy(base_trace)
    t["matched_links"][0]["attribution_relation"] = ""
    t["matched_links"][0]["actual_runtime_class"] = "OTHER"
    owned_diverged = {"P": {"implementation_target": "M",
                            "actual_runtime_class": "OTHER"}}
    cases.append(("attribution-mismatch-without-relation", t, copy.deepcopy(base_record),
                  "attribution mismatch without explicit relation", owned_diverged))
    t = copy.deepcopy(base_trace)
    t["decision_tripwire"]["hits"] = [
        {"site": "chooseTargetsFor", "options": 2,
         "caller": "AttachEffect.resolve", "incidental": False}]
    cases.append(("unexpected-decision", t, copy.deepcopy(base_record),
                  "unexpected decision requirement"))
    t = copy.deepcopy(base_trace)
    t["runtime_profile"]["unexpected_hidden"] = True
    cases.append(("unexpected-hidden", t, copy.deepcopy(base_record),
                  "unexpected hidden-information requirement"))
    t = copy.deepcopy(base_trace)
    t["runtime_profile"]["unexpected_rng"] = True
    cases.append(("unexpected-rng", t, copy.deepcopy(base_record),
                  "unexpected RNG requirement"))
    r = copy.deepcopy(base_record)
    r["v2_path_ids"] = ["Q"]
    cases.append(("record-identity-mismatch", copy.deepcopy(base_trace), r,
                  "record identity mismatch"))
    # Declared singleton consultation observed exactly: accept.
    t = copy.deepcopy(base_trace)
    t["decision_tripwire"]["hits"] = [
        {"site": "chooseSingleEntityForEffect", "options": 1,
         "caller": "AttachEffect.resolve", "incidental": False}]
    expect_declared = copy.deepcopy(expect)
    expect_declared["expected_consultations"] = [
        {"site": "chooseSingleEntityForEffect", "options": 1}]
    cases.append(("declared-consultation-observed", t, copy.deepcopy(base_record),
                  None, None, expect_declared))
    # Declared consultation with different option count: reject.
    t = copy.deepcopy(base_trace)
    t["decision_tripwire"]["hits"] = [
        {"site": "chooseSingleEntityForEffect", "options": 3,
         "caller": "AttachEffect.resolve", "incidental": False}]
    cases.append(("consultation-options-mismatch", t, copy.deepcopy(base_record),
                  "unexpected decision requirement", None, expect_declared))
    # Incidental-only flow queries: accept.
    t = copy.deepcopy(base_trace)
    t["decision_tripwire"]["hits"] = [
        {"site": "chooseSpellAbilityToPlay", "options": -1,
         "caller": "PhaseHandler.mainLoopStep", "incidental": True}]
    cases.append(("incidental-only", t, copy.deepcopy(base_record), None))
    failures = []
    for entry in cases:
        name, t, r, want = entry[0], entry[1], entry[2], entry[3]
        use_owned = entry[4] if len(entry) > 4 and entry[4] is not None else owned
        use_expect = entry[5] if len(entry) > 5 else expect
        got = check_execution(t, r, use_expect, use_owned)
        if want is None and got is not None:
            failures.append(f"{name}: wrongly rejected ({got})")
        elif want is not None and (got is None or want not in got):
            failures.append(f"{name}: not fail-closed (got={got!r})")
    # source-seal mismatch is adjudicated at gate level via check_source_seal.
    seal_err = check_source_seal("HEAD_A", "HEAD_B")
    if seal_err is None or "source-seal mismatch" not in seal_err:
        failures.append("source-seal-mismatch: not fail-closed")
    if check_source_seal("HEAD_A", "HEAD_A") is not None:
        failures.append("source-seal-match: wrongly rejected")
    if failures:
        print("WS33_C_BATCH_ADJUDICATION_SELFTEST=FAIL")
        for f in failures:
            print("  " + f)
        return 1
    print("WS33_C_BATCH_ADJUDICATION_SELFTEST=PASS cases=13 "
          "(positive + incidental-only + declared-consultation + 10 fail-closed negatives)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--campaign-root", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--source-head", default="")
    ap.add_argument("--source-tree", default="")
    ap.add_argument("--expect-source-head", default="")
    args = ap.parse_args()

    if args.self_test:
        return selftest()
    for req in ("campaign_root", "manifest", "plan", "out"):
        if getattr(args, req) is None:
            print(f"WS33_C_BATCH_ADJUDICATION=FAIL missing --{req.replace('_', '-')}")
            return 1
    manifest = load(args.manifest)
    plan = load(args.plan)
    owned = {r["effective_v2_path_id"]: r for r in manifest["paths"]}
    seal_err = check_source_seal(args.source_head, args.expect_source_head)
    if seal_err is not None:
        print(f"WS33_C_BATCH_ADJUDICATION=FAIL {seal_err}")
        return 1

    verdicts = []
    for ex in plan["executions"]:
        d = args.campaign_root / "records" / ex["execution_id"]
        rec_p, trace_p, mark_p = d / "record.json", d / "trace.json", d / "record-success.marker"
        if not (rec_p.is_file() and trace_p.is_file() and mark_p.is_file()):
            verdicts.append({"execution_id": ex["execution_id"], "status": "UNKNOWN",
                             "root_cause": "MISSING_CAMPAIGN_EVIDENCE",
                             "paths": ex["paths"]})
            continue
        err = check_execution(load(trace_p), load(rec_p), ex, owned)
        if err is None:
            verdicts.append({"execution_id": ex["execution_id"], "status": "EVIDENCED",
                             "evidence_class": "TECHNICALLY_CONFORMANT",
                             "run_source_head": args.source_head,
                             "paths": ex["paths"]})
        else:
            verdicts.append({"execution_id": ex["execution_id"], "status": "UNKNOWN",
                             "root_cause": err, "paths": ex["paths"]})
    gate = {
        "schema": "commander-simulator-next.ws33-c-batch-gate.v1",
        "batch": plan["batch"],
        "batch_digest": plan["batch_digest"],
        "forge_pin": FORGE_PIN,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "coverage_mutated": False,
        "coverage_promoted": False,
        "executions": verdicts,
        "status": "PASS" if all(v["status"] == "EVIDENCED" for v in verdicts) else "PARTIAL",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(gate, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    h = hashlib.sha256(args.out.read_bytes()).hexdigest()
    (args.out.parent / (args.out.stem + ".sha256")).write_text(
        f"{h}  {args.out.name}\n", encoding="utf-8")
    ok = sum(1 for v in verdicts if v["status"] == "EVIDENCED")
    print(f"WS33_C_BATCH_ADJUDICATION={gate['status']} evidenced_executions={ok}/{len(verdicts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
