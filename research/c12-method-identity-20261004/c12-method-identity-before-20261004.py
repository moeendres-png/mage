import importlib.util, json, sys, subprocess
from pathlib import Path
repo=Path('/home/moeen/work/ci479-mage-c12-20261003')
qual=repo/'.github/qualification'
sys.path.insert(0,str(qual))
spec=importlib.util.spec_from_file_location('qualification_selftest',qual/'qualification_selftest.py')
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)
tmp=Path('/var/lib/c12-nested-identity-before-v3-20261004')
tmp.mkdir(mode=0o700)
h=m.Harness(tmp,'/usr/bin/mvn',True,'/home/moeen/.m2/repository/org/junit/platform/junit-platform-console-standalone/1.9.3/junit-platform-console-standalone-1.9.3.jar','nobody')
h.seed='/home/moeen/.m2/repository'
h.sandbox_dir=Path('/srv/c12-nested-identity-before-v3-20261004')
h.bundle_dir=tmp/'bundle'
h.runtime_dir=tmp/'runtime'
def source(two):
    return '''package probe;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Nested;
public class ProbeTest {
  @Nested class Left { @Test public void proof() {} }
'''+('  @Nested class Right { @Test public void proof() {} }\n' if two else '')+'}\n'
rows={}
for name,candidate in [('unchanged-two-nested-tests',None),('removed-one-same-named-nested-test',m.project({'ProbeTest':source(False)}))]:
    fx=h.fixture(name,m.project({'ProbeTest':source(True)}),candidate)
    result=h.pipeline(fx)
    records={name:json.loads((fx['evidence']/name).read_text()) for name in ['SOURCE_LOCK.json','TRUSTED_WITNESS.json','INTEGRITY.json','QUALIFICATION_EVIDENCE.json'] if (fx['evidence']/name).exists()}
    rows[name]={'result':result,'records':records}
    print(json.dumps({'case':name,'result':result}),flush=True)
report={'qualification_source_sha':subprocess.check_output(['git','-c',f'safe.directory={repo}','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'class':'DIRECTLY_VERIFIED synthetic corpus control, not Mage Rules behavior','cases':rows}
out=Path('/home/moeen/work/takeover-evidence-20261003/C12-nested-identity-BEFORE-v3.json')
out.write_text(json.dumps(report,indent=2)+'\n')
out.chmod(0o644)

