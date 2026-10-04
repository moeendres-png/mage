from pathlib import Path
import json, os, sys, subprocess, tempfile

repo = Path('/home/moeen/work/ci479-mage-c12-20261003')
qual = repo / '.github/qualification'
sys.path.insert(0, str(qual))
import qualification_selftest as m

mode = sys.argv[1]
root = Path('/var/lib/c12-log-' + mode + '-20261004')
root.mkdir(exist_ok=True, parents=True)
h = m.Harness(Path(tempfile.mkdtemp(dir=root)), '/usr/bin/mvn', False,
    '/home/moeen/.m2/repository/org/junit/platform/junit-platform-console-standalone/1.9.3/junit-platform-console-standalone-1.9.3.jar', 'nobody')
h.seed = '/home/moeen/.m2/repository'
h.bundle_dir = root / 'bundle'
h.runtime_dir = root / 'runtime'
h.sandbox_dir = Path('/srv/c12-log-' + mode + '-20261004')
pom = m.build_pom().replace('<groupId>org.junit.jupiter</groupId>\n      <artifactId>junit-jupiter</artifactId>\n      <version>5.8.1</version>', '<groupId>junit</groupId>\n      <artifactId>junit</artifactId>\n      <version>4.13.2</version>', 1)
probe = '''package probe;
import org.junit.Test;
import org.junit.runner.RunWith;
@RunWith(ProbeRunner.class)
public class ProbeTest { @Test public void proof() {} }
'''
runner = r'''package probe;
import org.junit.runner.Runner;
import org.junit.runner.Description;
import org.junit.runner.notification.RunNotifier;
import org.junit.runner.notification.Failure;
public class ProbeRunner extends Runner {
 public ProbeRunner(Class<?> cls) {}
 private Description bad() { return Description.createSuiteDescription("candidate\n::notice::FORGED-C12-LOG"); }
 public Description getDescription() {
  Description root = Description.createSuiteDescription(ProbeTest.class);
  root.addChild(bad());
  return root;
 }
 public void run(RunNotifier n) {
  Description d = bad();
  n.fireTestStarted(d);
  n.fireTestFailure(new Failure(d, new AssertionError("failed")));
  n.fireTestFinished(d);
 }
}
'''
fx = h.fixture('workflow-command-' + mode, m.project({'ProbeTest':probe,'ProbeRunner':runner}, pom=pom))
original = subprocess.run
stdout = []
def capture(*args, **kwargs):
    result = original(*args, **kwargs)
    if any(str(x).endswith('/witness.py') for x in args[0]):
        stdout.append(result.stdout)
    return result
subprocess.run = capture
result = h.pipeline(fx)
def identity(ref):
    return original(['/usr/bin/git','-c','safe.directory='+str(repo),'-C',str(repo),'rev-parse',ref],capture_output=True,text=True,check=True).stdout.strip()
doc = {'source_sha': identity('HEAD'), 'source_tree': identity('HEAD^{tree}'),
       'result':result, 'witness_stdout':stdout, 'command_lines':[line for out in stdout for line in out.splitlines() if line.startswith('::')]}
out = repo / 'research/c12-log-safety-20261004' / (mode.upper() + '.json')
out.parent.mkdir(parents=True, exist_ok=True)
original(['/usr/bin/git','-C',str(fx['repo']),'bundle','create',str(out.with_suffix('.bundle')),'--all'],check=True)
import gzip
raw = {p.name:json.loads(p.read_text()) for p in fx['evidence'].glob('*.json')}
out.with_suffix('.raw.json.gz').write_bytes(gzip.compress(json.dumps(raw,sort_keys=True).encode(),mtime=0))
out.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
print(json.dumps(doc, indent=2))
