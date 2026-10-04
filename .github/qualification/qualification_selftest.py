#!/usr/bin/env python3
"""Adversarial and positive controls for the Mage trusted exact-SHA qualification gate.

Every control asserts the verdict the pipeline *actually* produced against the
verdict it must produce, and red controls also assert the intended reason. A
control that deviates fails the selftest, and the selftest failing fails the
qualification job before any candidate result is read.

Each pipeline control builds a real Git fixture (trusted/base commit with the
trusted baseline, candidate commit), then runs the production path end to end:
source lock -> build-definition audit -> sandbox prepare (separate OS identity,
writability probe) -> candidate build AS THE SANDBOX ACCOUNT -> per-module
classpath collection -> witness (corpus policy, trusted test compile from the
Git export, sandboxed driver) -> evidence seals -> integrity verify -> scorer.
The trusted scripts executed are the copies committed in the fixture's trusted
commit, so a candidate that could overwrite them would overwrite the scorer
that actually runs.

Families:
  * P1-1 trust domain: candidate build or test code tries to overwrite
    qualify.py, witness.py, the source lock and sealed evidence, plants a daemon,
    mutates its test bytecode, or adds an initialize-phase plugin; simulated
    breaches prove the integrity check catches what the boundary should prevent;
  * P1-2 corpus: rename, delete, move, regex escape, green-subset shrink,
    additions, the approved removal path and malformed/missing/stale baselines;
  * the earlier report-forgery, suppression, binding and per-module controls.

Missing toolchain or sandbox reports NOT_RUN, which fails the selftest: a gate
whose controls could not run is not a gate.
"""

from __future__ import annotations

import argparse
import ast
import re
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import build_definition_audit  # noqa: E402
import corpus_policy  # noqa: E402
import resolve_classpaths  # noqa: E402
import sandbox  # noqa: E402

SCHEMA = "mage.candidate-qualification.selftest/3"
QUALIFICATION_DIR = Path(__file__).resolve().parent
QUALIFY = QUALIFICATION_DIR / "qualify.py"
WITNESS = QUALIFICATION_DIR / "witness.py"
SOURCE_LOCK = QUALIFICATION_DIR / "source_lock.py"
DRIVER = QUALIFICATION_DIR / "TrustedTestDriver.java"
OBSERVER = QUALIFICATION_DIR / "TrustedTestObserver.java"
WORKFLOW = QUALIFICATION_DIR.parent / "workflows" / "candidate-qualification.yml"
FIXTURE_QUAL = ".github/qualification"
TRUSTED_FILES = (
    "TrustedTestDriver.java",
    "TrustedTestObserver.java",
    "build_definition_audit.py",
    "corpus_policy.py",
    "qualify.py",
    "resolve_classpaths.py",
    "sandbox.py",
    "witness.py",
)

QUALIFY_OVERRIDE = os.environ.get("C12_QUALIFY_OVERRIDE", "").strip()
CANARY = "C12_SELFTEST_CANARY"

OTHER_SHA = "9" * 40

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


