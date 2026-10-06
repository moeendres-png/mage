#!/usr/bin/env python3
"""C16: source-bound verifier omissions; source inventory is not runtime proof."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'qualification'))
import corpus_policy

SCHEMA = 'mage.verifier-gap-inventory/1'
BASELINE = '.github/ci/verifier_gap_baseline.json'
UTILITY_METHODS = {'list_ChangelogHelper', 'downloadAndPrepareCommanderBracketsData'}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def c16_method_name(identity):
    """Adapt C12 full method identities to C16's established name-only schema."""
    local = str(identity).rsplit('#', 1)[-1]
    return local.split('(', 1)[0]

def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)

def inventory(repo, rev):
    files, records = {}, []
    lines = git(repo, 'ls-tree', '-r', '-z', rev, 'Mage.Verify/src').split(b'\0')
    for item in lines:
        if not item:
            continue
        header, rawpath = item.split(b'\t', 1)
        path = rawpath.decode('utf-8')
        if not path.endswith('.java'):
            continue
        if header.split()[0] != b'100644':
            raise ValueError('non-regular verifier source: ' + path)
        raw = git(repo, 'show', rev + ':' + path)
        files[path] = digest(raw)
        text = raw.decode('utf-8')
        enabled, disabled = corpus_policy.java_test_methods(text)
        for method in sorted({c16_method_name(identity) for identity in disabled}):
            records.append({'kind': 'DISABLED_TEST', 'path': path, 'method': method,
                            'status': 'NOT_RUN', 'evidence_class': 'CODE_DERIVED',
                            'role': 'MAINTENANCE_UTILITY' if method in UTILITY_METHODS else 'VERIFICATION_GAP'})
        for number, line in enumerate(text.splitlines(), 1):
            # Deliberately conservative review surface: normal exits and comments
            # can occur here. These are potential omissions, not proven disabled behavior.
            if re.search(r'\b(return|continue|skipListAddName|skipListHaveName|Assume|assume\w*)\b|TODO|CHECK_\w+|//\s*check\w+\s*\(', line):
                records.append({'kind': 'REVIEW_SURFACE', 'path': path, 'line': number,
                                'source': line.strip(), 'status': 'UNKNOWN',
                                'evidence_class': 'CODE_DERIVED_POTENTIAL_OMISSION'})
    if not files:
        raise ValueError('Verifier source inventory missing')
    return {'schema': SCHEMA, 'source_files': files, 'records': records,
            'qualification_credit': False, 'complete_semantic_coverage_claimed': False}

def read_baseline(repo, rev):
    return json.loads(git(repo, 'show', rev + ':' + BASELINE))

def is_ancestor(repo, older, newer):
    return subprocess.run(
        ['git', '-C', str(repo), 'merge-base', '--is-ancestor', older, newer],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ).returncode == 0

def compare(actual, candidate_baseline, anchor_inventory, anchor_baseline):
    # The reviewed anchor must be self-consistent before it can ratchet anything.
    if anchor_baseline != anchor_inventory:
        return 'UNKNOWN'
    # Candidate baseline edits cannot authorize themselves.
    if candidate_baseline != actual:
        return 'REVIEW_REQUIRED'
    # Even coordinated candidate source+baseline drift requires explicit adjudication.
    if actual != anchor_inventory:
        return 'REVIEW_REQUIRED'
    return 'SOURCE_INVENTORY_MATCH'

