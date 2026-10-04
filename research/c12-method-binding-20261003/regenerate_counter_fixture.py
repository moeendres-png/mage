#!/usr/bin/env python3
"""Regenerate the counter-contract positive fixture through the full trusted pipeline.

The retained fixture in ../c12-independent-review-20261003 predates the
method-bound corpus (corpus-policy/1, no observed_methods), so the current scorer
correctly refuses it. This produces the same shape of evidence, one passing
ProbeTest method, with the current trusted code, and writes the source lock,
witness and a git bundle of the synthetic fixture next to this script.

Run as root with an existing unprivileged sandbox user and a cached Maven
repository; candidate Maven/Java runs only as that user:
    python3 regenerate_counter_fixture.py --sandbox-user nobody
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUAL = HERE.parents[1] / ".github" / "qualification"
sys.path.insert(0, str(QUAL))
import qualification_selftest as st  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--sandbox-user", required=True)
parser.add_argument("--maven", default="mvn")
args = parser.parse_args()

tmp = Path(tempfile.mkdtemp(prefix="c12-counter-fixture-"))
h = st.Harness(tmp, args.maven, True, st.discover_junit_classpath(), args.sandbox_user)
try:
    ok, why = st.toolchain_available(h)
    if not ok:
        sys.exit("toolchain unavailable: {}".format(why))
    fx = h.fixture("counter-fixture", st.project({"ProbeTest": st.many_methods(1)}))
    result = h.pipeline(fx)
    if result["verdict"] != "PASS":
        sys.exit("positive fixture did not PASS: {}".format(result))
    shutil.copy2(fx["evidence"] / "SOURCE_LOCK.json", HERE / "counter-fixture-SOURCE_LOCK.json")
    shutil.copy2(fx["evidence"] / "TRUSTED_WITNESS.json", HERE / "counter-fixture-TRUSTED_WITNESS.json")
    subprocess.run(["git", "-C", str(fx["repo"]), "bundle", "create", str(HERE / "counter-fixture.bundle"), "--all"],
                   check=True, capture_output=True)
    print(json.dumps({k: result[k] for k in ("verdict", "integrity", "corpus", "classes_entered")}))
finally:
    h.cleanup()
    shutil.rmtree(tmp, ignore_errors=True)