def sha256_path(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def test_file(name: str, source: str, module: str = ".") -> dict:
    prefix = "" if module == "." else module + "/"
    return {"{}src/test/java/probe/{}.java".format(prefix, name): source}


def project(tests: dict, pom: str | None = None, module: str = ".", extra: dict | None = None) -> dict:
    """Files of one Maven project; ``tests`` maps class name -> Java source."""
    prefix = "" if module == "." else module + "/"
    files = {prefix + "pom.xml": pom or build_pom()}
    for name, source in tests.items():
        files.update(test_file(name, source, module))
    files.update(extra or {})
    return files


def passing(name: str) -> str:
    return PASSING_TEST.replace("class ProbeTest", "class {}".format(name))


def failing(name: str) -> str:
    return FAILING_TEST.replace("class ProbeTest", "class {}".format(name))


class Harness:
    """Runs the production pipeline against Git fixtures, as the sandbox account."""

    def __init__(self, tmp: Path, maven: str, offline: bool, junit_classpath: str, user: str):
        self.tmp = tmp
        self.maven = maven
        self.offline = offline
        self.junit_classpath = junit_classpath
        self.user = user
        self.sandbox_dir = Path(os.environ.get("C12_SELFTEST_SANDBOX_DIR", "/srv/c12-selftest-sandbox"))
        # Root-owned parents only (/opt is world-writable on hosted runners).
        self.bundle_dir = Path("/var/lib/c12-selftest/bundle")
        self.runtime_dir = Path("/var/lib/c12-selftest/runtime")
        self.seed = str(Path(os.environ.get("HOME", "/root")) / ".m2" / "repository")

    # -- fixtures ---------------------------------------------------------

    def _write(self, root: Path, files: dict) -> None:
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content)

    def _clear(self, repo: Path) -> None:
        for child in repo.iterdir():
            if child.name == ".git":
                continue
            if child.name == ".github":
                continue
            shutil.rmtree(child) if child.is_dir() else child.unlink()

    def _baseline(self, repo: Path, approvals=None) -> str:
        paths = [p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file() and ".git" not in p.relative_to(repo).parts[:1]]
        entries = corpus_policy.enumerate_paths(paths)
        methods, _ = corpus_policy.enumerate_methods(
            entries, lambda rel: (repo / rel).read_bytes() if (repo / rel).is_file() else None)
        doc = corpus_policy.build_baseline(corpus_policy.pairs_of(entries), approvals, methods)
        return json.dumps(doc, indent=1, sort_keys=True) + "\n"

    def fixture(self, name: str, base: dict, candidate: dict | None = None, *, trusted_baseline="auto",
                candidate_baseline="auto", approvals=None, candidate_approvals=None,
                trusted_followup: dict | None = None, followup_rebaseline: bool = True) -> dict:
        root = self.tmp / name
        repo = root / "repo"
        work = root / "work"
        work.mkdir(parents=True)
        git_ok(self.tmp, "-c", "init.defaultBranch=master", "init", "--quiet", str(repo))
        for item in TRUSTED_FILES:
            target = repo / FIXTURE_QUAL / item
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(QUALIFICATION_DIR / item, target)
        self._write(repo, base)
        baseline_path = repo / corpus_policy.BASELINE_PATH
        if trusted_baseline == "auto":
            baseline_path.write_text(self._baseline(repo, approvals))
        elif isinstance(trusted_baseline, str):
            baseline_path.write_text(trusted_baseline)
        git_ok(repo, "add", "-A")
        git_ok(repo, "commit", "--quiet", "-m", "trusted base")
        base_sha = git_ok(repo, "rev-parse", "HEAD")
        trusted_sha = base_sha
        if trusted_followup:
            self._write(repo, trusted_followup)
            if followup_rebaseline and trusted_baseline == "auto":
                baseline_path.write_text(self._baseline(repo, approvals))
            git_ok(repo, "add", "-A")
            git_ok(repo, "commit", "--quiet", "-m", "trusted follow-up")
            trusted_sha = git_ok(repo, "rev-parse", "HEAD")
        git_ok(repo, "checkout", "--quiet", "-b", "candidate", base_sha)
        if candidate is not None:
            self._clear(repo)
            self._write(repo, candidate)
        if candidate_baseline == "keep":
            pass
        elif candidate_baseline == "auto":
            baseline_path.write_text(self._baseline(repo, candidate_approvals))
        elif candidate_baseline is None:
            if baseline_path.exists():
                baseline_path.unlink()
        elif isinstance(candidate_baseline, str):
            baseline_path.write_text(candidate_baseline)
        git_ok(repo, "add", "-A")
        git_ok(repo, "commit", "--quiet", "--allow-empty", "-m", "candidate")
        cand_sha = git_ok(repo, "rev-parse", "HEAD")
        git_ok(repo, "checkout", "--quiet", "--detach", trusted_sha)
        return {
            "name": name, "repo": repo, "work": work, "evidence": work / "evidence",
            "trusted_sha": trusted_sha, "base_sha": base_sha, "cand_sha": cand_sha,
            "trusted_tree": git_ok(repo, "rev-parse", trusted_sha + "^{tree}"),
            "base_tree": git_ok(repo, "rev-parse", base_sha + "^{tree}"),
            "cand_tree": git_ok(repo, "rev-parse", cand_sha + "^{tree}"),
            "qual": repo / FIXTURE_QUAL,
        }

    # -- sandbox helpers ----------------------------------------------------

    def as_candidate(self, cwd: Path, cmd: list[str]) -> subprocess.CompletedProcess:
        return sandbox.run_candidate(self.user, sandbox.sandbox_home(self.sandbox_dir), cwd, cmd)

    def mvn(self, *goals: str) -> list[str]:
        return [self.maven, "-B"] + (["-o"] if self.offline else []) + list(goals)

    def install_artifact(self, jar: Path, group: str, artifact: str, version: str) -> None:
        """Place a jar and a minimal POM in the candidate's local Maven repository, as the candidate.

        Done directly in the repository layout rather than through install:install-file,
        so the control does not depend on the install plugin being resolvable offline.
        """
        relative = Path(*group.split(".")) / artifact / version
        target = sandbox.sandbox_home(self.sandbox_dir) / ".m2" / "repository" / relative
        trusted_target = Path(self.seed) / relative
        pom = ('<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'
               "<groupId>{}</groupId><artifactId>{}</artifactId><version>{}</version></project>").format(group, artifact, version)
        stem = "{}-{}".format(artifact, version)
        proc = self.as_candidate(self.sandbox_dir, [
            "/bin/sh", "-c", 'mkdir -p "$1" && cp "$2" "$1/$3.jar" && printf "%s" "$4" > "$1/$3.pom"',
            "c12", str(target), str(jar), stem, pom])
        if proc.returncode != 0:
            raise RuntimeError("could not install {}:{}:{}: {}".format(group, artifact, version, proc.stderr[-300:]))
        trusted_target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(jar, trusted_target / (stem + ".jar"))
        (trusted_target / (stem + ".pom")).write_text(pom)

    def stage_readonly(self, src: Path, name: str) -> Path:
        dest = Path("/var/lib/c12-selftest") / name
        sandbox.stage_readonly(src, dest)
        return dest

    def cleanup(self) -> None:
        try:
            sandbox.reap(self.user)
        except sandbox.SandboxError:
            pass
        subprocess.run(sandbox._priv(["rm", "-rf", "/var/lib/c12-selftest", str(self.sandbox_dir)]),
                       capture_output=True, check=False)

    # -- the production pipeline -------------------------------------------

    def pipeline(self, fx: dict, *, build_modules=None, classpath_override=None, after_build=None,
                 after_seal=None, corrupt_witness=False, lock_candidate_sha=None, before_prepare=None,
                 trusted_path_prefix=None) -> dict:
        evidence = fx["evidence"]
        evidence.mkdir(parents=True, exist_ok=True)
        py = [sys.executable, "-I", "-S", "-B"]
        qual = fx["qual"]
        lock_path = evidence / "SOURCE_LOCK.json"
        lock_path.write_text(json.dumps({
            "schema": "mage.candidate-qualification.source-lock/1",
            "status": "LOCKED",
            "repository": "moeendres-png/mage",
            "default_branch": "master",
            "pull_request_number": 39,
            "trusted_validator": {"sha": fx["trusted_sha"], "tree": fx["trusted_tree"]},
            "candidate": {"sha": lock_candidate_sha or fx["cand_sha"], "tree": fx["cand_tree"]},
            "comparison_base": {"sha": fx["base_sha"], "tree": fx["base_tree"]},
            "candidate_code_executed_as_validator": False,
        }, indent=2, sort_keys=True) + "\n")
        audit = build_definition_audit.audit(fx["repo"], fx["base_sha"], fx["cand_sha"])
        audit_path = evidence / "BUILD_DEFINITION_AUDIT.json"
        audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")

        if before_prepare:
            before_prepare(self, fx)
        prepare_path = evidence / "SANDBOX_PREPARE.json"
        probes = ["--probe", str(fx["work"]), "--probe", str(fx["repo"])]
        trusted_env = dict(os.environ)
        if trusted_path_prefix:
            trusted_env["PATH"] = os.pathsep.join([str(trusted_path_prefix), trusted_env.get("PATH", "")])
        prep = subprocess.run(py + [str(qual / "sandbox.py"), "prepare", "--user", self.user,
                                    "--repo", str(fx["repo"]), "--candidate-sha", fx["cand_sha"],
                                    "--sandbox-dir", str(self.sandbox_dir), "--bundle-dir", str(self.runtime_dir),
                                    "--seed-maven-repo", self.seed, "--work-dir", str(fx["work"]),
                                    "--out", str(prepare_path)] + probes,
                              capture_output=True, text=True, check=False, env=trusted_env)
        seal1 = fx["work"] / "seal-before.json"
        sandbox_ok = prep.returncode == 0
        subprocess.run(py + [str(qual / "sandbox.py"), "seal", "--out", str(seal1),
                             str(lock_path), str(audit_path), str(prepare_path)],
                       capture_output=True, text=True, check=False)

        build_path = evidence / "BUILD_RESULT.json"
        build_record = {"schema": sandbox.SCHEMA_RUN, "status": "UNKNOWN", "user": self.user, "exit_code": None}
        if sandbox_ok:
            modules = build_modules or ["."]
            for module in modules:
                rec = fx["work"] / "build-{}.json".format(module.replace("/", "_"))
                subprocess.run(py + [str(qual / "sandbox.py"), "run", "--user", self.user,
                                     "--label", "build-" + module, "--sandbox-dir", str(self.sandbox_dir),
                                     "--cwd", str(self.sandbox_dir / "candidate" / module), "--out", str(rec), "--"]
                               + self.mvn("test-compile", "dependency:build-classpath", "-DincludeScope=test",
                                          "-Dmdep.outputFile=" + resolve_classpaths.CLASSPATH_FILE,
                                          "-Dmaven.compiler.proc=none"),
                               capture_output=True, text=True, check=False)
                record = json.loads(rec.read_text()) if rec.is_file() else {"status": "UNKNOWN", "user": self.user}
                # The first failing module decides; otherwise any recorded module.
                if build_record.get("status") != "RECORDED" or (build_record.get("exit_code") == 0 and record.get("exit_code") != 0):
                    build_record = record
        build_path.write_text(json.dumps(build_record, indent=2, sort_keys=True) + "\n")
        if after_build and sandbox_ok:
            after_build(self, fx)

        mapping, _ = resolve_classpaths.collect(str(fx["repo"]), fx["cand_sha"], self.sandbox_dir / "candidate")
        if classpath_override:
            mapping = classpath_override(self, fx, dict(mapping))
        classpaths_path = evidence / "MODULE_CLASSPATHS.json"
        classpaths_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")

        witness_path = evidence / "TRUSTED_WITNESS.json"
        env = dict(os.environ)
        env["TRUSTED_JUNIT_CLASSPATH"] = self.junit_classpath
        witness_proc = subprocess.run(
            py + [str(qual / "witness.py"), "--source-lock", str(lock_path), "--git-repo", str(fx["repo"]),
                  "--trusted-root", str(qual), "--sandbox-dir", str(self.sandbox_dir),
                  "--sandbox-user", self.user, "--sandbox-prepare", str(prepare_path),
                  "--bundle-dir", str(self.bundle_dir), "--work-dir", str(fx["work"] / "witness"),
                  "--build-result", str(build_path), "--build-definition-audit", str(audit_path),
                  "--module-classpaths", str(classpaths_path), "--trusted-maven-repo", self.seed,
                  "--out", str(witness_path)],
            capture_output=True, text=True, check=False, env=env)
        if corrupt_witness and witness_path.is_file():
            witness_path.write_text("{ this is not valid json")

        seal2 = fx["work"] / "seal-after.json"
        sealed = [p for p in (build_path, classpaths_path, witness_path) if p.is_file()]
        subprocess.run(py + [str(qual / "sandbox.py"), "seal", "--out", str(seal2)] + [str(p) for p in sealed],
                       capture_output=True, text=True, check=False)
        if after_seal:
            after_seal(self, fx)

        integrity_path = evidence / "INTEGRITY.json"
        integrity_proc = subprocess.run(
            py + [str(qual / "sandbox.py"), "verify", "--user", self.user, "--repo", str(fx["repo"]),
                  "--trusted-sha", fx["trusted_sha"], "--seal", str(seal1), "--seal", str(seal2),
                  "--probe", str(fx["work"]), "--probe", str(fx["repo"]),
                  "--probe", str(self.bundle_dir), "--probe", str(self.runtime_dir), "--out", str(integrity_path)],
            capture_output=True, text=True, check=False, env=trusted_env)

        evidence_path = evidence / "QUALIFICATION_EVIDENCE.json"
        qualify_cmd = py + [QUALIFY_OVERRIDE or str(qual / "qualify.py"), "--source-lock", str(lock_path),
                            "--witness", str(witness_path), "--integrity", str(integrity_path),
                            "--trusted-root", str(qual), "--out", str(evidence_path)]
        if QUALIFY_OVERRIDE:
            qualify_cmd += ["--guard", QUALIFY_OVERRIDE]
        qualify_proc = subprocess.run(qualify_cmd, capture_output=True, text=True, check=False)
        ev = load(evidence_path)
        witness = load(witness_path) if not corrupt_witness else {}
        integrity = load(integrity_path)

        # Mirror the workflow's enforce step: integrity and verdict independently.
        verdict = ev.get("verdict")
        if integrity_proc.returncode != 0:
            verdict = "FAIL" if integrity.get("status") == "VIOLATION" or verdict == "FAIL" else "UNKNOWN"
        test_evidence = ev.get("test_evidence") or {}
        return {
            "verdict": verdict,
            "scorer_verdict": ev.get("verdict"),
            "credit": ev.get("qualification_credit"),
            "reasons": (ev.get("reasons") or []) + list(integrity.get("violations") or []),
            "integrity": integrity.get("status"),
            "integrity_exit": integrity_proc.returncode,
            "sandbox_prepared": sandbox_ok,
            "sandbox_error": load(prepare_path).get("error"),
            "reports_parsed": ev.get("candidate_reports_parsed"),
            "build_exit": build_record.get("exit_code"),
            "witness_status": witness.get("status"),
            "witness_notes": (witness.get("notes") or [])[:5],
            "corpus": (witness.get("corpus_policy") or {}).get("status"),
            "modules_with_witness": test_evidence.get("modules_with_witness"),
            "modules_without_witness": test_evidence.get("modules_without_witness"),
            "classes_entered": test_evidence.get("classes_entered_total"),
            "required_selected": test_evidence.get("trusted_selected_classes"),
            "qualify_exit": 0 if verdict == "PASS" else 1,
            "witness_exit": witness_proc.returncode,
            "witness_stdout": witness_proc.stdout,
            "qualify_stdout": qualify_proc.stdout,
            "witness_stderr": witness_proc.stderr.strip()[-400:],
        }


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def toolchain_available(harness: Harness) -> tuple[bool, str]:
    if not harness.junit_classpath or not Path(harness.junit_classpath.split(os.pathsep)[0]).is_file():
        return False, "trusted junit classpath unavailable"
    for tool in ("javac", "java", "git", harness.maven):
        if not shutil.which(tool):
            return False, "{} unavailable".format(tool)
    try:
        home = sandbox.prepare_sandbox(harness.user, harness.sandbox_dir)
        sandbox.seed_maven_repository(harness.user, home, Path(harness.seed))
        probe = harness.as_candidate(harness.sandbox_dir, ["/usr/bin/env"])
    except (sandbox.SandboxError, OSError) as exc:
        return False, "sandbox unavailable: {}".format(exc)
    if probe.returncode != 0:
        return False, "sandbox command failed: {}".format(probe.stderr[-300:])
    return True, "ok"


