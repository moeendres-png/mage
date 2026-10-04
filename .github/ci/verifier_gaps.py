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
        for method in sorted(disabled):
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

def compare(actual, baseline):
    # Full source bytes are bound, so an unrecognized suppression spelling,
    # removal, rename, comment trick or new source file also requires adjudication.
    if baseline != actual:
        return 'REVIEW_REQUIRED'
    return 'SOURCE_INVENTORY_MATCH'

def observe(repo, rev, runtime_root):
    try:
        actual = inventory(repo, rev)
        baseline = json.loads(git(repo, 'show', rev+':'+BASELINE))
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
        return {'status': compare(actual, baseline), 'inventory': actual,
                'disabled_tests': disabled, 'runtime_skipped': skipped,
                'runtime_executed_count': len(executed), 'runtime_reports_present': bool(reports),
                'runtime_problems': invalid, 'qualification_credit': False,
                'scope': 'Source omissions are CODE_DERIVED. XML names are candidate-controlled observations. No full branch or hostile-code authority claim.'}
    except (subprocess.CalledProcessError, ValueError, OSError, KeyError, TypeError) as exc:
        return {'status': 'UNKNOWN', 'reason':'Verifier source or baseline unavailable/invalid at declared revision', 'qualification_credit':False}

def render(doc):
    lines=['# Mage.Verify execution and omission inventory', '',
           'Inventory status: '+doc['status'], '',
           'Source inventory does not prove runtime coverage. Disabled checks are NOT_RUN; branch review surfaces remain UNKNOWN.', '']
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
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--markdown',type=Path)
    args=parser.parse_args()
    if args.mode=='generate':
        doc=inventory(args.repo,args.rev)
    else:
        doc=observe(args.repo,args.rev,args.repo)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    if args.markdown:
        args.markdown.write_text(render(doc))
    print('Verifier gap inventory: '+doc.get('status','GENERATED'))
    return 0 if args.mode=='generate' or doc['status']=='SOURCE_INVENTORY_MATCH' else 1

if __name__=='__main__':
    sys.exit(main())
