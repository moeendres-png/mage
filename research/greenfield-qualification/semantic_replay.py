#!/usr/bin/env python3
"""Compare semantic replay evidence without using process noise or log text.

Only three streams are replay criteria:
  * canonical semantic engine state checkpoints,
  * game-scoped RNG events,
  * authoritative external Decision Tape events.

stdout, stderr, timestamps, PIDs, host names, job ids, and textual logs are
never compared.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from strict_decision import canonical_json_hash, canonical_semantic_state
from tape_contract import (
    validate_decision_tape,
    validate_monotonic_event_ids,
    validate_rng_tape,
    validate_state_stream,
)


SCHEMA = "commander-simulator-next.semantic-replay.v2"
WS06_RUN_SCHEMA = "commander-simulator-next.ws06-game-run.v1"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"replay evidence must be an object: {path}")
    return value


def semantic_stream(document: dict[str, Any], key: str) -> list[Any] | None:
    """Read a semantic stream from current or historical evidence."""

    value = document.get(key)
    if value is None and key == "states":
        value = document.get("semantic_trajectory", document.get("semantic_states"))
        if value is None:
            hashes = document.get("semantic_state_hashes")
            if isinstance(hashes, list):
                value = [{"sha256": item} for item in hashes]
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return [canonical_semantic_state(item) for item in value]


def provenance(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_head": document.get("source_head"),
        "source_tree": document.get("source_tree"),
        "external_pins": canonical_semantic_state(document.get("external_pins", {})),
        "scenario": document.get("scenario"),
        "seed": document.get("seed"),
        "players": document.get("players"),
        "game_id": document.get("game_id"),
        "initial_state_id": document.get("initial_state_id"),
        "decision_tape_input_sha256": document.get("decision_tape_input_sha256"),
        "rng_tape_input_sha256": document.get("rng_tape_input_sha256"),
    }


def _difference_path(expected: Any, actual: Any, prefix: str = "$") -> str:
    if type(expected) is not type(actual):
        return prefix
    if isinstance(expected, dict):
        ekeys = list(expected.keys())
        akeys = list(actual.keys())
        if ekeys != akeys:
            return prefix
        for key in ekeys:
            if expected[key] != actual[key]:
                return _difference_path(expected[key], actual[key], f"{prefix}.{key}")
        return prefix
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return prefix
        for index, (left, right) in enumerate(zip(expected, actual)):
            if left != right:
                return _difference_path(left, right, f"{prefix}[{index}]")
        return prefix
    return prefix


def first_divergence(left: list[Any], right: list[Any]) -> dict[str, Any] | None:
    for index, (expected, actual) in enumerate(zip(left, right)):
        if expected != actual:
            return {
                "index": index,
                "path": _difference_path(expected, actual),
                "expected": expected,
                "actual": actual,
            }
    if len(left) != len(right):
        index = min(len(left), len(right))
        return {
            "index": index,
            "path": "$",
            "expected": left[index] if index < len(left) else None,
            "actual": right[index] if index < len(right) else None,
        }
    return None


def stream_summary(stream: list[Any]) -> dict[str, Any]:
    return {"count": len(stream), "sha256": canonical_json_hash(stream)}


def _strict_validate_ws06(document: dict[str, Any], key: str, stream: list[Any]) -> None:
    if document.get("schema") != WS06_RUN_SCHEMA:
        # Historical unit/evidence compatibility. The WS06 workflow emits
        # WS06_RUN_SCHEMA and therefore always takes the strict path.
        if key in {"rng_events", "decision_tape"} and all(isinstance(item, dict) for item in stream):
            validate_monotonic_event_ids(stream)
        return
    if not all(isinstance(item, dict) for item in stream):
        raise ValueError(f"{key} entries must be objects")
    if key == "states":
        validate_state_stream(stream)
    elif key == "rng_events":
        validate_rng_tape(stream)
    elif key == "decision_tape":
        validate_decision_tape(stream)


def compare(inputs: list[Path]) -> dict[str, Any]:
    documents = [load(path) for path in inputs]
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "inputs": [str(path) for path in inputs],
        "fresh_processes": len(documents),
        "process_count": len(documents),
        "status": "NOT_RUN",
        "provenance": [provenance(document) for document in documents],
        "streams": {},
        "divergences": [],
        "failures": [],
        "semantic_state_divergences": None,
        "rng_event_divergences": None,
        "decision_event_divergences": None,
        "stdout_used_as_replay_criterion": False,
    }
    if len(documents) != 3:
        result["failures"].append(
            {"code": "E_PROCESS_COUNT", "message": "exactly three fresh-process records are required"}
        )
        return result

    prov = result["provenance"]
    if any(item.get("source_head") in {None, "", "UNKNOWN_SOURCE_HEAD"} for item in prov):
        result["failures"].append({"code": "E_SOURCE_HEAD", "message": "source_head is missing or unknown"})
    if any(item.get("source_tree") in {None, "", "UNKNOWN_SOURCE_TREE"} for item in prov):
        result["failures"].append({"code": "E_SOURCE_TREE", "message": "source_tree is missing or unknown"})

    # A is the record run; B/C are replay runs. Source pin, initial-state id,
    # seed, player count, scenario, and game identity must be the same. The
    # replay-input tape digests are intentionally not part of A's provenance.
    comparable_fields = (
        "source_head",
        "source_tree",
        "external_pins",
        "scenario",
        "seed",
        "players",
        "game_id",
        "initial_state_id",
    )
    for field in comparable_fields:
        if any(item.get(field) != prov[0].get(field) for item in prov[1:]):
            result["failures"].append(
                {"code": "E_PROVENANCE_MISMATCH", "field": field, "message": "replay inputs are not identically pinned"}
            )

    stream_keys = ("states", "rng_events", "decision_tape")
    divergence_counts = {key: 0 for key in stream_keys}
    for key in stream_keys:
        values = [semantic_stream(document, key) for document in documents]
        if any(value is None for value in values):
            result["failures"].append(
                {"code": "E_STREAM_MISSING", "stream": key, "message": "required semantic stream is absent"}
            )
            continue
        assert all(value is not None for value in values)
        malformed = False
        for document_index, stream in enumerate(values):
            assert stream is not None
            try:
                _strict_validate_ws06(documents[document_index], key, stream)
            except (KeyError, TypeError, ValueError) as exc:
                result["failures"].append(
                    {
                        "code": "E_TAPE_MALFORMED" if key != "states" else "E_STATE_STREAM_MALFORMED",
                        "stream": key,
                        "document": document_index,
                        "message": str(exc),
                    }
                )
                malformed = True
        if malformed:
            continue

        first = values[0]
        assert first is not None
        result["streams"][key] = {"baseline": stream_summary(first), "replays": []}
        for input_path, replay in zip(inputs[1:], values[1:]):
            assert replay is not None
            divergence = first_divergence(first, replay)
            result["streams"][key]["replays"].append(
                {
                    "input": str(input_path),
                    "summary": stream_summary(replay),
                    "matches": divergence is None,
                }
            )
            if divergence is not None:
                divergence_counts[key] += 1
                result["divergences"].append({"stream": key, "input": str(input_path), **divergence})

    result["semantic_state_divergences"] = divergence_counts["states"]
    result["rng_event_divergences"] = divergence_counts["rng_events"]
    result["decision_event_divergences"] = divergence_counts["decision_tape"]
    result["first_divergence"] = result["divergences"][0] if result["divergences"] else None

    if result["failures"]:
        result["status"] = "NOT_RUN"
    elif result["divergences"]:
        result["status"] = "FAIL"
        result["failures"].append(
            {
                "code": "E_SEMANTIC_DIVERGENCE",
                "message": "canonical semantic streams diverged; first divergence is preserved structurally",
            }
        )
    else:
        result["status"] = "PASS"
    result["canonical_result_sha256"] = canonical_json_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="inputs", action="append", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = compare([Path(value) for value in args.inputs])
    except Exception as exc:  # fail closed
        result = {
            "schema": SCHEMA,
            "status": "NOT_RUN",
            "stdout_used_as_replay_criterion": False,
            "failures": [{"code": "E_REPLAY_INPUT", "message": repr(exc)}],
        }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failures": result.get("failures", [])}, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