def discover_junit_classpath() -> str:
    override = os.environ.get("TRUSTED_JUNIT_CLASSPATH", "").strip()
    if override:
        return override
    repo = Path(os.environ.get("HOME", "/root")) / ".m2" / "repository"
    jar = repo / "org/junit/platform/junit-platform-console-standalone/1.9.3/junit-platform-console-standalone-1.9.3.jar"
    return str(jar) if jar.is_file() else ""


def row(name, kind, expectation, expected, result, reason=None, extra_ok=True, extra=None):
    """A control row. Red rows must also carry their intended reason."""
    reasons = " ".join(result.get("reasons") or [])
    reason_ok = reason is None or any(r in reasons for r in ([reason] if isinstance(reason, str) else reason))
    ok = result.get("verdict") == expected and reason_ok and bool(extra_ok)
    out = {
        "control": name,
        "kind": kind,
        "expectation": expectation,
        "expected_verdict": expected,
        "expected_reason": reason,
        "observed_verdict": result.get("verdict"),
        "ok": bool(ok),
    }
    out.update(result)
    out.update(extra or {})
    return out


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




TAMPER_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

import org.junit.jupiter.api.Test;

class TamperTest {{

    @Test
    void rewriteTrustedState() {{
        // Candidate test bytecode, executing in the trusted driver's JVM as the
        // sandbox account, tries to replace a trusted file with an always-PASS
        // payload and to leave a daemon behind. Both attempts must be inert.
        try {{
            Files.write(Paths.get("{target}"), "{payload}".getBytes(StandardCharsets.UTF_8),
                    StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE);
        }} catch (Exception ignored) {{
            // denied, as it must be
        }}
        try {{
            new ProcessBuilder("sh", "-c", "sleep 900").start();
        }} catch (Exception ignored) {{
            // nothing to do
        }}
    }}

    @Test
    void genuinelyFails() {{
        assertEquals(3, 1 + 1);
    }}
}}
"""

FORGER_TEST = """package probe;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.junit.jupiter.api.Test;

class ForgerTest {{

    @Test
    void forgeTheWitness() throws Exception {{
        String forged = "{{\\"observed_classes\\": [\\"probe.ForgerTest\\"], \\"tests_found\\": 1, "
                + "\\"tests_started\\": 1, \\"tests_succeeded\\": 1, \\"tests_failed\\": 0, "
                + "\\"classes_never_entered\\": [], \\"code_origin_violations\\": [], "
                + "\\"driver_verdict\\": \\"PASS\\"}}";
        Files.write(Paths.get("{path}"), forged.getBytes(StandardCharsets.UTF_8));
        Files.write(Paths.get("{path}.mac"), "00".getBytes(StandardCharsets.US_ASCII));
        Runtime.getRuntime().halt(0);
    }}
}}
"""

ALWAYS_PASS_SCORER = "import sys; print('QUALIFICATION = PASS'); sys.exit(0)\\n"

ENV_PROBE_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Map;

import org.junit.jupiter.api.Test;

class EnvProbeTest {

    @Test
    void noRunnerHandleCrossesTheBoundary() {
        for (Map.Entry<String, String> entry : System.getenv().entrySet()) {
            String key = entry.getKey();
            assertTrue(!key.startsWith("GITHUB_") && !key.startsWith("ACTIONS_")
                    && !key.startsWith("RUNNER_") && !key.equals("C12_SELFTEST_CANARY"),
                    "leaked into the candidate environment: " + key);
        }
    }
}
"""

INITIALIZE_PLUGIN = """      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-antrun-plugin</artifactId>
        <version>3.1.0</version>
        <executions>
          <execution>
            <id>replace-the-scorer</id>
            <phase>initialize</phase>
            <goals>
              <goal>run</goal>
            </goals>
            <configuration>
              <target>
                <echo file="{target}" message="import sys; sys.exit(0)"/>
              </target>
            </configuration>
          </execution>
        </executions>
      </plugin>
"""


def many_methods(count: int, disabled=frozenset()) -> str:
    """A public Jupiter class ProbeTest with ``count`` passing test methods."""
    lines = ["package probe;", "", "import org.junit.jupiter.api.Disabled;", "import org.junit.jupiter.api.Test;",
             "", "public class ProbeTest {"]
    for index in range(count):
        if index in disabled:
            lines.append('    @Disabled("candidate suppressed this test")')
        lines.append("    @Test public void test{}() {{ }}".format(index))
    return "\n".join(lines + ["}", ""])


HOOKED_BASE_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

public class ProbeTest {
    protected int value() { return 1; }

    @Test public void test0() { assertEquals(1, value()); }
}
"""


def hooked_subclass(value: int, abstract: bool = False) -> str:
    """SubProbeTest: declares no test, inherits ProbeTest's, overrides its hook."""
    return (
        "package probe;\n\n"
        "public {}class SubProbeTest extends ProbeTest {{\n"
        "    @Override protected int value() {{ return {}; }}\n"
        "}}\n"
    ).format("abstract " if abstract else "", value)


FAKE_TEST_ANNOTATION = """package probe;

import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

@Retention(RetentionPolicy.RUNTIME)
public @interface Test {
}
"""


def three_tests(**override) -> dict:
    tests = {"AlphaTest": passing("AlphaTest"), "BetaTest": passing("BetaTest"), "GammaTest": passing("GammaTest")}
    tests.update(override)
    return {k: v for k, v in tests.items() if v is not None}


def trust_controls(h: Harness) -> list[dict]:
    """P1-1: candidate execution has no write authority over trusted state."""
    rows: list[dict] = []

    def tamper_control(control: str, label: str, target_of) -> None:
        name = control
        root = h.tmp / name
        # Paths are deterministic, so the candidate can name them in its source.
        repo, work = root / "repo", root / "work"
        target = target_of(repo, work)
        tamper = TAMPER_TEST.format(target=str(target), payload=ALWAYS_PASS_SCORER)
        files = project({"TamperTest": tamper})
        fx = h.fixture(name, files)
        before = {}

        def remember(_h, _fx):
            before["digest"] = sha256_path(target)

        result = h.pipeline(fx, after_build=remember)
        unchanged = before.get("digest") is not None and sha256_path(target) == before["digest"]
        rows.append(row(
            control, "red",
            "candidate test bytecode that tries to overwrite {} cannot change it, and a genuinely failing "
            "candidate stays FAIL".format(label),
            "FAIL", result, reason="test_failures",
            extra_ok=unchanged and result.get("integrity") == "OK",
            extra={"target_unchanged": unchanged},
        ))

    tamper_control("CTRL-26-test-code-overwrites-qualify", "qualify.py",
                   lambda repo, work: repo / FIXTURE_QUAL / "qualify.py")
    tamper_control("CTRL-27-test-code-overwrites-witness", "witness.py",
                   lambda repo, work: repo / FIXTURE_QUAL / "witness.py")
    tamper_control("CTRL-28-test-code-overwrites-source-lock", "the source lock",
                   lambda repo, work: work / "evidence" / "SOURCE_LOCK.json")
    tamper_control("CTRL-29-test-code-overwrites-evidence", "recorded build evidence",
                   lambda repo, work: work / "evidence" / "BUILD_RESULT.json")

    # Build-time code: an initialize-phase plugin (the reviewed P1 vector).
    name = "CTRL-30-initialize-plugin-overwrites-qualify"
    target = h.tmp / name / "repo" / FIXTURE_QUAL / "qualify.py"
    honest = project({"ProbeTest": FAILING_TEST})
    attacked = project({"ProbeTest": FAILING_TEST}, pom=build_pom(INITIALIZE_PLUGIN.format(target=target)))
    fx = h.fixture(name, honest, attacked)
    digest = sha256_path(target)
    result = h.pipeline(fx)
    unchanged = sha256_path(target) == digest
    rows.append(row(
        name, "red",
        "a candidate plugin bound to initialize cannot overwrite the scorer; the build definition change is caught",
        "FAIL", result, reason="build_definition_changed",
        extra_ok=unchanged and result.get("integrity") == "OK",
        extra={"target_unchanged": unchanged},
    ))

    # Test-bytecode mutation: candidate code rewrites its compiled test class to a
    # passing one after the build. The executed bytecode must still be compiled
    # by trusted code from the locked commit's failing source.
    name = "CTRL-31-test-bytecode-mutation"
    fx = h.fixture(name, project({"ProbeTest": FAILING_TEST}))
    mutated = {}

    def mutate(_h, _fx):
        green_src = h.tmp / name / "green" / "probe" / "ProbeTest.java"
        green_src.parent.mkdir(parents=True)
        green_src.write_text(PASSING_TEST)
        green_out = h.tmp / name / "green-classes"
        subprocess.run(["javac", "-proc:none", "-nowarn", "-cp", h.junit_classpath, "-d", str(green_out),
                        str(green_src)], capture_output=True, check=False)
        staged = h.stage_readonly(green_out, "green-classes")
        dest = h.sandbox_dir / "candidate" / "target" / "test-classes"
        h.as_candidate(h.sandbox_dir, ["/bin/sh", "-c", 'cp -r "$1"/. "$2"/', "c12", str(staged), str(dest)])
        mutated["applied"] = sha256_path(dest / "probe" / "ProbeTest.class") == sha256_path(staged / "probe" / "ProbeTest.class")

    result = h.pipeline(fx, after_build=mutate)
    rows.append(row(
        name, "red",
        "candidate code that replaces its compiled test bytecode with a passing class gains nothing: "
        "the trusted compile of the locked source runs instead",
        "FAIL", result, reason="test_failures",
        extra_ok=mutated.get("applied") is True,
        extra={"mutation_applied": mutated.get("applied")},
    ))

    # Candidate test code forges the driver's witness file in the (candidate-
    # writable) output directory and halts the JVM before the driver writes.
    name = "CTRL-38-test-code-forges-witness"
    forged_path = h.sandbox_dir / "witness-out" / "module-000-_.json"
    forger = FORGER_TEST.format(path=str(forged_path))
    fx = h.fixture(name, project({"ForgerTest": forger}))
    result = h.pipeline(fx)
    rows.append(row(
        name, "red",
        "a witness file written by candidate test code carries no valid MAC and earns nothing",
        "FAIL", result, reason="witness_authentication_failed",
    ))

    # The candidate environment carries no runner handle (GITHUB_ENV etc.).
    name = "CTRL-32-candidate-environment-scrubbed"
    os.environ[CANARY] = "must-not-cross"
    os.environ.setdefault("GITHUB_ENV", str(h.tmp / "github-env-canary"))
    fx = h.fixture(name, project({"EnvProbeTest": ENV_PROBE_TEST}))
    result = h.pipeline(fx)
    rows.append(row(
        name, "positive",
        "candidate code sees only the allowlisted environment: no GITHUB_*/ACTIONS_*/RUNNER_* handle or canary",
        "PASS", result, extra_ok=result.get("integrity") == "OK",
    ))

    # Simulated breaches: what the boundary prevents must also be detected.
    def breach(control, label, mutate_fn, reason):
        fx = h.fixture(control, project({"ProbeTest": PASSING_TEST}))
        result = h.pipeline(fx, after_seal=lambda _h, f: mutate_fn(f))
        rows.append(row(
            control, "red",
            "a trusted-state change after candidate execution ({}) fails the job even if the scorer says PASS".format(label),
            "FAIL", result, reason=reason, extra_ok=result.get("integrity") == "VIOLATION",
        ))

    breach("CTRL-33-breach-scorer-replaced", "scorer replaced by an always-PASS payload",
           lambda f: (f["qual"] / "qualify.py").write_text(ALWAYS_PASS_SCORER.replace("\\n", "\n")),
           "trusted_validator_changed")
    breach("CTRL-34-breach-evidence-rewritten", "sealed source lock rewritten",
           lambda f: (f["evidence"] / "SOURCE_LOCK.json").write_text("{}\n"),
           "sealed_evidence_changed")
    breach("CTRL-35-breach-module-planted", "module planted next to the trusted scripts",
           lambda f: (f["qual"] / "json.py").write_text("raise SystemExit(0)\n"),
           "trusted_validator_changed")

    # A trusted path the sandbox account could write fails closed before any
    # candidate code runs.
    name = "CTRL-36-writable-trusted-path-refused"
    fx = h.fixture(name, project({"ProbeTest": PASSING_TEST}))

    def open_up(_h, f):
        os.chmod(h.tmp, 0o755)
        os.chmod(f["work"].parent, 0o755)
        os.chmod(f["work"], 0o777)

    result = h.pipeline(fx, before_prepare=open_up)
    rows.append(row(
        name, "red",
        "if any trusted path is writable by the sandbox account the sandbox is refused and nothing earns credit",
        "FAIL", result, reason="trusted_path_writable_by_candidate",
        extra_ok=result.get("sandbox_prepared") is False,
    ))
    os.chmod(fx["work"], 0o700)
    os.chmod(h.tmp, 0o700)
    return rows


