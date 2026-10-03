#!/usr/bin/env python3
"""Produce the trusted execution witness for an exact candidate SHA, per module.

Trust boundary: this script, ``build_definition_audit.py`` and
``TrustedTestDriver.java`` are trusted default-branch source. Nothing here reads
a candidate-produced test report, and no candidate-authored artifact can become
qualification credit.

Per-module execution is the point. Surefire normally runs each module with its own
test classpath in its own forked JVM. Reproducing that here is what makes the
witness faithful at reactor scale: a single combined classpath would let a class
resolve from a sibling module or an unrelated jar, and a required test could be
credited to the wrong module. So:

  * required test classes are enumerated per module from candidate SOURCE, which
    is content, not evidence;
  * every module that owns required classes MUST have a resolved classpath in the
    supplied map, or the witness fails - a module is never dropped because
    resolving it was inconvenient;
  * the trusted driver is executed once per module with that module's classpath
    and that module's classes only;
  * the driver verifies each executed class actually loaded from its own module's
    output directory, so a classpath collision cannot be credited;
  * results are aggregated only here, in trusted code, and the aggregation is
    fail-closed: a partial or missing module result can never become PASS.

The classpath map is candidate-influenced *input* - it is unavoidable, because
executing a candidate's tests requires the candidate's declared dependencies. It
is never authority: it can change which class loads, never whether a required
class counts as executed, and never the verdict rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA = "mage.candidate-qualification.witness/2"
WITNESS_SCHEMA = "mage.candidate-qualification.trusted-execution-witness/1"
DRIVER = "TrustedTestDriver.java"

# Selection heuristic for what must run, never an evidence heuristic: a class that
# matches but is missing makes the witness FAIL rather than shrinking the set.
TEST_CLASS_RE = r"(Test|Tests|TestCase|Spec|IT)$"
SOURCE_DIR_MARKERS = ("src/test/java", "src/test/kotlin", "src/test/groovy")
COMPILED_DIR = "target/test-classes"
MAIN_CLASSES_DIR = "target/classes"
DRIVER_CLASSES = "trusted-driver-classes"

# Maven's own artifacts, as installed in the local repository. Resolving a
# sibling module from an installed jar means executing code that is NOT the
# candidate's, and the workflow restores ~/.m2 between runs via the Maven cache,
# so such a jar can be silently stale. These entries are dropped and replaced by
# the candidate's own reactor output directories.
STALE_SIBLING_MARKERS = ("/org/mage/",)


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


def module_of(candidate_root: Path, source_root: Path) -> str | None:
    """Nearest ancestor of a test source root that carries a pom.xml."""
    for parent in [source_root] + list(source_root.parents):
        if parent == candidate_root.parent:
            break
        if (parent / "pom.xml").is_file():
            try:
                return parent.relative_to(candidate_root).as_posix() or "."
            except ValueError:
                return None
    return None


def enumerate_required_tests(candidate_root: Path) -> list[dict]:
    """Enumerate required test classes per module from candidate SOURCE, as data."""
    import re

    pattern = re.compile(TEST_CLASS_RE)
    found: dict[str, set] = {}
    for marker in SOURCE_DIR_MARKERS:
        for source_root in candidate_root.glob("**/" + marker):
            module = module_of(candidate_root, source_root)
            if module is None:
                continue
            for path in source_root.rglob("*.java"):
                if pattern.search(path.stem):
                    rel = path.relative_to(source_root).with_suffix("")
                    found.setdefault(module, set()).add(".".join(rel.parts))
    return [
        {"module": module, "class_name": name}
        for module in sorted(found)
        for name in sorted(found[module])
    ]


def module_output_dirs(candidate_root: Path, module: str) -> list[Path]:
    module_dir = candidate_root / module
    return [
        path
        for path in (module_dir / COMPILED_DIR, module_dir / MAIN_CLASSES_DIR)
        if path.is_dir()
    ]


def sanitize_classpath(
    module: str, resolved: str, candidate_root: Path, all_modules: list[str]
) -> tuple[str, list[str], list[str]]:
    """Replace stale installed sibling jars with the candidate's reactor output.

    Maven's ``dependency:build-classpath`` run outside a full reactor resolves a
    sibling module to an installed jar. For exact-SHA qualification that is wrong:
    the witness would run the candidate's tests against a framework jar that may
    predate the candidate. So every org/mage repository entry is dropped and the
    candidate's own compiled module outputs are put first, mirroring reactor
    semantics. The trusted driver then independently verifies that each required
    class actually loaded from its own module output.
    """
    dropped: list[str] = []
    kept: list[str] = []
    for entry in (resolved or "").split(os.pathsep):
        entry = entry.strip()
        if not entry:
            continue
        normalised = entry.replace("\\", "/")
        if any(marker in normalised for marker in STALE_SIBLING_MARKERS):
            dropped.append(entry)
        else:
            kept.append(entry)

    prefixes = [str(path) for path in module_output_dirs(candidate_root, module)]
    for other in all_modules:
        if other == module:
            continue
        candidate_classes = candidate_root / other / MAIN_CLASSES_DIR
        if candidate_classes.is_dir():
            prefixes.append(str(candidate_classes))

    return os.pathsep.join(prefixes + kept), dropped, prefixes


def compiled_classes(module_dir: Path) -> set:
    root = module_dir / COMPILED_DIR
    if not root.is_dir():
        return set()
    names = set()
    for path in root.rglob("*.class"):
        rel = path.relative_to(root).with_suffix("")
        name = ".".join(rel.parts)
        if "$" not in name:
            names.add(name)
    return names


def compile_driver(trusted_root: Path, workdir: Path, junit_classpath: str) -> tuple[Path, str]:
    source = trusted_root / DRIVER
    if not source.is_file():
        raise FileNotFoundError("trusted driver source is missing: {}".format(source))
    if not junit_classpath:
        raise ValueError("trusted junit classpath is required to compile and run the driver")
    out = workdir / DRIVER_CLASSES
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    proc = run(["javac", "-nowarn", "-cp", junit_classpath, "-d", str(out), str(source)], trusted_root)
    if proc.returncode != 0:
        raise RuntimeError("javac failed: {}".format(proc.stderr.strip()[:2000]))
    return out, sha256_file(source)


def module_witnesses(
    candidate_root: Path,
    modules: dict,
    driver_classes: Path,
    workdir: Path,
    locked_sha: str,
    locked_tree: str,
    junit_classpath: str,
) -> list[dict]:
    """Run the trusted driver once per module. Never merges two modules into one JVM."""
    results = []
    for module in sorted(modules):
        entry = modules[module]
        classes = entry["required_classes"]
        module_dir = candidate_root / module
        module_output = module_dir / COMPILED_DIR

        if not classes:
            # A module with no required classes contributes nothing and must not be
            # able to manufacture positive credit.
            results.append(
                {
                    "module": module,
                    "required_classes": 0,
                    "executed": False,
                    "reason": "no_required_classes_in_module",
                    "witness": None,
                }
            )
            continue

        if not module_output.is_dir():
            results.append(
                {
                    "module": module,
                    "required_classes": len(classes),
                    "executed": False,
                    "reason": "module_test_classes_not_compiled",
                    "witness": None,
                }
            )
            continue

        witness_path = workdir / "module-{}.json".format(module.replace("/", "_"))
        if witness_path.exists():
            witness_path.unlink()

        classpath = os.pathsep.join(
            [str(driver_classes), junit_classpath, entry.get("classpath", ""), str(module_output)]
        )
        cmd = [
            "java",
            "-cp",
            classpath,
            "TrustedTestDriver",
            "--evidence", str(witness_path),
            "--class-path", classpath,
            "--bind-sha", locked_sha,
            "--bind-tree", locked_tree,
            "--module-id", module,
            "--module-output", str(module_output),
        ]
        for name in classes:
            cmd += ["--select", name]

        proc = run(cmd, candidate_root)
        witness = None
        if witness_path.is_file():
            try:
                witness = json.loads(witness_path.read_text())
            except json.JSONDecodeError:
                witness = None
        results.append(
            {
                "module": module,
                "required_classes": len(classes),
                "executed": witness is not None,
                "driver_exit_code": proc.returncode,
                "driver_stdout": proc.stdout.strip()[-2000:],
                "driver_stderr": proc.stderr.strip()[-2000:],
                "reason": None if witness else "trusted_driver_produced_no_witness",
                "witness": witness,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", required=True)
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--observed-candidate-sha", default="")
    parser.add_argument("--trusted-root", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--build-exit-code", default="")
    parser.add_argument("--build-definition-audit", default="")
    parser.add_argument(
        "--module-classpaths",
        required=True,
        help="JSON map of module root to its resolved test classpath; candidate-influenced input, never authority",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    trusted_root = Path(args.trusted_root).resolve()
    candidate_root = Path(args.candidate_root).resolve()
    workdir = Path(args.work_dir).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    junit_classpath = os.environ.get("TRUSTED_JUNIT_CLASSPATH", "").strip()

    witness_doc: dict = {
        "schema": SCHEMA,
        "status": "UNKNOWN",
        "trusted_validator": None,
        "candidate": None,
        "comparison_base": None,
        "observed_candidate_sha": args.observed_candidate_sha or None,
        "source_binding_ok": False,
        "candidate_build_exit_code": args.build_exit_code or None,
        "candidate_build_exit_code_semantics":
            "binding control only; a non-zero exit is an unconditional qualification failure",
        "build_definition_audit": None,
        "required_test_classes": [],
        "modules": [],
        "module_execution": [],
        "module_classpath_completeness": None,
        "execution_mode": "per_module_trusted_driver",
        "trusted_execution_witness": None,
        "driver": {"name": DRIVER, "sha256": None},
        "candidate_authored_evidence_used": False,
        "candidate_reports_parsed": False,
        "module_classpaths_are_authority": False,
        "notes": [],
    }

    try:
        lock = json.loads(Path(args.source_lock).read_text())
        if lock.get("status") != "LOCKED":
            raise ValueError("source lock is not LOCKED")
        witness_doc["trusted_validator"] = lock.get("trusted_validator")
        witness_doc["candidate"] = lock.get("candidate")
        witness_doc["comparison_base"] = lock.get("comparison_base")

        locked_sha = (lock.get("candidate") or {}).get("sha")
        locked_tree = (lock.get("candidate") or {}).get("tree", "")
        observed = args.observed_candidate_sha.strip()
        if not observed:
            raise ValueError("observed candidate sha was not supplied; binding unproven")
        if observed != locked_sha:
            raise ValueError("observed candidate sha {} != locked {}".format(observed, locked_sha))
        witness_doc["source_binding_ok"] = True

        if not candidate_root.is_dir():
            raise ValueError("candidate root does not exist")

        if args.build_definition_audit:
            audit = json.loads(Path(args.build_definition_audit).read_text())
            witness_doc["build_definition_audit"] = {
                "status": audit.get("status"),
                "violations": audit.get("violations") or [],
                "audited_poms": [e.get("path") for e in audit.get("audited_poms") or []],
            }
            if audit.get("status") == "UNKNOWN":
                raise ValueError("build definition audit is UNKNOWN: {}".format(audit.get("error")))
            if audit.get("status") != "CLEAN":
                witness_doc["notes"].append(
                    "build_definition_audit_violation: {}".format(
                        ", ".join(
                            "{}:{}".format(v.get("kind"), v.get("detail"))
                            for v in (audit.get("violations") or [])[:5]
                        )
                    )
                )

        required = enumerate_required_tests(candidate_root)
        witness_doc["required_test_classes"] = required

        classpath_map = json.loads(Path(args.module_classpaths).read_text())
        if not isinstance(classpath_map, dict):
            raise ValueError("module classpath map must be a JSON object")

        modules: dict = {}
        for entry in required:
            modules.setdefault(entry["module"], set()).add(entry["class_name"])

        missing_modules = sorted(set(modules) - set(classpath_map))
        witness_doc["module_classpath_completeness"] = {
            "modules_with_required_tests": sorted(modules),
            "modules_with_classpath": sorted(classpath_map),
            "modules_missing_classpath": missing_modules,
            "complete": not missing_modules,
        }
        if missing_modules:
            # Fail closed: a module is never skipped because resolving it was hard.
            raise ValueError(
                "module_classpath_missing for required modules: {}".format(
                    ",".join(missing_modules)
                )
            )

        driver_classes, driver_digest = compile_driver(trusted_root, workdir, junit_classpath)
        witness_doc["driver"]["sha256"] = driver_digest

        resolved = {}
        all_modules = sorted(modules)
        dropped_total: list[dict] = []
        for module, classes in modules.items():
            module_dir = candidate_root / module
            compiled = compiled_classes(module_dir)
            not_compiled = sorted(c for c in classes if c not in compiled)
            sanitized, dropped, prefixes = sanitize_classpath(
                module, str(classpath_map.get(module, "")), candidate_root, all_modules
            )
            for entry in dropped:
                dropped_total.append({"module": module, "dropped": entry})
            resolved[module] = {
                "required_classes": sorted(classes),
                "classpath": sanitized,
                "not_compiled": not_compiled,
                "stale_sibling_entries_dropped": dropped,
                "candidate_output_prefixes": prefixes,
            }
            if dropped:
                witness_doc["notes"].append(
                    "stale_sibling_artifact_dropped in {}: {}".format(module, ",".join(dropped))
                )
            if not_compiled:
                witness_doc["notes"].append(
                    "required_tests_not_compiled in {}: {}".format(module, ",".join(not_compiled[:5]))
                )
        witness_doc["stale_sibling_artifacts_dropped"] = dropped_total
        witness_doc["modules"] = [
            {
                "module": m,
                "required_class_count": len(v["required_classes"]),
                "not_compiled": v["not_compiled"],
                "stale_sibling_entries_dropped": v["stale_sibling_entries_dropped"],
            }
            for m, v in sorted(resolved.items())
        ]

        if not modules:
            raise ValueError("no required test class was enumerated from the candidate source tree")

        execution = module_witnesses(
            candidate_root, resolved, driver_classes, workdir, locked_sha, locked_tree, junit_classpath
        )
        witness_doc["module_execution"] = execution

        aggregated = aggregate(execution)
        witness_doc["trusted_execution_witness"] = aggregated
        witness_doc["status"] = "WITNESSED"

    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        witness_doc["notes"].append("witness_unavailable: {}".format(exc))
        out.write_text(json.dumps(witness_doc, indent=2, sort_keys=True) + "\n")
        print("TRUSTED_WITNESS = UNKNOWN ({})".format(exc), file=sys.stderr)
        return 2

    out.write_text(json.dumps(witness_doc, indent=2, sort_keys=True) + "\n")
    aggregated = witness_doc["trusted_execution_witness"]
    print(
        "TRUSTED_WITNESS = {} modules={} required={} entered={} started={} failed={} driver={}".format(
            witness_doc["status"],
            len(witness_doc["module_execution"]),
            len(witness_doc["required_test_classes"]),
            aggregated.get("classes_entered_total"),
            aggregated.get("tests_started"),
            aggregated.get("tests_failed"),
            witness_doc["driver"]["sha256"][:12] if witness_doc["driver"]["sha256"] else None,
        )
    )
    return 0


def aggregate(execution: list[dict]) -> dict:
    """Aggregate per-module witnesses in trusted code. Fail closed on any gap."""
    totals = {
        "tests_found": 0,
        "tests_started": 0,
        "tests_succeeded": 0,
        "tests_failed": 0,
        "tests_aborted": 0,
        "tests_skipped": 0,
        "containers_failed": 0,
    }
    entered_pairs: set = set()
    observed: set = set()
    never_entered: set = set()
    origin_violations: set = set()
    entered_modules: list = []
    modules_without_witness: list = []
    origin_paths: dict = {}

    for entry in execution:
        module = entry.get("module")
        if entry.get("required_classes", 0) > 0 and not entry.get("executed"):
            modules_without_witness.append(module)
        witness = entry.get("witness")
        if not witness:
            continue
        entered_modules.append(module)
        for key in totals:
            totals[key] += witness.get(key, 0) or 0
        # Count (module, class) pairs, not bare class names: two modules may
        # legitimately declare a test class with the same FQN, and collapsing them
        # would undercount real coverage.
        for name in witness.get("observed_classes") or []:
            entered_pairs.add("{}::{}".format(module, name))
            observed.add(name)
        for name in witness.get("classes_never_entered") or []:
            never_entered.add("{}::{}".format(module, name))
        for violation in witness.get("code_origin_violations") or []:
            origin_violations.add("{}: {}".format(module, violation))
        for name, location in (witness.get("class_code_origins") or {}).items():
            origin_paths["{}::{}".format(module, name)] = location

    return {
        "schema": WITNESS_SCHEMA,
        "producer": "witness.py per-module aggregation",
        "evidence_origin": "trusted_side_direct_execution",
        "candidate_authored_evidence_used": False,
        "execution_mode": "per_module_trusted_driver",
        "bound_candidate_sha": next(
            (e["witness"].get("bound_candidate_sha") for e in execution if e.get("witness")), None
        ),
        "bound_candidate_tree": next(
            (e["witness"].get("bound_candidate_tree") for e in execution if e.get("witness")), None
        ),
        "modules_with_required_tests": [
            e["module"] for e in execution if e.get("required_classes", 0) > 0
        ],
        "modules_with_witness": entered_modules,
        "modules_without_witness": modules_without_witness,
        "trusted_selected_classes": sum(e.get("required_classes", 0) for e in execution),
        "entered_pairs": sorted(entered_pairs),
        "classes_entered_total": len(entered_pairs),
        "classes_never_entered": sorted(never_entered),
        "code_origin_violations": sorted(origin_violations),
        "class_code_origins": origin_paths,
        "driver_verdict": "PENDING",
        "totals": totals,
        **{k: v for k, v in totals.items()},
    }


if __name__ == "__main__":
    sys.exit(main())