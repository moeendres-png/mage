#!/usr/bin/env python3
"""Reproduce the two C12 findings through the published trusted pipeline.

Requires root, an existing unprivileged sandbox user and cached Maven/JUnit.
No candidate code is run as root. Work roots must be new bounded directories.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--work-root", type=Path, required=True)
parser.add_argument("--sandbox-root", type=Path, required=True)
parser.add_argument("--seed-maven-repo", required=True)
parser.add_argument("--junit-classpath", required=True)
parser.add_argument("--sandbox-user", required=True)
parser.add_argument("--maven", default="mvn")
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
qual = args.repo.resolve() / ".github/qualification"
sys.path.insert(0, str(qual))
spec = importlib.util.spec_from_file_location("qualification_selftest", qual / "qualification_selftest.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
args.work_root.mkdir(mode=0o700)
h = m.Harness(args.work_root, args.maven, True, args.junit_classpath, args.sandbox_user)
h.seed = args.seed_maven_repo
h.sandbox_dir = args.sandbox_root
h.bundle_dir = args.work_root / "bundle"
h.runtime_dir = args.work_root / "runtime"

def source(n):
    return "package probe; import org.junit.jupiter.api.Test; public class ProbeTest {\n" + "".join(
        "@Test public void test%d() {}\n" % i for i in range(n)
    ) + "}\n"

driver = (qual / "TrustedTestDriver.java").read_text()
# Replace only the emitted counter, retaining honest execution and exit status.
needle = next(line for line in driver.splitlines() if 'tests_failed' in line and '.append(failed)' in line)
driver = driver.replace(needle, needle.replace(".append(failed)", ".append(-1)"))
cases = [
    ("unchanged-ten-methods", m.project({"ProbeTest": source(10)}), None, {}),
    ("ten-methods-to-one", m.project({"ProbeTest": source(10)}), m.project({"ProbeTest": source(1)}), {}),
    ("authenticated-negative-counter", m.project({"ProbeTest": m.passing("ProbeTest")}), None,
     {"trusted_followup": {m.FIXTURE_QUAL + "/TrustedTestDriver.java": driver}}),
]
results = {}
for name, base, candidate, kwargs in cases:
    fixture = h.fixture(name, base, candidate, **kwargs)
    results[name] = h.pipeline(fixture)
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
