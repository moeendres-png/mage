#!/usr/bin/env python3
"""Deterministic tests for the WS33-C install transaction.

All installs target synthetic scratch directories. The real canonical books
are never touched (a dedicated test asserts they stay byte-identical).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

WS33_ROOT = Path(__file__).resolve().parent.parent
CPROM = WS33_ROOT / "c-promotion"
INSTALLER = CPROM / "ws33_c_install_transaction.py"
SCHEMA = WS33_ROOT / "abi" / "WS33_WITNESS_ABI_V2_1.schema.json"
VALIDATOR = WS33_ROOT / "abi" / "WS33_WITNESS_SEMANTIC_VALIDATOR.py"


def load_helpers():
    spec = importlib.util.spec_from_file_location(
        "ws33_c_dualbook_promotion_tests",
        CPROM / "test_ws33_c_dualbook_promotion.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load_helpers()
BOOK_FILES = ("WS33_PATH_COVERAGE.json", "WS33_CASE_LEDGER.jsonl",
              "WS33_EXECUTION_LEDGER.jsonl", "WS33_PER_IDENTITY.jsonl",
              "WS33_SCENARIO_TEMPLATE_REGISTRY.json",
              "WS33_IMPLEMENTATION_TARGET_REGISTRY.json", "WS33_Q6_CANDIDATE_GATE.json",
              "WS33_WITNESSES.jsonl", "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl",
              "WS33_INTEGRATED_WORK_QUEUE.json", "WS33_INTEGRATED_FRONTIER_GATE.json")


def run_cmd(argv, env_extra=None, **kwargs):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(argv, capture_output=True, text=True, env=env, **kwargs)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InstallFixture:
    """Synthetic world + staged promotion + scratch install target."""

    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.world = H.synthetic_world(tmp)
        rec, tr, gate = H.real_evidence_inputs(tmp)
        out = tmp / "adapted" / "w1"
        proc = run_cmd(H.adapter_argv(tmp, rec, tr, gate, self.world, out,
                                      "adapted/w1/trace.json"))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        proposal = {"proposal_index": "T", "path_ids": [H.TARGET],
                    "proposal_digest": hashlib.sha256(
                        H.canon({"proposal_index": "T",
                                 "path_ids": [H.TARGET]}).encode()).hexdigest(),
                    "c_evidence": {"batch_id": "WS33_C_BATCH_5"}}
        H.write_json(tmp / "proposal.json", proposal)
        self.staging = tmp / "staging"
        proc = run_cmd(H.promoter_argv(tmp, self.staging, tmp / "adapted",
                                       tmp / "proposal.json", self.world["provenance"], "R1"))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        self.receipt = self.staging / "receipt.json"
        self.authorization = sha(self.receipt)
        self.target = tmp / "target"
        self.target.mkdir()
        for name in BOOK_FILES:
            shutil.copy2(tmp / name, self.target / name)
        self.prestate = {name: sha(self.target / name) for name in BOOK_FILES}

    def installer_argv(self, receipt_id="T-INSTALL-001", authorization=None,
                       install_root=None, extra=()):
        return ["python3", str(INSTALLER), "--staging-root", str(self.staging),
                "--base-root", str(self.tmp), "--proposal", str(self.tmp / "proposal.json"),
                "--adapted-dir", str(self.tmp / "adapted"),
                "--provenance", str(self.world["provenance"]),
                "--schema", str(SCHEMA), "--validator", str(VALIDATOR),
                "--manifest", str(self.world["manifest"]),
                "--overlay-manifest", str(self.world["overlay"]),
                "--c-campaign-root", str(H.C_CAMPAIGN_ROOT),
                "--install-root", str(install_root or self.target),
                "--install-receipt-id", receipt_id,
                "--authorization", authorization or self.authorization,
                "--work-dir", str(self.tmp / f"work-{receipt_id}"), *extra]

    def assert_target_untouched(self):
        for name in BOOK_FILES:
            self.assertEqual(sha(self.target / name), self.prestate[name], name)

    def assertEqual(self, a, b, msg=""):
        unittest.TestCase().assertEqual(a, b, msg)


class InstallTransactionTests(unittest.TestCase):
    def test_success_and_contract(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv())
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("WS33_C_INSTALL=COMMITTED", proc.stdout)
            rel = "c-promotion/receipts/T-INSTALL-001.json"
            r1 = json.loads((fx.target / rel).read_text(encoding="utf-8"))
            # Post-install receipt contract.
            self.assertTrue(r1["coverage_promotion_installed"])
            self.assertEqual(r1["supersedes_dryrun_receipt"], "R1")
            self.assertEqual(r1["promoted_path_ids"], [H.TARGET])
            self.assertEqual(r1["proposal_digest"],
                             json.loads((fx.tmp / "proposal.json").read_text())["proposal_digest"])
            self.assertEqual(r1["post_install_invariant"]["result"], "PASS")
            self.assertTrue(r1["post_install_invariant"]["tc_preserved"])
            self.assertEqual(r1["validation"][0]["WS33_WITNESS_VALIDATION"], "PASS")
            for name in BOOK_FILES:
                self.assertEqual(r1["installed_hashes"][name], sha(fx.target / name), name)
            # Every promotion_evidence ref resolves to the installed receipt.
            cov = json.loads((fx.target / "WS33_PATH_COVERAGE.json").read_text())
            rows = [json.loads(x) for x in
                    (fx.target / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl")
                    .read_text().splitlines() if x.strip()]
            gate = json.loads((fx.target / "WS33_INTEGRATED_FRONTIER_GATE.json").read_text())
            self.assertEqual(gate["promotion_evidence"], rel)
            hit = [p for p in cov["paths"] if p["effective_v2_path_id"] == H.TARGET]
            self.assertEqual(len(hit), 1)
            self.assertEqual(hit[0]["promotion_evidence"], rel)
            self.assertEqual(hit[0]["status"], "PASS")
            self.assertEqual(hit[0]["evidence_classification"], "TECHNICALLY_CONFORMANT")
            # Exactly one authorized UNKNOWN->PASS transition in each book.
            promoted_a = [p for p in cov["paths"] if p.get("promotion_evidence") == rel]
            self.assertEqual(len(promoted_a), 1)
            self.assertEqual(promoted_a[0]["effective_v2_path_id"], H.TARGET)
            promoted_b = [r for r in rows if r.get("promotion_evidence") == rel]
            self.assertEqual(len(promoted_b), 1)
            self.assertEqual(promoted_b[0]["effective_path_id"], H.TARGET)
            self.assertEqual(promoted_b[0]["current_status"], "PASS")
            self.assertEqual(promoted_b[0]["evidence_classification"],
                             "TECHNICALLY_CONFORMANT")
            # Second installation attempt fails closed as duplicate.
            proc2 = run_cmd(fx.installer_argv(receipt_id="T-INSTALL-002"))
            self.assertEqual(proc2.returncode, 2)
            self.assertIn("DUPLICATE_ALREADY_PROMOTED", proc2.stdout)

    def test_no_authorization_refused_and_target_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            for bad_auth in ("", "0" * 64):
                argv = fx.installer_argv(receipt_id=f"NOAUTH-{bad_auth[:4]}",
                                         authorization=bad_auth or "missing")
                proc = run_cmd(argv)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("INSTALL_REFUSED", proc.stdout)
            fx.assert_target_untouched()
            self.assertFalse((fx.target / "c-promotion").exists())

    def test_canonical_target_requires_env(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv(receipt_id="CANON",
                                             install_root=fx.tmp))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("INSTALL_REFUSED_CANONICAL", proc.stdout)

    def test_stale_prestate_refused_before_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            # mutate an unrelated target row -> counts/hash drift
            led = fx.target / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"
            lines = led.read_text(encoding="utf-8").splitlines()
            row = json.loads(lines[1])
            row["current_status"] = "PASS"
            lines[1] = json.dumps(row, sort_keys=True)
            led.write_text("\n".join(lines) + "\n", encoding="utf-8")
            proc = run_cmd(fx.installer_argv(receipt_id="STALE"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("INSTALL_REFUSED_PRESTATE", proc.stdout)
            # the stale mutation itself is present (it was our setup), but the
            # installer wrote nothing else: coverage untouched, no receipt.
            self.assertEqual(sha(fx.target / "WS33_PATH_COVERAGE.json"),
                             fx.prestate["WS33_PATH_COVERAGE.json"])
            self.assertFalse((fx.target / "c-promotion").exists())

    def test_staged_tamper_refused(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            staged_cov = fx.staging / "books" / "WS33_PATH_COVERAGE.json"
            data = staged_cov.read_bytes()
            staged_cov.write_bytes(data[:100] + b"X" + data[101:])
            proc = run_cmd(fx.installer_argv(receipt_id="TAMPER"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("STAGED_TAMPERED", proc.stdout)
            fx.assert_target_untouched()

    def test_real_oserror_mid_copy_rolls_back(self):
        # Genuine OSError (not InstallError) after 2 successful target writes:
        # installer fails, rolls back, all 11 target hashes equal prestate,
        # no installed receipt survives, original cause stays identifiable.
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv(receipt_id="OSERROR"),
                           env_extra={"WS33_C_INSTALL_FAULT": "oserror-mid-copy-2"})
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("INSTALL_ROLLED_BACK", proc.stdout)
            self.assertIn("UNEXPECTED_OSERROR", proc.stdout)
            self.assertIn("OSError", proc.stdout)
            self.assertIn("injected real copy failure", proc.stdout)
            fx.assert_target_untouched()
            self.assertFalse((fx.target / "c-promotion").exists())

    def test_unexpected_audit_failure_rolls_back(self):
        # Non-InstallError during post-install audit after copying: rollback
        # occurs and the original cause remains identifiable.
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv(receipt_id="UNEXPAUDIT"),
                           env_extra={"WS33_C_INSTALL_FAULT": "unexpected-audit"})
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("INSTALL_ROLLED_BACK", proc.stdout)
            self.assertIn("UNEXPECTED_RUNTIMEERROR", proc.stdout)
            self.assertIn("injected unexpected audit failure", proc.stdout)
            fx.assert_target_untouched()
            self.assertFalse((fx.target / "c-promotion").exists())

    def test_unexpected_failure_after_receipt_rolls_back(self):
        # Non-InstallError after receipt creation but before final success:
        # books restored and the installed receipt removed.
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv(receipt_id="AFTERRECEIPT"),
                           env_extra={"WS33_C_INSTALL_FAULT": "unexpected-after-receipt"})
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("INSTALL_ROLLED_BACK", proc.stdout)
            self.assertIn("UNEXPECTED_RUNTIMEERROR", proc.stdout)
            self.assertIn("injected unexpected failure after receipt creation",
                          proc.stdout)
            fx.assert_target_untouched()
            self.assertFalse((fx.target / "c-promotion" / "receipts"
                              / "AFTERRECEIPT.json").exists())

    def test_companion_stale_prestate_refused_before_mutation(self):
        # Mutate ONLY a companion file (case ledger) while coverage and the
        # integrated ledger stay untouched: full prestate binding must refuse
        # before the first target write.
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            case = fx.target / "WS33_CASE_LEDGER.jsonl"
            lines = case.read_text(encoding="utf-8").splitlines()
            row = json.loads(lines[0])
            row["scenario_status"] = "STALE-COMPANION-DRIFT"
            lines[0] = json.dumps(row, sort_keys=True)
            case.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertNotEqual(sha(case), fx.prestate["WS33_CASE_LEDGER.jsonl"])
            self.assertEqual(sha(fx.target / "WS33_PATH_COVERAGE.json"),
                             fx.prestate["WS33_PATH_COVERAGE.json"])
            self.assertEqual(sha(fx.target / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"),
                             fx.prestate["WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"])
            proc = run_cmd(fx.installer_argv(receipt_id="COMPANION"))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("INSTALL_REFUSED_PRESTATE", proc.stdout)
            self.assertIn("WS33_CASE_LEDGER.jsonl", proc.stdout)
            # Installer wrote nothing: the 2 watched files are untouched, no
            # receipt exists, and the other 10 files still match prestate
            # except for our own setup mutation.
            self.assertEqual(sha(fx.target / "WS33_PATH_COVERAGE.json"),
                             fx.prestate["WS33_PATH_COVERAGE.json"])
            self.assertEqual(sha(fx.target / "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"),
                             fx.prestate["WS33_INTEGRATED_CLOSURE_LEDGER.jsonl"])
            for name in BOOK_FILES:
                if name == "WS33_CASE_LEDGER.jsonl":
                    continue
                self.assertEqual(sha(fx.target / name), fx.prestate[name], name)
            self.assertFalse((fx.target / "c-promotion").exists())

    def test_mid_copy_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv(receipt_id="MIDFAIL"),
                           env_extra={"WS33_C_INSTALL_FAULT": "fail-mid-copy-3"})
            self.assertEqual(proc.returncode, 2)
            self.assertIn("INSTALL_ROLLED_BACK", proc.stdout)
            fx.assert_target_untouched()
            self.assertFalse((fx.target / "c-promotion").exists())

    def test_corrupt_after_copy_rolls_back(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            proc = run_cmd(fx.installer_argv(receipt_id="CORRUPT"),
                           env_extra={"WS33_C_INSTALL_FAULT": "corrupt-after-copy"})
            self.assertEqual(proc.returncode, 2)
            self.assertIn("INSTALL_ROLLED_BACK", proc.stdout)
            self.assertIn("POST_COPY_HASH_MISMATCH", proc.stdout)
            fx.assert_target_untouched()

    def test_receipt_write_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as td:
            fx = InstallFixture(Path(td))
            # block receipt installation: a directory at the receipt path
            blocked = fx.target / "c-promotion" / "receipts" / "BLOCKED.json"
            blocked.parent.mkdir(parents=True)
            blocked.mkdir()
            proc = run_cmd(fx.installer_argv(receipt_id="BLOCKED"))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("INSTALL_ROLLED_BACK", proc.stdout)
            self.assertIn("RECEIPT_WRITE_FAILED", proc.stdout)
            for name in BOOK_FILES:
                self.assertEqual(sha(fx.target / name), fx.prestate[name], name)

    def test_real_canonical_books_untouched(self):
        proc = run_cmd(["git", "status", "--porcelain=v1", "--",
                        "WS33_PATH_COVERAGE.json", "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl",
                        "WS33_CASE_LEDGER.jsonl", "WS33_EXECUTION_LEDGER.jsonl",
                        "WS33_WITNESSES.jsonl", "WS33_Q6_CANDIDATE_GATE.json",
                        "WS33_INTEGRATED_WORK_QUEUE.json", "WS33_INTEGRATED_FRONTIER_GATE.json"],
                       cwd=WS33_ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
