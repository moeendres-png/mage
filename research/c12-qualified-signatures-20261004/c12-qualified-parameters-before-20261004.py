import importlib.util, json, sys, subprocess
from pathlib import Path
repo=Path('/home/moeen/work/ci479-mage-c12-20261003')
qual=repo/'.github/qualification'
sys.path.insert(0,str(qual))
spec=importlib.util.spec_from_file_location('qualification_selftest',qual/'qualification_selftest.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
tmp=Path('/var/lib/c12-qualified-parameters-before-20261004'); tmp.mkdir(mode=0o700)
h=m.Harness(tmp,'/usr/bin/mvn',True,'/home/moeen/.m2/repository/org/junit/platform/junit-platform-console-standalone/1.9.3/junit-platform-console-standalone-1.9.3.jar','nobody')
h.seed='/home/moeen/.m2/repository'; h.sandbox_dir=Path('/srv/c12-qualified-parameters-before-20261004'); h.bundle_dir=tmp/'bundle'; h.runtime_dir=tmp/'runtime'
source='''package probe;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
public class ProbeTest {
 @ParameterizedTest @MethodSource("arguments") void proof(one.Foo value) {}
 static java.util.stream.Stream<one.Foo> arguments() { return java.util.stream.Stream.of(new one.Foo()); }
}
'''
extra={'src/main/java/one/Foo.java':'package one; public class Foo {}', 'src/main/java/two/Foo.java':'package two; public class Foo {}'}
base=m.project({'ProbeTest':source},extra=extra)
rows={}
for name,candidate in [('unchanged-qualified-type',None),('replaced-qualified-type',m.project({'ProbeTest':source.replace('one.Foo','two.Foo')},extra=extra))]:
 fx=h.fixture(name,base,candidate); result=h.pipeline(fx)
 records={p:json.loads((fx['evidence']/p).read_text()) for p in ['SOURCE_LOCK.json','TRUSTED_WITNESS.json','INTEGRITY.json','QUALIFICATION_EVIDENCE.json'] if (fx['evidence']/p).exists()}
 rows[name]={'result':result,'records':records}; print(json.dumps({'case':name,'result':result}),flush=True)
 candidate_sha=records['SOURCE_LOCK.json']['candidate']['sha']
 subprocess.run(['git','-c',f'safe.directory={fx["repo"]}','-C',str(fx['repo']),'branch','audit-c12-qualified-before',candidate_sha],check=True)
 subprocess.run(['git','-c',f'safe.directory={fx["repo"]}','-C',str(fx['repo']),'bundle','create',str(tmp/(name+'.bundle')),'audit-c12-qualified-before'],check=True)
report={'qualification_source_sha':subprocess.check_output(['git','-c',f'safe.directory={repo}','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'class':'DIRECTLY_VERIFIED synthetic full-path controls; not Rules or hostile-JVM qualification','cases':rows}
out=Path('/home/moeen/work/takeover-evidence-20261003/C12-qualified-parameters-BEFORE.json'); out.write_text(json.dumps(report,indent=2)+'\n'); out.chmod(0o644)