SKIP_FAILING_EXTENSION = """package probe;

import org.junit.jupiter.api.extension.ConditionEvaluationResult;
import org.junit.jupiter.api.extension.ExecutionCondition;
import org.junit.jupiter.api.extension.ExtensionContext;

public class SkipFailing implements ExecutionCondition {

    @Override
    public ConditionEvaluationResult evaluateExecutionCondition(ExtensionContext context) {
        if (context.getTestMethod().isPresent() && context.getTestMethod().get().getName().startsWith("fails")) {
            return ConditionEvaluationResult.disabled("hidden by candidate configuration");
        }
        return ConditionEvaluationResult.enabled("visible");
    }
}
"""

MIXED_TEST = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class MixedTest {

    @Test
    void passesOne() {
        assertEquals(2, 1 + 1);
    }

    @Test
    void failsOnPurpose() {
        assertEquals(3, 1 + 1);
    }
}
"""

AUTODETECT = "junit.jupiter.extensions.autodetection.enabled=true\n"
EXTENSION_SERVICE = "META-INF/services/org.junit.jupiter.api.extension.Extension"
MAIN_JUPITER_DEPENDENCY = """    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter-api</artifactId>
      <version>5.8.1</version>
    </dependency>
  </dependencies>"""
EVIL_DEPENDENCY = """    <dependency>
      <groupId>c12.evil</groupId>
      <artifactId>skip-failing</artifactId>
      <version>1.0</version>
      <scope>test</scope>
    </dependency>
  </dependencies>"""


def junit_controls(h: Harness) -> list[dict]:
    """P1-A: candidate code cannot reconfigure the trusted JUnit launcher.

    Each route registers an auto-detected Jupiter extension (via
    META-INF/services and junit-platform.properties) that disables the failing
    test method, so a launcher honouring candidate configuration would report
    one passing test and no failure. The driver disables every auto-registration
    and all implicit configuration, so the failing method runs and fails.
    """
    rows: list[dict] = []
    honest = project({"MixedTest": MIXED_TEST})

    def run(control, expectation, candidate):
        fx = h.fixture(control, honest, candidate)
        rows.append(row(control, "red", expectation, "FAIL", h.pipeline(fx), reason="test_failures"))

    via_test_resources = project({"MixedTest": MIXED_TEST}, extra={
        "src/test/java/probe/SkipFailing.java": SKIP_FAILING_EXTENSION,
        "src/test/resources/junit-platform.properties": AUTODETECT,
        "src/test/resources/" + EXTENSION_SERVICE: "probe.SkipFailing\n",
    })
    run("CTRL-60-junit-config-via-test-resources",
        "an extension and configuration shipped in test resources cannot hide a failing test", via_test_resources)

    via_main = project({"MixedTest": MIXED_TEST}, pom=build_pom().replace("  </dependencies>", MAIN_JUPITER_DEPENDENCY, 1),
                       extra={
                           "src/main/java/probe/SkipFailing.java": SKIP_FAILING_EXTENSION,
                           "src/main/resources/junit-platform.properties": AUTODETECT,
                           "src/main/resources/" + EXTENSION_SERVICE: "probe.SkipFailing\n",
                       })
    run("CTRL-61-junit-config-via-main-resources",
        "an extension and configuration shipped in main classes cannot hide a failing test", via_main)

    # Route 3: a newly declared dependency jar (dependency changes pass the audit).
    work = h.tmp / "evil-jar"
    src = work / "src" / "probe"
    src.mkdir(parents=True)
    (src / "SkipFailing.java").write_text(SKIP_FAILING_EXTENSION)
    classes = work / "classes"
    (classes / "META-INF" / "services").mkdir(parents=True)
    (classes / EXTENSION_SERVICE).write_text("probe.SkipFailing\n")
    (classes / "junit-platform.properties").write_text(AUTODETECT)
    m2 = Path(h.seed)
    api = sorted(m2.glob("org/junit/jupiter/junit-jupiter-api/*/junit-jupiter-api-*.jar"))
    extra_cp = sorted(m2.glob("org/apiguardian/apiguardian-api/*/*.jar")) + sorted(m2.glob("org/opentest4j/opentest4j/*/*.jar"))
    compiled = subprocess.run(["javac", "-proc:none", "-nowarn", "-cp", os.pathsep.join(str(p) for p in api + extra_cp),
                               "-d", str(classes), str(src / "SkipFailing.java")], capture_output=True, text=True, check=False)
    jar = work / "jar" / "skip-failing-1.0.jar"
    jar.parent.mkdir()
    packed = subprocess.run(["jar", "cf", str(jar), "-C", str(classes), "."], capture_output=True, text=True, check=False)
    if compiled.returncode != 0 or packed.returncode != 0 or not api:
        rows.append({"control": "CTRL-62-junit-config-via-dependency-jar", "kind": "not_run",
                     "expectation": "needs junit-jupiter-api to build the dependency jar",
                     "observed_verdict": "NOT_RUN", "expected_verdict": "FAIL", "ok": False,
                     "error": (compiled.stderr or packed.stderr)[-400:]})
    else:
        staged = h.stage_readonly(jar.parent, "evil-jar")
        h.install_artifact(staged / jar.name, "c12.evil", "skip-failing", "1.0")
        via_dependency = project({"MixedTest": MIXED_TEST},
                                 pom=build_pom().replace("  </dependencies>", EVIL_DEPENDENCY, 1))
        run("CTRL-62-junit-config-via-dependency-jar",
            "an extension and configuration shipped in a dependency jar cannot hide a failing test", via_dependency)

    # Codex P1 on witness.py:178: a .class test resource must not replace the
    # failing test that trusted javac compiled from the locked source.
    name = "CTRL-66-test-resource-class-overwrite"
    forged = h.tmp / "forged-class"
    (forged / "src" / "probe").mkdir(parents=True)
    (forged / "src" / "probe" / "MixedTest.java").write_text(
        MIXED_TEST.replace("assertEquals(3, 1 + 1)", "assertEquals(2, 1 + 1)"))
    compiled = subprocess.run(
        ["javac", "-proc:none", "-nowarn", "-cp", os.pathsep.join(str(p) for p in api + extra_cp),
         "-d", str(forged / "classes"), str(forged / "src" / "probe" / "MixedTest.java")],
        capture_output=True, text=True, check=False)
    bytecode = forged / "classes" / "probe" / "MixedTest.class"
    if compiled.returncode != 0 or not bytecode.is_file():
        rows.append({"control": name, "kind": "not_run",
                     "expectation": "needs junit-jupiter-api to compile the forged bytecode",
                     "observed_verdict": "NOT_RUN", "expected_verdict": "FAIL", "ok": False,
                     "error": compiled.stderr[-400:]})
    else:
        overwrite = project({"MixedTest": MIXED_TEST},
                            extra={"src/test/resources/probe/MixedTest.class": bytecode.read_bytes()})
        run(name, "a passing MixedTest.class shipped as a test resource cannot replace the failing compiled test",
            overwrite)

    # P1-B: a trusted step must never resolve tools from a candidate-writable
    # PATH entry; prepare and verify both probe every PATH entry.
    name = "CTRL-63-candidate-writable-path-entry-refused"
    fx = h.fixture(name, project({"ProbeTest": PASSING_TEST}))
    evil_bin = h.sandbox_dir / "evil-bin"
    h.as_candidate(h.sandbox_dir, ["/bin/mkdir", "-p", str(evil_bin)])
    result = h.pipeline(fx, trusted_path_prefix=evil_bin)
    rows.append(row(name, "red",
                    "a PATH entry the candidate account can write refuses the sandbox and fails integrity",
                    "FAIL", result, reason="trusted_path_writable_by_candidate",
                    extra_ok=result.get("sandbox_prepared") is False))

    # Review P1: git archive applies the candidate's own .gitattributes. With
    # export-subst, the committed blob fails (2 != 3) while the exported copy
    # passes (1 + 1 + 1); the export must equal the blobs or nothing is built.
    name = "CTRL-67-gitattributes-export-subst-refused"
    substituted = MIXED_TEST.replace(
        "assertEquals(3, 1 + 1);", "assertEquals(3, 1 + 1 /*$Format:%x2a%x2f + 1 /*$*/);"
    )
    fx = h.fixture(name, project({"MixedTest": MIXED_TEST}),
                   project({"MixedTest": substituted}, extra={".gitattributes": "*.java export-subst\n"}))
    result = h.pipeline(fx)
    rows.append(row(name, "red",
                    "an export that differs from the locked blobs (.gitattributes export-subst) is refused",
                    "UNKNOWN", result, reason="differs from its blobs",
                    extra_ok=result.get("sandbox_prepared") is False))
    return rows


def corpus_controls(h: Harness) -> list[dict]:
    """P1-2: the required corpus is anchored to the trusted baseline."""
    rows: list[dict] = []
    base = project(three_tests())

    def run(control, kind, expectation, expected, reason, candidate, **fixture_kwargs):
        fx = h.fixture(control, base if "base" not in fixture_kwargs else fixture_kwargs.pop("base"),
                       candidate, **fixture_kwargs)
        result = h.pipeline(fx)
        rows.append(row(control, kind, expectation, expected, result, reason=reason))
        return result

    run("CTRL-40-corpus-honest", "positive", "an unchanged corpus with a matching baseline qualifies",
        "PASS", None, None)
    run("CTRL-41-mass-rename-leaving-one", "red",
        "renaming most required tests out of the class regex, leaving one green test, is a removal",
        "FAIL", "baseline_test_removed",
        project({"AlphaTest": passing("AlphaTest"), "BetaCheck": passing("BetaCheck"),
                 "GammaCheck": passing("GammaCheck")}))
    run("CTRL-42-delete-required-tests", "red", "deleting required tests is a removal",
        "FAIL", "baseline_test_removed", project({"AlphaTest": passing("AlphaTest")}))
    moved = project({"AlphaTest": passing("AlphaTest"), "GammaTest": passing("GammaTest")},
                    extra={"src/other/java/probe/BetaTest.java": passing("BetaTest")})
    run("CTRL-43-move-outside-test-roots", "red",
        "moving a required test outside every test source root is a removal",
        "FAIL", "baseline_test_removed", moved)
    run("CTRL-44-rename-outside-regex", "red", "renaming one required test outside the class regex is a removal",
        "FAIL", "baseline_test_removed",
        project({"AlphaCheck": passing("AlphaCheck"), "BetaTest": passing("BetaTest"),
                 "GammaTest": passing("GammaTest")}))
    run("CTRL-45-keep-small-green-subset", "red",
        "dropping the failing required test to keep a green subset is a removal, not a PASS",
        "FAIL", "baseline_test_removed",
        project({"AlphaTest": passing("AlphaTest")}),
        base=project(three_tests(GammaTest=failing("GammaTest"))))
    run("CTRL-46-legitimate-addition", "positive",
        "adding a passing test and its baseline entry qualifies, and the addition is required",
        "PASS", None, project(three_tests(DeltaTest=passing("DeltaTest"))))
    run("CTRL-47-addition-without-baseline-update", "red",
        "a candidate whose own baseline does not describe it cannot merge a stale baseline",
        "FAIL", "candidate_corpus_baseline_not_updated",
        project(three_tests(DeltaTest=passing("DeltaTest"))), candidate_baseline="keep")
    approval = [{"entry": ".::probe.BetaTest", "reason": "superseded by AlphaTest", "reference": "review#1"}]
    run("CTRL-48-approved-removal-path", "positive",
        "a removal approved on the default branch first, then performed, qualifies",
        "PASS", None, project(three_tests(BetaTest=None)), approvals=approval)
    run("CTRL-49-removal-without-default-branch-approval", "red",
        "a removal is only approved by the default-branch baseline, never by the candidate's own copy",
        "FAIL", "baseline_test_removed", project(three_tests(BetaTest=None)))
    run("CTRL-50-malformed-baseline", "red", "a malformed trusted baseline is UNKNOWN, never PASS",
        "UNKNOWN", "corpus_baseline_malformed", None, trusted_baseline='{"schema": "nope"}\n')
    run("CTRL-51-missing-baseline", "red", "a missing trusted baseline is UNKNOWN, never PASS",
        "UNKNOWN", "corpus_baseline_missing", None, trusted_baseline=None)
    run("CTRL-52-stale-baseline", "red",
        "a trusted baseline that no longer matches the trusted enumeration is UNKNOWN",
        "UNKNOWN", "corpus_baseline_stale", None,
        trusted_followup=test_file("DeltaTest", passing("DeltaTest")), followup_rebaseline=False)
    run("CTRL-53-candidate-behind-default-branch", "red",
        "a test added to the default branch after the merge base is required; the candidate is told to merge",
        "FAIL", "candidate_behind_default_branch", None,
        trusted_followup=test_file("DeltaTest", passing("DeltaTest")))
    # A trusted producer fault is still authenticated: this full-path control
    # proves the scorer validates counts rather than merely provenance.
    observer = OBSERVER.read_text()
    needle = 'out.append("  \\"tests_failed\\": ").append(testsFailed).append(",\\n");'
    assert observer.count(needle) == 1
    malformed = observer.replace(needle, needle.replace(".append(testsFailed)", ".append(-1)"))
    fx = h.fixture(
        "CTRL-54-parent-negative-counter", project({"ProbeTest": passing("ProbeTest")}),
        trusted_followup={FIXTURE_QUAL + "/TrustedTestObserver.java": malformed},
    )
    result = h.pipeline(fx)
    rows.append(row(
        "CTRL-54-parent-negative-counter", "red",
        "a trusted parent observer fault cannot grant PASS for a negative execution counter",
        "FAIL", result, reason="invalid_execution_counter",
    ))
    malformed = observer.replace(needle, needle.replace(".append(testsFailed)", ".append(-1.0)"))
    fx = h.fixture(
        "CTRL-55-parent-noninteger-module-counter", project({"ProbeTest": passing("ProbeTest")}),
        trusted_followup={FIXTURE_QUAL + "/TrustedTestObserver.java": malformed},
    )
    result = h.pipeline(fx)
    rows.append(row(
        "CTRL-55-parent-noninteger-module-counter", "red",
        "a malformed parent-observed module count must not disappear into a coerced-zero aggregate",
        "FAIL", result, reason="invalid_module_counter",
    ))
    # Codex P1 on corpus_policy.py:132: a class can stay while its methods go.
    ten = project({"ProbeTest": many_methods(10)})
    run("CTRL-56-within-class-method-shrink", "red",
        "deleting nine of ten required methods from a retained class is a removal, not a PASS",
        "FAIL", "baseline_test_method_removed", project({"ProbeTest": many_methods(1)}), base=ten)
    run("CTRL-57-baseline-method-disabled", "red",
        "disabling a required method is a removal unless the default branch approves it",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeTest": many_methods(10, disabled={3})}), base=ten)
    run("CTRL-58-baseline-method-renamed", "red", "renaming a required method is a removal",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeTest": many_methods(10).replace("test7()", "renamed7()")}), base=ten)
    # The static reading still sees @Test, but the annotation is the candidate's
    # own: nine required methods never run, and only the driver can tell.
    evasive = many_methods(10).replace(
        "import org.junit.jupiter.api.Test;", "import probe.Test;"
    ).replace("@Test public void test0()", "@org.junit.jupiter.api.Test public void test0()")
    run("CTRL-59-required-method-never-started", "red",
        "a required method the static reading accepts but the launcher never starts earns no credit",
        "FAIL", "required_test_methods_not_started",
        project({"ProbeTest": evasive}, extra={"src/main/java/probe/Test.java": FAKE_TEST_ANNOTATION}),
        base=ten)
    run("CTRL-64-approved-method-removal", "positive",
        "a method removal approved on the default branch first, then performed, qualifies",
        "PASS", None, project({"ProbeTest": many_methods(9)}), base=ten,
        approvals=[{"entry": ".::probe.ProbeTest#test9()", "reason": "duplicate of test8", "reference": "review#2"}])
    run("CTRL-65-method-addition-required", "positive",
        "adding methods to a retained class qualifies when they pass and the baseline lists them",
        "PASS", None, project({"ProbeTest": many_methods(12)}), base=ten)
    # Review P2 on witness.py:407: a concrete class that only inherits its tests
    # (Mage's SmoothedLondonMulliganTest) must still run them, and be entered.
    inherited = project({"ProbeTest": HOOKED_BASE_TEST, "SubProbeTest": hooked_subclass(1)})
    run("CTRL-68-inherited-tests-run", "positive",
        "a class that only inherits its tests is run, entered and credited",
        "PASS", None, inherited, base=inherited)
    run("CTRL-69-inherited-test-regression", "red",
        "a regression only an inheriting class exposes fails qualification",
        "FAIL", "test_failures",
        project({"ProbeTest": HOOKED_BASE_TEST, "SubProbeTest": hooked_subclass(2)}), base=inherited)
    run("CTRL-70-inheriting-class-made-abstract", "red",
        "making a trusted inheriting class abstract does not stop it being owed",
        "FAIL", ["required_tests_never_entered", "required_pairs_not_entered"],
        project({"ProbeTest": HOOKED_BASE_TEST, "SubProbeTest": hooked_subclass(1, abstract=True)}),
        base=inherited)
    nested = """package probe;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Nested;
