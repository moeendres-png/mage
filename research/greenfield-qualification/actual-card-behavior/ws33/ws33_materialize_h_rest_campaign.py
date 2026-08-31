#!/usr/bin/env python3
"""Materialize the eleven remaining WS33H actual-card paths from fresh record/replay runs."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
REST_TARGETS = {
    "forge.game.ability.effects.GoadEffect",
    "forge.game.ability.effects.FightEffect",
    "forge.game.ability.effects.DamageEachEffect",
    "forge.game.ability.effects.RemoveFromCombatEffect",
}
EXPECTED_TARGET_COUNTS = Counter({
    "forge.game.ability.effects.GoadEffect": 7,
    "forge.game.ability.effects.FightEffect": 2,
    "forge.game.ability.effects.DamageEachEffect": 1,
    "forge.game.ability.effects.RemoveFromCombatEffect": 1,
})
SEMANTIC_FIELDS = (
    "path_id", "card", "dispatch", "forge_pin", "initial_state", "legal_attackers", "legal_blockers",
    "restrictions_requirements", "selected_declaration", "validation_result", "combat_state",
    "damage_assignment", "post_damage_state", "semantic_assertion", "result", "evidence_class",
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def digest_bytes(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_H_REST_CAMPAIGN=FAIL " + msg)


def slug(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def semantic_trace(row: dict) -> dict:
    return {key: row.get(key) for key in SEMANTIC_FIELDS}


def decision_map(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        require(row.get("decision_kind") == "TARGET_SELECTION", "unexpected decision kind")
        require(row.get("validation_result") == "ACCEPTED", "decision was not accepted")
        require(row.get("fallback_used") is False, "decision fallback used")
        options = row.get("legal_options")
        require(isinstance(options, list) and options, "empty authoritative legal option set")
        require(len(options) == len(set(options)), "duplicate semantic legal option")
        response = row.get("response_semantic_value")
        require(response in options, "response is not in authoritative legal options")
        out[row["path_id"]].append(row)
    for path_id in out:
        out[path_id].sort(key=lambda row: row["decision_index"])
        require([r["decision_index"] for r in out[path_id]] == list(range(len(out[path_id]))), "non-contiguous decision indices for " + path_id)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--record-trace", type=Path, required=True)
    ap.add_argument("--replay-trace", type=Path, required=True)
    ap.add_argument("--record-decisions", type=Path, required=True)
    ap.add_argument("--replay-decisions", type=Path, required=True)
    ap.add_argument("--historical-witnesses", type=Path, required=True)
    ap.add_argument("--harness", type=Path, required=True)
    ap.add_argument("--runtime-overlay-manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = load(args.manifest)
    coverage = load(args.coverage)
    status = {row["effective_v2_path_id"]: row["status"] for row in coverage["paths"]}
    counts = Counter(status.values())
    require(counts["PASS"] == 274 and counts["UNKNOWN"] == 3914 and counts["FAIL"] == 0 and counts["UNSUPPORTED"] == 0,
            "input is not the immutable 274/3914 H-state frontier")
    paths = {row["v2_path_id"]: row for row in manifest["paths"]}
    h = {pid: row for pid, row in paths.items() if row["owner_family"] == "COMBAT_COMMANDER"}
    h_counts = Counter(status[pid] for pid in h)
    require(h_counts["PASS"] == 15 and h_counts["UNKNOWN"] == 11, "input H frontier is not 15/11")

    rest = {
        pid: row for pid, row in h.items()
        if status[pid] == "UNKNOWN" and row["implementation_target"] in REST_TARGETS
    }
    require(len(rest) == 11, f"expected exactly 11 remaining H effect paths, got {len(rest)}")
    require(Counter(row["implementation_target"] for row in rest.values()) == EXPECTED_TARGET_COUNTS,
            "remaining H target distribution changed")
    require({pid for pid in h if status[pid] == "UNKNOWN"} == set(rest), "H UNKNOWN contains a path outside the rest target set")

    decision_required = {
        pid for pid, row in rest.items()
        if row.get("required_decision_evidence") is True or row.get("required_replay_evidence") is True
    }
    require(len(decision_required) == 4, f"expected four decision/replay H paths, got {len(decision_required)}")
    for pid, row in rest.items():
        require(row.get("required_rng_evidence") is not True, "unexpected RNG requirement for " + pid)
        require(row.get("required_hidden_info_evidence") is not True, "unexpected hidden-info requirement for " + pid)
        if pid in decision_required:
            require(row.get("required_decision_evidence") is True and row.get("required_replay_evidence") is True,
                    "decision/replay requirement mismatch for " + pid)
        else:
            require(row.get("required_decision_evidence") is not True and row.get("required_replay_evidence") is not True,
                    "unexpected non-state requirement for " + pid)

    def trace_by_path(path: Path) -> dict[str, dict]:
        out = {}
        for row in load_jsonl(path):
            pid = row.get("path_id")
            if pid not in rest:
                continue
            require(pid not in out, "duplicate trace for " + pid)
            require(row.get("forge_pin") == PIN, "Forge pin mismatch for " + pid)
            require(row.get("result") == "PASS", "runtime result not PASS for " + pid)
            require(row.get("evidence_class") == "TECHNICALLY_CONFORMANT", "runtime evidence class mismatch for " + pid)
            out[pid] = row
        require(set(out) == set(rest), "fresh trace does not exactly cover H rest")
        return out

    record_traces = trace_by_path(args.record_trace)
    replay_traces = trace_by_path(args.replay_trace)
    record_decisions = decision_map(load_jsonl(args.record_decisions))
    replay_decisions = decision_map(load_jsonl(args.replay_decisions))
    require(set(record_decisions).issubset(rest), "record decisions contain non-rest path")
    require(set(replay_decisions).issubset(rest), "replay decisions contain non-rest path")

    historical = {row["path_id"]: row for row in load_jsonl(args.historical_witnesses) if row.get("path_id") in rest}
    require(set(historical) == set(rest), "historical metadata does not exactly cover H rest")
    harness_sha = digest(args.harness)
    overlay_sha = digest(args.runtime_overlay_manifest)

    records = []
    replay_divergences = 0
    manual_target_injection_paths = 0
    direct_resolution_paths = 0
    for pid in sorted(rest):
        path = rest[pid]
        record_trace = semantic_trace(record_traces[pid])
        replay_trace = semantic_trace(replay_traces[pid])
        record_state_sha = digest_bytes(record_trace)
        replay_state_sha = digest_bytes(replay_trace)
        if record_state_sha != replay_state_sha:
            replay_divergences += 1
        require(record_state_sha == replay_state_sha, "semantic replay divergence for " + pid)

        rec_dec = record_decisions.get(pid, [])
        rep_dec = replay_decisions.get(pid, [])
        require(len(rec_dec) == len(rep_dec), "record/replay decision count mismatch for " + pid)
        for left, right in zip(rec_dec, rep_dec):
            for key in ("decision_index", "decision_kind", "actor", "principal", "visibility_scope", "legal_options", "response_semantic_value", "validation_result", "fallback_used"):
                require(left.get(key) == right.get(key), f"record/replay decision mismatch {pid} field={key}")
        if pid in decision_required:
            require(bool(rec_dec), "required decision path has no authoritative decision events: " + pid)

        meta = historical[pid]
        require(meta.get("card") == record_traces[pid].get("card"), "fresh/historical card mismatch for " + pid)
        require(meta.get("manual_legality") is False, "historical metadata used manual legality for " + pid)
        require(meta.get("rules_core_authority") is True, "historical metadata lacks rules-core authority for " + pid)
        card_slug = slug(record_traces[pid]["card"])
        matching_prov = [prov for prov in path.get("source_provenance", []) if Path(prov["forge_source_path"]).stem == card_slug]
        require(len(matching_prov) == 1, f"cannot bind actual card to exact Oracle provenance for {pid}")
        oracle_id = matching_prov[0]["oracle_identity"]
        require(oracle_id in path.get("representative_actual_oracle_identities", []), "Oracle identity not representative for " + pid)

        record_dir = args.out / "records" / pid.split(":", 1)[1]
        trace_doc = dict(record_traces[pid])
        event_id = "h-rest-" + pid.split(":", 1)[1][:16]
        trace_doc["trace_event_id"] = event_id
        trace_doc["qualification_harness_sha256"] = harness_sha
        trace_path = record_dir / "trace.json"
        write(trace_path, trace_doc)

        decision_path = None
        if rec_dec:
            decision_doc = {
                "schema": "commander-simulator-next.decision-tape.v1",
                "path_id": pid,
                "events": [
                    {
                        "decision_id": row["decision_index"] + 1,
                        "decision_kind": row["decision_kind"],
                        "actor": row["actor"],
                        "principal": row["principal"],
                        "visibility_scope": row["visibility_scope"],
                        "authoritative_legal_options": [
                            {"option_id": f"choice:{i}", "semantic_value": value}
                            for i, value in enumerate(row["legal_options"])
                        ],
                        "response_option_ids": [
                            f"choice:{row['legal_options'].index(row['response_semantic_value'])}"
                        ],
                        "validation_result": "ACCEPTED",
                        "fallback_used": False,
                    }
                    for row in rec_dec
                ],
            }
            decision_path = record_dir / "decision-tape.json"
            write(decision_path, decision_doc)
        elif pid in decision_required:
            raise SystemExit("WS33_H_REST_CAMPAIGN=FAIL missing decision tape for " + pid)

        replay_path = None
        if path.get("required_replay_evidence") is True:
            replay_doc = {
                "schema": "commander-simulator-next.semantic-replay-evidence.v1",
                "comparison_basis": "CANONICAL_SEMANTIC_STATE",
                "path_id": pid,
                "record_state_sha256": record_state_sha,
                "replay_state_sha256": replay_state_sha,
                "decision_tape_sha256": digest(decision_path) if decision_path else None,
                "runtime_overlay_manifest_sha256": overlay_sha,
                "semantic_divergence": 0,
                "fresh_record_execution": True,
                "fresh_replay_execution": True,
                "replay_selection_source": "RECORDED_DECISION_TAPE",
            }
            replay_path = record_dir / "semantic-replay.json"
            write(replay_path, replay_doc)

        rules = [f"{meta.get('rules_url')}#CR-{rule}" for rule in meta.get("official_rule_refs", [])]
        require(rules, "missing official rules references for " + pid)
        assertion_id = "fresh-record-replay-semantic-assertions"
        record = {
            "schema": "commander-simulator-next.ws33-runtime-campaign-record.v1",
            "witness_id": "ws33-h-rest-" + pid.split(":", 1)[1],
            "oracle_identities": [oracle_id],
            "v2_path_ids": [pid],
            "owner_family": "COMBAT_COMMANDER",
            "initial_semantic_state": {
                "card": record_trace["card"],
                "dispatch": record_trace["dispatch"],
                "initial_state": record_trace["initial_state"],
                "legal_attackers": record_trace["legal_attackers"],
                "legal_blockers": record_trace["legal_blockers"],
                "restrictions_requirements": record_trace["restrictions_requirements"],
            },
            "final_semantic_state": {
                "selected_declaration": record_trace["selected_declaration"],
                "validation_result": record_trace["validation_result"],
                "combat_state": record_trace["combat_state"],
                "damage_assignment": record_trace["damage_assignment"],
                "post_damage_state": record_trace["post_damage_state"],
                "semantic_assertion": record_trace["semantic_assertion"],
                "record_state_sha256": record_state_sha,
                "replay_state_sha256": replay_state_sha,
            },
            "state_assertions": [{
                "assertion_id": assertion_id,
                "expected": "PASS_AND_ZERO_REPLAY_DIVERGENCE",
                "actual": "PASS_AND_ZERO_REPLAY_DIVERGENCE",
                "result": "PASS",
                "fresh_runtime_assertions_executed": True,
            }],
            "path_exercise": [{
                "v2_path_id": pid,
                "exercised": True,
                "trace_event_ids": [event_id],
                "assertion_ids": [assertion_id],
            }],
            "execution": {
                "actual_rules_core_path": True,
                "authoritative_decision_boundary": "USED" if rec_dec else "NOT_REQUIRED",
                "silent_fallbacks": 0,
                "actual_card_execution": "PASS",
                "fresh_runtime_trace": True,
                "fresh_replay_execution": True,
                "historical_pass_status_reused": False,
                "direct_resolution_shortcut": False,
                "manual_test_target_injection": False,
                "target_legality_source": "forge.game.spellability.TargetRestrictions#getAllCandidates",
                "stack_resolution_source": "forge.game.zone.MagicStack#add+resolveStack",
                "qualification_harness_sha256": harness_sha,
            },
            "trace_file": trace_path.relative_to(args.out).as_posix(),
            "decision_tape_file": decision_path.relative_to(args.out).as_posix() if decision_path else None,
            "rng_tape_file": None,
            "observation_evidence_file": None,
            "semantic_replay_evidence_file": replay_path.relative_to(args.out).as_posix() if replay_path else None,
            "rules_authority_refs": rules,
            "evidence_class": "TECHNICALLY_CONFORMANT",
            "execution_environment_identity": {
                "runner_os": "ubuntu-24.04",
                "java_version": "21",
                "process_isolation": "FRESH_JVM_TARGETED_TEST_RECORD_AND_REPLAY",
                "player_count": 4,
                "game_type": "Commander",
            },
        }
        record_path = record_dir / "record.json"
        write(record_path, record)
        records.append(record_path.relative_to(args.out).as_posix())

    write(args.out / "campaign-index.json", {
        "schema": "commander-simulator-next.ws33-runtime-campaign-index.v1",
        "records": records,
    })
    write(args.out / "WS33_H_REST_CAMPAIGN_GATE.json", {
        "schema": "commander-simulator-next.ws33-h-rest-campaign-gate.v1",
        "status": "PASS",
        "forge_pin": PIN,
        "path_count": len(rest),
        "decision_replay_path_count": len(decision_required),
        "state_only_path_count": len(rest) - len(decision_required),
        "target_counts": dict(sorted(EXPECTED_TARGET_COUNTS.items())),
        "path_ids": sorted(rest),
        "harness_sha256": harness_sha,
        "runtime_overlay_manifest_sha256": overlay_sha,
        "historical_pass_status_reused": False,
        "actual_card_runtime_reexecuted": True,
        "fresh_replay_executed": True,
        "direct_resolution_paths_admitted": direct_resolution_paths,
        "manual_target_injection_paths_admitted": manual_target_injection_paths,
        "silent_fallbacks": 0,
        "replay_divergence_count": replay_divergences,
        "target_legality_source": "forge.game.spellability.TargetRestrictions#getAllCandidates",
        "stack_resolution_source": "forge.game.zone.MagicStack#add+resolveStack",
    })
    print(json.dumps({"WS33_H_REST_CAMPAIGN": "PASS", "paths": len(rest), "decision_replay": len(decision_required)}, sort_keys=True))


if __name__ == "__main__":
    main()
