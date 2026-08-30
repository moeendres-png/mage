#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_CAMPAIGN_REPLAY_BIND=FAIL " + message)


def under(base: Path, relative: str) -> Path:
    base = base.resolve()
    path = (base / relative).resolve()
    require(base in path.parents, "path escapes campaign root: " + relative)
    require(path.is_file(), "missing campaign evidence: " + relative)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--overlay-manifest", type=Path, required=True)
    args = parser.parse_args()

    campaign = args.campaign_root.resolve()
    index_path = campaign / "campaign-index.json"
    if not index_path.is_file():
        print("WS33_CAMPAIGN_REPLAY_BIND=NOOP no campaign-index.json")
        return
    require(args.overlay_manifest.is_file(), "runtime overlay manifest missing")
    overlay_sha = digest(args.overlay_manifest)
    index = load(index_path)
    require(index.get("schema") == "commander-simulator-next.ws33-runtime-campaign-index.v1", "wrong campaign index schema")

    bound = 0
    for record_ref in index.get("records", []):
        record = load(under(campaign, record_ref))
        replay_ref = record.get("semantic_replay_evidence_file")
        if not replay_ref:
            continue
        replay_path = under(campaign, replay_ref)
        replay = load(replay_path)
        require(replay.get("semantic_divergence") == 0, "nonzero semantic replay divergence")
        require(replay.get("comparison_basis") == "CANONICAL_SEMANTIC_STATE", "invalid replay comparison basis")
        decision_ref = record.get("decision_tape_file")
        if replay.get("decision_tape_sha256") is not None:
            require(bool(decision_ref), "replay claims decision-tape hash without a decision tape")
            require(replay["decision_tape_sha256"] == digest(under(campaign, decision_ref)), "replay decision-tape hash mismatch")
        replay["runtime_overlay_manifest_sha256"] = overlay_sha
        replay_path.write_text(canonical(replay), encoding="utf-8")
        bound += 1

    print(json.dumps({"WS33_CAMPAIGN_REPLAY_BIND": "PASS", "bound_replays": bound, "overlay_sha256": overlay_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
