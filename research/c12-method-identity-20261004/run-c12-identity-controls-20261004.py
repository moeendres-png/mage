import importlib.util
import json
import os
import sys
from pathlib import Path

repo = Path('/home/moeen/work/ci479-mage-c12-20261003')
qual = repo/'.github/qualification'
sys.path.insert(0, str(qual))
spec = importlib.util.spec_from_file_location('qualification_selftest', qual/'qualification_selftest.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
original = m.Harness.__init__
def init(self, *args, **kwargs):
    original(self, *args, **kwargs)
    self.seed = '/home/moeen/.m2/repository'
    self.bundle_dir = Path('/var/lib/c12-method-v3-selftest-20261004/bundle')
    self.runtime_dir = Path('/var/lib/c12-method-v3-selftest-20261004/runtime')
    self.sandbox_dir = Path('/srv/c12-method-v3-selftest-20261004')
m.Harness.__init__ = init
os.environ['TRUSTED_JUNIT_CLASSPATH'] = '/home/moeen/.m2/repository/org/junit/platform/junit-platform-console-standalone/1.9.3/junit-platform-console-standalone-1.9.3.jar'
sys.argv = [str(qual/'qualification_selftest.py'), '--maven', '/usr/bin/mvn', '--offline', '--sandbox-user', 'nobody', '--out', '/home/moeen/work/takeover-evidence-20261003/C12-method-v3-controls.json']
raise SystemExit(m.main())
