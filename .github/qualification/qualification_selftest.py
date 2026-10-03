#!/usr/bin/env python3
"""Adversarial and positive controls for the Mage trusted exact-SHA qualification gate.

Every control asserts the verdict the pipeline *actually* produced against the
verdict it must produce. A control that deviates fails the selftest, and the
selftest failing fails the qualification job before any candidate result is read.

The gate under test has three independent trusted-side controls, none of which
consumes a candidate-authored artifact:

  1. build-definition audit - the candidate's own test-execution definition is
     compared against the comparison base through Git, as data;
  2. Maven/build-result binding - a non-zero candidate build exit is an
     unconditional qualification failure;
  3. trusted execution witness - the trusted JUnit launcher runs the trusted
     enumeration of required tests and the trusted code owns the counts.

Candidate-produced reports are never read. Controls 02, 03, 04 and 05 below
prove that by having the candidate fabricate, copy and suppress reports while
the verdict stays red.

Maven- or JUnit-less environments report NOT_RUN, never PASS: a missing
toolchain must not silently weaken the gate.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_definition_audit  # noqa: E402

SCHEMA = "mage.candidate-qualification.selftest/2"
QUALIFICATION_DIR = Path(__file__).resolve().parent
QUALIFY = QUALIFICATION_DIR / "qualify.py"
WITNESS = QUALIFICATION_DIR / "witness.py"
SOURCE_LOCK = QUALIFICATION_DIR / "source_lock.py"
DRIVER = QUALIFICATION_DIR / "TrustedTestDriver.java"
WORKFLOW = QUALIFICATION_DIR.parent / "workflows" / "candidate-qualification.yml"

QUALIFY_OVERRIDE = os.environ.get("C12_QUALIFY_OVERRIDE", "").strip()

CANDIDATE_SHA = "c" * 40
OTHER_SHA = "9" * 40
TRUSTED_SHA = "a" * 40
JUNIT_PROPERTY = "maven.compiler.source"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "mage-c12-controls",
    "GIT_AUTHOR_EMAIL": "controls@example.invalid",
    "GIT_COMMITTER_NAME": "mage-c12-controls",
    "GIT_COMMITTER_EMAIL": "controls@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}

PASSING_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ProbeTest {

    @Test
    void passesOne() {
        assertEquals(2, 1 + 1);
    }

    @Test
    void passesTwo() {
        assertEquals(4, 2 * 2);
    }
}
"""

FAILING_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ProbeTest {

    @Test
    void failsOnPurpose() {
        assertEquals(3, 1 + 1);
    }
}
"""

DISABLED_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

class ProbeTest {

    @Test
    @Disabled("candidate suppressed this test")
    void neverRuns() {
        assertEquals(2, 1 + 1);
    }
}
"""

UNCOMPILABLE_TEST = """package probe;

this is not valid java and must never compile
"""

FORGED_REPORT = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<testsuite version="3.0" name="probe.ForgedTest" time="0.001" tests="999" '
    'errors="0" skipped="0" failures="0"/>\n'
)

POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>probe</groupId>
  <artifactId>mage-c12-control</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>5.8.1</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.8.1</version>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.1.2</version>
        <configuration>
          <printSummary>true</printSummary>
          <reportFormat>brief</reportFormat>
          <useFile>false</useFile>
        </configuration>
      </plugin>
{extra}    </plugins>
  </build>
</project>
"""

ANTRUN_FORGE = """      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-antrun-plugin</artifactId>
        <version>3.1.0</version>
        <executions>
          <execution>
            <id>forge-green-evidence</id>
            <phase>{phase}</phase>
            <goals>
              <goal>run</goal>
            </goals>
            <configuration>
              <target>
                <copy file="${{project.basedir}}/forged/TEST-probe.ForgedTest.xml"
                      todir="${{project.build.directory}}/surefire-reports"/>
              </target>
            </configuration>
          </execution>
        </executions>
      </plugin>
"""

SUREFIRE_SKIP = """      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.1.2</version>
        <configuration>
          <printSummary>true</printSummary>
          <reportFormat>brief</reportFormat>
          <useFile>false</useFile>
          <skipTests>true</skipTests>
          <excludes>
            <exclude>**/*</exclude>
          </excludes>
        </configuration>
      </plugin>
"""


def build_pom(extra: str = "") -> str:
    return POM.format(extra=extra)


def write_project(root: Path, pom: str, test_source: str | None, forged_report: bool = False) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pom.xml").write_text(pom)
    if test_source is not None:
        test_file = root / "src" / "test" / "java" / "probe" / "ProbeTest.java"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(test_source)
    if forged_report:
        forged = root / "forged"
        forged.mkdir(parents=True, exist_ok=True)
        (forged / "TEST-probe.ForgedTest.xml").write_text(FORGED_REPORT)
    return root


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(GIT_ENV)
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False, env=env
    )


def git_ok(cwd: Path, *args: str) -> str:
    proc = git(cwd, *args)
    if proc.returncode != 0:
        raise RuntimeError("git {} failed: {}".format(" ".join(args), proc.stderr.strip()))
    return proc.stdout.strip()


def write_source_lock(path: Path, candidate_sha: str = CANDIDATE_SHA, status: str = "LOCKED") -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "mage.candidate-qualification.source-lock/1",
                "status": status,
                "repository": "moeendres-png/mage",
                "default_branch": "master",
                "pull_request_number": 39,
                "trusted_validator": {"sha": TRUSTED_SHA, "tree": "1" * 40},
                "candidate": {"sha": candidate_sha, "tree": "2" * 40},
                "comparison_base": {"sha": "3" * 40, "tree": "4" * 40},
                "candidate_code_executed_as_validator": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return path


def run_build(project: Path, maven: str, offline: bool, extra_flags: list | None = None) -> subprocess.CompletedProcess:
    cmd = [maven, "-B"] + (["-o"] if offline else [])
    cmd += [
        "test",
        "-DskipTests=false",
        "-Dmaven.test.skip=false",
        "-Dsurefire.skip=false",
    ] + list(extra_flags or [])
    return subprocess.run(cmd, cwd=str(project), capture_output=True, text=True, check=False)


def discover_modules(candidate_root: Path) -> list[str]:
    """Modules that own test sources, matching the trusted enumeration's rule."""
    modules = []
    for pom in sorted(candidate_root.glob("**/pom.xml")):
        module_dir = pom.parent
        for marker in ("src/test/java", "src/test/kotlin", "src/test/groovy"):
            if (module_dir / marker).is_dir():
                modules.append(module_dir.relative_to(candidate_root).as_posix() or ".")
                break
    return modules


