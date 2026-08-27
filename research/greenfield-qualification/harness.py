#!/usr/bin/env python3
"""Neutral greenfield engine qualification harness.

This module does not implement Magic rules. It executes candidate-owned probes,
records exact inputs/outputs, and normalizes status/artifact metadata. A probe is
PASS only when the invoked process exits 0 and, when requested, produces a valid
observable JSON document. Missing probes are NOT_RUN; declared unsupported probes
must be marked explicitly by the caller.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

VALID_STATUS = {"PASS", "FAIL", "UNSUPPORTED", "NOT_RUN"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def canonical_json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def base_result(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "candidate": args.candidate,
        "commit": args.commit,
        "scenario": args.scenario,
        "seed": args.seed,
        "players": args.players,
        "decisions": [],
        "state_hashes": [],
        "events": [],
        "result": {"status": "NOT_RUN"},
        "runtime": {},
        "failures": [],
        "evidence_level": args.evidence_level,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--scenario", required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--players", type=int, default=0)
    p.add_argument("--evidence-level", default="L3_LOCALLY_EXECUTED")
    p.add_argument("--command")
    p.add_argument("--cwd", default=".")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--observable-json")
    p.add_argument("--status", choices=sorted(VALID_STATUS))
    p.add_argument("--reason")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    record = base_result(args)

    if args.status in {"UNSUPPORTED", "NOT_RUN"}:
        record["result"]["status"] = args.status
        if args.reason:
            record["failures"].append({"code": "E_" + args.status, "message": args.reason})
        out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0

    if not args.command:
        record["failures"].append({"code": "E_HARNESS", "message": "No command supplied"})
        record["result"]["status"] = "NOT_RUN"
        out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 2

    started = time.monotonic()
    started_epoch = time.time()
    try:
        proc = subprocess.run(
            args.command,
            cwd=args.cwd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=args.timeout,
            env=os.environ.copy(),
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        proc = None
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

    elapsed = time.monotonic() - started
    record["runtime"] = {
        "wall_seconds": round(elapsed, 6),
        "started_epoch": started_epoch,
        "timeout_seconds": args.timeout,
        "command": args.command,
        "cwd": args.cwd,
    }

    stdout_path = out.with_suffix(out.suffix + ".stdout.log")
    stderr_path = out.with_suffix(out.suffix + ".stderr.log")

    if timed_out:
        stdout_path.write_text(str(stdout), encoding="utf-8")
        stderr_path.write_text(str(stderr), encoding="utf-8")
        record["result"]["status"] = "FAIL"
        record["failures"].append({"code": "E_TIMEOUT", "message": "Probe timed out"})
        record["runtime"]["exit_code"] = None
    else:
        assert proc is not None
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")
        record["runtime"]["exit_code"] = proc.returncode
        record["runtime"]["stdout_sha256"] = sha256_file(stdout_path)
        record["runtime"]["stderr_sha256"] = sha256_file(stderr_path)
        if proc.returncode != 0:
            record["result"]["status"] = "FAIL"
            record["failures"].append({"code": "E_PROBE_EXIT", "message": f"Probe exit {proc.returncode}"})
        else:
            record["result"]["status"] = "PASS"

    if args.observable_json:
        obs_path = Path(args.observable_json)
        if not obs_path.is_absolute():
            obs_path = Path(args.cwd) / obs_path
        if not obs_path.exists():
            record["result"]["status"] = "FAIL"
            record["failures"].append({"code": "E_OBSERVABLE_MISSING", "message": str(obs_path)})
        else:
            try:
                observable = load_json(obs_path)
                record["events"].append({"kind": "canonical_observable", "sha256": canonical_json_hash(observable)})
                record["state_hashes"].append(canonical_json_hash(observable))
                record["runtime"]["observable_file_sha256"] = sha256_file(obs_path)
            except Exception as exc:  # fail closed
                record["result"]["status"] = "FAIL"
                record["failures"].append({"code": "E_OBSERVABLE_INVALID", "message": repr(exc)})

    if args.status == "FAIL":
        record["result"]["status"] = "FAIL"
        if args.reason:
            record["failures"].append({"code": "E_DECLARED_FAIL", "message": args.reason})

    out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if record["result"]["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
