#!/usr/bin/env python3
"""Separate native Maven signals. These reports are NOT trusted C12 evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

MODULES = ("Mage.Tests", "Mage.Verify")
SCHEMA = "mage.native-module-signals/1"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_suite(path):
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("XML declarations are unsupported")
    node = ET.fromstring(raw)
    if node.tag != "testsuite":
        raise ValueError("expected a single testsuite")
    counts = {}
    for key in ("tests", "failures", "errors", "skipped"):
        value = node.get(key)
        if value is None or not re.fullmatch(r"[0-9]+", value):
            raise ValueError("missing/nonnegative integer required: " + key)
        counts[key] = int(value)
    cases = node.findall("testcase")
    actual = {"tests": len(cases), "failures": sum(c.find("failure") is not None for c in cases),
              "errors": sum(c.find("error") is not None for c in cases),
              "skipped": sum(c.find("skipped") is not None for c in cases)}
    if counts != actual or sum(counts[k] for k in ("failures", "errors", "skipped")) > counts["tests"]:
        raise ValueError("suite counters disagree with testcases")
    return {"name": node.get("name"), "sha256": hashlib.sha256(raw).hexdigest(), **counts}

def collect(root, identity):
    results = {}
    log = root/'evidence/reactor.log'
    try:
        text = log.read_text()
        reactor_digest = digest(log)
    except OSError:
        text, reactor_digest = "", None
    for module in MODULES:
        paths = sorted((root/module/'target/surefire-reports').glob('TEST-*.xml'))
        suites, problems = [], []
        for path in paths:
            try:
                if path.is_symlink() or not path.is_file():
                    raise ValueError("non-regular report")
                suites.append({"path": path.relative_to(root).as_posix(), **read_suite(path)})
            except (ValueError, OSError, ET.ParseError) as exc:
                problems.append(path.name + ": " + str(exc))
        totals = {key: sum(s[key] for s in suites) for key in ("tests", "failures", "errors", "skipped")}
        reactor_name = module.replace('.', ' ')
        summaries = re.findall(r"^\[INFO\] " + re.escape(reactor_name) + r" \.+ (SUCCESS|FAILURE|SKIPPED)\b", text, re.M)
        completion = summaries[0] if len(summaries) == 1 else 'UNKNOWN'
        if problems or completion == 'UNKNOWN':
            outcome = "UNKNOWN"
        elif completion == 'FAILURE':
            outcome = "FAIL"
        elif completion == 'SKIPPED' or not paths:
            outcome = "NOT_RUN"
        elif totals['failures'] or totals['errors'] or totals['tests'] == totals['skipped']:
            outcome = "FAIL"
        else:
            outcome = "PASS"
        results[module] = {"native_outcome": outcome, "reactor_completion": completion, "reactor_log_sha256": reactor_digest, "counts": totals, "reports": suites, "problems": problems,
                           "qualification_credit": False, "complete_coverage_claimed": False,
                           "disabled_coverage": "UNKNOWN_PENDING_C16",
                           "reference_binding": "UNKNOWN_PENDING_C14" if module == "Mage.Verify" else "NOT_APPLICABLE"}
    return {"schema": SCHEMA, "identity": identity, "producer": "native Maven reports, candidate-controlled",
            "evidence_class": "NATIVE_REPORT_OBSERVED", "trusted_qualification": False, "modules": results}

def consume(doc, module, expected_sha, expected_run):
    if (doc.get('schema') != SCHEMA or doc.get('trusted_qualification') is not False
            or doc.get('identity', {}).get('checkout_sha') != expected_sha
            or str(doc.get('identity', {}).get('run_id')) != str(expected_run)):
        return "UNKNOWN"
    record = doc.get('modules', {}).get(module, {})
    outcome = record.get('native_outcome')
    counts = record.get('counts', {})
    if not all(type(counts.get(k)) is int and counts[k] >= 0 for k in ('tests', 'failures', 'errors', 'skipped')):
        return "UNKNOWN"
    completion = record.get('reactor_completion')
    derived = ('UNKNOWN' if record.get('problems') or completion not in ('SUCCESS', 'FAILURE', 'SKIPPED') else
               'FAIL' if completion == 'FAILURE' else
               'NOT_RUN' if completion == 'SKIPPED' or not record.get('reports') else
               'FAIL' if counts['failures'] or counts['errors'] or counts['tests'] == counts['skipped'] else 'PASS')
    return outcome if outcome == derived else "UNKNOWN"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    c = sub.add_parser('collect')
    c.add_argument('--root', type=Path, default=Path('.'))
    c.add_argument('--out', type=Path, required=True)
    s = sub.add_parser('signal')
    s.add_argument('--input', type=Path, required=True)
    s.add_argument('--module', choices=MODULES, required=True)
    s.add_argument('--expected-sha', required=True)
    s.add_argument('--expected-run', required=True)
    args = parser.parse_args()
    if args.mode == 'collect':
        def git(*a):
            return subprocess.check_output(['git', '-C', str(args.root), *a], text=True).strip()
        identity = {'checkout_sha': git('rev-parse', 'HEAD'), 'checkout_tree': git('rev-parse', 'HEAD^{tree}'),
                    'event_head_sha': os.environ.get('EVENT_HEAD_SHA'), 'run_id': os.environ.get('GITHUB_RUN_ID'),
                    'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
                    'workflow': '.github/workflows/maven.yml',
                    'producer_sha256': digest(Path(__file__))}
        doc = collect(args.root, identity)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
        return 0
    try:
        doc = json.loads(args.input.read_text())
        outcome = consume(doc, args.module, args.expected_sha, args.expected_run)
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        print('Native signal unavailable:', exc)
        return 2
    record = doc.get('modules', {}).get(args.module, {})
    text = f"{args.module}: native {outcome}; {record.get('counts')}; qualification credit=false; disabled coverage={record.get('disabled_coverage')}"
    print(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(text + '\n\nSource: `' + args.expected_sha + '`, run `' + args.expected_run + '`.\n')
    return 0 if outcome == 'PASS' else 1 if outcome == 'FAIL' else 2

if __name__ == '__main__':
    sys.exit(main())
