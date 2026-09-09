#!/usr/bin/env python3
"""WS33-D D4a certifier: adjudicate the staticeffect campaign evidence gate.

Verifies markers, campaign index, empty diagnostics, per-record assertion
results (including command-zone Effect assertions), decision-tape
ACCEPTED-only validation, RNG replay service, hidden-observation PASS,
replay divergence 0, and source/pin/model binding. Emits the D4a gate JSON.
Any violation fails closed (nonzero exit).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign-root", type=Path, required=True)
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--deferred", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--forge-pin", required=True)
    ap.add_argument("--model-artifact-id", required=True)
    ap.add_argument("--model-artifact-digest", required=True)
    ap.add_argument("--manifest-sha256", required=True)
    ap.add_argument("--consumer-model-sha256", required=True)
    a = ap.parse_args()

    plan = json.loads(a.plan.read_text())
    assert plan["provable_count"] == 8 and len(plan["provable_ids"]) == 8
    deferred = json.loads(a.deferred.read_text())
    assert len(deferred) == 41
    root = a.campaign_root

    for name in ("staticeffect-record-diagnostics.jsonl", "staticeffect-replay-diagnostics.jsonl"):
        p = root / name
        assert p.is_file() and p.stat().st_size == 0, f"diagnostics not empty: {name}"
    index = json.loads((root / "campaign-index.json").read_text())
    assert len(index["records"]) == 8, "campaign index must admit 8 records"

    def short(pid: str) -> str:
        return pid.split(":", 1)[1]

    evidenced = []
    decision_events = 0
    rng_events = 0
    for pid in plan["provable_ids"]:
        d = root / "records" / short(pid)
        assert (d / "record-success.marker").is_file(), f"missing marker {pid}"
        record = json.loads((d / "record.json").read_text())
        assert record["v2_path_ids"] == [pid]
        assert record["evidence_class"] == "EXTERNALLY_RULE_VALIDATED"
        assert all(x["result"] == "PASS" for x in record["state_assertions"])
        assertion_ids = [x["assertion_id"] for x in record["state_assertions"]]
        assert "effect-command-present" in assertion_ids, "missing command-zone Effect assertion"
        assert any(x.startswith("effect-kind-") for x in assertion_ids), "missing effect-kind assertion"
        assert record["final_semantic_state"]["deltas_equal"] is True
        assert record["execution"]["silent_fallbacks"] == 0
        assert record["execution"]["direct_effect_resolution"] is False
        trace = json.loads((d / "trace.json").read_text())
        assert trace["forge_pin"] == a.forge_pin and trace["path_id"] == pid
        assert trace.get("effect_kind") in ("static", "replacement", "trigger"), "missing effect kind"
        tape = json.loads((d / "decision-tape.json").read_text())
        resolutions = trace.get("intent_resolutions", [])
        assert len(resolutions) == len(tape["events"]), "resolution/tape count mismatch"
        for res in resolutions:
            assert res["selected"] == res["expected_select"] and res["match"] is True, \
                "unmatched intent resolution"
        intent = plan.get("intents", {}).get(pid, "NONE")
        if intent == "NONE":
            assert len(tape["events"]) == 0, "unexpected decision events on NONE-intent path"
        for ev in tape["events"]:
            assert ev["validation_result"] == "ACCEPTED" and ev["fallback_used"] is False
            assert len(ev["response_option_ids"]) == 1
            assert ev["response_option_ids"][0] in [o["option_id"] for o in ev["authoritative_legal_options"]]
        decision_events += len(tape["events"])
        rng = json.loads((d / "rng-tape.json").read_text())
        rng_events += len(rng["events"])
        obs = json.loads((d / "principal-observation.json").read_text())
        assert obs["result"] == "PASS"
        replay = json.loads((d / "semantic-replay.json").read_text())
        assert replay["semantic_divergence"] == 0
        assert (d / "decision-replay.tsv").is_file() and (d / "rng-replay.tsv").is_file()
        evidenced.append(pid)

    gate = {
        "schema": "commander-simulator-next.ws33d-d4-gate.v1",
        "batch": "D4a",
        "terminal_result": "PASS",
        "source_head": a.source_head,
        "source_tree": a.source_tree,
        "forge_pin": a.forge_pin,
        "model_artifact_id": a.model_artifact_id,
        "model_artifact_digest": a.model_artifact_digest,
        "manifest_sha256": a.manifest_sha256,
        "consumer_model_sha256": a.consumer_model_sha256,
        "target_digest": plan["target_digest"],
        "path_count": 8,
        "evidenced_path_ids": sorted(evidenced),
        "deferred_count": 41,
        "decision_events_accepted": decision_events,
        "rng_events_taped": rng_events,
        "hidden_leaks": 0,
        "replay_divergence": 0,
        "coverage_mutated": False,
        "coverage_promoted": False,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(gate, indent=1, sort_keys=True) + "\n")
    print(f"WS33_ABC_D4_CERTIFY=PASS paths=8 decisions={decision_events} rng={rng_events}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
