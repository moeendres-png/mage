#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

SUCCESSOR_MODEL_SHA = "cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224"
ARTIFACT_ONLY = {
    "WS33_CAMPAIGN_MERGE_GATE.json",
    "WS33_PARALLEL_BASE_REPAIR_DIFF.json",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit("WS33_G_REQUIREMENT_CANONICAL_MATERIALIZATION=FAIL " + message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--successor", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    root = args.root.resolve()
    base = args.base.resolve()
    successor = args.successor.resolve()
    out = args.out.resolve()
    if not root.is_dir() or not base.is_dir() or not successor.is_dir():
        fail("missing input directory")

    manifest = successor / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"
    if sha(manifest) != SUCCESSOR_MODEL_SHA:
        fail("successor model digest mismatch")

    base_files = {p.relative_to(base) for p in base.rglob("*") if p.is_file()}
    successor_files = {p.relative_to(successor) for p in successor.rglob("*") if p.is_file()}
    removed = sorted(base_files - successor_files)
    if removed:
        fail("successor removed files: " + ",".join(map(str, removed)))

    delta = []
    copied = []
    already = []
    skipped = []
    for rel in sorted(successor_files):
        rels = rel.as_posix()
        if rels == "WS33_HASHES.sha256" or "__pycache__" in rel.parts:
            skipped.append(rels)
            continue
        sp = successor / rel
        bp = base / rel
        ssha = sha(sp)
        bsha = sha(bp) if bp.is_file() else None
        if bsha == ssha:
            continue
        delta.append(rels)
        if rels in ARTIFACT_ONLY:
            if (root / rel).exists():
                fail("artifact-only sidecar unexpectedly canonical: " + rels)
            skipped.append(rels)
            continue
        tp = root / rel
        if not tp.is_file():
            fail("missing canonical delta target: " + rels)
        current = sha(tp)
        if current == ssha:
            already.append(rels)
            continue
        if bsha is None or current != bsha:
            fail(f"intervening canonical drift: {rels} current={current} base={bsha} successor={ssha}")
        shutil.copy2(sp, tp)
        copied.append(rels)

    if len(delta) != 319:  # excludes generated WS33_HASHES.sha256 from the 320-file artifact diff
        fail(f"unexpected errata delta cardinality: {len(delta)}")
    expected_skips = ARTIFACT_ONLY | {p.as_posix() for p in successor_files if "__pycache__" in p.parts}
    actual_special_skips = {x for x in skipped if x != "WS33_HASHES.sha256"}
    if not expected_skips.issubset(actual_special_skips):
        fail("artifact-only skip contract mismatch")

    hp = root / "WS33_HASHES.sha256"
    hp.unlink(missing_ok=True)
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.name != "WS33_HASHES.sha256" and "__pycache__" not in p.parts
    )
    hp.write_text(
        "".join(f"{sha(p)}  {p.relative_to(root).as_posix()}\n" for p in files),
        encoding="utf-8",
    )
    copied.append("WS33_HASHES.sha256")

    if sha(root / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json") != SUCCESSOR_MODEL_SHA:
        fail("canonical model digest mismatch after materialization")
    cov = load(root / "WS33_PATH_COVERAGE.json")
    counts = cov["status_counts"]
    if counts.get("PASS") != 285 or counts.get("UNKNOWN") != 3903 or counts.get("FAIL", 0) != 0 or counts.get("UNSUPPORTED", 0) != 0:
        fail("coverage mutated during model migration")
    mg = load(root / "WS33_MODEL_GATE.json")
    if not (
        mg.get("WS33_MODEL_ERRATA_GATE") == "PASS"
        and mg.get("evidence_requirement_errata_generation") == 1
        and mg.get("evidence_requirement_corrected_path_count") == 60
        and mg.get("evidence_requirement_pass_paths_changed") == 0
    ):
        fail("canonical model gate mismatch")
    abi = load(root / "abi/WS33_WITNESS_ABI_GATE.json")
    if not (
        abi.get("WS33_WITNESS_ABI_V2_1_GATE") == "PASS"
        and abi.get("negative_fixtures_rejected_for_intended_reason") is True
        and abi.get("campaign_positives_accepted") is True
        and abi.get("evidence_requirement_errata_generation") == 1
    ):
        fail("canonical ABI gate mismatch")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(copied) + "\n", encoding="utf-8")
    report = {
        "schema": "commander-simulator-next.ws33-g-requirement-canonical-materialization.v1",
        "status": "PASS",
        "successor_model_sha256": SUCCESSOR_MODEL_SHA,
        "artifact_delta_count_excluding_hashes": len(delta),
        "copied_count_including_hashes": len(copied),
        "already_successor_count": len(already),
        "artifact_only_sidecars_skipped": sorted(ARTIFACT_ONLY),
        "pycache_skipped": sorted(x for x in skipped if "__pycache__" in x),
        "coverage_mutated": False,
    }
    (out.parent / "WS33_G_REQUIREMENT_CANONICAL_MATERIALIZATION.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print("WS33_G_REQUIREMENT_CANONICAL_MATERIALIZATION=PASS " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
