#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE_HEAD = "c69686431c7296cb3e1a2f9e0de8b82886c92c46"
TARGET = "forge.game.spellability.TargetRestrictions"
OWNER = "ACTION_COST_DECISION"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33A_LOOKUP_PREPARE=FAIL " + message)


def profile(path: dict) -> str:
    names = []
    for name, key in (
        ("DECISION", "required_decision_evidence"),
        ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"),
        ("REPLAY", "required_replay_evidence"),
    ):
        if path.get(key):
            names.append(name)
    return "+".join(names) if names else "STATE_ONLY"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    args = parser.parse_args()

    base = args.base_root.resolve()
    source = args.source_root.resolve()
    out = args.out_root.resolve()
    out.mkdir(parents=True, exist_ok=True)

    coverage = load(base / "WS33_PATH_COVERAGE.json")
    manifest = load(base / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json")
    by_id = {item["v2_path_id"]: item for item in manifest["paths"]}
    assigned = {
        row["effective_v2_path_id"]
        for row in coverage["paths"]
        if row["status"] == "UNKNOWN"
        and by_id[row["effective_v2_path_id"]]["owner_family"] == OWNER
        and by_id[row["effective_v2_path_id"]]["implementation_target"] == TARGET
    }
    require(len(assigned) == 179, f"base frontier drift: expected 179, got {len(assigned)}")
    counts = Counter(profile(by_id[path_id]) for path_id in assigned)
    require(counts == Counter({
        "DECISION+REPLAY": 122,
        "DECISION+HIDDEN+REPLAY": 53,
        "DECISION+RNG+REPLAY": 2,
        "DECISION+RNG+HIDDEN+REPLAY": 2,
    }), f"base evidence-profile drift: {dict(counts)}")

    temp_tsv = out / "all-conservative.tsv"
    temp_plan = out / "all-conservative-plan.json"
    subprocess.run([
        sys.executable,
        str(source / "ws33_prepare_target_campaign.py"),
        "--manifest", str(base / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"),
        "--forge-root", str(args.forge_root.resolve()),
        "--out-tsv", str(temp_tsv),
        "--out-plan", str(temp_plan),
    ], check=True)

    lines = temp_tsv.read_text(encoding="utf-8").splitlines()
    header = [line for line in lines if line.startswith("#")]
    rows = [line for line in lines if line and not line.startswith("#")]
    selected = [line for line in rows if line.split("\t", 1)[0] in assigned]
    selected_ids = {line.split("\t", 1)[0] for line in selected}
    require(len(selected) == len(selected_ids), "duplicate selected path")
    require(len(selected) == 50, f"historical lookup-probe partition drift: expected 50, got {len(selected)}")
    require(selected_ids <= assigned, "probe selected path outside assigned frontier")

    (out / "target-cases.tsv").write_text("\n".join(header + selected) + "\n", encoding="utf-8")
    selected_profiles = Counter(profile(by_id[path_id]) for path_id in selected_ids)
    plan = {
        "schema": "commander-simulator-next.ws33a-lookup-probe-plan.v1",
        "base_head": BASE_HEAD,
        "assigned_paths_total": len(assigned),
        "probe_paths_total": len(selected_ids),
        "probe_path_ids": sorted(selected_ids),
        "probe_evidence_profiles": dict(sorted(selected_profiles.items())),
        "out_of_scope_admissions": 0,
        "purpose": "Test the systemic ability-lookup/min-max hypothesis only on base-UNKNOWN TargetRestrictions paths already selected by the shared conservative preparer.",
    }
    (out / "WS33A_LOOKUP_PROBE_PLAN.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_tsv.unlink()
    temp_plan.unlink()
    print(json.dumps({"WS33A_LOOKUP_PREPARE": "PASS", "assigned": 179, "probe": len(selected_ids)}, sort_keys=True))


if __name__ == "__main__":
    main()