public class ProbeTest {
  @Nested class Left { @Test public void proof() {} }
  @Nested class Right { @Test public void proof() {} }
}
"""
    run("CTRL-71-nested-same-name-positive", "positive",
        "both nested declarations are independently required and actually started",
        "PASS", None, project({"ProbeTest": nested}), base=project({"ProbeTest": nested}))
    run("CTRL-72-nested-same-name-removal", "red",
        "deleting one same-named nested method cannot retain the other's credit",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeTest": nested.replace("  @Nested class Right { @Test public void proof() {} }\n", "")}),
        base=project({"ProbeTest": nested}))
    run("CTRL-73-nested-same-name-disabled", "red",
        "disabling one nested test cannot be masked by another nested declaration",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeTest": nested.replace("class Right { @Test", "class Right { @org.junit.jupiter.api.Disabled @Test")}),
        base=project({"ProbeTest": nested}))
    overloads = """package probe;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
public class ProbeTest {
  @ParameterizedTest @ValueSource(ints={1}) void proof(int value) {}
  @ParameterizedTest @ValueSource(strings={"one"}) void proof(java.lang.String value) {}
}
"""
    run("CTRL-74-overloaded-signature-positive", "positive",
        "overloaded parameterized tests have distinct runtime-bound signatures",
        "PASS", None, project({"ProbeTest": overloads}), base=project({"ProbeTest": overloads}))
    run("CTRL-75-overloaded-signature-removal", "red",
        "one surviving overloaded test cannot replace a removed signature",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeTest": overloads.replace('  @ParameterizedTest @ValueSource(strings={"one"}) void proof(java.lang.String value) {}\n', '')}),
        base=project({"ProbeTest": overloads}))
    qualified = """package probe;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