def default_classpath_map(candidate_root: Path, junit_classpath: str) -> dict:
    """Every module gets the trusted JUnit platform. Real dependency resolution is
    the workflow's job; what matters here is that no module is ever silently
    dropped, which the completeness check enforces independently."""
    return {module: junit_classpath for module in discover_modules(candidate_root)}


def run_pipeline(
    tmp: Path,
    name: str,
    project: Path,
    base_pom: str,
    candidate_pom: str,
    build: subprocess.CompletedProcess,
    junit_classpath: str,
    observed_sha: str = CANDIDATE_SHA,
    audit_enabled: bool = True,
    corrupt_witness: bool = False,
    module_classpaths: dict | None = None,
) -> dict:
    """Source lock -> audit -> per-module witness -> verdict, all trusted-driven."""
    work = tmp / name
    work.mkdir(parents=True, exist_ok=True)
    lock = write_source_lock(work / "SOURCE_LOCK.json")

    audit_path = None
    if audit_enabled:
        result = build_definition_audit.audit_pom_pairs(
            [("pom.xml", base_pom.encode(), candidate_pom.encode())]
        )
        audit_path = work / "BUILD_DEFINITION_AUDIT.json"
        audit_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    classpaths = module_classpaths
    if classpaths is None:
        classpaths = default_classpath_map(project, junit_classpath)
    classpath_path = work / "MODULE_CLASSPATHS.json"
    classpath_path.write_text(json.dumps(classpaths, indent=2, sort_keys=True) + "\n")

    witness_out = work / "TRUSTED_WITNESS.json"
    env = dict(os.environ)
    env["TRUSTED_JUNIT_CLASSPATH"] = junit_classpath
    witness_cmd = [
        sys.executable,
        str(WITNESS),
        "--source-lock", str(lock),
        "--candidate-root", str(project),
        "--observed-candidate-sha", observed_sha,
        "--trusted-root", str(QUALIFICATION_DIR),
        "--work-dir", str(work / "witness-work"),
        "--build-exit-code", str(build.returncode),
        "--module-classpaths", str(classpath_path),
        "--out", str(witness_out),
    ]
    if audit_path:
        witness_cmd += ["--build-definition-audit", str(audit_path)]
    witness_proc = subprocess.run(
        witness_cmd, capture_output=True, text=True, check=False, env=env
    )

    if corrupt_witness and witness_out.is_file():
        witness_out.write_text("{ this is not valid json")

    evidence_out = work / "QUALIFICATION_EVIDENCE.json"
    qualify_cmd = [
        sys.executable,
        QUALIFY_OVERRIDE or str(QUALIFY),
        "--source-lock", str(lock),
        "--witness", str(witness_out),
        "--trusted-root", str(QUALIFICATION_DIR),
        "--out", str(evidence_out),
    ]
    if QUALIFY_OVERRIDE:
        # An overriding guard lives outside the trusted root by construction; the
        # trusted-root check must reject it rather than silently accept it.
        qualify_cmd += ["--guard", QUALIFY_OVERRIDE]
    qualify_proc = subprocess.run(
        qualify_cmd, capture_output=True, text=True, check=False
    )
    evidence = json.loads(evidence_out.read_text()) if evidence_out.is_file() else {}
    witness = json.loads(witness_out.read_text()) if witness_out.is_file() and not corrupt_witness else {}

    return {
        "verdict": evidence.get("verdict"),
        "credit": evidence.get("qualification_credit"),
        "reasons": evidence.get("reasons") or [],
        "reports_parsed": evidence.get("candidate_reports_parsed"),
        "authored_evidence_used": evidence.get("candidate_authored_evidence_used"),
        "build_exit": evidence.get("candidate_build_exit_code"),
        "witness_status": witness.get("status"),
        "modules_with_witness": (evidence.get("test_evidence") or {}).get("modules_with_witness"),
        "modules_without_witness": (evidence.get("test_evidence") or {}).get("modules_without_witness"),
        "classes_entered": (evidence.get("test_evidence") or {}).get("classes_entered_total"),
        "required_selected": (evidence.get("test_evidence") or {}).get("trusted_selected_classes"),
        "qualify_exit": qualify_proc.returncode,
        "witness_exit": witness_proc.returncode,
    }


