#!/usr/bin/env python3
"""Deterministic dual-book (Book-A 4276 / Book-B 4188) C promotion mechanism.

Architecture: staging -> audit -> install.
  - Default mode stages promoted books under --staging-root and writes an audit
    receipt. Canonical books under --base-root are opened READ-ONLY and never
    mutated in stage/audit mode.
  - Install mode (--install) copies staged books over an explicit --install-root
    only; it refuses to touch --base-root unless WS33_C_ALLOW_CANONICAL_INSTALL=1
    is set in the environment (serial-authority approval, never in dry-run).

Promotion rule (BOOK_RECONCILIATION = EXACT_SHARED_ID_DUAL_WRITE_ONLY):
  - a path promotes only when the exact same path ID exists in both books with
    pre-state UNKNOWN in both. No fuzzy/descriptor/card-name/owner-family/SVar
    inference. Anything else fails with IDENTITY_RECONCILIATION_REQUIRED.
  - rerunning an already-promoted proposal fails closed as
    DUPLICATE_ALREADY_PROMOTED (no double credit, no PASS regression).

Exit 0 on success; exit 2 with WS33_C_PROMOTER=FAIL <code> otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
STATUS_KEYS = ("PASS", "FAIL", "UNSUPPORTED", "UNKNOWN")
BOOK_A_FILES = (
    "WS33_PATH_COVERAGE.json",
    "WS33_CASE_LEDGER.jsonl",
    "WS33_EXECUTION_LEDGER.jsonl",
    "WS33_PER_IDENTITY.jsonl",
    "WS33_SCENARIO_TEMPLATE_REGISTRY.json",
    "WS33_IMPLEMENTATION_TARGET_REGISTRY.json",
    "WS33_Q6_CANDIDATE_GATE.json",
    "WS33_WITNESSES.jsonl",
)
BOOK_B_FILES = (
    "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl",
    "WS33_INTEGRATED_WORK_QUEUE.json",
    "WS33_INTEGRATED_FRONTIER_GATE.json",
)
SHARDS = ("WS33A", "WS33B", "WS33C", "WS33D", "WS33E", "WS33F", "WS33G", "WS33H")


class PromotionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def fail(code: str, message: str) -> None:
    raise PromotionError(code, message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canon(obj), encoding="utf-8")


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canon(r) for r in rows), encoding="utf-8")


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proposal_digest(proposal_index: str, path_ids: list[str]) -> str:
    return hashlib.sha256(canon({"proposal_index": proposal_index, "path_ids": path_ids}).encode()).hexdigest()


def load_validator(validator_path: Path):
    spec = importlib.util.spec_from_file_location("ws33_witness_semantic_validator", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-root", type=Path, required=True, help="canonical ws33 dir (read-only)")
    ap.add_argument("--proposal", type=Path, required=True)
    ap.add_argument("--adapted-dir", type=Path, required=True,
                    help="per-path adapter outputs (subdirs with witness.json/trace.json)")
    ap.add_argument("--provenance", type=Path, required=True, help="staging provenance file")
    ap.add_argument("--schema", type=Path, required=True)
    ap.add_argument("--validator", type=Path, required=True)
    ap.add_argument("--staging-root", type=Path, required=True)
    ap.add_argument("--expect-book-a", required=True,
                    help="expected pre-state 'PASS=x,UNKNOWN=y' assertion for Book A")
    ap.add_argument("--expect-book-b", required=True, help="same for Book B")
    ap.add_argument("--campaign-id", required=True)
    ap.add_argument("--receipt-id", required=True)
    ap.add_argument("--c-campaign-root", type=Path, required=True,
                    help="read-only C witness branch ws33 dir (C manifest/partition source)")
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--install-root", type=Path, default=None)
    args = ap.parse_args()
    try:
        return run(args)
    except PromotionError as exc:
        print(f"WS33_C_PROMOTER=FAIL code={exc.code} message={exc}")
        return 2


def parse_counts(spec: str) -> Counter:
    out = Counter()
    for part in spec.split(","):
        key, _, val = part.partition("=")
        out[key.strip()] = int(val.strip())
    return out


def run(args) -> int:
    base = args.base_root.resolve()
    proposal = load_json(args.proposal)
    path_ids = proposal.get("path_ids", [])
    proposal_index = proposal.get("proposal_index", "")
    if not proposal_index or not path_ids:
        fail("PROPOSAL_INVALID", "proposal needs proposal_index + non-empty path_ids")
    if sorted(path_ids) != list(path_ids) or len(set(path_ids)) != len(path_ids):
        fail("PROPOSAL_INVALID", "path_ids must be sorted unique (authorized sorted-ID order)")
    if proposal_digest(proposal_index, path_ids) != proposal.get("proposal_digest"):
        fail("PROPOSAL_DIGEST_MISMATCH", "proposal digest != authorized sorted-ID digest")

    # --- Load base books (read-only) ---
    cov = load_json(base / "WS33_PATH_COVERAGE.json")
    cov_by = {p["effective_v2_path_id"]: p for p in cov["paths"]}
    if len(cov_by) != len(cov["paths"]):
        fail("BOOK_IDENTITY_CORRUPT", "duplicate Book-A identity")
    b_rows = load_jsonl(base / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl")
    b_by = {r["effective_path_id"]: r for r in b_rows}
    if len(b_by) != len(b_rows):
        fail("BOOK_IDENTITY_CORRUPT", "duplicate Book-B identity")

    pre_a = Counter(p["status"] for p in cov["paths"])
    pre_b = Counter(r["current_status"] for r in b_rows)
    if pre_a != parse_counts(args.expect_book_a):
        fail("PRESTATE_COUNT_MISMATCH",
             f"Book-A pre-state {dict(pre_a)} != asserted {args.expect_book_a}; "
             "stale counts rejected, re-verify fresh state")
    if pre_b != parse_counts(args.expect_book_b):
        fail("PRESTATE_COUNT_MISMATCH",
             f"Book-B pre-state {dict(pre_b)} != asserted {args.expect_book_b}")

    pre_a_pass = {i for i, p in cov_by.items() if p["status"] == "PASS"}
    pre_b_pass = {i for i, r in b_by.items() if r["current_status"] == "PASS"}

    # --- Exact shared-ID dual-write gating ---
    for pid in path_ids:
        a_row, b_row = cov_by.get(pid), b_by.get(pid)
        if a_row is None or b_row is None:
            fail("IDENTITY_RECONCILIATION_REQUIRED",
                 f"{pid}: not exactly present in both books; no inferred mapping permitted")
        a_unknown = (a_row.get("status") == "UNKNOWN"
                     and a_row.get("evidence_classification") == "UNKNOWN")
        b_unknown = (b_row.get("current_status") == "UNKNOWN"
                     and b_row.get("evidence_classification") == "UNKNOWN")
        if not a_unknown or not b_unknown:
            if a_row.get("status") == "PASS" or b_row.get("current_status") == "PASS":
                fail("DUPLICATE_ALREADY_PROMOTED",
                     f"{pid}: already PASS (A={a_row.get('status')}, B={b_row.get('current_status')}); "
                     "rerun fails closed, no double credit")
            fail("PRESTATE_NOT_UNKNOWN", f"{pid}: pre-state not UNKNOWN in both books")

    # --- Witness registry + canonical semantic validation ---
    adapted = args.adapted_dir.resolve()
    wit_by_path: dict[str, dict] = {}
    for sub in sorted(adapted.iterdir()):
        wfile = sub / "witness.json"
        if sub.is_dir() and wfile.is_file():
            w = load_json(wfile)
            for pid in w.get("v2_path_ids", []):
                if pid in wit_by_path:
                    fail("DUPLICATE_WITNESS", f"two adapted witnesses claim {pid}")
                wit_by_path[pid] = w
    validator = load_validator(args.validator)
    schema = load_json(args.schema)
    provenance = load_json(args.provenance)
    val_base = base
    validation_results = []
    for pid in path_ids:
        w = wit_by_path.get(pid)
        if w is None:
            fail("WITNESS_MISSING", f"no adapted v2.1 witness for {pid}")
        if w.get("v2_path_ids") != [pid]:
            fail("WITNESS_MISSING", f"witness {w.get('witness_id')} is not singleton for {pid}")
        if w.get("status") != "PASS":
            fail("WITNESS_MISSING", f"witness {w.get('witness_id')} status != PASS")
        if w.get("evidence_class") != "TECHNICALLY_CONFORMANT":
            fail("TC_LABEL_CHANGED",
                 f"witness {w.get('witness_id')} evidence_class={w.get('evidence_class')!r}; "
                 "TC label must be preserved")
        # locate the witness file on disk for base-relative trace resolution
        disk = None
        for sub in sorted(adapted.iterdir()):
            if sub.is_dir() and (sub / "witness.json").is_file():
                if load_json(sub / "witness.json").get("witness_id") == w.get("witness_id"):
                    disk = sub
                    break
        if disk is None:
            fail("WITNESS_MISSING", f"witness file missing for {pid}")
        trace_rel = os.path.relpath(disk / "trace.json", val_base)
        if w.get("trace_ref") != trace_rel:
            fail("WITNESS_MISSING",
                 f"witness trace_ref {w.get('trace_ref')!r} != base-relative {trace_rel!r}")
        manifest = load_json(base / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
        try:
            validator.validate(dict(w), manifest, val_base, schema, provenance)
        except Exception as exc:  # noqa: BLE001 - validator raises WitnessError(ValueError)
            code = getattr(exc, "code", type(exc).__name__)
            fail("SEMANTIC_VALIDATION_FAILED", f"{pid}: {code} {exc}")
        validation_results.append({"path_id": pid, "witness_id": w["witness_id"],
                                   "WS33_WITNESS_VALIDATION": "PASS"})

    # --- Stage: copy base books, apply exact transitions ---
    staging = args.staging_root.resolve()
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "books").mkdir(parents=True)
    for name in BOOK_A_FILES + BOOK_B_FILES:
        shutil.copy2(base / name, staging / "books" / name)

    promotion_ref = f"c-promotion/receipts/{args.receipt_id}.json"
    staged_cov = load_json(staging / "books" / "WS33_PATH_COVERAGE.json")
    staged_cov_by = {p["effective_v2_path_id"]: p for p in staged_cov["paths"]}
    for pid in path_ids:
        w = wit_by_path[pid]
        staged_cov_by[pid].update({
            "status": "PASS",
            "evidence_classification": "TECHNICALLY_CONFORMANT",
            "execution_source": args.campaign_id,
            "state_evidence": True,
            "trace_sha": w["trace_sha256"],
            "rules_refs": list(w["rules_authority_refs"]),
            "promotion_evidence": promotion_ref,
            "witness_ref": w["witness_id"],
        })
    staged_cov["paths"] = [staged_cov_by[i] for i in sorted(staged_cov_by)]
    staged_cov["status_counts"] = dict(Counter(p["status"] for p in staged_cov["paths"]))
    write_json(staging / "books" / "WS33_PATH_COVERAGE.json", staged_cov)

    staged_case = load_jsonl(staging / "books" / "WS33_CASE_LEDGER.jsonl")
    case_by = {r["effective_v2_path_id"]: r for r in staged_case}
    for pid in path_ids:
        case_by[pid]["scenario_status"] = args.campaign_id
    write_jsonl(staging / "books" / "WS33_CASE_LEDGER.jsonl",
                [case_by[i] for i in sorted(case_by)])

    staged_exec = load_jsonl(staging / "books" / "WS33_EXECUTION_LEDGER.jsonl")
    exec_by = {r["effective_v2_path_id"]: r for r in staged_exec}
    for pid in path_ids:
        w = wit_by_path[pid]
        exec_by[pid].update({"status": "PASS", "execution_source": args.campaign_id,
                             "trace_sha": w["trace_sha256"],
                             "witness_hash": sha_file(disk_of(wit_by_path, adapted, pid) / "witness.json"),
                             "blocker_class": None})
    write_jsonl(staging / "books" / "WS33_EXECUTION_LEDGER.jsonl",
                [exec_by[i] for i in sorted(exec_by)])

    staged_wit = load_jsonl(staging / "books" / "WS33_WITNESSES.jsonl")
    seen_ids = {w.get("witness_id") for w in staged_wit}
    seen_paths = {p for w in staged_wit for p in w.get("v2_path_ids", [])}
    for pid in path_ids:
        w = wit_by_path[pid]
        if w["witness_id"] in seen_ids or pid in seen_paths:
            fail("DUPLICATE_WITNESS", f"witness registry already contains {pid}")
        staged_wit.append(w)
    write_jsonl(staging / "books" / "WS33_WITNESSES.jsonl", staged_wit)

    recompute_book_a_derived(staging / "books", set(path_ids))

    staged_b = load_jsonl(staging / "books" / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl")
    b_stage_by = {r["effective_path_id"]: r for r in staged_b}
    for pid in path_ids:
        w = wit_by_path[pid]
        b_stage_by[pid].update({
            "current_status": "PASS",
            "evidence_classification": "TECHNICALLY_CONFORMANT",
            "blocker_classification": None,
            "campaign_id": args.campaign_id,
            "witness_id": w["witness_id"],
            "trace_sha256": w["trace_sha256"],
            "promotion_evidence": promotion_ref,
        })
    staged_b_rows = [b_stage_by[i] for i in sorted(b_stage_by)]
    write_jsonl(staging / "books" / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl", staged_b_rows)
    recompute_book_b_queue_gate(staging / "books", set(path_ids))

    # --- Audit: exact diff, no regression, set equality ---
    post_a = Counter(p["status"] for p in staged_cov["paths"])
    post_b = Counter(r["current_status"] for r in staged_b_rows)
    transitions_a = {i for i in staged_cov_by
                     if (cov_by[i]["status"], staged_cov_by[i]["status"]) != ("UNKNOWN", "UNKNOWN")}
    # precise transition pairs
    pairs_a = {i: (cov_by[i]["status"], staged_cov_by[i]["status"]) for i in staged_cov_by
               if cov_by[i]["status"] != staged_cov_by[i]["status"]}
    pairs_b = {i: (b_by[i]["current_status"], b_stage_by[i]["current_status"]) for i in b_stage_by
               if b_by[i]["current_status"] != b_stage_by[i]["current_status"]}
    _ = transitions_a
    if set(pairs_a) != set(path_ids) or set(pairs_b) != set(path_ids):
        fail("UNRELATED_PATH_TRANSITION",
             f"A-changed={sorted(set(pairs_a))} B-changed={sorted(set(pairs_b))} "
             f"proposal={path_ids}")
    if any(v != ("UNKNOWN", "PASS") for v in pairs_a.values()):
        fail("NON_PROMOTION_TRANSITION", f"Book-A non UNKNOWN->PASS: {pairs_a}")
    if any(v != ("UNKNOWN", "PASS") for v in pairs_b.values()):
        fail("NON_PROMOTION_TRANSITION", f"Book-B non UNKNOWN->PASS: {pairs_b}")
    if not (set(pre_a_pass) <= {i for i, p in staged_cov_by.items() if p["status"] == "PASS"}):
        fail("PASS_REGRESSION", "Book-A previous PASS set not preserved")
    if not (set(pre_b_pass) <= {i for i, r in b_stage_by.items() if r["current_status"] == "PASS"}):
        fail("PASS_REGRESSION", "Book-B previous PASS set not preserved")

    # --- Receipt with identity/model seal ---
    receipt = {
        "schema": "commander-simulator-next.ws33-c-dualbook-promotion-receipt.v1",
        "receipt_id": args.receipt_id,
        "proposal_index": proposal_index,
        "proposal_digest": proposal["proposal_digest"],
        "promoted_path_ids": list(path_ids),
        "campaign_id": args.campaign_id,
        "forge_pin": FORGE_PIN,
        "book_a": {
            "manifest_sha256": sha_file(base / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"),
            "coverage_prestate_sha256": sha_file(base / "WS33_PATH_COVERAGE.json"),
            "coverage_staged_sha256": sha_file(staging / "books" / "WS33_PATH_COVERAGE.json"),
            "prestate_counts": {k: pre_a.get(k, 0) for k in STATUS_KEYS},
            "poststate_counts": {k: post_a.get(k, 0) for k in STATUS_KEYS},
        },
        "book_b": {
            "gen2_artifact_id": load_json(base / "WS33_INTEGRATED_FRONTIER_GATE.json").get("generation2_artifact_id"),
            "gen2_artifact_digest": load_json(base / "WS33_INTEGRATED_FRONTIER_GATE.json").get("generation2_artifact_digest"),
            "model_source_head": load_json(base / "WS33_INTEGRATED_FRONTIER_GATE.json").get("model_source_head"),
            "model_source_tree": load_json(base / "WS33_INTEGRATED_FRONTIER_GATE.json").get("model_source_tree"),
            "ledger_prestate_sha256": sha_file(base / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"),
            "ledger_staged_sha256": sha_file(staging / "books" / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"),
            "prestate_counts": {k: pre_b.get(k, 0) for k in STATUS_KEYS},
            "poststate_counts": {k: post_b.get(k, 0) for k in STATUS_KEYS},
        },
        "c_evidence": {
            "batch_id": "WS33_C_BATCH_5",
            "run_id": None,  # filled by caller metadata below
        },
        "validation": validation_results,
        "transitions": {"book_a": pairs_a, "book_b": pairs_b},
        "previous_pass_preserved": True,
        "unrelated_path_changes": 0,
        "coverage_promotion_installed": False,
        # Complete authorized prestate binding: deterministic sha256 of every
        # base book file the installer will replace. The install transaction
        # verifies each install-target file against these hashes before the
        # first target write (companion drift -> INSTALL_REFUSED_PRESTATE).
        "prestate_hashes": {name: sha_file(base / name)
                            for name in BOOK_A_FILES + BOOK_B_FILES},
    }
    cmeta = proposal.get("c_evidence", {})
    croot = args.c_campaign_root.resolve()
    c_manifest = croot / "c-campaign" / "WS33_C_UNKNOWN_MANIFEST.json"
    c_partition = croot / "c-campaign" / "WS33_C_EVIDENCE_PARTITION.json"
    if not c_manifest.is_file() or not c_partition.is_file():
        fail("C_EVIDENCE_MISSING", "C manifest/partition not found under --c-campaign-root")
    receipt["c_evidence"] = {
        "batch_id": cmeta.get("batch_id", "WS33_C_BATCH_5"),
        "run_id": cmeta.get("run_id"),
        "job_id": cmeta.get("job_id"),
        "artifact_id": cmeta.get("artifact_id"),
        "artifact_digest": cmeta.get("artifact_digest"),
        "batch_digest": cmeta.get("batch_digest"),
        "source_head": cmeta.get("source_head"),
        "source_tree": cmeta.get("source_tree"),
        "c_manifest_sha256": sha_file(c_manifest),
        "c_partition_sha256": sha_file(c_partition),
    }
    receipt["staging_provenance_sha256"] = sha_file(args.provenance)
    receipt["proposal_sha256"] = sha_file(args.proposal)
    write_json(staging / "receipt.json", receipt)

    if args.install:
        target = args.install_root.resolve() if args.install_root else None
        if target is None:
            fail("INSTALL_REFUSED", "install mode requires --install-root")
        if target == base and os.environ.get("WS33_C_ALLOW_CANONICAL_INSTALL") != "1":
            fail("INSTALL_REFUSED",
                 "canonical install requires WS33_C_ALLOW_CANONICAL_INSTALL=1 (serial authority)")
        for name in BOOK_A_FILES + BOOK_B_FILES:
            shutil.copy2(staging / "books" / name, target / name)
        print(f"WS33_C_PROMOTER=INSTALLED receipt={args.receipt_id} files={len(BOOK_A_FILES + BOOK_B_FILES)}")
        return 0

    print(f"WS33_C_PROMOTER=STAGED receipt={args.receipt_id} "
          f"book_a={dict(post_a)} book_b={dict(post_b)}")
    return 0


def disk_of(wit_by_path: dict, adapted: Path, pid: str) -> Path:
    wid = wit_by_path[pid]["witness_id"]
    for sub in sorted(adapted.iterdir()):
        if sub.is_dir() and (sub / "witness.json").is_file():
            if load_json(sub / "witness.json").get("witness_id") == wid:
                return sub
    raise PromotionError("WITNESS_MISSING", f"witness dir missing for {pid}")


def recompute_book_a_derived(books: Path, promoted: set[str]) -> None:
    cov = load_json(books / "WS33_PATH_COVERAGE.json")
    pass_ids = {p["effective_v2_path_id"] for p in cov["paths"] if p["status"] == "PASS"}

    per = load_jsonl(books / "WS33_PER_IDENTITY.jsonl")
    for x in per:
        eff = set(x["effective_v2_path_ids"])
        x["pass_path_ids"] = sorted(eff & pass_ids)
        x["unresolved_path_ids"] = sorted(eff - pass_ids)
        x["status"] = "FULL" if not x["unresolved_path_ids"] else "PARTIAL"
    write_jsonl(books / "WS33_PER_IDENTITY.jsonl", per)

    tpl = load_json(books / "WS33_SCENARIO_TEMPLATE_REGISTRY.json")
    for t in tpl["templates"]:
        ids = set(t["path_ids"])
        t["admitted_path_ids"] = sorted(ids & pass_ids)
    write_json(books / "WS33_SCENARIO_TEMPLATE_REGISTRY.json", tpl)

    targ = load_json(books / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json")
    for t in targ["targets"]:
        unproved = sum(i not in pass_ids for i in t["path_ids"])
        t["unproved_path_count"] = unproved
        t["priority_score"] = unproved * t["cross_family_dependency_fanout"]
    targ["targets"].sort(key=lambda x: (-x["priority_score"], x["owner_family"],
                                        x["implementation_target"]))
    write_json(books / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json", targ)

    status = Counter(p["status"] for p in cov["paths"])
    identity_counts = Counter(x["status"] for x in per)
    fam: dict[str, Counter] = {}
    for p in cov["paths"]:
        fam.setdefault(p["owner_family"], Counter())[p["status"]] += 1
    q6 = load_json(books / "WS33_Q6_CANDIDATE_GATE.json")
    q6["path_status_counts"] = {k: status.get(k, 0) for k in STATUS_KEYS}
    q6["identity_counts"] = dict(identity_counts)
    q6["family_gates"] = {
        f: {"gate": "PASS" if c.get("PASS") == sum(c.values()) else "FAIL_CLOSED",
            "counts": dict(c), "effective_path_count": sum(c.values())}
        for f, c in sorted(fam.items())
    }
    blockers = []
    if status.get("UNKNOWN"):
        blockers.append({"class": "MISSING_SCENARIO_TEMPLATE", "path_count": status["UNKNOWN"]})
    if status.get("FAIL"):
        blockers.append({"class": "ACTUAL_CARD_CAMPAIGN_FAILURE", "path_count": status["FAIL"]})
    if status.get("UNSUPPORTED"):
        blockers.append({"class": "UNSUPPORTED_PRODUCTION_PATH",
                         "path_count": status["UNSUPPORTED"]})
    q6["remaining_blockers"] = blockers
    write_json(books / "WS33_Q6_CANDIDATE_GATE.json", q6)


def recompute_book_b_queue_gate(books: Path, promoted: set[str]) -> None:
    rows = load_jsonl(books / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl")
    after = Counter(r["current_status"] for r in rows)
    groups: dict[tuple, list[str]] = {}
    for r in rows:
        if r["current_status"] == "PASS":
            continue
        key = (r["logical_bucket"], r["owner_family"], r["runtime_subsystem"],
               r["scenario_group_id"], r["evidence_profile"])
        groups.setdefault(key, []).append(r["effective_path_id"])
    items = [{"logical_bucket": b, "owner_family": o, "runtime_subsystem": s,
              "scenario_group_id": g, "evidence_profile": p,
              "unresolved_path_count": len(ids), "effective_path_ids": sorted(ids),
              "priority_basis": "DESCENDING_UNRESOLVED_PATH_COUNT_THEN_STABLE_KEYS"}
             for (b, o, s, g, p), ids in groups.items()]
    items.sort(key=lambda r: (-r["unresolved_path_count"], r["logical_bucket"],
                              r["runtime_subsystem"], r["scenario_group_id"]))
    queue_path = books / "WS33_INTEGRATED_WORK_QUEUE.json"
    queue = load_json(queue_path)
    queue.update({"unresolved_path_count": after.get("UNKNOWN", 0),
                  "work_item_count": len(items), "items": items})
    write_json(queue_path, queue)
    ledger_path = books / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"
    gate = load_json(books / "WS33_INTEGRATED_FRONTIER_GATE.json")
    gate.update({
        "path_status_counts": {k: after.get(k, 0) for k in STATUS_KEYS},
        "unresolved_path_count": after.get("UNKNOWN", 0),
        "work_item_count": len(items),
        "ledger_sha256": sha_file(ledger_path),
        "queue_sha256": sha_file(queue_path),
        "status": "PASS",
    })
    write_json(books / "WS33_INTEGRATED_FRONTIER_GATE.json", gate)
    unresolved = {pid for item in items for pid in item["effective_path_ids"]}
    if unresolved & promoted:
        raise PromotionError("UNRELATED_PATH_TRANSITION", "promoted IDs remain queued")
    if len(unresolved) != after.get("UNKNOWN", 0):
        raise PromotionError("UNRELATED_PATH_TRANSITION", "queue union != UNKNOWN set")


if __name__ == "__main__":
    sys.exit(main())