public class ProbeTest {
 @ParameterizedTest @MethodSource("arguments") void proof(one.Foo value) {}
 static java.util.stream.Stream<one.Foo> arguments() { return java.util.stream.Stream.of(new one.Foo()); }
}
"""
    extra = {"src/main/java/one/Foo.java": "package one; public class Foo {}",
             "src/main/java/two/Foo.java": "package two; public class Foo {}"}
    qualified_base = project({"ProbeTest": qualified}, extra=extra)
    run("CTRL-76-qualified-parameter-positive", "positive",
        "the exact qualified parameter declaration is required and actually started",
        "PASS", None, qualified_base, base=qualified_base)
    run("CTRL-77-qualified-parameter-replacement", "red",
        "replacing one.Foo with two.Foo cannot supply the previous test's identity",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeTest": qualified.replace("one.Foo", "two.Foo")}, extra=extra), base=qualified_base)
    for spelling in ("Foo", "T", "String"):
        try:
            corpus_policy.java_test_methods("class ProbeTest { @Test void proof(" + spelling + " value) {} }")
            refused = False
        except corpus_policy.CorpusError as exc:
            refused = "unresolved parameter type" in str(exc)
        rows.append({"control": "CTRL-78-unresolved-parameter-refused-" + spelling, "kind": "red",
                     "expectation": "import or bound resolution is never guessed",
                     "expected_verdict": "REFUSED", "observed_verdict": "REFUSED" if refused else "ACCEPTED",
                     "ok": refused})
    # A JUnit 4 test named like an inherited public helper (Mage's
    # AlpineHoundmasterTest#attack() next to CardTestPlayerAPIImpl's
    # attack(int, TestPlayer, String)): JUnit Vintage reports it without a
    # MethodSource, and it must still count as started under its own identity.
    junit4_pom = build_pom().replace(
        "<groupId>org.junit.jupiter</groupId>\n      <artifactId>junit-jupiter</artifactId>\n      <version>5.8.1</version>",
        "<groupId>junit</groupId>\n      <artifactId>junit</artifactId>\n      <version>4.13.2</version>", 1)
    helper = """package probe;
public class ProbeBase {
  public void attack(int turn, String attacker) {}
}
"""
    overloaded = """package probe;
import org.junit.Test;
public class ProbeTest extends ProbeBase {
  @Test public void attack() {}
  @Test public void proof() {}
}
"""
    overloaded_base = project({"ProbeBase": helper, "ProbeTest": overloaded}, pom=junit4_pom)
    run("CTRL-79-junit4-overloaded-name-positive", "positive",
        "a JUnit 4 test overloaded by an inherited helper is identified and actually started",
        "PASS", None, overloaded_base, base=overloaded_base)
    run("CTRL-80-junit4-overloaded-name-removal", "red",
        "the inherited helper of the same name cannot stand in for a removed test",
        "FAIL", "baseline_test_method_removed",
        project({"ProbeBase": helper, "ProbeTest": overloaded.replace("  @Test public void attack() {}\n", "")},
                pom=junit4_pom),
        base=overloaded_base)

    # Vintage can report arbitrary runner descriptions without a typed source.
    # Exercise the complete build/compile/launch/aggregate/enforce path, rather
    # than constructing a diagnostic mapping in Python.
    log_probe = """package probe;
import org.junit.Test;
import org.junit.runner.RunWith;
@RunWith(ProbeRunner.class)
public class ProbeTest { @Test public void proof() {} }
"""
    log_runner = r"""package probe;
import org.junit.runner.Runner;
import org.junit.runner.Description;
import org.junit.runner.notification.RunNotifier;
import org.junit.runner.notification.Failure;
public class ProbeRunner extends Runner {
 public ProbeRunner(Class<?> cls) {}
 private Description bad() { return Description.createSuiteDescription("candidate\n::notice::FORGED-C12-LOG"); }
 public Description getDescription() {
  Description root = Description.createSuiteDescription(ProbeTest.class);
  root.addChild(bad()); return root;
 }
 public void run(RunNotifier n) {
  Description d = bad(); n.fireTestStarted(d);
  n.fireTestFailure(new Failure(d, new AssertionError("failed")));
  n.fireTestFinished(d);
 }
}
"""
    fx = h.fixture("CTRL-81-candidate-log-command-refused",
                   project({"ProbeTest": log_probe, "ProbeRunner": log_runner}, pom=junit4_pom))
    result = h.pipeline(fx)
    output = result.get("witness_stdout", "")
    safe = ("FORGED-C12-LOG" in output and "\\n::notice::" in output
            and all(line.startswith("TRUSTED_WITNESS ") for line in output.splitlines())
            and all(line.startswith("QUALIFICATION = ") for line in result.get("qualify_stdout", "").splitlines()))
    rows.append(row("CTRL-81-candidate-log-command-refused", "red",
                    "a real malicious runner failure stays FAIL and cannot inject workflow commands",
                    "FAIL", result, reason="required_test_methods_not_started", extra_ok=safe))
    fx = h.fixture("CTRL-82-ordinary-failure-diagnostic", project({"ProbeTest": FAILING_TEST}))
    result = h.pipeline(fx)
    output = result.get("witness_stdout", "")
    safe = ('non-successful: ".::probe.ProbeTest" x1' in output
            and all(line.startswith("TRUSTED_WITNESS ") for line in output.splitlines())
            and all(line.startswith("QUALIFICATION = ") for line in result.get("qualify_stdout", "").splitlines()))
    rows.append(row("CTRL-82-ordinary-failure-diagnostic", "red",
                    "an ordinary real failing test keeps a useful single-line diagnostic",
                    "FAIL", result, reason="test_failures", extra_ok=safe))
    return rows



def containment_controls(h: Harness) -> list[dict]:
    """Hostile candidate bytecode executes, but never owns qualification authority."""
    rows: list[dict] = []

    benign = """package probe;
public final class Attack {
 public static boolean reflectionBlocked() { return true; }
 public static boolean observerHidden() { return true; }
 public static boolean channelBlocked() { return true; }
 public static boolean processBlocked() { return true; }
 public static boolean fdDiscoveryBlocked() { return true; }
 public static boolean hookBlocked() { return true; }
 public static boolean nativeLoadBlocked() { return true; }
 public static boolean managerRemovalBlocked() { return true; }
 public static boolean exitBlocked() { return true; }
 public static boolean noAuthoritySecrets() { return true; }
}
"""
    test = """package probe;
import static org.junit.jupiter.api.Assertions.assertTrue;
import org.junit.jupiter.api.Test;
public class ProbeTest {
 @Test public void reflection() { assertTrue(Attack.reflectionBlocked()); }
 @Test public void observer() { assertTrue(Attack.observerHidden()); }
 @Test public void channel() { assertTrue(Attack.channelBlocked()); }
 @Test public void process() { assertTrue(Attack.processBlocked()); }
 @Test public void fds() { assertTrue(Attack.fdDiscoveryBlocked()); }
 @Test public void hook() { assertTrue(Attack.hookBlocked()); }
 @Test public void nativeLoad() { assertTrue(Attack.nativeLoadBlocked()); }
 @Test public void manager() { assertTrue(Attack.managerRemovalBlocked()); }
 @Test public void exit() { assertTrue(Attack.exitBlocked()); }
 @Test public void secrets() { assertTrue(Attack.noAuthoritySecrets()); }
}
"""
    hostile = r"""package probe;
import java.lang.management.ManagementFactory;
import java.lang.reflect.Method;
import java.net.Socket;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Map;

public final class Attack {
 private static boolean blocked(Throwing action) {
  try { action.run(); return false; }
  catch (SecurityException | ReflectiveOperationException | java.io.IOException exc) { return true; }
  catch (RuntimeException exc) { return true; }
 }
 @FunctionalInterface private interface Throwing { void run() throws Exception; }

