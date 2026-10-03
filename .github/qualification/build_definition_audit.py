#!/usr/bin/env python3
"""Audit whether the candidate changed its own test-execution build definition.

Trust boundary: trusted default-branch code. The candidate tree is read as Git
data through the trusted object store; nothing here executes candidate build
code, and nothing here reads the candidate's build output.

Why this exists: the trusted witness runs the required tests itself, so a
candidate that suppresses its own Maven test run cannot gain anything by doing
so. That still leaves the candidate free to *edit the definition of its own
qualification* - hardcoding surefire skip, repointing the test source
directory, or binding a plugin into a post-test lifecycle phase. This audit
compares the test-execution fingerprint of the candidate against the
comparison base and fails closed on any difference, so the qualification
definition cannot be edited in the same PR that is being qualified.

Scope: dependency declarations and ordinary source edits are untouched. What is
compared is everything that makes Maven execute code during the build: every
build plugin in any lifecycle phase (an ``initialize``-bound plugin runs before
anything else, so restricting the audit to post-test phases left a hole), core
build extensions, profiles, the parent POM, every property the build section
interpolates, and the ``.mvn/`` directory (``extensions.xml``, ``maven.config``,
``jvm.config``). A build-definition change cannot be qualified in the PR that
makes it; it needs trusted review, exactly like a CI gate-definition change.

This audit is defence in depth, not the trust boundary: candidate build code
runs as a separate OS account that cannot write trusted state (sandbox.py).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCHEMA = "mage.candidate-qualification.build-definition-audit/1"

# Plugins that decide whether or how tests run.
TEST_EXECUTION_PLUGINS = {
    "maven-surefire-plugin",
    "maven-failsafe-plugin",
    "surefire-junit-platform",
}
# Properties that switch test execution off.
TEST_EXECUTION_PROPERTIES = {"skipTests", "maven.test.skip", "surefire.skip", "skipTestsByDefault"}
# Build directories and source roots that decide where tests come from.
BUILD_DIRECTORIES = {"testSourceDirectory", "testTargetDirectory", "outputDirectory"}
# Lifecycle phases at or after the test phase: anything bound here can act after
# the tests and tamper with their results.
POST_TEST_PHASES = {
    "process-test-classes",
    "test",
    "prepare-package",
    "package",
    "pre-integration-test",
    "integration-test",
    "post-integration-test",
    "verify",
    "install",
    "deploy",
}


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find_all(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if _localname(child.tag) == name]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if _localname(child.tag) == name:
            return child
    return None


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if _localname(child.tag) == name]


def _canonical(element: ET.Element | None) -> str:
    """Whitespace-insensitive serialisation, so formatting is not a change."""
    if element is None:
        return ""
    parts = ["<{}".format(_localname(element.tag))]
    for key in sorted(element.attrib):
        parts.append(" {}={!r}".format(key, element.attrib[key]))
    parts.append(">")
    if element.text and element.text.strip():
        parts.append(element.text.strip())
    for child in element:
        if not isinstance(child.tag, str):
            continue
        parts.append(_canonical(child))
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    parts.append("</{}>".format(_localname(element.tag)))
    return "".join(parts)


PROPERTY_REFERENCE = re.compile(r"\$\{([^}]+)\}")


def _build_code_fingerprint(root: ET.Element) -> dict:
    """Everything in a POM that makes Maven run code, in any lifecycle phase."""
    plugins: dict[str, str] = {}
    build = _child(root, "build")
    profiles = _child(root, "profiles")
    for scope in [e for e in (build, profiles) if e is not None]:
        for plugin in _find_all(scope, "plugin"):
            key = "{}:{}".format(
                _text(_child(plugin, "groupId")) or "org.apache.maven.plugins",
                _text(_child(plugin, "artifactId")),
            )
            plugins.setdefault(key, [])
            plugins[key].append(_canonical(plugin))
    referenced = set()
    for scope in [e for e in (build, profiles) if e is not None]:
        referenced.update(PROPERTY_REFERENCE.findall(_canonical(scope)))
    properties = _child(root, "properties")
    values = {}
    if properties is not None:
        for child in properties:
            if isinstance(child.tag, str) and _localname(child.tag) in referenced:
                values[_localname(child.tag)] = _text(child)
    return {
        "build_plugins": {k: sorted(v) for k, v in sorted(plugins.items())},
        "build_extensions": _canonical(_child(build, "extensions")) if build is not None else "",
        "profiles": _canonical(profiles),
        "parent": _canonical(_child(root, "parent")),
        "interpolated_build_properties": dict(sorted(values.items())),
    }


BUILD_CODE_KEYS = (
    "build_plugins",
    "build_extensions",
    "profiles",
    "parent",
    "interpolated_build_properties",
)


def fingerprint(pom_bytes: bytes) -> dict:
    """Reduce a POM to the parts that define how tests are executed."""
    try:
        root = ET.fromstring(pom_bytes)
    except ET.ParseError as exc:
        # An unparseable POM cannot be audited, so it cannot be trusted either.
        return {"unparseable": str(exc)}

    props: dict[str, str] = {}
    properties = _child(root, "properties")
    if properties is not None:
        for child in properties:
            if _localname(child.tag) in TEST_EXECUTION_PROPERTIES:
                props[_localname(child.tag)] = _text(child)

    directories: dict[str, str] = {}
    build = _child(root, "build")
    if build is not None:
        for child in build:
            if _localname(child.tag) in BUILD_DIRECTORIES:
                directories[_localname(child.tag)] = _text(child)

    test_plugins: dict[str, str] = {}
    post_test_bindings: list[str] = []
    extensions: list[str] = []

    for container_name in ("plugins", "pluginManagement"):
        for container in _find_all(root, container_name):
            for plugin in _children(container, "plugin"):
                artifact = _text(_child(plugin, "artifactId"))
                config = _child(plugin, "configuration")
                serialized = ET.tostring(config, encoding="unicode") if config is not None else ""

                if artifact in TEST_EXECUTION_PLUGINS:
                    test_plugins["{}::{}".format(container_name, artifact)] = serialized

                ext = _child(plugin, "extensions")
                if ext is not None and _text(ext).lower() == "true":
                    extensions.append(artifact)

                for executions in _children(plugin, "executions"):
                    for execution in _children(executions, "execution"):
                        phase = _text(_child(execution, "phase"))
                        goals = ",".join(_text(g) for g in _children(execution, "goal"))
                        if phase in POST_TEST_PHASES:
                            post_test_bindings.append(
                                "{}:{}:{}@{}".format(
                                    artifact, execution.get("id", "?"), goals, phase
                                )
                            )

    return {
        "unparseable": None,
        **_build_code_fingerprint(root),
        "test_execution_properties": props,
        "build_directories": directories,
        "test_execution_plugin_configuration": test_plugins,
        "post_test_lifecycle_bindings": sorted(set(post_test_bindings)),
        "plugin_extensions": sorted(set(extensions)),
    }


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError("git {} failed: {}".format(" ".join(args), proc.stderr.strip()))
    return proc.stdout


def changed_poms(repo: Path, base_rev: str, candidate_rev: str) -> list[str]:
    out = git(repo, "diff", "--name-only", base_rev, candidate_rev, "--", "**/pom.xml", "pom.xml")
    return [line for line in out.splitlines() if line.strip().endswith("pom.xml")]


def read_blob(repo: Path, rev: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", "{}:{}".format(rev, path)],
        cwd=str(repo),
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _compare_pom(path: str, base_blob, candidate_blob, violations: list) -> dict:
    entry = {
        "path": path,
        "base_present": base_blob is not None,
        "candidate_present": candidate_blob is not None,
    }

    if candidate_blob is None:
        entry["verdict"] = "POM_REMOVED"
        violations.append(
            {
                "path": path,
                "kind": "test_execution_pom_removed",
                "detail": "candidate removes a POM",
            }
        )
        return entry

    base_fp = fingerprint(base_blob if base_blob is not None else b"<project/>")
    candidate_fp = fingerprint(candidate_blob)

    if candidate_fp.get("unparseable"):
        violations.append(
            {
                "path": path,
                "kind": "test_execution_pom_unparseable",
                "detail": candidate_fp["unparseable"],
            }
        )
        entry["verdict"] = "UNPARSEABLE"
        return entry

    for key in (
        "test_execution_properties",
        "build_directories",
        "test_execution_plugin_configuration",
        "post_test_lifecycle_bindings",
        "plugin_extensions",
    ):
        if base_fp.get(key) != candidate_fp.get(key):
            violations.append(
                {
                    "path": path,
                    "kind": "test_execution_definition_changed",
                    "detail": key,
                    "base": base_fp.get(key),
                    "candidate": candidate_fp.get(key),
                }
            )
    for key in BUILD_CODE_KEYS:
        if base_fp.get(key) != candidate_fp.get(key):
            violations.append(
                {
                    "path": path,
                    "kind": "build_definition_changed",
                    "detail": key,
                }
            )
    entry["verdict"] = "AUDITED"
    return entry


def audit_pom_pairs(pairs) -> dict:
    """Audit (path, base_bytes, candidate_bytes) triples. Git-free core."""
    violations: list = []
    audited = [
        _compare_pom(path, base_blob, candidate_blob, violations)
        for path, base_blob, candidate_blob in pairs
    ]
    return {
        "schema": SCHEMA,
        "status": "VIOLATION" if violations else "CLEAN",
        "audited_poms": audited,
        "violations": violations,
    }


MAVEN_CONFIG_DIR = ".mvn"


def changed_maven_config(repo: Path, base_rev: str, candidate_rev: str) -> list[str]:
    out = git(repo, "diff", "--name-only", base_rev, candidate_rev, "--", MAVEN_CONFIG_DIR)
    return [line for line in out.splitlines() if line.strip()]


def audit(repo: Path, base_rev: str, candidate_rev: str) -> dict:
    pairs = []
    for path in changed_poms(repo, base_rev, candidate_rev):
        pairs.append((path, read_blob(repo, base_rev, path), read_blob(repo, candidate_rev, path)))
    result = audit_pom_pairs(pairs)
    config = changed_maven_config(repo, base_rev, candidate_rev)
    result["maven_config_changes"] = config
    for path in config:
        # .mvn/extensions.xml loads build extensions and maven.config/jvm.config
        # inject arguments before any POM is read: always a build-code change.
        result["violations"].append({"path": path, "kind": "maven_config_changed", "detail": path})
    if result["violations"]:
        result["status"] = "VIOLATION"
    result["comparison_base_rev"] = base_rev
    result["candidate_rev"] = candidate_rev
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--comparison-base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = audit(repo, args.comparison_base, args.candidate)
    except (RuntimeError, OSError) as exc:
        result = {
            "schema": SCHEMA,
            "status": "UNKNOWN",
            "comparison_base_rev": args.comparison_base,
            "candidate_rev": args.candidate,
            "audited_poms": [],
            "violations": [],
            "error": str(exc),
        }
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("BUILD_DEFINITION_AUDIT = UNKNOWN ({})".format(exc), file=sys.stderr)
        return 2

    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        "BUILD_DEFINITION_AUDIT = {} poms_changed={} violations={}".format(
            result["status"],
            len(result["audited_poms"]),
            len(result["violations"]),
        )
    )
    return 0 if result["status"] == "CLEAN" else 1


if __name__ == "__main__":
    sys.exit(main())