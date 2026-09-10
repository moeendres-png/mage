#!/usr/bin/env python3
"""D3 Q6 experiment runner: sample, parse, stratify, measure.

Reads blobs from a partial Forge clone via `git show FETCH_HEAD:<path>`.
Deterministic: --seed controls shuffle; input pin recorded in provenance.
Writes results JSON + summary JSON. Never promotes behavior PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_script_parser import analyze_one, PARSER_VERSION

FORGE_REMOTE = "https://github.com/Card-Forge/forge.git"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
FORGE_PIN_SUBJECT = "Fix Nori, Teller of Tales (#11713)"
FORGE_PIN_DATE = "2026-08-27T11:56:16Z"

DEFAULT_CORPUS_DIR = os.environ.get("D3Q6_CORPUS_DIR", "/home/moeen/forge-corpus")
DEFAULT_CACHE_DIR = os.environ.get("D3Q6_CACHE_DIR", "/home/moeen/.cache/d3q6")

STRATA_QUOTA = {
    "trigger": 180, "replacement": 80, "static": 110, "ability": 180,
    "keyword_vanilla": 80, "svar_heavy": 120, "targets": 150, "choices": 100,
}


def git(args, cwd):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                       timeout=120)
    return r


def list_files(corpus_dir, ref="FETCH_HEAD"):
    r = git(["ls-tree", "-r", "--name-only", ref, "--",
             "forge-gui/res/cardsfolder"], cwd=corpus_dir)
    assert r.returncode == 0, r.stderr[:500]
    files = [l for l in r.stdout.splitlines() if l.endswith(".txt")]
    # Exclude token subfolders if any leak in; keep cards + upcoming.
    return sorted(files)


def fetch_text(corpus_dir, ref, path, cache_dir):
    h = hashlib.sha256(path.encode()).hexdigest()[:16]
    cp = os.path.join(cache_dir, h + ".txt")
    if os.path.exists(cp):
        with open(cp, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=corpus_dir,
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"git show failed for {path}: {r.stderr[:300]}")
    os.makedirs(cache_dir, exist_ok=True)
    with open(cp, "w", encoding="utf-8") as f:
        f.write(r.stdout)
    return r.stdout


def primary_stratum(a):
    f = a["features"]
    if f["has_trigger"]:
        return "trigger"
    if f["has_replacement"]:
        return "replacement"
    if f["has_static"]:
        return "static"
    if f.get("nested_svar") or f["svar_edge_count"] >= 2:
        return "svar_heavy"
    if f["has_targets"]:
        return "targets"
    if f["has_choices"]:
        return "choices"
    if f["has_ability"]:
        return "ability"
    return "keyword_vanilla"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR)
    ap.add_argument("--ref", default="FETCH_HEAD")
    ap.add_argument("--seed", type=int, default=20260910)
    ap.add_argument("--candidates", type=int, default=3500)
    ap.add_argument("--sample", type=int, default=1000)
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR)
    ap.add_argument("--out", default="research/d3-q6-import-automation/results_sample.json")
    ap.add_argument("--summary", default="research/d3-q6-import-automation/results_summary.json")
    args = ap.parse_args()

    t0 = time.time()
    files = list_files(args.corpus_dir, args.ref)
    pop = len(files)
    rng = random.Random(args.seed)
    order = list(range(pop))
    rng.shuffle(order)
    cand_idx = order[: args.candidates]
    cand_paths = [files[i] for i in cand_idx]

    prov = {"forge_remote": FORGE_REMOTE, "forge_pin": FORGE_PIN,
            "forge_pin_subject": FORGE_PIN_SUBJECT, "forge_pin_date": FORGE_PIN_DATE,
            "parser_version": PARSER_VERSION, "seed": args.seed,
            "population": pop, "ref": args.ref}
    analyses, fetch_errors = [], []
    for i, p in enumerate(cand_paths):
        try:
            text = fetch_text(args.corpus_dir, args.ref, p, args.cache_dir)
        except Exception as e:  # noqa: BLE001 - record, never crash sampling
            fetch_errors.append({"path": p, "error": str(e)[:200]})
            continue
        try:
            a = analyze_one(p, text, prov)
        except Exception as e:  # noqa: BLE001 - parser must never fail overall
            fetch_errors.append({"path": p, "error": f"analyze: {e!r}"[:200]})
            continue
        analyses.append(a)
        if (i + 1) % 500 == 0:
            print(f"parsed {i+1}/{len(cand_paths)}", flush=True)

    # Stratify to target sample across mechanics (not alphabetical).
    by_stratum: dict = {}
    for a in analyses:
        by_stratum.setdefault(primary_stratum(a), []).append(a)
    for v in by_stratum.values():
        rng.shuffle(v)
    # Adversarial minimums: ensure >=15 per tag when available.
    tags_needed = ["nested_svar", "targets", "choices_modes", "mana_cost",
                   "triggers", "replacements", "hidden_info", "randomness",
                   "copy_control", "multiplayer"]
    picked, picked_paths = [], set()

    def take(a):
        if a["path"] not in picked_paths:
            picked.append(a)
            picked_paths.add(a["path"])

    for tag in tags_needed:
        c = 0
        for a in analyses:
            if len(picked) >= args.sample:
                break
            if tag in (a["taxonomy"]["adversarial_tags"]
                       if isinstance(a["taxonomy"], dict) else []) or \
               (tag == "mana_cost" and a["features"]["has_mana_cost"]) or \
               (tag == "triggers" and a["features"]["has_trigger"]) or \
               (tag == "replacements" and a["features"]["has_replacement"]):
                if a["path"] not in picked_paths:
                    take(a)
                    c += 1
                    if c >= 15:
                        break
    for stratum, quota in STRATA_QUOTA.items():
        have = sum(1 for a in picked if primary_stratum(a) == stratum)
        for a in by_stratum.get(stratum, []):
            if have >= quota or len(picked) >= args.sample:
                break
            if a["path"] not in picked_paths:
                take(a)
                have += 1
    for a in analyses:
        if len(picked) >= args.sample:
            break
        take(a)
    picked = picked[: args.sample]

    # Metrics
    n = len(picked)
    parsed_ok = sum(1 for a in picked if a["parsed"] and not any(
        d["code"] in ("missing_colon", "svar_missing_name_sep")
        for d in a["skeleton"]["diagnostics"]))
    structured = sum(1 for a in picked if a["total_params"] > 0)
    skel_gen = sum(1 for a in picked if a["skeleton_generatable"])
    manual = sum(1 for a in picked if a["manual_review_required"])
    unsup = sum(1 for a in picked if a["unsupported"])
    ambig = sum(1 for a in picked if a["ambiguous"])
    total_params = sum(a["total_params"] for a in picked)
    typed_params = sum(a["typed_params"] for a in picked)
    fp = sum(1 for a in picked if a["false_positive_probe"])
    unsup_directives: dict = {}
    for a in picked:
        for u in a["unsupported"]:
            unsup_directives[u] = unsup_directives.get(u, 0) + 1
    tag_counts: dict = {}
    fam_counts: dict = {}
    for a in picked:
        for t in a["taxonomy"]["adversarial_tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
        for f in a["taxonomy"]["families"]:
            fam_counts[f] = fam_counts.get(f, 0) + 1

    # Bounded subset: prototype trace vs independent re-extraction (20 simplest).
    simple = [a for a in picked if not a["features"].get("nested_svar")
              and not a["features"]["has_hidden"] and not a["features"]["has_random"]
              and not a["features"]["has_copy_control"]
              and not a["features"]["has_multiplayer"]]
    simple = sorted(simple, key=lambda a: (a["total_params"], a["path"]))[:20]
    trace_rows = []
    import re as _re
    for a in simple:
        text = fetch_text(args.corpus_dir, args.ref, a["path"], args.cache_dir)
        # Independent representation: crude regex line inventory (not the parser).
        ind_abilities = len(_re.findall(r"^[ATSR]:", text, flags=_re.M))
        ind_svars = len(_re.findall(r"^SVar:", text, flags=_re.M))
        f = a["features"]
        proto_n = (1 if f["has_ability"] else 0) + (1 if f["has_trigger"] else 0) + \
                  (1 if f["has_static"] else 0) + (1 if f["has_replacement"] else 0)
        match = (ind_abilities >= 1) == (proto_n >= 1) and \
                (ind_svars > 0) == (len(f["svar_names"]) > 0)
        trace_rows.append({"path": a["path"], "independent_abilities": ind_abilities,
                           "independent_svars": ind_svars,
                           "prototype_families": a["taxonomy"]["families"],
                           "trace_match": match, "behavior_pass": False,
                           "evidence_class": "SYNTHETIC"})

    summary = {
        "provenance": prov,
        "population_txt": pop,
        "candidates_fetched": len(analyses),
        "fetch_errors": len(fetch_errors),
        "sample": n,
        "metrics": {
            "parsed": parsed_ok,
            "parsed_rate": parsed_ok / n if n else 0,
            "structured": structured,
            "structured_rate": structured / n if n else 0,
            "scenario_skeleton_generatable": skel_gen,
            "skeleton_rate": skel_gen / n if n else 0,
            "manual_review_required": manual,
            "manual_rate": manual / n if n else 0,
            "unsupported_files": unsup,
            "unsupported_rate": unsup / n if n else 0,
            "ambiguous_files": ambig,
            "ambiguity_rate": ambig / n if n else 0,
            "total_params": total_params,
            "typed_params": typed_params,
            "semantic_extraction_rate": (typed_params / total_params) if total_params else 0,
            "false_positive_probes": fp,
            "false_positive_rate": fp / n if n else 0,
        },
        "unsupported_directives_top": sorted(unsup_directives.items(),
                                             key=lambda kv: -kv[1])[:30],
        "adversarial_tag_counts": tag_counts,
        "family_counts": fam_counts,
        "stratum_counts": {k: sum(1 for a in picked if primary_stratum(a) == k)
                           for k in set(primary_stratum(a) for a in picked)},
        "bounded_trace_subset": {"n": len(trace_rows),
                                 "matches": sum(1 for r in trace_rows if r["trace_match"]),
                                 "rows": trace_rows},
        "elapsed_s": round(time.time() - t0, 1),
        "disclaimer": "PARSE/IMPORT != BEHAVIOR PASS. All behavior rows remain "
                      "UNKNOWN/SYNTHETIC. No coverage promotion.",
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"provenance": prov, "sample": picked,
                   "fetch_errors": fetch_errors[:50]}, f, indent=1)
    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary["metrics"], indent=1))
    print(f"sample={n} elapsed={summary['elapsed_s']}s out={args.out}")


if __name__ == "__main__":
    main()