 public static boolean reflectionBlocked() {
  return blocked(() -> {
   Class<?> type = Class.forName("c12.trusted.TrustedTestDriver");
   Method hook = type.getDeclaredMethod("observerComplete");
   hook.setAccessible(true);
   hook.invoke(null);
  });
 }
 public static boolean observerHidden() {
  try { Class.forName("TrustedTestObserver"); return false; }
  catch (ClassNotFoundException expected) { return true; }
 }
 public static boolean channelBlocked() {
  String address = null;
  for (String arg : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
   int p = arg.indexOf("address=");
   if (p >= 0) {
    address = arg.substring(p + 8);
    int comma = address.indexOf(',');
    if (comma >= 0) address = address.substring(0, comma);
   }
  }
  if (address == null || address.isEmpty()) return false;
  final String addr = address;
  return blocked(() -> {
   String host = "127.0.0.1";
   String portText = addr;
   int colon = addr.lastIndexOf(':');
   if (colon >= 0) { host = addr.substring(0, colon); portText = addr.substring(colon + 1); }
   try (Socket ignored = new Socket(host, Integer.parseInt(portText))) { }
  });
 }
 public static boolean processBlocked() {
  return blocked(() -> new ProcessBuilder("/bin/true").start());
 }
 public static boolean fdDiscoveryBlocked() {
  return blocked(() -> { try (java.util.stream.Stream<java.nio.file.Path> ignored =
      Files.list(Paths.get("/proc/self/fd"))) { ignored.count(); } });
 }
 public static boolean hookBlocked() {
  return blocked(() -> Runtime.getRuntime().addShutdownHook(new Thread(() -> {})));
 }
 public static boolean nativeLoadBlocked() {
  return blocked(() -> System.loadLibrary("c12_candidate_escape_probe"));
 }
 @SuppressWarnings("removal")
 public static boolean managerRemovalBlocked() {
  return blocked(() -> System.setSecurityManager(null));
 }
 public static boolean exitBlocked() {
  return blocked(() -> System.exit(0));
 }
 public static boolean noAuthoritySecrets() {
  for (Map.Entry<String,String> e : System.getenv().entrySet()) {
   String k = e.getKey().toUpperCase(java.util.Locale.ROOT);
   if (k.contains("WITNESS") || k.contains("RECEIPT") || k.contains("SECRET") || k.contains("TOKEN")) return false;
  }
  for (String arg : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
   if (arg.contains("observer-receipts") || arg.contains("TRUSTED_WITNESS")) return false;
  }
  return System.getProperty("c12.receipt") == null && System.getProperty("c12.witness.key") == null;
 }
}
"""
    base = project({"ProbeTest": test}, extra={"src/main/java/probe/Attack.java": benign})
    candidate = project({"ProbeTest": test}, extra={"src/main/java/probe/Attack.java": hostile})
    fx = h.fixture("CTRL-84-hostile-bytecode-contained", base, candidate)
    result = h.pipeline(fx)
    rows.append(row(
        "CTRL-84-hostile-bytecode-contained", "positive",
        "hostile candidate production bytecode can execute but reflection, authority discovery, channel reuse, process/socket/fd/native/shutdown/exit escape paths are denied",
        "PASS", result, extra_ok=result.get("credit") is True,
    ))

    # Candidate test source preserves the method identity but weakens a failing
    # assertion. C12 must still run the trusted default-branch assertion and fail.
    trusted_failing = """package probe;
import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;
public class ProbeTest { @Test public void proof() { assertEquals(3, 1 + 1); } }
"""
    candidate_passing = trusted_failing.replace("assertEquals(3, 1 + 1)", "assertEquals(2, 1 + 1)")
    fx = h.fixture(
        "CTRL-85-candidate-test-weakening-no-credit",
        project({"ProbeTest": trusted_failing}),
        project({"ProbeTest": candidate_passing}),
    )
    result = h.pipeline(fx)
    rows.append(row(
        "CTRL-85-candidate-test-weakening-no-credit", "red",
        "candidate-edited test assertions never replace the trusted baseline test bytecode",
        "FAIL", result, reason="test_failures",
    ))

    # A candidate-added green test is delta-visible, but it cannot increase the
    # authoritative execution set or manufacture credit.
    one = project({"ProbeTest": PASSING_TEST})
    two = project({"ProbeTest": PASSING_TEST, "AddedTest": passing("AddedTest")})
    fx = h.fixture("CTRL-86-candidate-added-test-no-credit", one, two)
    result = h.pipeline(fx)
    rows.append(row(
        "CTRL-86-candidate-added-test-no-credit", "positive",
        "candidate-added test bytecode contributes zero trusted witness credit",
        "PASS", result,
        extra_ok=result.get("classes_entered") == 1 and result.get("required_selected") == 1,
    ))

    return rows


def legacy_controls(h: Harness) -> list[dict]:
    """The report-forgery, suppression, binding and witness controls, on the new pipeline."""
    rows: list[dict] = []
    honest = project({"ProbeTest": PASSING_TEST})

    def run(control, kind, expectation, expected, reason, base, candidate=None, **pipeline_kwargs):
        fx = h.fixture(control, base, candidate)
        rows.append(row(control, kind, expectation, expected, h.pipeline(fx, **pipeline_kwargs), reason=reason))

    run("CTRL-01-honest-execution", "positive",
        "an honest candidate whose tests the trusted launcher actually runs earns credit", "PASS", None, honest)
    forged_pom = build_pom(extra=ANTRUN_FORGE.format(phase="test"))
    forged = dict(project({"ProbeTest": PASSING_TEST}, pom=forged_pom))
    forged["forged/TEST-probe.ForgedTest.xml"] = FORGED_REPORT
    run("CTRL-02-forged-evidence-zero-execution", "red",
        "a candidate lifecycle hook that fabricates green reports earns no credit", "FAIL",
        "test_execution_definition_altered", honest, forged)
    failing_forged = dict(project({"ProbeTest": FAILING_TEST}, pom=forged_pom))
    failing_forged["forged/TEST-probe.ForgedTest.xml"] = FORGED_REPORT
    run("CTRL-03-real-failure-plus-forged-evidence", "red",
        "a real failing test plus forged green XML is a FAIL", "FAIL", "test_failures",
        project({"ProbeTest": FAILING_TEST}), failing_forged)
    copied = dict(project({"ProbeTest": UNCOMPILABLE_TEST}))
    copied["src/test/resources/TEST-probe.ForgedTest.xml"] = FORGED_REPORT
    run("CTRL-04-copied-report-no-trusted-provenance", "red",
        "a copied report grants nothing without trusted execution provenance", "FAIL",
        "candidate_build_failed", honest, copied)
    suppressed = build_pom().replace(
        "          <useFile>false</useFile>\n        </configuration>",
        "          <useFile>false</useFile>\n          <skipTests>true</skipTests>\n"
        "          <excludes>\n            <exclude>**/*</exclude>\n          </excludes>\n        </configuration>",
    )
    run("CTRL-05-hardcoded-surefire-suppression", "red",
        "hardcoded surefire suppression still fails qualification", "FAIL", "test_execution_definition_altered",
        honest, project({"ProbeTest": PASSING_TEST}, pom=suppressed))
    run("CTRL-06-all-tests-disabled", "red", "a candidate whose only tests are @Disabled earns no credit",
        "FAIL", ["all_tests_skipped", "no_enabled_required_test_methods"], project({"ProbeTest": DISABLED_TEST}))
    run("CTRL-07-no-required-tests", "red", "a candidate with no required test class is UNKNOWN, never PASS",
        "UNKNOWN", "no required test class", project({}))
    run("CTRL-08-malformed-witness", "red", "malformed witness evidence is never PASS", "UNKNOWN",
        "input_unusable", honest, corrupt_witness=True)
    run("CTRL-09-source-binding-mismatch", "red",
        "a sandbox holding a tree other than the locked candidate is never PASS", "UNKNOWN",
        "witness_unavailable", honest, lock_candidate_sha=OTHER_SHA)
    return rows


def module_controls(h: Harness) -> list[dict]:
    rows: list[dict] = []
    helper_dir = h.tmp / "helper"
    helper_jar = Path(build_helper_jar(helper_dir))
    jar_dir = helper_dir / "jar"
    jar_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(helper_jar, jar_dir / helper_jar.name)
    staged = h.stage_readonly(jar_dir, "helper")
    h.install_artifact(staged / helper_jar.name, HELPER_GROUP, HELPER_ARTIFACT, HELPER_VERSION)

    multi = {}
    multi.update(project({"ModuleATest": MODULE_A_TEST}, module="modA"))
    multi.update(project({"ModuleBTest": MODULE_B_TEST}, pom=POM_WITH_HELPER, module="modB"))
    both = ["modA", "modB"]

    def run(control, kind, expectation, expected, reason, files, modules, extra_check=None, **kwargs):
        fx = h.fixture(control, files)
        result = h.pipeline(fx, build_modules=modules, **kwargs)
        extra_ok = extra_check(result) if extra_check else True
        rows.append(row(control, kind, expectation, expected, result, reason=reason, extra_ok=extra_ok))

    run("CTRL-18-multi-module-execution", "positive",
        "two modules with different test classpaths both execute and aggregate honestly",
        "PASS", None, multi, both)
    run("CTRL-19-module-only-dependency-entered", "positive",
        "a required class whose dependency exists only on its own module classpath is actually entered",
        "PASS", None, multi, both, extra_check=lambda r: (r.get("classes_entered"), r.get("required_selected")) == (2, 2))

    def drop(module):
        def override(_h, _fx, mapping):
            mapping.pop(module, None)
            return mapping
        return override

    run("CTRL-20-missing-module-classpath", "red",
        "a required module whose classpath was not resolved cannot be silently skipped",
        "UNKNOWN", "module_classpath_missing", multi, both, classpath_override=drop("modB"))

    def without_helper(_h, _fx, mapping):
        mapping["modB"] = os.pathsep.join(e for e in mapping.get("modB", "").split(os.pathsep) if "only-on-b" not in e)
        return mapping

    run("CTRL-21-unresolved-module-dependency", "red",
        "a required class that cannot resolve on its module classpath earns no credit and is not skipped",
        "FAIL", "required_tests_not_compiled", multi, both, classpath_override=without_helper)

    with_c = dict(multi)
    with_c.update(project({"ModuleCTest": MODULE_C_TEST}, module="modC"))
    run("CTRL-22-sibling-cannot-mask-failure", "red",
        "one genuinely failing module is not masked by successful sibling modules",
        "FAIL", "test_failures", with_c, ["modA", "modB", "modC"],
        extra_check=lambda r: set(r.get("modules_with_witness") or []) >= {"modA", "modB", "modC"})

    partial = {}
    partial.update(project({"ModuleATest": MODULE_A_TEST}, module="modA"))
    partial.update(project({"ModuleBTest": MODULE_B_USES_MAIN}, module="modB",
                           extra={"modB/src/main/java/probe/LibB.java": LIB_B_SOURCE}))

    def unbuilt_b(_h, _fx, mapping):
        mapping.setdefault("modB", "")
        return mapping

    run("CTRL-23-partial-aggregation-not-pass", "red",
        "a module that cannot be built and compiled cannot be aggregated into PASS",
        "FAIL", "required_tests_not_compiled", partial, ["modA"], classpath_override=unbuilt_b)

    collision = {}
    collision.update(project({"SharedTest": SHARED_TEST}, module="modA"))
    collision.update(project({"SharedTest": DIVERGENT_SOURCE}, module="modB"))

    def sibling_tests(_h, _fx, mapping):
        mapping["modB"] = os.pathsep.join(
            [str(h.sandbox_dir / "candidate" / "modA" / "target" / "test-classes"), mapping.get("modB", "")])
        return mapping

    run("CTRL-24-required-class-not-credited-from-sibling", "red",
        "a required class present only in another module's output cannot be credited",
        "FAIL", "required_tests_not_compiled", collision, ["modA", "modB"], classpath_override=sibling_tests)

    empty = {}
    empty.update(project({"ModuleATest": MODULE_A_TEST}, module="modA"))
    empty.update(project({"Helper": "package probe;\n\npublic final class Helper {\n}\n"}, module="modEmpty"))
    run("CTRL-25-zero-required-classes-no-credit", "positive",
        "a module with zero required classes contributes nothing and cannot fabricate credit",
        "PASS", None, empty, ["modA", "modEmpty"],
        extra_check=lambda r: r.get("modules_with_witness") == ["modA"])

    dollar = project({"DollarTest": passing("DollarTest")}, module="mod$dollar")
    run("CTRL-83-dollar-module-owner-positive", "positive",
        "a legal dollar sign in a Maven module path is preserved when deriving a method owner",
        "PASS", None, dollar, ["mod$dollar"],
        extra_check=lambda r: r.get("modules_with_witness") == ["mod$dollar"])
    return rows


MODULE_B_USES_MAIN = """package probe;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ModuleBTest {

    @Test
    void usesItsOwnMainClass() {
        assertEquals(5, LibB.five());
    }
}
"""

LIB_B_SOURCE = """package probe;