def toolchain_available(maven: str, offline: bool, junit_classpath: str) -> tuple[bool, str]:
    probe = Path(tempfile.mkdtemp(prefix="c12-probe-"))
    try:
        write_project(probe / "p", build_pom(), PASSING_TEST)
        cmd = [maven, "-B"] + (["-o"] if offline else []) + ["validate"]
        if subprocess.run(cmd, cwd=str(probe / "p"), capture_output=True, check=False).returncode != 0:
            return False, "maven unavailable"
        if not junit_classpath or not Path(junit_classpath.split(os.pathsep)[0]).is_file():
            return False, "trusted junit classpath unavailable"
        compile_proc = subprocess.run(
            ["javac", "-nowarn", "-cp", junit_classpath, "-d", str(probe / "drv"), str(DRIVER)],
            capture_output=True,
            text=True,
            check=False,
        )
        if compile_proc.returncode != 0:
            return False, "trusted driver does not compile"
        return True, "ok"
    except OSError as exc:
        return False, str(exc)
    finally:
        shutil.rmtree(probe, ignore_errors=True)


def discover_junit_classpath() -> str:
    override = os.environ.get("TRUSTED_JUNIT_CLASSPATH", "").strip()
    if override:
        return override
    repo = Path(os.environ.get("HOME", "/root")) / ".m2" / "repository"
    matches = sorted(repo.glob("org/junit/platform/junit-platform-console-standalone/*/*.jar"))
    return str(matches[-1]) if matches else ""


def control(name, kind, expectation, expected, run, extra=None):
    result = run()
    ok = result.get("verdict") == expected and (result.get("qualify_exit", 1) == 0) == (expected == "PASS")
    row = {
        "control": name,
        "kind": kind,
        "expectation": expectation,
        "expected_verdict": expected,
        "observed_verdict": result.get("verdict"),
        "ok": bool(ok),
    }
    row.update(result)
    if extra:
        row.update(extra)
    return row


def pipeline_controls(tmp: Path, maven: str, offline: bool, junit_classpath: str) -> list[dict]:
    rows: list[dict] = []
    honest_pom = build_pom()

    # G / positive: honest candidate, trusted execution, nothing altered.
    proj = write_project(tmp / "CTRL-01-honest", honest_pom, PASSING_TEST)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-01-honest-execution",
            "positive",
            "an honest candidate whose tests the trusted launcher actually runs earns credit",
            "PASS",
            lambda: run_pipeline(tmp, "CTRL-01-honest", proj, honest_pom, honest_pom, build, junit_classpath),
            {"maven_exit_code": build.returncode},
        )
    )

    # A: candidate lifecycle hook fabricates green XML while its own build runs
    # zero required tests.
    forged_pom = build_pom(extra=ANTRUN_FORGE.format(phase="test"))
    proj = write_project(tmp / "CTRL-02-forged-evidence", forged_pom, PASSING_TEST, forged_report=True)
    build = run_build(proj, maven, offline)
    fabricated = list(proj.glob("target/surefire-reports/TEST-*.xml"))
    rows.append(
        control(
            "CTRL-02-forged-evidence-zero-execution",
            "red",
            "fabricated green TEST-*.xml while the candidate build executes nothing earns no credit",
            "FAIL",
            lambda: run_pipeline(tmp, "CTRL-02-forged", proj, honest_pom, forged_pom, build, junit_classpath),
            {
                "maven_exit_code": build.returncode,
                "fabricated_reports_present": [p.name for p in fabricated],
            },
        )
    )

    # B: a genuine test failure plus fabricated green XML.
    proj = write_project(tmp / "CTRL-03-real-failure", forged_pom, FAILING_TEST, forged_report=True)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-03-real-failure-plus-forged-evidence",
            "red",
            "a real failing test plus forged green XML is a FAIL, never a PASS",
            "FAIL",
            lambda: run_pipeline(tmp, "CTRL-03-failure", proj, honest_pom, forged_pom, build, junit_classpath),
            {"maven_exit_code": build.returncode},
        )
    )

    # 4. Copied/renamed fabricated report with the required test never compiled. A
    #    failed build plus missing execution is a proven FAIL, which is the stronger
    #    of the two permitted outcomes (FAIL or UNKNOWN), so FAIL is asserted.
    proj = write_project(tmp / "CTRL-04-copied-report", honest_pom, UNCOMPILABLE_TEST, forged_report=True)
    build = run_build(proj, maven, offline)
    fabricated = list(proj.glob("target/surefire-reports/TEST-*.xml")) + list(proj.glob("forged/TEST-*.xml"))
    rows.append(
        control(
            "CTRL-04-copied-report-no-trusted-provenance",
            "red",
            "a copied or renamed fabricated report grants nothing without trusted execution provenance",
            "FAIL",
            lambda: run_pipeline(tmp, "CTRL-04-copied", proj, honest_pom, honest_pom, build, junit_classpath),
            {"fabricated_reports_present": [p.name for p in fabricated]},
        )
    )

    # D: existing hardcoded surefire suppression control stays red.
    suppressed_pom = build_pom().replace(
        """          <useFile>false</useFile>
        </configuration>""",
        """          <useFile>false</useFile>
          <skipTests>true</skipTests>
          <excludes>
            <exclude>**/*</exclude>
          </excludes>
        </configuration>""",
    )
    proj = write_project(tmp / "CTRL-05-suppressed", suppressed_pom, PASSING_TEST)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-05-hardcoded-surefire-suppression",
            "red",
            "hardcoded surefire suppression keeps BUILD SUCCESS and still fails qualification",
            "FAIL",
            lambda: run_pipeline(tmp, "CTRL-05-suppressed", proj, honest_pom, suppressed_pom, build, junit_classpath),
            {"maven_exit_code": build.returncode, "maven_reported_success": build.returncode == 0},
        )
    )

    # D2: all discovered tests disabled.
    proj = write_project(tmp / "CTRL-06-all-disabled", honest_pom, DISABLED_TEST)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-06-all-tests-disabled",
            "red",
            "a candidate whose only tests are @Disabled earns no credit",
            "FAIL",
            lambda: run_pipeline(tmp, "CTRL-06-disabled", proj, honest_pom, honest_pom, build, junit_classpath),
            {"maven_exit_code": build.returncode},
        )
    )

    # E1: no required test source at all.
    proj = write_project(tmp / "CTRL-07-no-tests", honest_pom, None)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-07-no-required-tests",
            "red",
            "a candidate with no required test class is UNKNOWN, never PASS",
            "UNKNOWN",
            lambda: run_pipeline(tmp, "CTRL-07-no-tests", proj, honest_pom, honest_pom, build, junit_classpath),
            {"maven_exit_code": build.returncode},
        )
    )

    # E2: unusable witness evidence.
    proj = write_project(tmp / "CTRL-08-malformed", honest_pom, PASSING_TEST)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-08-malformed-witness",
            "red",
            "malformed witness evidence is never PASS",
            "UNKNOWN",
            lambda: run_pipeline(
                tmp, "CTRL-08-malformed", proj, honest_pom, honest_pom, build, junit_classpath,
                corrupt_witness=True,
            ),
            {"maven_exit_code": build.returncode},
        )
    )

    # E3: source binding broken - observed sha is not the locked candidate.
    proj = write_project(tmp / "CTRL-09-binding", honest_pom, PASSING_TEST)
    build = run_build(proj, maven, offline)
    rows.append(
        control(
            "CTRL-09-source-binding-mismatch",
            "red",
            "evidence for a tree that is not the locked candidate is never PASS",
            "UNKNOWN",
            lambda: run_pipeline(
                tmp, "CTRL-09-binding", proj, honest_pom, honest_pom, build, junit_classpath,
                observed_sha=OTHER_SHA,
            ),
            {"maven_exit_code": build.returncode},
        )
    )

    return rows