def observe(repo, rev, runtime_root, baseline_rev):
    try:
        if not baseline_rev:
            raise ValueError('baseline revision is required')
        source_sha = git(repo, 'rev-parse', rev).decode().strip()
        anchor_sha = git(repo, 'rev-parse', baseline_rev).decode().strip()
        if not is_ancestor(repo, anchor_sha, source_sha):
            raise ValueError('baseline revision is not an ancestor of candidate revision')

        actual = inventory(repo, source_sha)
        candidate_baseline = read_baseline(repo, source_sha)
        anchor_inventory = inventory(repo, anchor_sha)
        anchor_baseline = read_baseline(repo, anchor_sha)
        status = compare(actual, candidate_baseline, anchor_inventory, anchor_baseline)

        disabled = [r for r in actual['records'] if r['kind']=='DISABLED_TEST']
        skipped, executed, invalid = [], [], []
        reports = sorted((runtime_root/'Mage.Verify/target/surefire-reports').glob('TEST-*.xml'))
        for path in reports:
            try:
                raw=path.read_bytes()
                if path.is_symlink() or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                    raise ValueError('non-regular/unsupported XML')
                node=ET.fromstring(raw)
                if node.tag!='testsuite':
                    raise ValueError('unsupported suite')
                for case in node.findall('testcase'):
                    entry={'class':case.get('classname'), 'method':case.get('name'),
                           'report_sha256':digest(raw)}
                    (skipped if case.find('skipped') is not None else executed).append(entry)
            except (OSError, ValueError, ET.ParseError) as exc:
                invalid.append(path.name+':'+str(exc))
        return {'status': status, 'source_sha': source_sha,
                'source_tree':git(repo,'rev-parse',source_sha+'^{tree}').decode().strip(),
                'baseline_anchor_sha': anchor_sha,
                'baseline_anchor_tree':git(repo,'rev-parse',anchor_sha+'^{tree}').decode().strip(),
                'baseline_anchor_relation':'ANCESTOR_OR_SELF',
                'anchor_baseline_matches_source': anchor_baseline == anchor_inventory,
                'candidate_baseline_matches_source': candidate_baseline == actual,
                'source_changed_from_anchor': actual != anchor_inventory,
                'baseline_changed_from_anchor': candidate_baseline != anchor_baseline,
                'inventory': actual, 'disabled_tests': disabled, 'runtime_skipped': skipped,
                'runtime_executed_count': len(executed), 'runtime_reports_present': bool(reports),
                'runtime_problems': invalid, 'qualification_credit': False,
                'scope': 'Source omissions are CODE_DERIVED. XML names are candidate-controlled observations. The base revision is a review/ratchet anchor only; no full branch or hostile-code authority claim.'}
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError, OSError, KeyError, TypeError) as exc:
        return {'status': 'UNKNOWN',
                'reason':'Verifier source or baseline unavailable/invalid at candidate or declared base revision',
                'qualification_credit':False}

def render(doc):
    lines=['# Mage.Verify execution and omission inventory', '',
           'Inventory status: '+doc['status'], '',
           'Source inventory does not prove runtime coverage. Disabled checks are NOT_RUN; branch review surfaces remain UNKNOWN.', '']
    if doc.get('baseline_anchor_sha'):
        lines += ['Review anchor: `'+doc['baseline_anchor_sha']+'` ('+doc.get('baseline_anchor_relation','UNKNOWN')+')',
                  'Anchor baseline/source match: '+str(doc.get('anchor_baseline_matches_source'))+
                  '; candidate baseline/source match: '+str(doc.get('candidate_baseline_matches_source'))+
                  '; source drift: '+str(doc.get('source_changed_from_anchor'))+
                  '; baseline drift: '+str(doc.get('baseline_changed_from_anchor')), '']
    for record in doc.get('disabled_tests', []):
        lines.append('- '+record['method']+' — '+record['role']+' / NOT_RUN (`'+record['path']+'`)')
    lines += ['', 'Runtime XML: executed='+str(doc.get('runtime_executed_count',0))+
              ', skipped='+str(len(doc.get('runtime_skipped',[])))+'. These counts have no qualification credit.', '']
    for record in doc.get('inventory',{}).get('records',[]):
        if record['kind']=='REVIEW_SURFACE':
            lines.append('- UNKNOWN `'+record['path']+':'+str(record['line'])+'`: '+record['source'])
    return '\n'.join(lines)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['check','generate'])
    parser.add_argument('--repo',type=Path,default=Path('.'))
    parser.add_argument('--rev',default='HEAD')
    parser.add_argument('--baseline-rev')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--markdown',type=Path)
    args=parser.parse_args()
    if args.mode=='generate':
        doc=inventory(args.repo,args.rev)
    else:
        doc=observe(args.repo,args.rev,args.repo,args.baseline_rev)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    if args.markdown:
        args.markdown.write_text(render(doc))
    print('Verifier gap inventory: '+doc.get('status','GENERATED'))
    return 0 if args.mode=='generate' or doc['status']=='SOURCE_INVENTORY_MATCH' else 1

if __name__=='__main__':
    sys.exit(main())