public final class LibB {

    private LibB() {
    }

    public static int five() {
        return 5;
    }
}
"""


def build_helper_jar(workdir: Path) -> str:
    """Build a jar only module B may depend on (installed later as the sandbox account)."""
    src = workdir / "helpersrc" / "helper"
    src.mkdir(parents=True, exist_ok=True)
    (src / "OnlyOnB.java").write_text(HELPER_SOURCE)
    classes = workdir / "helperclasses"
    classes.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["javac", "-proc:none", "-nowarn", "-d", str(classes), str(src / "OnlyOnB.java")],
                          capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError("helper javac failed: {}".format(proc.stderr[:500]))
    jar = workdir / HELPER_JAR_NAME
    jar_proc = subprocess.run(["jar", "cf", str(jar), "-C", str(classes), "helper"],
                              capture_output=True, text=True, check=False)
    if jar_proc.returncode != 0:
        raise RuntimeError("helper jar failed: {}".format(jar_proc.stderr[:500]))
    return str(jar)


def static_controls() -> list[dict]:
    rows: list[dict] = []

    text = WORKFLOW.read_text() if WORKFLOW.is_file() else ""
    problems = []
    if not text:
        problems.append("trusted workflow file is missing")
    for required in (
        "pull_request_target",
        "persist-credentials: false",
        "contents: read",
        "SOURCE_LOCK.json",
        "BUILD_DEFINITION_AUDIT.json",
        "SANDBOX_PREPARE.json",
        "BUILD_RESULT.json",
        "MODULE_CLASSPATHS.json",
        "TRUSTED_WITNESS.json",
        "INTEGRITY.json",
        "QUALIFICATION_EVIDENCE.json",
        'sandbox.py" prepare',
        'sandbox.py" run',
        'sandbox.py" verify',
        "--integrity",
        "INTEGRITY_EXIT",
        'bin/mvn" -B test-compile dependency:build-classpath',
        "-Dmaven.compiler.proc=none",
        "--harden-world-writable",
        "--stage-jdk",
        "--stage-maven",
        'export PATH="$C12_TRUSTED_PATH"',
        "shell: /usr/bin/bash --noprofile --norc {0}",
    ):
        if required not in text:
            problems.append("trusted workflow is missing {!r}".format(required))
    for forbidden in (
        "--candidate-ref",
        "continue-on-error",
        "secrets.",
        "pull-requests: write",
        "path: candidate",
        "working-directory",
    ):
        if forbidden in text:
            problems.append("trusted workflow contains forbidden {!r}".format(forbidden))
    for line in text.splitlines():
        stripped = line.strip()
        if "python3" in stripped and "$QUALIFICATION_DIR" in stripped and not stripped.startswith("/usr/bin/python3 -I -S -B "):
            problems.append("trusted script not run as /usr/bin/python3 -I -S -B: {}".format(stripped[:80]))
        if re.search(r"(^|[\s;&|(])mvn\s+-", stripped) and "dependency:get" not in stripped and not stripped.startswith("-- mvn "):
            problems.append("Maven invoked outside the sandbox: {}".format(stripped[:80]))
    rows.append(
        {
            "control": "CTRL-15-workflow-contract",
            "kind": "red",
            "expectation": "candidate code runs only through the sandbox; integrity and verdict are enforced independently; no credentials",
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

    # The executed test bytecode must never be the candidate's build output.
    leaks = []
    try:
        witness_tree = ast.parse(WITNESS.read_text(), str(WITNESS))
        for node in ast.walk(witness_tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and "test-classes" in node.value:
                if not (node.value.strip().startswith(("Produce", "Trust")) or "\n" in node.value):
                    leaks.append("witness.py names candidate test-classes: {!r}".format(node.value[:60]))
    except (OSError, SyntaxError) as exc:
        leaks.append("witness.py unreadable: {}".format(exc))
    rows.append(
        {
            "control": "CTRL-37-no-candidate-test-bytecode",
            "kind": "red",
            "expectation": "witness.py never points execution at the candidate's target/test-classes",
            "expected_verdict": "PASS",
            "observed_verdict": "FAIL" if leaks else "PASS",
            "reasons": leaks,
            "ok": not leaks,
        }
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maven", default="mvn")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--sandbox-user", default=sandbox.CANDIDATE_USER)
    parser.add_argument("--harden-world-writable", action="store_true",
                        help="hosted runners: remove o+w from non-sticky world-writable directories first")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    if args.harden_world_writable:
        print("hardened: {}".format(", ".join(sandbox.harden_world_writable()) or "nothing to harden"))

    tmp = Path(tempfile.mkdtemp(prefix="mage-c12-selftest-"))
    harness = Harness(tmp, args.maven, args.offline, discover_junit_classpath(), args.sandbox_user)
    families = (
        ("legacy", legacy_controls),
        ("module", module_controls),
        ("trust", trust_controls),
        ("junit", junit_controls),
        ("corpus", corpus_controls),
        ("containment", containment_controls),
    )
    try:
        results = list(static_controls()) + source_lock_controls(tmp)
        available, reason = toolchain_available(harness)
        for family, runner in families:
            if not available:
                results.append({
                    "control": "{}-controls".format(family),
                    "kind": "not_run",
                    "expectation": "control family needs a real Maven/JDK toolchain and the sandbox: {}".format(reason),
                    "observed_verdict": "NOT_RUN",
                    "expected_verdict": "RUN",
                    "ok": False,
                })
                continue
            try:
                results += runner(harness)
            except Exception as exc:  # a crashed family is a failed family, never a skipped one
                results.append({
                    "control": "{}-controls".format(family),
                    "kind": "error",
                    "expectation": "control family must run to completion",
                    "observed_verdict": "ERROR",
                    "expected_verdict": "RUN",
                    "error": "{}: {}".format(type(exc).__name__, exc),
                    "ok": False,
                })
    finally:
        harness.cleanup()
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
        "sandbox_user": args.sandbox_user,
        "controls_total": len(results),
        "controls_passed": len(passed),
        "controls_failed": len(failed),
        "controls_not_run": len(not_run),
        "positive_controls": sum(1 for r in results if r.get("kind") == "positive"),
        "red_controls": sum(1 for r in results if r.get("kind") == "red"),
        "maven": {"command": args.maven, "offline": args.offline},
        "results": results,
    }
    print("== Mage C12 trusted qualification gate controls ==")
    for item in results:
        print("[{}] {:<52} {:<9} expected={:<8} observed={}".format(
            "ok  " if item.get("ok") else "FAIL", item.get("control"), item.get("kind"),
            item.get("expected_verdict"), item.get("observed_verdict")))
        if not item.get("ok"):
            print("        expectation: {}".format(item.get("expectation")))
            for key in ("reasons", "witness_notes", "error", "sandbox_error", "witness_stderr"):
                if item.get(key):
                    print("        {}: {}".format(key, json.dumps(item[key], ensure_ascii=True)[:700]))
    print("SELFTEST = {} ({}/{} controls ok, {} not run)".format(status, len(passed), len(results), len(not_run)))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