def source_lock_controls(tmp: Path) -> list[dict]:
    rows: list[dict] = []
    try:
        remote = tmp / "lockfixture-origin"
        git_ok(tmp, "-c", "init.defaultBranch=master", "init", "--quiet", str(remote))
        (remote / "a.txt").write_text("trusted\n")
        git_ok(remote, "add", "a.txt")
        git_ok(remote, "commit", "--quiet", "-m", "trusted")
        trusted_sha = git_ok(remote, "rev-parse", "HEAD")
        git_ok(remote, "checkout", "--quiet", "-b", "candidate")
        (remote / "b.txt").write_text("candidate\n")
        git_ok(remote, "add", "b.txt")
        git_ok(remote, "commit", "--quiet", "-m", "candidate")
        candidate_sha = git_ok(remote, "rev-parse", "HEAD")
        git_ok(remote, "checkout", "--quiet", "master")
        checkout = tmp / "lockfixture-trusted"
        git_ok(tmp, "clone", "--quiet", str(remote), str(checkout))
    except (RuntimeError, OSError) as exc:
        return [
            {
                "control": "CTRL-10-source-lock",
                "kind": "not_run",
                "expectation": "source lock controls need git: {}".format(exc),
                "observed_verdict": "NOT_RUN",
                "expected_verdict": "LOCKED",
                "ok": False,
            }
        ]

    def lock(trusted: str, candidate: str, base_ref: str, tag: str) -> dict:
        out = tmp / "lock-{}.json".format(tag)
        env = dict(os.environ)
        env.update(GIT_ENV)
        env["TRUSTED_REPO_ROOT"] = str(checkout)
        proc = subprocess.run(
            [
                sys.executable, str(SOURCE_LOCK),
                "--repo=moeendres-png/mage",
                "--default-branch=master",
                "--trusted-sha={}".format(trusted),
                "--candidate-sha={}".format(candidate),
                "--base-ref={}".format(base_ref),
                "--pr-number=39",
                "--candidate-ref=refs/heads/candidate",
                "--out={}".format(out),
            ],
            capture_output=True, text=True, check=False, env=env, cwd=str(checkout),
        )
        data = json.loads(out.read_text()) if out.is_file() else {}
        return {"exit_code": proc.returncode, "lock": data}

    good = lock(trusted_sha, candidate_sha, "master", "ok")
    data = good["lock"]
    rows.append(
        {
            "control": "CTRL-10-source-lock-positive",
            "kind": "positive",
            "expectation": "a correct trusted/candidate pair locks with sha, tree and merge base",
            "expected_verdict": "LOCKED",
            "observed_verdict": data.get("status"),
            "ok": (
                good["exit_code"] == 0
                and data.get("status") == "LOCKED"
                and data.get("trusted_validator", {}).get("sha") == trusted_sha
                and data.get("candidate", {}).get("sha") == candidate_sha
                and data.get("comparison_base", {}).get("sha") == trusted_sha
                and data.get("candidate_code_executed_as_validator") is False
            ),
        }
    )

    for tag, label, kwargs, expect_fragment in [
        ("wrongtrusted", "CTRL-11-wrong-trusted-sha", (candidate_sha, candidate_sha, "master"), "trusted"),
        ("base", "CTRL-12-non-default-base", (trusted_sha, candidate_sha, "feature"), "default branch"),
        ("swap", "CTRL-13-candidate-substitution", (trusted_sha, trusted_sha, "master"), "does not match event head sha"),
        ("badsha", "CTRL-14-malformed-candidate-sha", (trusted_sha, "not-a-sha", "master"), "40-hex"),
    ]:
        result = lock(*kwargs, tag=tag)
        payload = result["lock"]
        rows.append(
            {
                "control": label,
                "kind": "red",
                "expectation": "an unprovable source identity must not lock",
                "expected_verdict": "UNKNOWN",
                "observed_verdict": payload.get("status"),
                "error": payload.get("error"),
                "ok": (
                    result["exit_code"] != 0
                    and payload.get("status") == "UNKNOWN"
                    and payload.get("qualification_credit") is False
                    and expect_fragment in (payload.get("error") or "")
                ),
            }
        )

    return rows


