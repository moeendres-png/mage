#!/usr/bin/env python3
"""Adversarial controls for the Mage trusted exact-SHA qualification guard.

Every control asserts the guard's *actual* verdict against an expected verdict.
A control that deviates fails the selftest, and the selftest failing fails the
qualification job before any candidate test result is read.

The positive control proves the guard can still award credit. The red controls
prove that a candidate cannot manufacture credit by suppressing its own tests,
forging evidence, shadowing the guard, or breaking source binding.

Controls that need a real Maven run are reported NOT_RUN (never PASS) when Maven
is unavailable, so a missing toolchain cannot silently weaken the gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "mage.candidate-qualification.selftest/1"
QUALIFICATION_DIR = Path(__file__).resolve().parent
GUARD = QUALIFICATION_DIR / "qualify.py"
SOURCE_LOCK = QUALIFICATION_DIR / "source_lock.py"
WORKFLOW = QUALIFICATION_DIR.parent / "workflows" / "candidate-qualification.yml"
MAVEN = ["mvn", False]

GIT_ENV = {
    "GIT_AUTHOR_NAME": "mage-c12-controls",
    "GIT_AUTHOR_EMAIL": "controls@example.invalid",
    "GIT_COMMITTER_NAME": "mage-c12-controls",
    "GIT_COMMITTER_EMAIL": "controls@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}

CANDIDATE_SHA = "1" * 40
OTHER_SHA = "2" * 40
TRUSTED_SHA = "3" * 40

HONEST_TEST = """package probe;

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

