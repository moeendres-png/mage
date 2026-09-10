#!/usr/bin/env python3
"""Auxiliary census: T-mode / verb coverage on the frozen 1000-sample.

Reads research/d3-q6-import-automation/results_sample.json, refetches texts
from the pinned corpus clone, recompiles mode/verb stats with correct
T-vs-S distinction. Output: results directory aux_census.json
(corpus dir via D3Q6_CORPUS_DIR env or --corpus-dir).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge_script_parser import KNOWN_TRIGGER_MODES, KNOWN_ABILITY_KINDS

T_RE = re.compile(r"^T:Mode\$\s*([A-Za-z0-9_]+)", re.M)
S_RE = re.compile(r"^S:Mode\$\s*([A-Za-z0-9_]+)", re.M)
VERB_RE = re.compile(r"\b(?:SP|AB|DB)\$\s*([A-Za-z0-9_]+)")


def show(corpus_dir, ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"],
                       cwd=corpus_dir, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, r.stderr[:300]
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-dir",
                    default=os.environ.get("D3Q6_CORPUS_DIR", "/home/moeen/forge-corpus"))
    ap.add_argument("--ref", default="FETCH_HEAD")
    ap.add_argument("--sample", default="research/d3-q6-import-automation/results_sample.json")
    ap.add_argument("--out", default="research/d3-q6-import-automation/aux_census.json")
    args = ap.parse_args()

    d = json.load(open(args.sample))
    samp = d["sample"]

    tmode_all = Counter()
    tmode_unknown = Counter()
    tmode_files = 0
    smode_all = Counter()
    verb_unknown = Counter()
    verb_all = Counter()
    verb_unknown_files = 0
    texts = []
    for a in samp:
        text = show(args.corpus_dir, args.ref, a["path"])
        texts.append(text)
        tm = T_RE.findall(text)
        if tm:
            tmode_files += 1
        for m in tm:
            tmode_all[m] += 1
            if m not in KNOWN_TRIGGER_MODES:
                tmode_unknown[m] += 1
        for m in S_RE.findall(text):
            smode_all[m] += 1
        verbs = VERB_RE.findall(text)
        for v in verbs:
            verb_all[v] += 1
        unk = [v for v in verbs if v not in KNOWN_ABILITY_KINDS]
        if unk:
            verb_unknown_files += 1
        for v in unk:
            verb_unknown[v] += 1

    n = 0
    for text in texts:
        if any(m not in KNOWN_TRIGGER_MODES for m in T_RE.findall(text)):
            n += 1
    out = {
        "tmode_files": tmode_files,
        "tmode_distinct": len(tmode_all),
        "tmode_top": tmode_all.most_common(20),
        "tmode_unknown_distinct": len(tmode_unknown),
        "tmode_unknown_files": n,
        "tmode_unknown_top": tmode_unknown.most_common(20),
        "smode_top": smode_all.most_common(12),
        "verb_distinct": len(verb_all),
        "verb_top": verb_all.most_common(20),
        "verb_unknown_distinct": len(verb_unknown),
        "verb_unknown_files": verb_unknown_files,
        "verb_unknown_top": verb_unknown.most_common(20),
    }
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