HELPER_GROUP = "c12.helper"
HELPER_ARTIFACT = "only-on-b"
HELPER_VERSION = "1.0"

POM_WITH_HELPER = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>probe</groupId>
  <artifactId>mage-c12-control-module-b</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>5.8.1</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>c12.helper</groupId>
      <artifactId>only-on-b</artifactId>
      <version>1.0</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.8.1</version>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>3.1.2</version>
        <configuration>
          <printSummary>true</printSummary>
          <reportFormat>brief</reportFormat>
          <useFile>false</useFile>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""

HELPER_SOURCE = """package helper;

public final class OnlyOnB {

    private OnlyOnB() {
    }

    public static int value() {
        return 42;
    }
}
"""

MODULE_C_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ModuleCTest {

    @Test
    void failsOnPurpose() {
        assertEquals(99, 1 + 1);
    }
}
"""

MODULE_A_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ModuleATest {

    @Test
    void passes() {
        assertEquals(2, 1 + 1);
    }
}
"""

MODULE_B_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import helper.OnlyOnB;

import org.junit.jupiter.api.Test;

class ModuleBTest {

    @Test
    void usesModuleBOnlyDependency() {
        assertEquals(42, OnlyOnB.value());
    }
}
"""

SHARED_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class SharedTest {

    @Test
    void passes() {
        assertEquals(2, 1 + 1);
    }
}
"""

HELPER_JAR_NAME = "c12-helper-b.jar"


def build_helper_jar(workdir: Path) -> str:
    """Build and install a jar only module B may depend on."""
    src = workdir / "helpersrc" / "helper"
    src.mkdir(parents=True, exist_ok=True)
    (src / "OnlyOnB.java").write_text(HELPER_SOURCE)
    classes = workdir / "helperclasses"
    classes.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["javac", "-nowarn", "-d", str(classes), str(src / "OnlyOnB.java")],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("helper javac failed: {}".format(proc.stderr[:500]))
    jar = workdir / HELPER_JAR_NAME
    jar_proc = subprocess.run(
        ["jar", "cf", str(jar), "-C", str(classes), "helper"],
        capture_output=True, text=True, check=False,
    )
    if jar_proc.returncode != 0:
        raise RuntimeError("helper jar failed: {}".format(jar_proc.stderr[:500]))
    install = subprocess.run(
        [
            "mvn", "-B", "-o", "install:install-file",
            "-Dfile={}".format(jar),
            "-DgroupId={}".format(HELPER_GROUP),
            "-DartifactId={}".format(HELPER_ARTIFACT),
            "-Dversion={}".format(HELPER_VERSION),
            "-Dpackaging=jar",
        ],
        capture_output=True, text=True, check=False,
    )
    if install.returncode != 0:
        raise RuntimeError(
            "helper install failed (offline install-file unavailable): {}".format(
                (install.stderr or install.stdout)[-400:]
            )
        )
    return str(jar)


def write_module(root: Path, module: str, test_name: str, test_source: str, pom: str | None = None) -> Path:
    module_dir = root / module if module != "." else root
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "pom.xml").write_text(pom or build_pom())
    test_file = module_dir / "src" / "test" / "java" / "probe" / (test_name + ".java")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_source)
    return module_dir


def build_multi_module(tmp: Path, name: str) -> dict:
    root = tmp / name
    helper_work = tmp / (name + "-helper")
    helper_jar = build_helper_jar(helper_work)

    write_module(root, "modA", "ModuleATest", MODULE_A_TEST)
    write_module(root, "modB", "ModuleBTest", MODULE_B_TEST, pom=POM_WITH_HELPER)
    return {"root": root, "helper_jar": helper_jar}


DIVERGENT_SOURCE = """package probe;

/* Filename stem is SharedTest, so the trusted enumeration requires probe.SharedTest
   for this module, but the compiled class is probe.DivergentTest. The module that
   legitimately owns probe.SharedTest is the sibling. */
class DivergentTest {

    int value() {
        return 7;
    }
}
"""


def build_shared_collision(tmp: Path, name: str) -> dict:
    """modA legitimately owns probe.SharedTest; modB requires it but never defines it."""
    root = tmp / name
    write_module(root, "modA", "SharedTest", SHARED_TEST)
    write_module(root, "modB", "SharedTest", DIVERGENT_SOURCE)
    return {"root": root}


