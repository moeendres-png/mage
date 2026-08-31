#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PARALLEL_BASE_HEAD = "c69686431c7296cb3e1a2f9e0de8b82886c92c46"
PARALLEL_BASE_TREE = "6b885d02e9a0bc8cad2f93af08db99bda75955a5"
MANIFEST_BLOB = "9144281acb8c1172070973305a39715298e009fb"
COVERAGE_BLOB = "8e129db497e1db80ab1898501141fa6cedc34472"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33D_PREPARE_V2=FAIL " + message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    require(git_blob_sha(args.manifest) == MANIFEST_BLOB,
            f"effective manifest blob differs from frozen parallel base: {git_blob_sha(args.manifest)}")
    require(git_blob_sha(args.coverage) == COVERAGE_BLOB,
            f"path coverage blob differs from frozen parallel base: {git_blob_sha(args.coverage)}")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    require(manifest.get("forge_pin") == FORGE_PIN,
            f"manifest forge pin differs: {manifest.get('forge_pin')}")

    legacy_path = Path(__file__).with_name("ws33d_prepare.py")
    spec = importlib.util.spec_from_file_location("ws33d_prepare_legacy", legacy_path)
    require(spec is not None and spec.loader is not None, "cannot load frontier materializer")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    # The effective manifest was produced earlier in WS33 and intentionally
    # retained byte-for-byte by the Parallel Base Freeze.  The child boundary is
    # therefore proven by the immutable blob identities above, not by pretending
    # the manifest's historical source_head/source_tree equal the later freeze.
    module.BASE_HEAD = manifest["source_head"]
    module.BASE_TREE = manifest["source_tree"]

    old_argv = sys.argv
    try:
        sys.argv = [str(legacy_path), "--manifest", str(args.manifest), "--coverage", str(args.coverage),
                    "--forge-root", str(args.forge_root), "--out", str(args.out)]
        module.main()
    finally:
        sys.argv = old_argv

    plan_path = args.out / "WS33D_CAMPAIGN_PLAN.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    require(plan.get("assigned_paths_total") == 963, "legacy materializer did not preserve 963-path scope")
    plan["parallel_base_head"] = PARALLEL_BASE_HEAD
    plan["parallel_base_tree"] = PARALLEL_BASE_TREE
    plan["effective_manifest_blob"] = MANIFEST_BLOB
    plan["path_coverage_blob"] = COVERAGE_BLOB
    plan["manifest_production_source_head"] = manifest["source_head"]
    plan["manifest_production_source_tree"] = manifest["source_tree"]
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "WS33D_PREPARE_V2": "PASS",
        "parallel_base_head": PARALLEL_BASE_HEAD,
        "parallel_base_tree": PARALLEL_BASE_TREE,
        "manifest_blob": MANIFEST_BLOB,
        "coverage_blob": COVERAGE_BLOB,
        "assigned_paths_total": 963,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
