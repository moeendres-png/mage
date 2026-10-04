from pathlib import Path
import subprocess,json,hashlib,gzip,xml.etree.ElementTree as ET,sys
repo=Path('/home/moeen/work/ci479-mage-c14-20261004');dest=repo/'research/c14-reference-20261004'
log=Path('/home/moeen/work/takeover-evidence-20261003/C14-native-33b000e6.log')
cmd=['mvn','-B','-pl','Mage.Verify','-am','-Dtest=VerifyCardDataTest','-Dsurefire.failIfNoSpecifiedTests=false','-Dxmage.verify.mtgjson.reference='+str(repo/'Mage.Verify/mtgjson-reference.json'),'-Dxmage.verify.mtgjson.dir=/home/moeen/work/c14-reference-20261004','test']
bad=len(sys.argv)>1 and sys.argv[1]=='missing'
report_dir=repo/'Mage.Verify/target/surefire-reports'
if bad:
 log=log.with_name('C14-missing-reference-33b000e6.log')
 report_dir=Path('/home/moeen/work/takeover-evidence-20261003/C14-missing-reference-reports')
 cmd=[arg.replace('-Dtest=VerifyCardDataTest','-Dtest=VerifyCardDataTest#test_verifyCards').replace('-Dxmage.verify.mtgjson.dir=/home/moeen/work/c14-reference-20261004','-Dxmage.verify.mtgjson.dir=/srv/c14-intentionally-missing-20261004') for arg in cmd]
 # The parent Surefire configuration does not honor reportsDirectory.
 report_dir=repo/'Mage.Verify/target/surefire-reports'
identity=lambda ref:subprocess.check_output(['git','-C',str(repo),'rev-parse',ref],text=True).strip()
sha,tree=identity('HEAD'),identity('HEAD^{tree}')
with log.open('wb') as out:proc=subprocess.run(cmd,cwd=repo,stdout=out,stderr=subprocess.STDOUT)
text=log.read_text(errors='replace')
if not (report_dir/'TEST-mage.verify.VerifyCardDataTest.xml').is_file():
 raise RuntimeError('Actual Verify report missing; execution cannot be credited')
reports={};totals={k:0 for k in ('tests','failures','errors','skipped')}
for p in report_dir.glob('TEST-*.xml'):
 raw=p.read_bytes();node=ET.fromstring(raw)
 record={k:int(node.get(k)) for k in totals};reports[p.name]={'sha256':hashlib.sha256(raw).hexdigest(),**record}
 for k in totals:totals[k]+=record[k]
 dest.joinpath(p.name+('.missing-ref' if bad else '')+'.gz').write_bytes(gzip.compress(raw,mtime=0))
lines=[l for l in text.splitlines() if any(x in l for x in ('bound reference','missing pinned file','[ERROR]','Tests run:','BUILD SUCCESS','BUILD FAILURE','Total time:'))]
doc={'source_sha':sha,'source_tree':tree,'head_after':identity('HEAD'),'command':cmd,'exit':proc.returncode,'counts':totals,'reports':reports,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'selected_log':lines,'evidence_class':'DIRECTLY_VERIFIED_NATIVE_SUBSET','qualification_credit':False,'scope':'VerifyCardDataTest only; other engine tests NOT_RUN in this local run'}
dest.joinpath('NATIVE_MISSING_REFERENCE.json' if bad else 'NATIVE_SUBSET.json').write_text(json.dumps(doc,indent=2)+'\n')
print(json.dumps(doc,indent=2))