def module_controls(tmp: Path, maven: str, offline: bool, junit_classpath: str) -> list[dict]:
    rows: list[dict] = []
    honest_pom = build_pom()
    multi = build_multi_module(tmp, "CTRL-18-multimodule")
    root = multi["root"]

    # Build both modules with their own Maven invocations, exactly as surefire would.
    build_a = run_build(root / "modA", maven, offline)
    build_b = run_build(root / "modB", maven, offline)
    helper_cp = os.pathsep.join([multi["helper_jar"], junit_classpath])
    classpaths = {"modA": junit_classpath, "modB": helper_cp}

    def run(tag, project, base, cand, build, cps, expected, kind, expectation, extra=None):
        rows.append(
            control(
                tag, kind, expectation, expected,
                lambda: run_pipeline(tmp, tag.replace(" ", "-"), project, base, cand, build,
                                     junit_classpath, module_classpaths=cps),
                extra,
            )
        )

    # 1. Two modules, different test dependencies, both executed through the witness.
    run("CTRL-18-multi-module-execution", root, honest_pom, honest_pom,
        build_a if build_a.returncode == 0 else build_b,
        classpaths, "PASS", "positive",
        "two modules with different test classpaths both execute and aggregate honestly",
        {"module_a_exit": build_a.returncode, "module_b_exit": build_b.returncode})

    # 2. A dependency reachable only on its own module classpath is genuinely entered.
    entered = None
    result = run_pipeline(tmp, "CTRL-19-dep-on-own-classpath", root, honest_pom, honest_pom,
                          build_b, junit_classpath, module_classpaths=classpaths)
    entered = (result.get("classes_entered"), result.get("required_selected"))
    ok = result.get("verdict") == "PASS" and entered == (2, 2)
    rows.append({
        "control": "CTRL-19-module-only-dependency-entered",
        "kind": "positive",
        "expectation": "a required class whose dependency exists only on its own module test classpath is actually entered",
        "expected_verdict": "PASS",
        "observed_verdict": result.get("verdict"),
        "classes_entered": entered[0],
        "required_selected": entered[1],
        "ok": bool(ok),
    })

    # 3. A required module with no resolved classpath is a gap, never a skip.
    partial = dict(classpaths)
    partial.pop("modB")
    result = run_pipeline(tmp, "CTRL-20-missing-module-classpath", root, honest_pom, honest_pom,
                          build_a, junit_classpath, module_classpaths=partial)
    reasons = " ".join(result.get("reasons") or [])
    ok = result.get("verdict") in ("FAIL", "UNKNOWN") and "module_classpath_missing" in reasons
    rows.append({
        "control": "CTRL-20-missing-module-classpath",
        "kind": "red",
        "expectation": "a required module whose classpath was not resolved cannot be silently skipped",
        "expected_verdict": "FAIL",
        "observed_verdict": result.get("verdict"),
        "reasons": result.get("reasons"),
        "ok": bool(ok),
    })

    # 4. Dependency missing from the module's runtime classpath: the required class is
    #    compiled but cannot run, and must fail rather than be skipped.
    no_helper = {"modA": junit_classpath, "modB": junit_classpath}
    result = run_pipeline(tmp, "CTRL-21-unresolved-module-dependency", root, honest_pom, honest_pom,
                          build_a, junit_classpath, module_classpaths=no_helper)
    reasons = " ".join(result.get("reasons") or [])
    ok = result.get("verdict") in ("FAIL", "UNKNOWN") and (
        "test_failures" in reasons or "tests_aborted" in reasons
        or "zero_tests_found" in reasons or "required_tests_never_entered" in reasons
        or "zero_tests_executed" in reasons
    )
    rows.append({
        "control": "CTRL-21-unresolved-module-dependency",
        "kind": "red",
        "expectation": "a required class that cannot resolve on its module classpath earns no credit and is not skipped",
        "expected_verdict": "FAIL",
        "observed_verdict": result.get("verdict"),
        "reasons": result.get("reasons"),
        "ok": bool(ok),
    })

    # 5. A module that genuinely fails at trusted-execution time must not be masked
    #    by passing siblings. Asserted on test_failures specifically: this control
    #    previously passed because the failing module had not compiled, which is a
    #    different property and would have hidden a masking bug.
    write_module(root, "modC", "ModuleCTest", MODULE_C_TEST)
    failing_cp = dict(classpaths)
    failing_cp["modC"] = junit_classpath
    build_c = run_build(root / "modC", maven, offline)
    result = run_pipeline(tmp, "CTRL-22-sibling-cannot-mask-failure", root, honest_pom, honest_pom,
                          build_a, junit_classpath, module_classpaths=failing_cp)
    reasons = " ".join(result.get("reasons") or [])
    ok = (
        result.get("verdict") == "FAIL"
        and "test_failures" in reasons
        and "required_tests_not_compiled" not in reasons
        and set(result.get("modules_with_witness") or []) >= {"modA", "modB", "modC"}
    )
    rows.append({
        "control": "CTRL-22-sibling-cannot-mask-failure",
        "kind": "red",
        "expectation": "one genuinely failing module is not masked by successful sibling modules",
        "expected_verdict": "FAIL",
        "observed_verdict": result.get("verdict"),
        "modules_with_witness": result.get("modules_with_witness"),
        "reasons": result.get("reasons"),
        "module_c_build_exit": build_c.returncode,
        "ok": bool(ok),
    })

    # 6. Aggregation cannot turn partial execution into PASS.
    broken_root = tmp / "CTRL-23-partial.root"
    write_module(broken_root, "modA", "ModuleATest", MODULE_A_TEST)
    write_module(broken_root, "modB", "ModuleBTest", PASSING_TEST)
    run_build(broken_root / "modA", maven, offline)
    # modB is left uncompiled on purpose: it owns required classes but cannot run.
    result = run_pipeline(tmp, "CTRL-23-partial-aggregation", broken_root, honest_pom, honest_pom,
                          run_build(broken_root / "modA", maven, offline), junit_classpath,
                          module_classpaths={"modA": junit_classpath, "modB": junit_classpath})
    reasons = " ".join(result.get("reasons") or [])
    ok = result.get("verdict") in ("FAIL", "UNKNOWN") and (
        "partial_module_execution" in reasons or "module_execution_incomplete" in reasons
        or "required_tests_not_compiled" in reasons
    )
    rows.append({
        "control": "CTRL-23-partial-aggregation-not-pass",
        "kind": "red",
        "expectation": "aggregation cannot convert partial module execution into PASS",
        "expected_verdict": "FAIL",
        "observed_verdict": result.get("verdict"),
        "modules_with_witness": result.get("modules_with_witness"),
        "reasons": result.get("reasons"),
        "ok": bool(ok),
    })