POM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
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
{properties}
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
{surefire}
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
"""


def pom(properties: dict, surefire: str) -> str:
    rendered = "".join(
        "    <{}>{}</{}>\n".format(key, value, key) for key, value in properties.items()
    )
    return POM_TEMPLATE.format(properties=rendered, surefire=surefire)


def make_project(root: Path, test_source: str, properties: dict, surefire: str) -> Path:
    test_file = root / "src" / "test" / "java" / "probe" / "ProbeTest.java"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_source)
    (root / "pom.xml").write_text(pom(properties or {}, surefire))
    return root


def make_source_lock(path: Path, candidate_sha: str = CANDIDATE_SHA) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "mage.candidate-qualification.source-lock/1",
                "status": "LOCKED",
                "repository": "moeendres-png/mage",
                "default_branch": "master",
                "pull_request_number": 1,
                "trusted_validator": {"sha": TRUSTED_SHA, "tree": "a" * 40},
                "candidate": {"sha": candidate_sha, "tree": "b" * 40},
                "comparison_base": {"sha": "c" * 40, "tree": "d" * 40},
                "candidate_code_executed_as_validator": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return path


def surefire_xml(name: str, tests: int, failures: int = 0, errors: int = 0, skipped: int = 0) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<testsuite version="3.0" name="{name}" time="0.1" tests="{tests}" '
        'errors="{errors}" skipped="{skipped}" failures="{failures}"/>\n'
    ).format(name=name, tests=tests, failures=failures, errors=errors, skipped=skipped)


def write_reports(candidate_root: Path, module: str = "Mage.Tests", **counts) -> Path:
    reports = candidate_root / module / "target" / "surefire-reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "TEST-probe.ProbeTest.xml").write_text(surefire_xml("probe.ProbeTest", **counts))
    return candidate_root


def run_guard(
    tmp: Path,
    name: str,
    candidate_root: Path,
    observed_sha: str = CANDIDATE_SHA,
    lock_sha: str = CANDIDATE_SHA,
) -> dict:
    lock = make_source_lock(tmp / "{}-lock.json".format(name), lock_sha)
    out = tmp / "{}-evidence.json".format(name)
    proc = subprocess.run(
        [
            sys.executable,
            str(GUARD),
            "--source-lock",
            str(lock),
            "--candidate-root",
            str(candidate_root),
            "--observed-candidate-sha",
            observed_sha,
            "--trusted-root",
            str(GUARD.parent),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    evidence = json.loads(out.read_text())
    return {"exit_code": proc.returncode, "evidence": evidence, "stdout": proc.stdout, "stderr": proc.stderr}


def mvn_available(maven: str, offline: bool) -> bool:
    probe = Path(tempfile.mkdtemp(prefix="mage-c12-mvnprobe-"))
    try:
        (probe / "pom.xml").write_text(pom({}, ""))
        cmd = [maven, "-B"]
        if offline:
            cmd.append("-o")
        cmd.append("validate")
        return subprocess.run(cmd, cwd=str(probe), capture_output=True, check=False).returncode == 0
    finally:
        shutil.rmtree(probe, ignore_errors=True)


def run_maven_build(maven: str, offline: bool, project: Path) -> subprocess.CompletedProcess:
    cmd = [maven, "-B"]
    if offline:
        cmd.append("-o")
    cmd += [
        "test",
        # Trusted-side overrides. These are necessary but deliberately treated as
        # insufficient: the guard must not award credit for a build that ran no
        # tests even when Maven reports success.
        "-DskipTests=false",
        "-Dmaven.test.skip=false",
        "-Dsurefire.skip=false",
    ]
    return subprocess.run(cmd, cwd=str(project), capture_output=True, text=True, check=False)


# --- fixture-only controls -------------------------------------------------

def ctrl_forged_evidence(tmp: Path) -> dict:
    name = "CTRL-04-forged-evidence"
    candidate = write_reports(tmp / name, tests=3)
    forged = candidate / "QUALIFICATION_EVIDENCE.json"
    forged.write_text(
        json.dumps({"verdict": "PASS", "qualification_credit": True, "reasons": ["trust me"]})
    )
    result = run_guard(tmp, name, candidate)
    emitted = result["evidence"]
    ok = (
        emitted.get("verdict") == "PASS"
        and emitted.get("qualification_credit") is True
        and "trust me" not in json.dumps(emitted)
        and (emitted.get("reasons") or []) == []
    )
    return {
        "control": name,
        "kind": "red",
        "expectation": "candidate-forged PASS evidence is never consumed; verdict derives from real reports",
        "observed_verdict": emitted.get("verdict"),
        "expected_verdict": "PASS",
        "forged_file_present": forged.is_file(),
        "reasons": emitted.get("reasons") or [],
        "ok": ok,
    }


def ctrl_guard_shadowing(tmp: Path) -> dict:
    name = "CTRL-05-guard-shadowing"
    candidate = write_reports(tmp / name, tests=2)
    shadow = candidate / ".github" / "qualification" / "qualify.py"
    shadow.parent.mkdir(parents=True, exist_ok=True)
    shadow.write_text("#!/usr/bin/env python3\nprint('PASS')\nsys.exit(0)\n")
    result = run_guard(tmp, name, candidate)
    guard = result["evidence"].get("guard") or {}
    trusted_digest = hashlib.sha256(GUARD.read_bytes()).hexdigest()
    ok = (
        result["evidence"].get("verdict") == "PASS"
        and guard.get("candidate_shadow_present") is True
        and guard.get("candidate_shadow_sha256") not in (None, trusted_digest)
        and guard.get("sha256") == trusted_digest
    )
    return {
        "control": name,
        "kind": "red",
        "expectation": "candidate copy of the guard is recorded but inert; trusted guard digest decides",
        "observed_verdict": result["evidence"].get("verdict"),
        "expected_verdict": "PASS",
        "trusted_guard_sha256": trusted_digest,
        "candidate_shadow_sha256": guard.get("candidate_shadow_sha256"),
        "reasons": result["evidence"].get("reasons", []),
        "ok": ok,
    }


def ctrl_binding_mismatch(tmp: Path) -> dict:
    name = "CTRL-06-source-binding"
    candidate = write_reports(tmp / name, tests=5)
    result = run_guard(tmp, name, candidate, observed_sha=OTHER_SHA)
    reasons = " ".join(result["evidence"].get("reasons") or [])
    ok = (
        result["evidence"].get("verdict") == "FAIL"
        and result["evidence"].get("qualification_credit") is False
        and "source_binding_mismatch" in reasons
        and result["exit_code"] == 1
    )
    return {
        "control": name,
        "kind": "red",
        "expectation": "green reports for a tree that is not the locked candidate are a FAIL",
        "observed_verdict": result["evidence"].get("verdict"),
        "expected_verdict": "FAIL",
        "reasons": result["evidence"].get("reasons") or [],
        "ok": ok,
    }


def ctrl_unusable_evidence(tmp: Path) -> dict:
    name = "CTRL-07-unusable-evidence"
    candidate = tmp / name
    reports = candidate / "Mage.Tests" / "target" / "surefire-reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "TEST-probe.ProbeTest.xml").write_text("<testsuite tests=\"not-a-number\"")
    result = run_guard(tmp, name, candidate)
    ok = (
        result["evidence"].get("verdict") == "FAIL"
        and result["evidence"].get("qualification_credit") is False
        and result["exit_code"] != 0
    )
    return {
        "control": name,
        "kind": "red",
        "expectation": "malformed test evidence never becomes PASS",
        "observed_verdict": result["evidence"].get("verdict"),
        "expected_verdict": "FAIL",
        "reasons": result["evidence"].get("reasons") or [],
        "ok": ok,
    }


def ctrl_not_run(tmp: Path) -> dict:
    name = "CTRL-10-not-run"
    candidate = tmp / name / "clean-checkout-without-build"
    candidate.mkdir(parents=True, exist_ok=True)
    result = run_guard(tmp, name, candidate)
    ok = (
        result["evidence"].get("verdict") == "FAIL"
        and result["evidence"].get("qualification_credit") is False
        and result["exit_code"] == 1
    )
    return {
        "control": name,
        "kind": "red",
        "expectation": "NOT_RUN (no build output at all) is never PASS",
        "observed_verdict": result["evidence"].get("verdict"),
        "expected_verdict": "FAIL",
        "reasons": result["evidence"].get("reasons") or [],
        "ok": ok,
    }


# --- source-lock controls (real git fixtures) ------------------------------


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


def build_git_fixture(tmp: Path) -> dict:
    """Create a local origin with a trusted master commit and a distinct candidate commit."""
    remote = tmp / "fixture-origin"
    remote.mkdir(parents=True, exist_ok=True)
    git_ok(remote.parent, "-c", "init.defaultBranch=master", "init", "--quiet", str(remote))
    (remote / "a.txt").write_text("trusted\n")
    git_ok(remote, "add", "a.txt")
    git_ok(remote, "commit", "--quiet", "-m", "trusted validator commit")
    trusted_sha = git_ok(remote, "rev-parse", "HEAD")

    git_ok(remote, "checkout", "--quiet", "-b", "candidate")
    (remote / "b.txt").write_text("candidate\n")
    git_ok(remote, "add", "b.txt")
    git_ok(remote, "commit", "--quiet", "-m", "candidate commit")
    candidate_sha = git_ok(remote, "rev-parse", "HEAD")
    git_ok(remote, "checkout", "--quiet", "master")

    trusted = tmp / "fixture-trusted"
    git_ok(tmp, "clone", "--quiet", str(remote), str(trusted))
    git_ok(trusted, "fetch", "--quiet", "--no-tags", "origin", "master")

    return {
        "remote": remote,
        "trusted": trusted,
        "trusted_sha": trusted_sha,
        "candidate_sha": candidate_sha,
    }


def run_source_lock(fixture_trusted: Path, out: Path, **overrides) -> dict:
    args = {
        "--repo": "moeendres-png/mage",
        "--default-branch": "master",
        "--trusted-sha": overrides.get("trusted_sha", ""),
        "--candidate-sha": overrides.get("candidate_sha", ""),
        "--base-ref": overrides.get("base_ref", "master"),
        "--pr-number": overrides.get("pr_number", "1"),
        "--candidate-ref": overrides.get("candidate_ref", "refs/heads/candidate"),
        "--out": str(out),
    }
    env = dict(os.environ)
    env.update(GIT_ENV)
    env["TRUSTED_REPO_ROOT"] = str(fixture_trusted)
    proc = subprocess.run(
        [sys.executable, str(SOURCE_LOCK), *[f"{k}={v}" for k, v in args.items() if v]],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=str(fixture_trusted),
    )
    lock = json.loads(out.read_text()) if out.is_file() else {}
    return {"exit_code": proc.returncode, "lock": lock, "stderr": proc.stderr}


def source_lock_controls(tmp: Path) -> list[dict]:
    try:
        fixture = build_git_fixture(tmp)
    except (RuntimeError, OSError) as exc:
        return [
            {
                "control": "CTRL-11-source-lock-positive",
                "kind": "not_run",
                "expectation": "source lock needs real git fixtures: {}".format(exc),
                "observed_verdict": "NOT_RUN",
                "expected_verdict": "LOCKED",
                "ok": False,
            }
        ]

    trusted_sha = fixture["trusted_sha"]
    candidate_sha = fixture["candidate_sha"]
    results = []

    positive = run_source_lock(
        fixture["trusted"], tmp / "CTRL-11-lock.json", trusted_sha=trusted_sha, candidate_sha=candidate_sha
    )
    lock = positive["lock"]
    ok = (
        positive["exit_code"] == 0
        and lock.get("status") == "LOCKED"
        and lock.get("trusted_validator", {}).get("sha") == trusted_sha
        and lock.get("candidate", {}).get("sha") == candidate_sha
        and len(lock.get("candidate", {}).get("tree", "")) == 40
        and lock.get("comparison_base", {}).get("sha") == trusted_sha
        and lock.get("candidate_code_executed_as_validator") is False
    )
    results.append(
        {
            "control": "CTRL-11-source-lock-positive",
            "kind": "positive",
            "expectation": "a correct trusted/candidate pair locks with sha, tree and merge base",
            "observed_verdict": lock.get("status"),
            "expected_verdict": "LOCKED",
            "candidate_fetch_ref": lock.get("candidate_fetch_ref"),
            "ok": ok,
        }
    )

    mismatch = run_source_lock(
        fixture["trusted"],
        tmp / "CTRL-12-lock.json",
        trusted_sha=candidate_sha,
        candidate_sha=candidate_sha,
    )
    ok = (
        mismatch["exit_code"] != 0
        and mismatch["lock"].get("status") == "UNKNOWN"
        and mismatch["lock"].get("qualification_credit") is False
    )
    results.append(
        {
            "control": "CTRL-12-wrong-trusted-sha",
            "kind": "red",
            "expectation": "a trusted sha that is not the executing checkout cannot lock",
            "observed_verdict": mismatch["lock"].get("status"),
            "expected_verdict": "UNKNOWN",
            "error": mismatch["lock"].get("error"),
            "ok": ok,
        }
    )

    wrong_base = run_source_lock(
        fixture["trusted"],
        tmp / "CTRL-13-lock.json",
        trusted_sha=trusted_sha,
        candidate_sha=candidate_sha,
        base_ref="some-feature-branch",
    )
    ok = (
        wrong_base["exit_code"] != 0
        and wrong_base["lock"].get("status") == "UNKNOWN"
        and "default branch" in (wrong_base["lock"].get("error") or "")
    )
    results.append(
        {
            "control": "CTRL-13-non-default-base",
            "kind": "red",
            "expectation": "a base ref other than the default branch cannot lock",
            "observed_verdict": wrong_base["lock"].get("status"),
            "expected_verdict": "UNKNOWN",
            "error": wrong_base["lock"].get("error"),
            "ok": ok,
        }
    )

    swapped = run_source_lock(
        fixture["trusted"],
        tmp / "CTRL-14-lock.json",
        trusted_sha=trusted_sha,
        candidate_sha=trusted_sha,
    )
    ok = (
        swapped["exit_code"] != 0
        and swapped["lock"].get("status") == "UNKNOWN"
        and "does not match event head sha" in (swapped["lock"].get("error") or "")
    )
    results.append(
        {
            "control": "CTRL-14-candidate-substitution",
            "kind": "red",
            "expectation": "a candidate sha that the fetched ref does not resolve to cannot lock",
            "observed_verdict": swapped["lock"].get("status"),
            "expected_verdict": "UNKNOWN",
            "error": swapped["lock"].get("error"),
            "ok": ok,
        }
    )

    malformed = run_source_lock(
        fixture["trusted"],
        tmp / "CTRL-15-lock.json",
        trusted_sha=trusted_sha,
        candidate_sha="not-a-sha",
    )
    ok = malformed["exit_code"] != 0 and malformed["lock"].get("status") == "UNKNOWN"
    results.append(
        {
            "control": "CTRL-15-malformed-sha",
            "kind": "red",
            "expectation": "a non-sha candidate identity cannot lock",
            "observed_verdict": malformed["lock"].get("status"),
            "expected_verdict": "UNKNOWN",
            "error": malformed["lock"].get("error"),
            "ok": ok,
        }
    )

    return results


def ctrl_workflow_contract(tmp: Path) -> dict:
    """Static proof that production does not use the test-only candidate-ref override."""
    name = "CTRL-16-workflow-contract"
    text = WORKFLOW.read_text() if WORKFLOW.is_file() else ""
    problems = []
    if not text:
        problems.append("trusted workflow file is missing")
    for required in (
        "pull_request_target",
        "persist-credentials: false",
        "SOURCE_LOCK.json",
        "QUALIFICATION_EVIDENCE.json",
        "contents: read",
    ):
        if required not in text:
            problems.append("trusted workflow is missing {!r}".format(required))
    # A test-only escape hatch must never reach production, and a masked step
    # would let a candidate buy green without producing evidence.
    for forbidden in ("--candidate-ref", "continue-on-error", "secrets.", "pull-requests: write"):
        if forbidden in text:
            problems.append("trusted workflow contains forbidden {!r}".format(forbidden))
    return {
        "control": name,
        "kind": "red",
        "expectation": "trusted workflow keeps the PR head ref, no-credential checkouts and no masked or escaped steps",
        "observed_verdict": "FAIL" if problems else "PASS",
        "expected_verdict": "PASS",
        "reasons": problems,
        "ok": not problems,
    }


# --- real-maven controls ---------------------------------------------------

def maven_control(
    tmp: Path,
    name: str,
    kind: str,
    expectation: str,
    expected: str,
    test_source: str,
    properties: dict,
    surefire: str = "",
    note: str = "",
) -> dict:
    project = make_project(tmp / name, test_source, properties, surefire)
    build = run_maven_build(MAVEN[0], MAVEN[1], project)
    result = run_guard(tmp, name, project)
    if expected == "PASS":
        ok = (
            build.returncode == 0
            and result["evidence"].get("verdict") == "PASS"
            and result["evidence"].get("qualification_credit") is True
            and result["exit_code"] == 0
        )
    else:
        ok = result["evidence"].get("verdict") == expected and result["exit_code"] != 0
    return {
        "control": name,
        "kind": kind,
        "expectation": expectation,
        "observed_verdict": result["evidence"].get("verdict"),
        "expected_verdict": expected,
        "maven_exit_code": build.returncode,
        "maven_reported_success": build.returncode == 0,
        "reasons": result["evidence"].get("reasons") or [],
        "totals": (result["evidence"].get("test_evidence") or {}).get("totals"),
        "note": note,
        "ok": ok,
    }


def main() -> int:
    global MAVEN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maven", default="mvn")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    MAVEN = [args.maven, args.offline]

    tmp = Path(tempfile.mkdtemp(prefix="mage-c12-selftest-"))
    results: list[dict] = []
    try:
        results += [
            ctrl_forged_evidence(tmp),
            ctrl_guard_shadowing(tmp),
            ctrl_binding_mismatch(tmp),
            ctrl_unusable_evidence(tmp),
            ctrl_not_run(tmp),
            ctrl_workflow_contract(tmp),
        ] + source_lock_controls(tmp)

        have_maven = mvn_available(args.maven, args.offline)
        if have_maven:
            results += [
                maven_control(
                    tmp,
                    "CTRL-01-honest-candidate",
                    "positive",
                    "an honest candidate that runs its tests earns qualification credit",
                    "PASS",
                    HONEST_TEST,
                    {},
                ),
                maven_control(
                    tmp,
                    "CTRL-02-suppressed-tests",
                    "red",
                    "a candidate that hardcodes surefire skip/excludes still gets BUILD SUCCESS but earns no credit",
                    "FAIL",
                    HONEST_TEST,
                    properties={"skipTests": "true", "maven.test.skip": "true"},
                    surefire="          <skipTests>true</skipTests>\n"
                    "          <excludes>\n            <exclude>**/*</exclude>\n          </excludes>\n",
                    note="headline red control: mvn exit code is 0, qualification verdict is FAIL",
                ),
                maven_control(
                    tmp,
                    "CTRL-03-maven-test-skip",
                    "red_defeated",
                    "a candidate that sets maven.test.skip via properties is neutralised by the "
                    "trusted -Dmaven.test.skip=false override, so its tests really run",
                    "PASS",
                    HONEST_TEST,
                    {"maven.test.skip": "true", "skipTests": "true"},
                    note="property-level suppression loses to trusted overrides; compare CTRL-02, "
                    "where plugin-configuration-level suppression survives them and only the "
                    "report-existence check can catch it",
                ),
                maven_control(
                    tmp,
                    "CTRL-08-real-test-failure",
                    "red",
                    "a genuinely failing test is a FAIL, not a suppressed PASS",
                    "FAIL",
                    FAILING_TEST,
                    {},
                ),
                maven_control(
                    tmp,
                    "CTRL-09-all-tests-skipped",
                    "red",
                    "a candidate whose tests are all @Disabled is a FAIL",
                    "FAIL",
                    DISABLED_TEST,
                    {},
                ),
            ]
        else:
            for name, expectation in [
                ("CTRL-01-honest-candidate", "positive control needs a real Maven run"),
                ("CTRL-02-suppressed-tests", "headline red control needs a real Maven run"),
                ("CTRL-03-maven-test-skip", "red control needs a real Maven run"),
                ("CTRL-08-real-test-failure", "red control needs a real Maven run"),
                ("CTRL-09-all-tests-skipped", "red control needs a real Maven run"),
            ]:
                results.append(
                    {
                        "control": name,
                        "kind": "not_run",
                        "expectation": expectation,
                        "observed_verdict": "NOT_RUN",
                        "expected_verdict": "PASS"
                        if "positive" in expectation or "03-maven" in name
                        else "FAIL",
                        "maven_available": False,
                        "ok": False,
                    }
                )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    not_run = [r for r in results if r["kind"] == "not_run"]
    status = "PASS" if not failed else "FAIL"

    summary = {
        "schema": SCHEMA,
        "status": status,
        "guard": str(GUARD),
        "controls_total": len(results),
        "controls_passed": len(passed),
        "controls_failed": len(failed),
        "controls_not_run": len(not_run),
        "positive_controls": sum(1 for r in results if r["kind"] == "positive"),
        "red_controls": sum(1 for r in results if r["kind"] == "red"),
        "maven": {"command": args.maven, "offline": args.offline},
        "results": results,
    }

    print("== Mage C12 qualification guard controls ==")
    for r in results:
        mark = "ok  " if r["ok"] else "FAIL"
        print(
            "[{}] {:<34} {:<9} expected={:<6} observed={}".format(
                mark,
                r["control"],
                r["kind"],
                r["expected_verdict"],
                r["observed_verdict"],
            )
        )
        if not r["ok"]:
            print("        expectation: {}".format(r["expectation"]))
            if r.get("reasons"):
                print("        reasons: {}".format("; ".join(r["reasons"])))
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