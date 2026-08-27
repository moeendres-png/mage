#!/usr/bin/env python3
"""Compare semantic replay evidence without using process noise or stderr.

The replay gate consumes only canonical state digests, RNG events, and decision
events.  It intentionally does not read logs, timestamps, process identifiers,
or wall-clock measurements as replay criteria.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from strict_decision import canonical_json_hash, canonical_semantic_state
from tape_contract import validate_monotonic_event_ids


SCHEMA = "commander-simulator-next.semantic-replay.v1"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"replay evidence must be an object: {path}")
    return value


def semantic_stream(document: dict[str, Any], key: str) -> list[Any] | None:
    """Read a stream from a GameRunEvidence or a direct replay document."""

    value = document.get(key)
    if value is None and key == "states":
        value = document.get("semantic_trajectory", document.get("semantic_states"))
        if value is None:
            hashes = document.get("semantic_state_hashes")
            if isinstance(hashes, list):
                # A producer may publish only already-canonical state digests.
                value = [{"sha256": item} for item in hashes]
    if value is None and key in {"rng_events", "decision_tape"}:
        value = document.get(key)
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
    }


def first_divergence(left: list[Any], right: list[Any]) -> dict[str, Any] | None:
    for index, (expected, actual) in enumerate(zip(left, right)):
        if expected != actual:
            return {"index": index, "expected": expected, "actual": actual}
    if len(left) != len(right):
        index = min(len(left), len(right))
        return {
            "index": index,
            "expected": left[index] if index < len(left) else None,
            "actual": right[index] if index < len(right) else None,
        }
    return None


def stream_summary(stream: list[Any]) -> dict[str, Any]:
    return {"count": len(stream), "sha256": canonical_json_hash(stream)}


def compare(inputs: list[Path]) -> dict[str, Any]:
    documents = [load(path) for path in inputs]
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "inputs": [str(path) for path in inputs],
        "process_count": len(documents),
        "status": "NOT_RUN",
        "provenance": [provenance(document) for document in documents],
        "streams": {},
        "divergences": [],
        "failures": [],
    }
    if len(documents) < 3:
        result["failures"].append({"code": "E_PROCESS_COUNT", "message": "at least three fresh-process records are required"})
        return result

    prov = result["provenance"]
    if any(item.get("source_head") in {None, "", "UNKNOWN_SOURCE_HEAD"} for item in prov):
        result["failures"].append({"code": "E_SOURCE_HEAD", "message": "source_head is missing or unknown"})
    if any(item.get("source_tree") in {None, "", "UNKNOWN_SOURCE_TREE"} for item in prov):
        result["failures"].append({"code": "E_SOURCE_TREE", "message": "source_tree is missing or unknown"})
    if any(item != prov[0] for item in prov[1:]):
        result["failures"].append({"code": "E_PROVENANCE_MISMATCH", "message": "replay inputs are not identically pinned"})

    stream_keys = ("states", "rng_events", "decision_tape")
    streams: list[tuple[str, list[Any]]] = []
    for key in stream_keys:
        values = [semantic_stream(document, key) for document in documents]
        if any(value is None for value in values):
            result["failures"].append({"code": "E_STREAM_MISSING", "stream": key, "message": "required semantic stream is absent"})
            continue
        assert all(value is not None for value in values)
        if key in {"rng_events", "decision_tape"}:
            for document_index, stream in enumerate(values):
                if not all(isinstance(item, dict) for item in stream):
                    result["failures"].append({"code": "E_TAPE_MALFORMED", "stream": key, "document": document_index, "message": "tape entries must be objects"})
                    continue
                try:
                    validate_monotonic_event_ids(stream)
                except ValueError as exc:
                    result["failures"].append({"code": "E_TAPE_ORDER", "stream": key, "document": document_index, "message": str(exc)})
            if result["failures"]:
                continue
        first = values[0]
        assert first is not None
        streams.append((key, first))
        result["streams"][key] = {"baseline": stream_summary(first), "replays": []}
        for input_path, replay in zip(inputs[1:], values[1:]):
            assert replay is not None
            divergence = first_divergence(first, replay)
            result["streams"][key]["replays"].append({
                "input": str(input_path),
                "summary": stream_summary(replay),
                "matches": divergence is None,
            })
            if divergence is not None:
                result["divergences"].append({"stream": key, "input": str(input_path), **divergence})

    if result["failures"]:
        result["status"] = "NOT_RUN"
    elif result["divergences"]:
        result["status"] = "FAIL"
        result["failures"].append({"code": "E_SEMANTIC_DIVERGENCE", "message": "canonical semantic streams diverged"})
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
        result = {"schema": SCHEMA, "status": "NOT_RUN", "failures": [{"code": "E_REPLAY_INPUT", "message": repr(exc)}]}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failures": result.get("failures", [])}, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