# 7. A required class that only exists in a sibling module's output must not be
    #    credited to this module. This is the property the driver's code-origin
    #    check defends, and the classpath sanitiser enforces by dropping stale
    #    installed sibling jars in favour of the candidate's reactor output.
    collision = build_shared_collision(tmp, "CTRL-24-origin-collision")
    collision_root = collision["root"]
    run_build(collision_root / "modA", maven, offline)
    run_build(collision_root / "modB", maven, offline)
    # modB requires probe.SharedTest, but only modA's test output defines it.
    # Sanitisation puts modB's own output first and adds sibling *main* output
    # only, so modA's test-classes must not satisfy modB's requirement.
    colliding = {
        "modA": junit_classpath,
        "modB": os.pathsep.join(
            [str(collision_root / "modA" / "target" / "test-classes"), junit_classpath]
        ),
    }
    result = run_pipeline(tmp, "CTRL-24-required-class-not-credited-from-sibling", collision_root, honest_pom, honest_pom,
                          run_build(collision_root / "modA", maven, offline), junit_classpath,
                          module_classpaths=colliding)
    reasons = " ".join(result.get("reasons") or [])
    ok = (
        result.get("verdict") in ("FAIL", "UNKNOWN")
        and (
            "required_tests_not_compiled" in reasons
            or "required_tests_never_entered" in reasons
            or "class_origin_mismatch" in reasons
            or "required_pairs_not_entered" in reasons
        )
    )
    rows.append({
        "control": "CTRL-24-required-class-not-credited-from-sibling",
        "kind": "red",
        "expectation": "a required class present only in another module's output cannot be credited",
        "expected_verdict": "FAIL",
        "observed_verdict": result.get("verdict"),
        "reasons": result.get("reasons"),
        "ok": bool(ok),
    })

    # 8. A module with zero required classes must not fabricate positive credit.
    empty_root = tmp / "CTRL-25-empty-module.root"
    write_module(empty_root, "modA", "ModuleATest", MODULE_A_TEST)
    write_module(empty_root, "modEmpty", "Helper", """package probe;

public final class Helper {
}
""")
    build_empty = run_build(empty_root / "modA", maven, offline)
    run_build(empty_root / "modEmpty", maven, offline)
    result = run_pipeline(tmp, "CTRL-25-empty-module-no-credit", empty_root, honest_pom, honest_pom,
                          build_empty, junit_classpath,
                          module_classpaths={"modA": junit_classpath, "modEmpty": junit_classpath})
    modules_with_witness = result.get("modules_with_witness")
    ok = result.get("verdict") == "PASS" and modules_with_witness == ["modA"]
    rows.append({
        "control": "CTRL-25-zero-required-classes-no-credit",
        "kind": "red",
        "expectation": "a module with zero required classes contributes nothing and cannot fabricate credit",
        "expected_verdict": "PASS",
        "observed_verdict": result.get("verdict"),
        "modules_with_witness": modules_with_witness,
        "ok": bool(ok),
    })

    return rows


