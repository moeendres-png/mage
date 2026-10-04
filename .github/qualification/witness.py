#!/usr/bin/env python3
"""Produce the trusted execution witness for an exact candidate SHA, per module.

Trust boundary: this script, ``corpus_policy.py``, ``sandbox.py``,
``build_definition_audit.py`` and ``TrustedTestDriver.java`` are trusted
default-branch source. Nothing here reads a candidate-produced test report, and
no candidate-authored artifact can become qualification credit.

What the candidate controls, and what it does not
-------------------------------------------------
* The required corpus is NOT the candidate's to choose. ``corpus_policy`` reads
  the trusted baseline at the trusted validator commit and the candidate's
  enumeration from Git objects of the locked SHA; removing, renaming or moving a
  baseline test without a default-branch approval is a FAIL.
* Neither are the required test methods: the baseline also binds each enabled
  test method, and ``qualify.py`` requires the driver to report every one of
  them started.
* The executed test bytecode is NOT the candidate's build output. Test sources
  are exported from the locked commit through Git and compiled here, by trusted
  code, with annotation processing disabled (``-proc:none``), so no candidate
  code runs during that compilation and a build that rewrites
  ``target/test-classes`` changes nothing that executes. Test resources are
  copied next to that bytecode without any ``.class`` file, and the compiled
  classes are verified byte-identical afterwards.
* Candidate code that must run (its main classes and its tests) runs only as
  the separate sandbox account, which cannot write any trusted path; every
  candidate process is killed after each module and the kill is verified.

Per-module execution mirrors surefire: required classes are grouped by module,
every module that owns required classes must have a resolved classpath (else
the witness fails closed), the driver runs once per module with that module's
classpath, verifies each executed class loaded from the trusted-compiled output
for that module, and results are aggregated only here.

The classpath map is candidate-influenced *input*: it can change which
dependency class loads, never which test bytecode runs, whether a required
class counts as executed, or the verdict rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import select
import tempfile
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Trusted code never resolves tools from the inherited PATH (see sandbox.TOOL_PATH).
GIT = shutil.which("git", path="/usr/sbin:/usr/bin:/sbin:/bin") or "/usr/bin/git"

sys.path.append(str(Path(__file__).resolve().parent))
import corpus_policy  # noqa: E402
import sandbox  # noqa: E402

SCHEMA = "mage.candidate-qualification.witness/6"
WITNESS_SCHEMA = "mage.candidate-qualification.trusted-execution-witness/4"
DRIVER = "TrustedTestDriver.java"
OBSERVER = "TrustedTestObserver.java"
MAIN_CLASSES_DIR = "target/classes"
TEST_SOURCE_DIRS = ("src/test/java",)
TEST_RESOURCE_DIRS = ("src/test/resources",)

# Maven's own artifacts, as installed in the local repository. Resolving a
# sibling module from an installed jar means executing code that is NOT the
# candidate's, and the Maven cache can make such a jar silently stale. These
# entries are dropped and replaced by the candidate's own reactor output.
STALE_SIBLING_MARKERS = ("/org/mage/",)

# Re-exported for callers that still import the rule from here.
TEST_CLASS_RE = corpus_policy.TEST_CLASS_RE
SOURCE_DIR_MARKERS = corpus_policy.SOURCE_DIR_MARKERS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jdk_tool(name: str) -> str:
    """java/javac from the staged trusted JDK (JAVA_HOME), never a PATH lookup."""
    home = os.environ.get("JAVA_HOME", "")
    candidate = Path(home) / "bin" / name if home else None
    if candidate and candidate.is_file():
        return str(candidate)
    found = shutil.which(name, path="/usr/sbin:/usr/bin:/sbin:/bin")
    if not found:
        raise RuntimeError("{} not found in JAVA_HOME or system directories".format(name))
    return found


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def read_parent_receipt(path: Path):
    """Read the receipt written by the trusted parent observer.

    The path is under the trusted witness work directory, not the candidate
    sandbox. The candidate OS identity cannot write it and the candidate JVM
    receives neither the path nor any receipt authority.
    """
    try:
        if path.is_symlink() or not path.is_file():
            return None, "trusted_parent_produced_no_receipt"
        return json.loads(path.read_text()), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "trusted_parent_receipt_unparseable"

def sanitize_classpath(module: str, resolved: str, candidate_root: Path, all_modules: list[str],
                       candidate_home: Path, trusted_maven_repo: Path):
    """Use candidate main output but only trusted-parent copies of dependencies."""
    dropped: list[str] = []
    kept: list[str] = []
    missing_trusted: list[str] = []
    candidate_repo = (candidate_home / ".m2" / "repository").resolve()
    trusted_repo = trusted_maven_repo.resolve()
    for entry in (resolved or "").split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        if any(marker in entry.replace("\\", "/") for marker in STALE_SIBLING_MARKERS):
            dropped.append(entry)
            continue
        path = Path(entry).resolve()
        try:
            rel = path.relative_to(candidate_repo)
        except ValueError:
            # Reactor outputs are supplied explicitly below. Any other external
            # entry is not authority-bound and is refused.
            try:
                path.relative_to(candidate_root)
            except ValueError:
                missing_trusted.append(entry)
            continue
        trusted = trusted_repo / rel
        if trusted.is_file():
            kept.append(str(trusted))
        else:
            missing_trusted.append(entry)
    prefixes = []
    for name in [module] + [m for m in all_modules if m != module]:
        classes = candidate_root / name / MAIN_CLASSES_DIR
        if classes.is_dir():
            prefixes.append(str(classes))
    if missing_trusted:
        raise ValueError("untrusted_classpath_entries_without_trusted_copy in {}: {}".format(
            module, ",".join(missing_trusted[:5])))
    return prefixes + kept, dropped, prefixes


def compile_runtime(trusted_root: Path, staging: Path, junit_classpath: str) -> dict:
    """Compile the closed driver module and the parent-side JDI observer."""
    driver_source = trusted_root / DRIVER
    observer_source = trusted_root / OBSERVER
    if not driver_source.is_file() or not observer_source.is_file():
        raise FileNotFoundError("trusted driver/observer source is missing")
    if not junit_classpath:
        raise ValueError("trusted junit classpath is required")

    driver_out = staging / "driver"
    observer_out = staging / "observer"
    for out in (driver_out, observer_out):
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)

    with tempfile.TemporaryDirectory(dir=str(staging)) as tmp:
        module_info = Path(tmp) / "module-info.java"
        module_info.write_text("module c12.trusted {}\\n")
        proc = run([
            jdk_tool("javac"), "--add-reads", "c12.trusted=ALL-UNNAMED",
            "-proc:none", "-nowarn", "-cp", junit_classpath,
            "-d", str(driver_out), str(module_info), str(driver_source)
        ], trusted_root)
        if proc.returncode != 0:
            raise RuntimeError("driver javac failed: {}".format(proc.stderr.strip()[:4000]))

    proc = run([
        jdk_tool("javac"), "--add-modules", "jdk.jdi", "-proc:none", "-nowarn",
        "-d", str(observer_out), str(observer_source)
    ], trusted_root)
    if proc.returncode != 0:
        raise RuntimeError("observer javac failed: {}".format(proc.stderr.strip()[:4000]))

    return {
        "driver_sha256": sha256_file(driver_source),
        "observer_sha256": sha256_file(observer_source),
    }

def trusted_compile_module(export_root: Path, module: str, classpath: list[str], out: Path) -> dict:
    """Compile a module's test sources from the exact-SHA Git export, in trusted code.

    -proc:none: no annotation processor (and so no candidate or dependency code)
    runs during compilation. The candidate's own target/test-classes is never used.
    """
    module_dir = export_root / module
    sources = []
    for rel in TEST_SOURCE_DIRS:
        root = module_dir / rel
        if root.is_dir():
            sources += sorted(str(p) for p in root.rglob("*.java") if p.is_file() and not p.is_symlink())
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    record = {"module": module, "sources": len(sources), "exit_code": None, "stderr_tail": ""}
    if not sources:
        record["exit_code"] = 0
        return record
    argfile = out.parent / "{}.sources".format(out.name)
    argfile.write_text("\n".join('"{}"'.format(s.replace("\\", "\\\\")) for s in sources) + "\n")
    proc = run(
        [jdk_tool("javac"), "-proc:none", "-nowarn", "-encoding", "UTF-8", "-d", str(out),
         "-cp", os.pathsep.join(classpath), "@{}".format(argfile)],
        module_dir,
    )
    record["exit_code"] = proc.returncode
    record["stderr_tail"] = proc.stderr.strip()[-2000:]
    record["dropped_test_resources"] = []
    compiled_before = class_file_digests(out)
    for rel in TEST_RESOURCE_DIRS:
        resources = module_dir / rel
        if resources.is_dir():
            def ignore(directory, names, root=resources):
                dropped = []
                for name in names:
                    path = Path(directory) / name
                    rel_path = path.relative_to(root).as_posix()
                    # JUnit registration and configuration never come from the
                    # candidate (the driver also disables auto-registration and
                    # implicit configuration; this is defence in depth).
                    # Bytecode never comes from resources either: a candidate
                    # RequiredTest.class resource would otherwise overwrite the
                    # class trusted javac just compiled, in the very directory the
                    # code-origin check accepts.
                    if path.is_symlink() or name == "junit-platform.properties" or name.endswith(".class") or (
                        rel_path.startswith("META-INF/services/org.junit")
                    ):
                        dropped.append(name)
                        record["dropped_test_resources"].append(rel_path)
                return dropped
            shutil.copytree(resources, out, dirs_exist_ok=True, symlinks=False, ignore=ignore)
    # Defence in depth: copying resources must leave every trusted-compiled
    # class byte-identical and add none.
    if class_file_digests(out) != compiled_before:
        raise RuntimeError("test resources altered trusted-compiled bytecode in {}".format(module))
    return record


def class_file_digests(root: Path) -> dict:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in root.rglob("*.class")
        if path.is_file()
    }


def compiled_classes(root: Path) -> set:
    if not root.is_dir():
        return set()
    names = set()
    for path in root.rglob("*.class"):
        name = ".".join(path.relative_to(root).with_suffix("").parts)
        if "$" not in name:
            names.add(name)
    return names


def _observer_address(proc: subprocess.Popen, timeout: float = 30.0) -> str:
    ready, _, _ = select.select([proc.stdout], [], [], timeout)
    if not ready:
        raise RuntimeError("trusted observer did not publish a listen address")
    line = proc.stdout.readline().strip()
    prefix = "TRUSTED_OBSERVER_LISTENING "
    if not line.startswith(prefix):
        raise RuntimeError("trusted observer startup failed: {}".format(line[:500]))
    address = line[len(prefix):].strip()
    if not address:
        raise RuntimeError("trusted observer published an empty address")
    return address


def module_witnesses(user, sandbox_dir, candidate_root, modules, bundle, outputs, locked_sha, locked_tree):
    """Run each module in a candidate JVM observed by a trusted parent JVM."""
    results = []
    home = sandbox.sandbox_home(sandbox_dir)
    outputs.mkdir(parents=True, exist_ok=True)
    for module in sorted(modules):
        entry = modules[module]
        classes = entry["selected_classes"]
        if not classes:
            results.append({"module": module, "required_classes": 0, "executed": False,
                            "reason": "no_trusted_required_classes_in_module", "witness": None})
            continue
        if set(classes) <= set(entry["not_compiled"]):
            results.append({"module": module, "required_classes": len(classes), "executed": False,
                            "reason": "module_test_classes_not_compiled", "witness": None})
            continue

        test_output = bundle / "tests" / entry["bundle_name"]
        receipt = outputs / "module-{}.json".format(entry["bundle_name"])
        if receipt.exists():
            receipt.unlink()
        junit = [str(bundle / "junit" / Path(j).name) for j in entry["junit"]]
        classpath = os.pathsep.join([*junit, str(test_output), *entry["classpath"]])

        observer_cmd = [
            jdk_tool("java"), "--add-modules", "jdk.jdi",
            "-cp", str(bundle / "observer"), "TrustedTestObserver",
            "--module-id", module, "--bind-sha", locked_sha, "--bind-tree", locked_tree,
            "--module-output", str(test_output), "--receipt", str(receipt),
        ]
        for name in classes:
            observer_cmd += ["--select", name]

        observer = subprocess.Popen(
            observer_cmd, cwd=str(outputs), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
        proc = None
        failure = None
        try:
            address = _observer_address(observer)
            cmd = [
                jdk_tool("java"),
                "-XX:+DisableAttachMechanism",
                "-agentlib:jdwp=transport=dt_socket,server=n,suspend=y,address={}".format(address),
                "--add-reads", "c12.trusted=ALL-UNNAMED",
                "--module-path", str(bundle / "driver"),
                "-cp", classpath,
                "-m", "c12.trusted/c12.trusted.TrustedTestDriver",
                "--module-output", str(test_output),
                "--untrusted-prefix", str(candidate_root),
                "--untrusted-prefix", str(home),
            ]
            for name in classes:
                cmd += ["--select", name]
            module_dir = candidate_root / module if (candidate_root / module).is_dir() else candidate_root
            proc = sandbox.run_candidate(user, home, module_dir, cmd, timeout=18000)
            try:
                observer.wait(timeout=30)
            except subprocess.TimeoutExpired:
                observer.kill()
                observer.wait()
                failure = "trusted_observer_did_not_terminate"
        except (sandbox.SandboxError, OSError, RuntimeError) as exc:
            failure = "contained_execution_failure: {}".format(exc)
            try:
                observer.kill()
                observer.wait(timeout=5)
            except Exception:
                pass

        witness, receipt_failure = read_parent_receipt(receipt)
        if receipt_failure:
            failure = failure or receipt_failure
        observer_stdout = ""
        observer_stderr = ""
        try:
            tail_out, tail_err = observer.communicate(timeout=1)
            observer_stdout = (tail_out or "")[-2000:]
            observer_stderr = (tail_err or "")[-2000:]
        except Exception:
            pass
        results.append({
            "module": module,
            "required_classes": len(classes),
            "executed": witness is not None,
            "driver_exit_code": proc.returncode if proc is not None else None,
            "driver_stdout": (proc.stdout if proc is not None else "").strip()[-2000:],
            "driver_stderr": (proc.stderr if proc is not None else "").strip()[-2000:],
            "observer_exit_code": observer.returncode,
            "observer_stdout": observer_stdout,
            "observer_stderr": observer_stderr,
            "reason": failure,
            "witness": witness,
        })
    return results

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--git-repo", required=True, help="trusted repository holding the locked commits")
    parser.add_argument("--trusted-root", required=True, help="trusted qualification directory")
    parser.add_argument("--sandbox-dir", required=True)
    parser.add_argument("--sandbox-user", default=sandbox.CANDIDATE_USER)
    parser.add_argument("--sandbox-prepare", required=True, help="SANDBOX_PREPARE.json written by sandbox.py prepare")
    parser.add_argument("--bundle-dir", required=True, help="root-owned read-only directory for trusted bytecode")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--build-result", required=True, help="sandbox.py run record of the candidate build")
    parser.add_argument("--build-definition-audit", required=True)
    parser.add_argument("--module-classpaths", required=True)
    parser.add_argument("--trusted-maven-repo", required=True,
                        help="parent-owned Maven repository resolved before candidate execution")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    trusted_root = Path(args.trusted_root).resolve()
    sandbox_dir = Path(args.sandbox_dir).resolve()
    candidate_root = sandbox_dir / "candidate"
    candidate_home = sandbox.sandbox_home(sandbox_dir)
    trusted_maven_repo = Path(args.trusted_maven_repo).resolve()
    workdir = Path(args.work_dir).resolve()
    bundle = Path(args.bundle_dir)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    junit_classpath = os.environ.get("TRUSTED_JUNIT_CLASSPATH", "").strip()

    doc: dict = {
        "schema": SCHEMA,
        "status": "UNKNOWN",
        "trusted_validator": None,
        "candidate": None,
        "comparison_base": None,
        "observed_candidate_sha": None,
        "source_binding_ok": False,
        "candidate_build_exit_code": None,
        "candidate_build_exit_code_semantics":
            "recorded by trusted code around the sandboxed build; a non-zero exit is an unconditional qualification failure",
        "build_definition_audit": None,
        "corpus_policy": None,
        "required_test_classes": [],
        "modules": [],
        "module_execution": [],
        "module_classpath_completeness": None,
        "execution_mode": "per_module_external_observer",
        "test_bytecode_origin": "trusted_compile_of_trusted_validator_export",
        "candidate_execution_identity": args.sandbox_user,
        "trusted_execution_witness": None,
        "driver": {"name": DRIVER, "sha256": None},
        "observer": {"name": OBSERVER, "sha256": None},
        "candidate_witness_authority": False,
        "candidate_authored_evidence_used": False,
        "candidate_reports_parsed": False,
        "candidate_test_classes_used": False,
        "module_classpaths_are_authority": False,
        "notes": [],
    }

    try:
        lock = json.loads(Path(args.source_lock).read_text())
        if lock.get("status") != "LOCKED":
            raise ValueError("source lock is not LOCKED")
        doc["trusted_validator"] = lock.get("trusted_validator")
        doc["candidate"] = lock.get("candidate")
        doc["comparison_base"] = lock.get("comparison_base")
        locked_sha = (lock.get("candidate") or {}).get("sha")
        locked_tree = (lock.get("candidate") or {}).get("tree", "")
        trusted_sha = (lock.get("trusted_validator") or {}).get("sha")
        base_sha = (lock.get("comparison_base") or {}).get("sha")

        prepared = json.loads(Path(args.sandbox_prepare).read_text())
        if prepared.get("status") != "READY":
            raise ValueError("sandbox is not READY: {}".format(prepared.get("error")))
        observed = prepared.get("candidate_sha") or ""
        doc["observed_candidate_sha"] = observed
        if observed != locked_sha:
            raise ValueError("sandbox candidate {} != locked {}".format(observed, locked_sha))
        repo_tree = subprocess.run(
            [GIT, "-C", args.git_repo, "rev-parse", "{}^{{tree}}".format(locked_sha)],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        if not locked_tree or repo_tree != locked_tree:
            raise ValueError("locked candidate tree {} is not the tree of {} ({})".format(locked_tree, locked_sha, repo_tree))
        doc["source_binding_ok"] = True

        build = json.loads(Path(args.build_result).read_text())
        if build.get("status") != "RECORDED" or build.get("user") != args.sandbox_user:
            raise ValueError("candidate build was not recorded by the sandbox runner")
        doc["candidate_build_exit_code"] = build.get("exit_code")

        audit = json.loads(Path(args.build_definition_audit).read_text())
        doc["build_definition_audit"] = {
            "status": audit.get("status"),
            "violations": audit.get("violations") or [],
            "audited_files": [e.get("path") for e in audit.get("audited_poms") or []]
            + list(audit.get("maven_config_changes") or []),
        }
        if audit.get("status") == "UNKNOWN":
            raise ValueError("build definition audit is UNKNOWN: {}".format(audit.get("error")))

        corpus = corpus_policy.evaluate(args.git_repo, trusted_sha, base_sha, locked_sha)
        doc["corpus_policy"] = corpus
        # Only the trusted default-branch corpus can earn C12 credit.
        # Candidate-added tests remain visible to the delta policy/native CI but
        # are not loaded into the authoritative JVM.
        trusted_pairs = corpus.get("trusted_required_pairs") or []
        trusted_methods = corpus.get("trusted_required_methods") or []
        trusted_inheriting = corpus.get("trusted_required_inheriting_classes") or []
        required = [
            {"module": m, "class_name": c}
            for m, c in (corpus_policy.split_pair(p) for p in trusted_pairs)
        ]
        doc["required_test_classes"] = required
        owning = {corpus_policy.class_of_method(m) for m in trusted_methods}
        owning |= set(trusted_inheriting)
        doc["selected_test_classes"] = [
            e for e in required if corpus_policy.pair(e["module"], e["class_name"]) in owning
        ]
        doc["corpus_classes_without_required_methods"] = sorted(
            p for p in trusted_pairs if p not in owning
        )

        modules: dict = {}
        for entry in required:
            modules.setdefault(entry["module"], set()).add(entry["class_name"])

        classpath_map = json.loads(Path(args.module_classpaths).read_text())
        if not isinstance(classpath_map, dict):
            raise ValueError("module classpath map must be a JSON object")
        missing_modules = sorted(set(modules) - set(classpath_map))
        doc["module_classpath_completeness"] = {
            "modules_with_required_tests": sorted(modules),
            "modules_with_classpath": sorted(classpath_map),
            "modules_missing_classpath": missing_modules,
            "complete": not missing_modules,
        }
        if missing_modules:
            raise ValueError("module_classpath_missing for required modules: {}".format(",".join(missing_modules)))
        if not modules:
            raise ValueError("no required test class was enumerated from the locked candidate")

        export = workdir / "trusted-test-export"
        # Test source is authority-bearing and therefore comes from the trusted
        # validator commit, never from candidate-authored test source.
        sandbox.export_commit(Path(args.git_repo), trusted_sha, export)

        staging = workdir / "bundle"
        if staging.exists():
            shutil.rmtree(staging)
        (staging / "junit").mkdir(parents=True)
        junit_jars = [j for j in junit_classpath.split(os.pathsep) if j]
        for jar in junit_jars:
            shutil.copy2(jar, staging / "junit" / Path(jar).name)
        runtime_hashes = compile_runtime(trusted_root, staging, junit_classpath)
        doc["driver"]["sha256"] = runtime_hashes["driver_sha256"]
        doc["observer"]["sha256"] = runtime_hashes["observer_sha256"]

        resolved = {}
        all_modules = sorted(modules)
        dropped_total = []
        compile_records = []
        for index, module in enumerate(all_modules):
            classes = modules[module]
            cp, dropped, prefixes = sanitize_classpath(
                module, str(classpath_map.get(module, "")), candidate_root, all_modules,
                candidate_home, trusted_maven_repo)
            bundle_name = "{:03d}-{}".format(index, module.replace("/", "_").replace(".", "_") or "root")
            compiled_out = staging / "tests" / bundle_name
            record = trusted_compile_module(export, module, junit_jars + cp, compiled_out)
            compile_records.append(record)
            compiled = compiled_classes(compiled_out)
            not_compiled = sorted(c for c in classes if c not in compiled)
            dropped_total += [{"module": module, "dropped": d} for d in dropped]
            resolved[module] = {
                "required_classes": sorted(classes),
                "selected_classes": sorted(c for c in classes if corpus_policy.pair(module, c) in owning),
                "classpath": cp,
                "junit": junit_jars,
                "bundle_name": bundle_name,
                "not_compiled": not_compiled,
                "stale_sibling_entries_dropped": dropped,
                "candidate_output_prefixes": prefixes,
            }
            if record["exit_code"] != 0:
                doc["notes"].append("trusted_test_compile_failed in {}: {}".format(module, record["stderr_tail"][-300:]))
            if not_compiled:
                doc["notes"].append("required_tests_not_compiled in {}: {}".format(module, ",".join(not_compiled[:5])))
        doc["trusted_test_compilation"] = compile_records
        doc["stale_sibling_artifacts_dropped"] = dropped_total
        doc["modules"] = [
            {"module": m, "required_class_count": len(v["required_classes"]), "not_compiled": v["not_compiled"],
             "stale_sibling_entries_dropped": v["stale_sibling_entries_dropped"]}
            for m, v in sorted(resolved.items())
        ]

        sandbox.stage_readonly(staging, bundle)
        # Receipts live only in the trusted work directory. Candidate code never
        # receives this path and its OS identity cannot write it.
        outputs = workdir / "observer-receipts"
        if outputs.exists():
            shutil.rmtree(outputs)
        outputs.mkdir(parents=True)
        execution = module_witnesses(args.sandbox_user, sandbox_dir, candidate_root, resolved, bundle, outputs,
                                     locked_sha, locked_tree)
        doc["module_execution"] = execution
        doc["trusted_execution_witness"] = aggregate(execution)
        doc["status"] = "WITNESSED"
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError,
            corpus_policy.CorpusError, sandbox.SandboxError) as exc:
        doc["notes"].append("witness_unavailable: {}".format(exc))
        out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
        print("TRUSTED_WITNESS = UNKNOWN ({})".format(json.dumps(str(exc), ensure_ascii=True)), file=sys.stderr)
        return 2

    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    agg = doc["trusted_execution_witness"]
    print("TRUSTED_WITNESS = {} modules={} required={} entered={} started={} failed={} corpus={}".format(
        doc["status"], len(doc["module_execution"]), len(doc["required_test_classes"]),
        agg.get("classes_entered_total"), agg.get("tests_started"), agg.get("tests_failed"),
        (doc["corpus_policy"] or {}).get("status")))
    # Legacy reporting names can be arbitrary candidate-controlled text.
    # JSON escaping keeps each diagnostic on one prefixed ASCII line, including
    # newlines, CR, terminal escapes and Unicode separators. The complete raw
    # name remains in the artifact; a diagnostic never becomes a workflow command.
    for name, count in list((agg.get("non_successful_by_class") or {}).items())[:20]:
        print("TRUSTED_WITNESS non-successful: {} x{}".format(
            json.dumps(str(name)[:300], ensure_ascii=True),
            json.dumps(count, ensure_ascii=True)))
    return 0


def aggregate(execution: list[dict]) -> dict:
    """Aggregate per-module witnesses in trusted code. Fail closed on any gap."""
    totals = {k: 0 for k in ("tests_found", "tests_started", "tests_succeeded", "tests_failed",
                             "tests_aborted", "tests_skipped", "containers_failed")}
    entered_pairs: set = set()
    observed_methods: set = set()
    never_entered: set = set()
    origin_violations: set = set()
    entered_modules: list = []
    modules_without_witness: list = []
    origin_paths: dict = {}
    non_successful: dict = {}
    for entry in execution:
        module = entry.get("module")
        if entry.get("required_classes", 0) > 0 and not entry.get("executed"):
            modules_without_witness.append(module)
        witness = entry.get("witness")
        if not isinstance(witness, dict):
            continue
        entered_modules.append(module)
        for key in totals:
            value = witness.get(key, 0)
            totals[key] += value if isinstance(value, int) else 0
        # (module, class) pairs: two modules may declare the same FQN.
        for name in witness.get("observed_classes") or []:
            entered_pairs.add(corpus_policy.pair(module, name))
        for name in witness.get("classes_never_entered") or []:
            never_entered.add(corpus_policy.pair(module, name))
        for name in witness.get("observed_methods") or []:
            if isinstance(name, str):
                observed_methods.add(corpus_policy.pair(module, name))
        for violation in witness.get("code_origin_violations") or []:
            origin_violations.add("{}: {}".format(module, violation))
        for name, location in (witness.get("class_code_origins") or {}).items():
            origin_paths[corpus_policy.pair(module, name)] = location
        for name, count in (witness.get("non_successful_by_class") or {}).items():
            if isinstance(count, int):
                key = corpus_policy.pair(module, name)
                non_successful[key] = non_successful.get(key, 0) + count
    bound = [e["witness"] for e in execution if isinstance(e.get("witness"), dict)]
    return {
        "schema": WITNESS_SCHEMA,
        "producer": "witness.py per-module aggregation",
        "evidence_origin": "trusted_parent_jdi_observation",
        "candidate_authored_evidence_used": False,
        "candidate_witness_authority": False,
        "execution_mode": "per_module_external_observer",
        "bound_candidate_sha": bound[0].get("bound_candidate_sha") if bound else None,
        "bound_candidate_shas": sorted({str(w.get("bound_candidate_sha")) for w in bound}),
        "bound_candidate_tree": bound[0].get("bound_candidate_tree") if bound else None,
        "modules_with_required_tests": [e["module"] for e in execution if e.get("required_classes", 0) > 0],
        "modules_with_witness": entered_modules,
        "modules_without_witness": modules_without_witness,
        "trusted_selected_classes": sum(e.get("required_classes", 0) for e in execution),
        "entered_pairs": sorted(entered_pairs),
        "classes_entered_total": len(entered_pairs),
        "classes_never_entered": sorted(never_entered),
        "observed_methods": sorted(observed_methods),
        "code_origin_violations": sorted(origin_violations),
        "class_code_origins": origin_paths,
        "non_successful_by_class": dict(sorted(non_successful.items())),
        "driver_verdict": "PENDING",
        "totals": totals,
        **totals,
    }


if __name__ == "__main__":
    sys.exit(main())
