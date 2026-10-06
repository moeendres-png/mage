import importlib.util,json,sys,subprocess,shutil
from pathlib import Path
repo=Path('/home/moeen/work/ci479-mage-c12-20261003'); q=repo/'.github/qualification'
sys.path.insert(0,str(q)); import qualification_selftest as m
tmp=Path('/var/lib/c12-current-counter-20261004'); tmp.mkdir(mode=0o700)
h=m.Harness(tmp,'/usr/bin/mvn',True,'/home/moeen/.m2/repository/org/junit/platform/junit-platform-console-standalone/1.9.3/junit-platform-console-standalone-1.9.3.jar','nobody')
h.seed='/home/moeen/.m2/repository'; h.sandbox_dir=Path('/srv/c12-current-counter-20261004'); h.bundle_dir=tmp/'bundle'; h.runtime_dir=tmp/'runtime'
fx=h.fixture('counter-positive',m.project({'ProbeTest':m.many_methods(1)})); result=h.pipeline(fx)
print(json.dumps(result),flush=True); assert result['verdict']=='PASS'
out=repo/'research/c12-qualified-signatures-20261004'
for file in ['SOURCE_LOCK.json','TRUSTED_WITNESS.json','INTEGRITY.json','QUALIFICATION_EVIDENCE.json']:
 shutil.copy(fx['evidence']/file,out/('counter-fixture-'+file))
subprocess.run(['git','-c',f'safe.directory={fx["repo"]}','-C',str(fx['repo']),'bundle','create',str(out/'counter-fixture.bundle'),'--all'],check=True)
(out/'COUNTER_REPRODUCTION.json').write_text(json.dumps({'actual_full_pipeline_result':result,'inputs':{'maven':'/usr/bin/mvn','offline':True,'maven_seed':'/home/moeen/.m2/repository','junit':'org.junit.platform:junit-platform-console-standalone:1.9.3','sandbox_user':'nobody','java':'OpenJDK21.0.12.1'},'producer_hashes':{p.name:__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in q.glob('*') if p.is_file() and p.suffix in ('.py','.java')}},indent=2)+'\n')
