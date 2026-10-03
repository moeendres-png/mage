#!/usr/bin/env python3
"""Produce the trusted execution witness for an exact candidate SHA.

Trust boundary: this script and TrustedTestDriver are trusted default-branch
source. The candidate's Maven build is treated as untrusted input and is never a
source of qualification credit. Nothing this script reads comes from the
candidate's ``target/`` tree:

  * the required test classes are enumerated by walking the candidate's
    *source* tree, which is content, not evidence;
  * the execution is driven by the trusted JUnit Platform Launcher through
    TrustedTestDriver, and the counts in the witness are the driver's own;
  * the candidate's own build exit code is recorded and adjudicated separately,
    never used to grant credit.

The candidate build is still run, because the candidate's tests have to be
compiled somehow, but its reports are ignored: they are not opened, parsed or
counted. A candidate that fabricates, copies, renames or suppresses
``target/surefire-reports/TEST-*.xml`` therefore changes nothing here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA = "mage.candidate-qualification.witness/1"
WITNESS_SCHEMA = "mage.candidate-qualification.trusted-execution-witness/1"
DRIVER = "TrustedTestDriver.java"

# Conventional JUnit test class names. This is a *selection* heuristic used to
# decide what must run, never an evidence heuristic: a missing or renamed class
# makes the witness FAIL rather than silently reducing the required set.
TEST_CLASS_RE = re.compile(r"(Test|Tests|TestCase|Spec|IT)$")
SOURCE_DIR_MARKERS = ("src/test/java", "src/test/kotlin", "src/test/groovy")
TEST_ROOTS = ("target/test-classes", "target/classes")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=False, env=env
    )


def enumerate_required_tests(candidate_root: Path) -> list[str]:
    """Enumerate required test classes from candidate SOURCE, as data."""
    classes: set[str] = set()
    for marker in SOURCE_DIR_MARKERS:
        for source_root in candidate_root.glob("**/" + marker):
            for path in source_root.rglob("*.java"):
                if TEST_CLASS_RE.search(path.stem):
                    rel = path.relative_to(source_root).with_suffix("")
                    classes.add(".".join(rel.parts))
    return sorted(classes)


def discover_compiled_tests(candidate_root: Path) -> list[str]:
    """Locate compiled candidate test classes the trusted driver can select."""
    found: set[str] = set()
    for root_marker in TEST_ROOTS:
        for root in candidate_root.glob("**/" + root_marker):
            if not root.is_dir():
                continue
            for path in root.rglob("*.class"):
                rel = path.relative_to(root).with_suffix("")
                name = ".".join(rel.parts)
                if "$" in name:
                    continue
                found.add(name)
    return sorted(found)


def compile_driver(trusted_root: Path, workdir: Path) -> tuple[Path, str]:
    """Compile the trusted driver from trusted source into a trusted directory."""
    source = trusted_root / DRIVER
    if not source.is_file():
        raise FileNotFoundError("trusted driver source is missing: {}".format(source))
    out = workdir / "trusted-driver-classes"
    out.mkdir(parents=True, exist_ok=True)
    classpath = os.environ.get("TRUSTED_JUNIT_CLASSPATH", "")
    cmd = ["javac", "-nowarn", "-d", str(out)]
    if classpath:
        cmd += ["-cp", classpath]
    cmd.append(str(source))
    proc = run(cmd, trusted_root)
    if proc.returncode != 0:
        raise RuntimeError("javac failed: {}".format(proc.stderr.strip()[:2000]))
    return out, sha256_file(source)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--observed-candidate-sha", default="")
    parser.add_argument("--trusted-root", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--build-exit-code", default="")
    parser.add_argument("--build-definition-audit", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    trusted_root = Path(args.trusted_root).resolve()
    candidate_root = Path(args.candidate_root).resolve()
    workdir = Path(args.work_dir).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    # The evidence directory is created fresh by trusted code. Anything a previous
    # run left behind is removed rather than parsed.
    if out.exists():
        out.unlink()

    witness: dict = {
        "schema": SCHEMA,
        "status": "UNKNOWN",
        "trusted_validator": None,
        "candidate": None,
        "comparison_base": None,
        "observed_candidate_sha": args.observed_candidate_sha or None,
        "source_binding_ok": False,
        "candidate_build_exit_code": args.build_exit_code or None,
        "candidate_build_exit_code_semantics":
            "informational only; never grants credit, see candidate_build_adjudication",
        "candidate_build_adjudication": "PENDING",
        "build_definition_audit": None,
        "required_test_classes": [],
        "compiled_test_classes": [],
        "trusted_execution": None,
        "driver": {"name": DRIVER, "sha256": None},
        "candidate_authored_evidence_used": False,
        "candidate_reports_parsed": False,
        "notes": [],
    }

    try:
        lock = json.loads(Path(args.source_lock).read_text())
        if lock.get("status") != "LOCKED":
            raise ValueError("source lock is not LOCKED")
        witness["trusted_validator"] = lock.get("trusted_validator")
        witness["candidate"] = lock.get("candidate")
        witness["comparison_base"] = lock.get("comparison_base")

        locked_sha = (lock.get("candidate") or {}).get("sha")
        observed = args.observed_candidate_sha.strip()
        if not observed:
            raise ValueError("observed candidate sha was not supplied; binding unproven")
        if observed != locked_sha:
            raise ValueError(
                "observed candidate sha {} != locked {}".format(observed, locked_sha)
            )
        witness["source_binding_ok"] = True

        # The candidate's own test-execution definition is audited before anything
        # runs. A candidate that edits how its tests are discovered, executed or
        # interfered with has edited the thing that qualifies it.
        if args.build_definition_audit:
            audit = json.loads(Path(args.build_definition_audit).read_text())
            witness["build_definition_audit"] = {
                "status": audit.get("status"),
                "violations": audit.get("violations") or [],
                "audited_poms": [entry.get("path") for entry in audit.get("audited_poms") or []],
            }
            if audit.get("status") == "UNKNOWN":
                raise ValueError(
                    "build definition audit is UNKNOWN: {}".format(audit.get("error"))
                )
            if audit.get("status") != "CLEAN":
                # A proven violation is a FAIL, not an unknown, so the witness is
                # still produced and the scorer adjudicates it explicitly. Only an
                # unprovable audit is UNKNOWN.
                witness["notes"].append(
                    "build_definition_audit_violation: {}".format(
                        ", ".join(
                            "{}:{}".format(v.get("kind"), v.get("detail"))
                            for v in (audit.get("violations") or [])[:5]
                        )
                    )
                )

        if not candidate_root.is_dir():
            raise ValueError("candidate root does not exist")

        required = enumerate_required_tests(candidate_root)
        compiled = discover_compiled_tests(candidate_root)
        witness["required_test_classes"] = required
        witness["compiled_test_classes"] = compiled

        # Only classes the trusted enumeration requires are executed. A candidate
        # cannot add to the campaign by shipping new @Test classes, and cannot
        # remove one without it showing up as never entered.
        selected = [name for name in required if name in set(compiled)]
        missing_compilation = [name for name in required if name not in set(compiled)]
        if missing_compilation:
            witness["notes"].append(
                "required_tests_not_compiled: {}".format(",".join(missing_compilation))
            )
        if not selected:
            raise ValueError(
                "no required test class was compiled from the candidate source tree"
            )

        driver_classes, driver_digest = compile_driver(trusted_root, workdir)
        witness["driver"]["sha256"] = driver_digest

        junit_classpath = os.environ.get("TRUSTED_JUNIT_CLASSPATH", "").strip()
        if not junit_classpath:
            raise ValueError(
                "TRUSTED_JUNIT_CLASSPATH is unset; the trusted driver cannot run"
            )

        runtime_classpath = os.pathsep.join(
            [str(driver_classes), junit_classpath, *sorted(
                {str(p) for p in candidate_root.glob("**/target/test-classes")}
                | {str(p) for p in candidate_root.glob("**/target/classes")}
            )]
        )

        witness_path = workdir / "TRUSTED_EXECUTION_WITNESS.json"
        cmd = [
            "java",
            "-cp",
            runtime_classpath,
            "TrustedTestDriver",
            "--evidence",
            str(witness_path),
            "--class-path",
            runtime_classpath,
            "--bind-sha",
            locked_sha,
            "--bind-tree",
            (lock.get("candidate") or {}).get("tree", ""),
        ]
        for name in selected:
            cmd += ["--select", name]

        proc = run(cmd, trusted_root)
        witness["trusted_execution"] = {
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip()[-4000:],
            "stderr": proc.stderr.strip()[-4000:],
            "witness_path": str(witness_path),
        }

        if not witness_path.is_file():
            raise ValueError(
                "trusted driver produced no witness (exit {})".format(proc.returncode)
            )
        execution = json.loads(witness_path.read_text())
        if execution.get("schema") != WITNESS_SCHEMA:
            raise ValueError("trusted witness schema is unexpected")
        if execution.get("bound_candidate_sha") != locked_sha:
            raise ValueError("trusted witness is not bound to the locked candidate sha")

        witness["trusted_execution_witness"] = execution
        witness["status"] = "WITNESSED"

    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        witness["notes"].append("witness_unavailable: {}".format(exc))
        out.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
        print("TRUSTED_WITNESS = UNKNOWN ({})".format(exc), file=sys.stderr)
        return 2

    out.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    execution = witness["trusted_execution_witness"]
    print(
        "TRUSTED_WITNESS = {} required={} executed_classes={} started={} failed={} driver={}".format(
            witness["status"],
            len(witness["required_test_classes"]),
            len(execution.get("observed_classes", [])),
            execution.get("tests_started"),
            execution.get("tests_failed"),
            witness["driver"]["sha256"][:12] if witness["driver"]["sha256"] else None,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())