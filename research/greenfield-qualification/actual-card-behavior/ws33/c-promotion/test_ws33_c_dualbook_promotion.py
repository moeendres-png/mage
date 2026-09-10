#!/usr/bin/env python3
"""Focused tests for the WS33-C deterministic dual-book promotion mechanism.

Unit layer: synthetic mini-books + mutated copies of the retained C evidence
fail closed on every guard (no fabrication, TC preservation, exact shared-ID
dual-write, proposal digest, duplicate, install refusal).

Integration layer: the real retained Batch-5 evidence adapts losslessly,
passes the canonical v2.1 validator, and the full dry-run restage is byte
deterministic with exactly one UNKNOWN->PASS transition per book.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

WS33_ROOT = Path(__file__).resolve().parent.parent
CPROM = WS33_ROOT / "c-promotion"
ADAPTER = CPROM / "ws33_c_to_v21_adapter.py"
PROMOTER = CPROM / "ws33_c_dualbook_promoter.py"
VALIDATOR = WS33_ROOT / "abi" / "WS33_WITNESS_SEMANTIC_VALIDATOR.py"
SCHEMA = WS33_ROOT / "abi" / "WS33_WITNESS_ABI_V2_1.schema.json"
MANIFEST = WS33_ROOT / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"
OVERLAY = WS33_ROOT / "WS33_RUNTIME_OVERLAY_MANIFEST.json"
STAGING_PROV = CPROM / "staging-inputs" / "WS33_C_WAVE_001_PROVENANCE.json"
PROPOSAL = CPROM / "proposals" / "WS33_C_WAVE_001.json"

TARGET = "forge-behavior-v2:634a4b2d09d12a138afd0544c87c7d2bdb57a05a"
SOURCE_HEAD = "c03b8c5d4c75a5589723b91794494c14dac22939"
SOURCE_TREE = "b3f85caf4cde9508404cb926e8ee4a71523dfb52"
C_CAMPAIGN_ROOT = Path("/home/moeen/code/mage-ws33/research/greenfield-qualification"
                       "/actual-card-behavior/ws33")
ARTIFACT_DIR = Path("/tmp/opencode/ws33c-batch5/unzipped/evidence")


def run_cmd(argv, **kwargs):
    return subprocess.run(argv, capture_output=True, text=True, **kwargs)


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canon(obj), encoding="utf-8")


def synthetic_world(tmp: Path, target_status_a="UNKNOWN", target_status_b="UNKNOWN"):
    """Minimal hermetic dual-book world reusing the real target's shapes."""
    manifest_full = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next(p for p in manifest_full["paths"] if p["v2_path_id"] == TARGET)
    other = next(p for p in manifest_full["paths"] if p["v2_path_id"] != TARGET)
    manifest = {
        "schema": manifest_full["schema"],
        "forge_pin": manifest_full["forge_pin"],
        "source_head": manifest_full["source_head"],
        "source_tree": manifest_full["source_tree"],
        "inherited_execution_sources": [],
        "paths": [entry, other],
    }
    write_json(tmp / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json", manifest)
    overlay = tmp / "WS33_RUNTIME_OVERLAY_MANIFEST.json"
    overlay.write_text("{}\n", encoding="utf-8")
    provenance = {
        "approved_qualification_sources": {
            f"{manifest_full['source_head']}:{manifest_full['source_tree']}": {
                "descends_from_model_base": True,
                "model_base_head": "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef",
                "model_base_tree": "837f445f78bb26462653c58baf1532e294151b10",
            }
        },
        "approved_execution_sources": [{"head": SOURCE_HEAD, "tree": SOURCE_TREE}],
        "effective_model_ref": "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json",
        "patched_forge_digests": {
            f"{manifest_full['source_head']}:{manifest_full['source_tree']}": "7b65af1d174c8acd75229cb0c6817b7801d02569131f9c73505ef84b38a1e8e9",
        },
        "ws26_manifest_sha256": "2585a0a001a63c11e4a50a63fc163eb1050b2e8fb79549bdd7be33031eea832d",
    }
    write_json(tmp / "provenance.json", provenance)
    cov = {"paths": [
        {"effective_v2_path_id": TARGET, "status": target_status_a,
         "evidence_classification": target_status_a, "owner_family": entry["owner_family"]},
        {"effective_v2_path_id": other["v2_path_id"], "status": "UNKNOWN",
         "evidence_classification": "UNKNOWN", "owner_family": other["owner_family"]},
    ], "status_counts": {}}
    write_json(tmp / "WS33_PATH_COVERAGE.json", cov)
    ledger = [
        {"effective_path_id": TARGET, "current_status": target_status_b,
         "evidence_classification": target_status_b, "owner_family": entry["owner_family"],
         "logical_bucket": "WS33C", "runtime_subsystem": entry["implementation_target"],
         "scenario_group_id": "ws33-g2-template-114", "evidence_profile": "STATE_ONLY",
         "blocker_classification": None, "campaign_id": None},
        {"effective_path_id": other["v2_path_id"], "current_status": "UNKNOWN",
         "evidence_classification": "UNKNOWN", "owner_family": other["owner_family"],
         "logical_bucket": "WS33D", "runtime_subsystem": "x",
         "scenario_group_id": "g", "evidence_profile": "STATE_ONLY",
         "blocker_classification": None, "campaign_id": None},
    ]
    (tmp / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl").write_text(
        "".join(canon(r) for r in ledger), encoding="utf-8")
    # Book-A derived companions expected by the promoter.
    (tmp / "WS33_CASE_LEDGER.jsonl").write_text("".join(
        canon({"effective_v2_path_id": r["effective_v2_path_id"],
               "scenario_status": "MISSING_SCENARIO_TEMPLATE"}) for r in cov["paths"]),
        encoding="utf-8")
    (tmp / "WS33_EXECUTION_LEDGER.jsonl").write_text("".join(
        canon({"effective_v2_path_id": r["effective_v2_path_id"], "status": "UNKNOWN",
               "execution_source": None, "trace_sha": None, "witness_hash": None,
               "blocker_class": None}) for r in cov["paths"]), encoding="utf-8")
    (tmp / "WS33_PER_IDENTITY.jsonl").write_text(
        canon({"effective_v2_path_ids": [TARGET], "pass_path_ids": [],
               "unresolved_path_ids": [TARGET], "status": "PARTIAL"}), encoding="utf-8")
    write_json(tmp / "WS33_SCENARIO_TEMPLATE_REGISTRY.json",
               {"templates": [{"template_id": "t", "path_ids": [TARGET],
                                "admitted_path_ids": [], "status": "MISSING_SCENARIO_TEMPLATE"}]})
    write_json(tmp / "WS33_IMPLEMENTATION_TARGET_REGISTRY.json",
               {"targets": [{"implementation_target": entry["implementation_target"],
                              "owner_family": entry["owner_family"], "path_ids": [TARGET],
                              "cross_family_dependency_fanout": 1, "unproved_path_count": 1,
                              "priority_score": 1}]})
    write_json(tmp / "WS33_Q6_CANDIDATE_GATE.json",
               {"path_status_counts": {}, "identity_counts": {}, "family_gates": {},
                "remaining_blockers": []})
    (tmp / "WS33_WITNESSES.jsonl").write_text("", encoding="utf-8")
    write_json(tmp / "WS33_INTEGRATED_WORK_QUEUE.json",
               {"items": [], "unresolved_path_count": 0, "work_item_count": 0})
    write_json(tmp / "WS33_INTEGRATED_FRONTIER_GATE.json",
               {"path_status_counts": {}, "unresolved_path_count": 0, "work_item_count": 0,
                "status": "PASS", "generation2_artifact_id": "9757382012"})
    return {"manifest": tmp / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json",
            "overlay": tmp / "WS33_RUNTIME_OVERLAY_MANIFEST.json",
            "provenance": tmp / "provenance.json"}


def real_evidence_inputs(tmp: Path):
    rec = tmp / "record.json"
    tr = tmp / "trace.json"
    gate = tmp / "gate.json"
    rec.write_bytes((ARTIFACT_DIR / "records" / "kappa-etb-other-place" / "record.json").read_bytes())
    tr.write_bytes((ARTIFACT_DIR / "records" / "kappa-etb-other-place" / "trace.json").read_bytes())
    gate.write_bytes((ARTIFACT_DIR / "WS33_C_BATCH_GATE.json").read_bytes())
    return rec, tr, gate


def adapter_argv(tmp: Path, rec: Path, tr: Path, gate: Path, world: dict,
                 out: Path, trace_ref: str, provenance: Path | None = None):
    return ["python3", str(ADAPTER), "--record", str(rec), "--trace", str(tr),
            "--gate", str(gate), "--manifest", str(world["manifest"]),
            "--provenance", str(provenance or world["provenance"]),
            "--overlay-manifest", str(world["overlay"]),
            "--overlay-manifest-rel", "WS33_RUNTIME_OVERLAY_MANIFEST.json",
            "--book-a-coverage", str(tmp / "WS33_PATH_COVERAGE.json"),
            "--book-b-ledger", str(tmp / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"),
            "--source-head", SOURCE_HEAD, "--source-tree", SOURCE_TREE,
            "--run-id", "34410975075", "--job-id", "102665052139",
            "--artifact-id", "10127286824",
            "--artifact-digest",
            "sha256:d44de127ef7c75a00d3c7bee580aa0d0eed700cac6a61c86e5d65432d0358e8d",
            "--batch-id", "WS33_C_BATCH_5", "--runner-os", "ubuntu-24.04",
            "--java-version", "21-temurin", "--workflow-source-head", SOURCE_HEAD,
            "--trace-ref", trace_ref, "--out-dir", str(out)]


class AdapterTests(unittest.TestCase):
    def test_pass_real_evidence_and_validator_accepts(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            rec, tr, gate = real_evidence_inputs(tmp)
            out = tmp / "adapted"
            proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, out, "trace.json"))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("WS33_C_ADAPTER=PASS", proc.stdout)
            witness = json.loads((out / "witness.json").read_text(encoding="utf-8"))
            # Preservation contract.
            self.assertEqual(witness["evidence_class"], "TECHNICALLY_CONFORMANT")
            self.assertEqual(witness["status"], "PASS")
            self.assertEqual(witness["source_head"], SOURCE_HEAD)
            self.assertEqual(witness["source_tree"], SOURCE_TREE)
            retained = json.loads(rec.read_text(encoding="utf-8"))
            self.assertEqual(witness["rules_authority_refs"],
                             retained["rules_authority_refs"])
            self.assertEqual(witness["state_assertions"], retained["state_assertions"])
            self.assertEqual((out / "trace.json").read_bytes(), tr.read_bytes())
            # Canonical validator is the sole semantic arbiter.
            v = run_cmd(["python3", str(VALIDATOR), str(out / "witness.json"),
                         "--manifest", str(world["manifest"]), "--schema", str(SCHEMA),
                         "--provenance", str(world["provenance"]), "--base", str(tmp)])
            self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
            self.assertIn("WS33_WITNESS_VALIDATION=PASS", v.stdout)

    def mutate_record(self, tmp: Path, fn):
        rec, tr, gate = real_evidence_inputs(tmp)
        doc = json.loads(rec.read_text(encoding="utf-8"))
        fn(doc)
        rec.write_text(json.dumps(doc), encoding="utf-8")
        return rec, tr, gate

    def test_rejects_tampered_gate(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            rec, tr, gate = real_evidence_inputs(tmp)
            g = json.loads(gate.read_text(encoding="utf-8"))
            g["status"] = "PARTIAL"
            gate.write_text(json.dumps(g), encoding="utf-8")
            proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, tmp / "o", "trace.json"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("C_GATE_NOT_PASS", proc.stdout)

    def test_rejects_wrong_source(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            rec, tr, gate = real_evidence_inputs(tmp)
            argv = adapter_argv(tmp, rec, tr, gate, world, tmp / "o", "trace.json")
            argv[argv.index("--source-head") + 1] = "0" * 40
            proc = run_cmd(argv)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("C_SOURCE_SEAL_MISMATCH", proc.stdout)

    def test_rejects_empty_rules_refs_without_fabrication(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            rec, tr, gate = self.mutate_record(
                tmp, lambda d: d.update({"rules_authority_refs": []}))
            proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, tmp / "o", "trace.json"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("C_RULES_AUTHORITY_MISSING", proc.stdout)

    def test_rejects_non_tc_class(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            rec, tr, gate = real_evidence_inputs(tmp)
            g = json.loads(gate.read_text(encoding="utf-8"))
            g["executions"][0]["evidence_class"] = "EXTERNALLY_RULE_VALIDATED"
            gate.write_text(json.dumps(g), encoding="utf-8")
            proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, tmp / "o", "trace.json"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("C_EVIDENCE_CLASS_NOT_TC", proc.stdout)

    def test_rejects_unapproved_execution_source(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            prov = json.loads(world["provenance"].read_text(encoding="utf-8"))
            prov["approved_execution_sources"] = []
            stripped = tmp / "prov-stripped.json"
            write_json(stripped, prov)
            rec, tr, gate = real_evidence_inputs(tmp)
            proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, tmp / "o", "trace.json",
                                        provenance=stripped))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("EXECUTION_SOURCE_NOT_APPROVED", proc.stdout)

    def test_rejects_prestate_pass(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp, target_status_a="PASS")
            rec, tr, gate = real_evidence_inputs(tmp)
            proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, tmp / "o", "trace.json"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("PRESTATE_NOT_UNKNOWN", proc.stdout)


def promoter_argv(base: Path, staging: Path, adapted: Path, proposal: Path,
                  provenance: Path, receipt: str, extra=()):
    return ["python3", str(PROMOTER), "--base-root", str(base),
            "--proposal", str(proposal), "--adapted-dir", str(adapted),
            "--provenance", str(provenance), "--schema", str(SCHEMA),
            "--validator", str(VALIDATOR), "--staging-root", str(staging),
            "--expect-book-a", "PASS=0,UNKNOWN=2", "--expect-book-b", "PASS=0,UNKNOWN=2",
            "--campaign-id", "WS33_C_BATCH_5_CERTIFIED_ARTIFACT",
            "--receipt-id", receipt, "--c-campaign-root", str(C_CAMPAIGN_ROOT),
            *extra]


class PromoterTests(unittest.TestCase):
    def stage_once(self, tmp: Path, world: dict, receipt="R1"):
        rec, tr, gate = real_evidence_inputs(tmp)
        out = tmp / "adapted" / "w1"
        proc = run_cmd(adapter_argv(tmp, rec, tr, gate, world, out, "adapted/w1/trace.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        proposal = {"proposal_index": "T", "path_ids": [TARGET],
                    "proposal_digest": hashlib.sha256(
                        canon({"proposal_index": "T",
                               "path_ids": [TARGET]}).encode()).hexdigest(),
                    "c_evidence": {"batch_id": "WS33_C_BATCH_5"}}
        write_json(tmp / "proposal.json", proposal)
        staging = tmp / "staging"
        proc = run_cmd(promoter_argv(tmp, staging, tmp / "adapted", tmp / "proposal.json",
                                     world["provenance"], receipt))
        return proc, staging

    def test_stage_success_single_transition_each_book(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, staging = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((staging / "receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["transitions"]["book_a"], {TARGET: ["UNKNOWN", "PASS"]})
            self.assertEqual(receipt["transitions"]["book_b"], {TARGET: ["UNKNOWN", "PASS"]})
            self.assertEqual(receipt["unrelated_path_changes"], 0)
            self.assertFalse(receipt["coverage_promotion_installed"])
            cov = json.loads((staging / "books" / "WS33_PATH_COVERAGE.json").read_text())
            self.assertEqual(cov["status_counts"], {"UNKNOWN": 1, "PASS": 1})

    def test_rerun_same_proposal_fails_closed_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, staging = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            # rerun against the staged (already-promoted) books: argparse takes
            # the last occurrence, so extra overrides the default expectations.
            proc2 = run_cmd(promoter_argv(
                staging / "books", tmp / "staging2", tmp / "adapted",
                tmp / "proposal.json", world["provenance"], "R2",
                extra=("--expect-book-a", "PASS=1,UNKNOWN=1",
                       "--expect-book-b", "PASS=1,UNKNOWN=1")))
            self.assertEqual(proc2.returncode, 2)
            self.assertIn("DUPLICATE_ALREADY_PROMOTED", proc2.stdout)

    def test_identity_reconciliation_required(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, _ = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            bad = {"proposal_index": "T", "path_ids": ["forge-behavior-v2:deadbeef"],
                   "proposal_digest": hashlib.sha256(
                       canon({"proposal_index": "T",
                              "path_ids": ["forge-behavior-v2:deadbeef"]}).encode()).hexdigest()}
            write_json(tmp / "bad.json", bad)
            proc2 = run_cmd(promoter_argv(tmp, tmp / "s2", tmp / "adapted", tmp / "bad.json",
                                          world["provenance"], "R3"))
            self.assertEqual(proc2.returncode, 2)
            self.assertIn("IDENTITY_RECONCILIATION_REQUIRED", proc2.stdout)

    def test_proposal_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, _ = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            bad = json.loads((tmp / "proposal.json").read_text(encoding="utf-8"))
            bad["proposal_digest"] = "0" * 64
            write_json(tmp / "bad2.json", bad)
            proc2 = run_cmd(promoter_argv(tmp, tmp / "s3", tmp / "adapted", tmp / "bad2.json",
                                          world["provenance"], "R4"))
            self.assertEqual(proc2.returncode, 2)
            self.assertIn("PROPOSAL_DIGEST_MISMATCH", proc2.stdout)

    def test_stage_is_byte_identical_across_runs(self):
        # Normal staging (no --install) is fully deterministic: two runs over
        # identical inputs produce byte-identical books and receipt bytes.
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, staging = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            staging2 = tmp / "staging-bis"
            proc2 = run_cmd(promoter_argv(tmp, staging2, tmp / "adapted",
                                          tmp / "proposal.json",
                                          world["provenance"], "R1"))
            self.assertEqual(proc2.returncode, 0, proc2.stdout + proc2.stderr)
            files1 = sorted(str(p.relative_to(staging)) for p in staging.rglob("*")
                            if p.is_file())
            files2 = sorted(str(p.relative_to(staging2)) for p in staging2.rglob("*")
                            if p.is_file())
            self.assertEqual(files1, files2)
            for rel in files1:
                self.assertEqual((staging / rel).read_bytes(),
                                 (staging2 / rel).read_bytes(), rel)

    def test_legacy_install_to_scratch_fails_closed_zero_writes(self):
        # The retired promoter --install path fails closed immediately and
        # performs zero target writes.
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, staging = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            target = tmp / "install-target"
            target.mkdir()
            sentinel = target / "sentinel.txt"
            sentinel.write_text("untouched\n", encoding="utf-8")
            proc2 = run_cmd(promoter_argv(
                tmp, tmp / "s4", tmp / "adapted", tmp / "proposal.json",
                world["provenance"], "R5",
                extra=("--install", "--install-root", str(target))))
            self.assertEqual(proc2.returncode, 2, proc2.stdout + proc2.stderr)
            self.assertIn("LEGACY_INSTALL_DISABLED_USE_TRANSACTION_INSTALLER",
                          proc2.stdout)
            self.assertEqual(sorted(p.name for p in target.iterdir()),
                             ["sentinel.txt"])
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "untouched\n")

    def test_legacy_install_canonical_shaped_fails_closed_zero_writes(self):
        # Even with WS33_C_ALLOW_CANONICAL_INSTALL=1 the retired promoter
        # path must refuse (the env gate is not honored here) and write
        # nothing anywhere under the base tree.
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            world = synthetic_world(tmp)
            proc, staging = self.stage_once(tmp, world)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            before = {str(p.relative_to(tmp)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(tmp.rglob("*")) if p.is_file()}
            env = dict(os.environ)
            env["WS33_C_ALLOW_CANONICAL_INSTALL"] = "1"
            proc2 = run_cmd(promoter_argv(
                tmp, tmp / "s5", tmp / "adapted", tmp / "proposal.json",
                world["provenance"], "R6",
                extra=("--install", "--install-root", str(tmp))), env=env)
            self.assertEqual(proc2.returncode, 2, proc2.stdout + proc2.stderr)
            self.assertIn("LEGACY_INSTALL_DISABLED_USE_TRANSACTION_INSTALLER",
                          proc2.stdout)
            after = {str(p.relative_to(tmp)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(tmp.rglob("*")) if p.is_file()}
            self.assertEqual(before, after)


class RealStagingAuditTests(unittest.TestCase):
    STAGING = CPROM / "staging" / "WS33_C_WAVE_001"

    def test_expected_counts_and_single_transitions(self):
        receipt = json.loads((self.STAGING / "receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["book_a"]["prestate_counts"],
                         {"PASS": 2, "FAIL": 0, "UNSUPPORTED": 0, "UNKNOWN": 4274})
        self.assertEqual(receipt["book_a"]["poststate_counts"]["PASS"], 3)
        self.assertEqual(receipt["book_a"]["poststate_counts"]["UNKNOWN"], 4273)
        self.assertEqual(receipt["book_b"]["prestate_counts"]["PASS"], 1152)
        self.assertEqual(receipt["book_b"]["poststate_counts"]["PASS"], 1153)
        self.assertEqual(receipt["book_b"]["poststate_counts"]["UNKNOWN"], 3035)
        self.assertEqual(set(receipt["transitions"]["book_a"]), {TARGET})
        self.assertEqual(set(receipt["transitions"]["book_b"]), {TARGET})
        self.assertEqual(receipt["validation"][0]["WS33_WITNESS_VALIDATION"], "PASS")
        self.assertFalse(receipt["coverage_promotion_installed"])

    def test_previous_pass_sets_preserved(self):
        cov_base = json.loads((WS33_ROOT / "WS33_PATH_COVERAGE.json").read_text(encoding="utf-8"))
        cov_staged = json.loads(
            (self.STAGING / "books" / "WS33_PATH_COVERAGE.json").read_text(encoding="utf-8"))
        base_pass = {p["effective_v2_path_id"] for p in cov_base["paths"]
                     if p["status"] == "PASS"}
        staged_pass = {p["effective_v2_path_id"] for p in cov_staged["paths"]
                       if p["status"] == "PASS"}
        self.assertEqual(staged_pass - base_pass, {TARGET})
        staged_rows = [json.loads(x) for x in
                       (self.STAGING / "books" / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl")
                       .read_text(encoding="utf-8").splitlines() if x.strip()]
        base_rows = [json.loads(x) for x in
                     (WS33_ROOT / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl")
                     .read_text(encoding="utf-8").splitlines() if x.strip()]
        base_b_pass = {r["effective_path_id"] for r in base_rows
                       if r["current_status"] == "PASS"}
        staged_b_pass = {r["effective_path_id"] for r in staged_rows
                         if r["current_status"] == "PASS"}
        self.assertEqual(staged_b_pass - base_b_pass, {TARGET})
        for r in staged_rows:
            if r["effective_path_id"] == TARGET:
                self.assertEqual(r["evidence_classification"], "TECHNICALLY_CONFORMANT")

    def test_canonical_books_untouched(self):
        proc = run_cmd(["git", "status", "--porcelain=v1", "--",
                        "WS33_PATH_COVERAGE.json", "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl",
                        "WS33_CASE_LEDGER.jsonl", "WS33_EXECUTION_LEDGER.jsonl",
                        "WS33_WITNESSES.jsonl", "WS33_Q6_CANDIDATE_GATE.json",
                        "WS33_INTEGRATED_WORK_QUEUE.json", "WS33_INTEGRATED_FRONTIER_GATE.json"],
                       cwd=WS33_ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_real_rerun_fails_closed_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            proc = run_cmd(
                ["python3", str(PROMOTER), "--base-root",
                 str(self.STAGING / "books"), "--proposal", str(PROPOSAL),
                 "--adapted-dir", str(CPROM / "adapted"), "--provenance", str(STAGING_PROV),
                 "--schema", str(SCHEMA), "--validator", str(VALIDATOR),
                 "--staging-root", str(Path(td) / "must-fail"),
                 "--expect-book-a", "PASS=3,UNKNOWN=4273",
                 "--expect-book-b", "PASS=1153,UNKNOWN=3035",
                 "--campaign-id", "WS33_C_BATCH_5_CERTIFIED_ARTIFACT",
                 "--receipt-id", "RERUN", "--c-campaign-root", str(C_CAMPAIGN_ROOT)])
            self.assertEqual(proc.returncode, 2)
            self.assertIn("DUPLICATE_ALREADY_PROMOTED", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