def static_controls() -> list[dict]:
    rows: list[dict] = []

    text = WORKFLOW.read_text() if WORKFLOW.is_file() else ""
    problems = []
    if not text:
        problems.append("trusted workflow file is missing")
    for required in (
        "pull_request_target",
        "persist-credentials: false",
        "SOURCE_LOCK.json",
        "QUALIFICATION_EVIDENCE.json",
        "TRUSTED_WITNESS.json",
        "BUILD_DEFINITION_AUDIT.json",
        "MODULE_CLASSPATHS.json",
        "dependency:build-classpath",
        "contents: read",
    ):
        if required not in text:
            problems.append("trusted workflow is missing {!r}".format(required))
    for forbidden in (
        "--candidate-ref",
        "continue-on-error",
        "secrets.",
        "pull-requests: write",
    ):
        if forbidden in text:
            problems.append("trusted workflow contains forbidden {!r}".format(forbidden))
    # The build step must compile, not author evidence, and must not hand a
    # candidate report location to anything.
    if "mvn -B test" in text and "test-compile" not in text:
        problems.append("trusted workflow runs a candidate test phase instead of test-compile")
    rows.append(
        {
            "control": "CTRL-15-workflow-contract",
            "kind": "red",
            "expectation": "the trusted workflow keeps its no-credential, unmasked, PR-head-ref contract and never harvests candidate reports",
            "expected_verdict": "PASS",
            "observed_verdict": "FAIL" if problems else "PASS",
            "reasons": problems,
            "ok": not problems,
        }
    )

    # Structural check, not a text match: the scorer must contain no directory
    # traversal and no candidate build-output path, so there is no code path that
    # could read a candidate-authored report. Matching the strings
    # "surefire-reports" or "TEST-*.xml" would only prove the docstring mentions
    # them, which is the opposite of what matters.
    traversal = []
    try:
        source = QUALIFY.read_text()
        tree = ast.parse(source, str(QUALIFY))
    except (OSError, SyntaxError) as exc:
        traversal.append("qualify.py unreadable: {}".format(exc))
        tree = None
    if tree is not None:
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = getattr(node, "body", [])
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    docstrings.add(id(body[0].value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                attr = func.attr if isinstance(func, ast.Attribute) else None
                if attr in ("rglob", "iglob", "glob", "walk", "scandir", "listdir"):
                    traversal.append("directory traversal via .{}()".format(attr))
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
            ):
                literal = node.value.lower()
                if "surefire" in literal or "/target" in literal or literal.startswith("target/"):
                    traversal.append("candidate build-output literal: {!r}".format(node.value))

    # The witness producer may walk the candidate tree - it has to, in order to
    # enumerate required tests and locate compiled classes - but it must never name
    # a surefire report location, because that is the evidence path being closed.
    try:
        witness_tree = ast.parse(WITNESS.read_text(), str(WITNESS))
    except (OSError, SyntaxError) as exc:
        traversal.append("witness.py unreadable: {}".format(exc))
        witness_tree = None
    if witness_tree is not None:
        witness_docstrings = set()
        for node in ast.walk(witness_tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = getattr(node, "body", [])
                if (
                    body
                    and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)
                ):
                    witness_docstrings.add(id(body[0].value))
        for node in ast.walk(witness_tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in witness_docstrings
                and "surefire" in node.value.lower()
            ):
                traversal.append("witness.py names a surefire report path: {!r}".format(node.value))
    rows.append(
        {
            "control": "CTRL-16-no-candidate-report-harvesting",
            "kind": "red",
            "expectation": "qualify.py traverses no directory and names no candidate build output, so it cannot read candidate reports",
            "expected_verdict": "PASS",
            "observed_verdict": "FAIL" if traversal else "PASS",
            "reasons": traversal,
            "ok": not traversal,
        }
    )

    driver_present = DRIVER.is_file()
    rows.append(
        {
            "control": "CTRL-17-trusted-driver-present",
            "kind": "positive",
            "expectation": "the trusted execution driver exists as trusted source",
            "expected_verdict": "PASS",
            "observed_verdict": "PASS" if driver_present else "FAIL",
            "ok": driver_present,
        }
    )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maven", default="mvn")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    junit_classpath = discover_junit_classpath()
    tmp = Path(tempfile.mkdtemp(prefix="mage-c12-selftest-"))
    try:
        results = list(static_controls()) + source_lock_controls(tmp)

        available, reason = toolchain_available(args.maven, args.offline, junit_classpath)
        if available:
            os.environ["TRUSTED_JUNIT_CLASSPATH"] = junit_classpath
            results += pipeline_controls(tmp, args.maven, args.offline, junit_classpath)
            results += module_controls(tmp, args.maven, args.offline, junit_classpath)
        else:
            for name in (
                "CTRL-01-honest-execution",
                "CTRL-02-forged-evidence-zero-execution",
                "CTRL-03-real-failure-plus-forged-evidence",
                "CTRL-04-copied-report-no-trusted-provenance",
                "CTRL-05-hardcoded-surefire-suppression",
                "CTRL-06-all-tests-disabled",
                "CTRL-07-no-required-tests",
                "CTRL-08-malformed-witness",
                "CTRL-09-source-binding-mismatch",
                "CTRL-18-multi-module-execution",
                "CTRL-19-module-only-dependency-entered",
                "CTRL-20-missing-module-classpath",
                "CTRL-21-unresolved-module-dependency",
                "CTRL-22-sibling-cannot-mask-failure",
                "CTRL-23-partial-aggregation-not-pass",
                "CTRL-24-required-class-not-credited-from-sibling",
                "CTRL-25-zero-required-classes-no-credit",
            ):
                results.append(
                    {
                        "control": name,
                        "kind": "not_run",
                        "expectation": "control needs a real Maven/JDK toolchain: {}".format(reason),
                        "observed_verdict": "NOT_RUN",
                        "expected_verdict": "UNKNOWN",
                        "ok": False,
                    }
                )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = [r for r in results if r.get("ok")]
    failed = [r for r in results if not r.get("ok")]
    not_run = [r for r in results if r.get("kind") == "not_run"]
    status = "PASS" if not failed else "FAIL"

    summary = {
        "schema": SCHEMA,
        "status": status,
        "qualify_used": QUALIFY_OVERRIDE or str(QUALIFY),
        "qualify_sha256": hashlib.sha256(Path(QUALIFY_OVERRIDE or QUALIFY).read_bytes()).hexdigest(),
        "controls_total": len(results),
        "controls_passed": len(passed),
        "controls_failed": len(failed),
        "controls_not_run": len(not_run),
        "positive_controls": sum(1 for r in results if r.get("kind") in ("positive", "honest")),
        "red_controls": sum(1 for r in results if r.get("kind") == "red"),
        "maven": {"command": args.maven, "offline": args.offline},
        "results": results,
    }

    print("== Mage C12 trusted qualification gate controls ==")
    for row in results:
        print(
            "[{}] {:<46} {:<9} expected={:<8} observed={}".format(
                "ok  " if row.get("ok") else "FAIL",
                row.get("control"),
                row.get("kind"),
                row.get("expected_verdict"),
                row.get("observed_verdict"),
            )
        )
        if not row.get("ok"):
            print("        expectation: {}".format(row.get("expectation")))
            if row.get("reasons"):
                print("        reasons: {}".format("; ".join(row["reasons"])[:600]))
            elif row.get("error"):
                print("        error: {}".format(row["error"])[:600])
    print(
        "SELFTEST = {} ({}/{} controls ok, {} not run)".format(
            status, len(passed), len(results), len(not_run)
        )
    )

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())