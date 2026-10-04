import copy
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
import native_signals as signals

PASS = '<testsuite name="test" tests="1" failures="0" errors="0" skipped="0"><testcase name="proof"/></testsuite>'
FAIL = PASS.replace('failures="0"', 'failures="1"').replace('<testcase name="proof"/>', '<testcase name="proof"><failure/></testcase>')

class NativeSignals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.identity = {'checkout_sha': 'source', 'run_id': 'run', 'checkout_tree': 'tree', 'producer_sha256': signals.digest(Path(signals.__file__))}
        self.log=self.root/'evidence/reactor.log'
        self.log.parent.mkdir()
        self.log.write_text('[INFO] Mage Tests .......... SUCCESS [1 s]\n[INFO] Mage Verify .......... SUCCESS [1 s]\n')
    def report(self, module, xml):
        path = self.root/module/'target/surefire-reports/TEST-probe.xml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(xml)
        return path
    def result(self, module):
        return signals.consume(signals.collect(self.root, self.identity), module, 'source', 'run', self.root)
    def test_mixed_outcomes_stay_mixed(self):
        self.report('Mage.Tests', PASS)
        self.report('Mage.Verify', FAIL)
        self.assertEqual(self.result('Mage.Tests'), 'PASS')
        self.assertEqual(self.result('Mage.Verify'), 'FAIL')
    def test_missing_is_not_run(self):
        self.assertEqual(self.result('Mage.Tests'), 'NOT_RUN')
    def test_malformed_is_unknown(self):
        self.report('Mage.Tests', 'broken')
        self.assertEqual(self.result('Mage.Tests'), 'UNKNOWN')
    def test_negative_is_unknown(self):
        self.report('Mage.Tests', PASS.replace('failures="0"', 'failures="-1"'))
        self.assertEqual(self.result('Mage.Tests'), 'UNKNOWN')
    def test_hidden_failure_is_unknown(self):
        self.report('Mage.Tests', FAIL.replace('failures="1"', 'failures="0"'))
        self.assertEqual(self.result('Mage.Tests'), 'UNKNOWN')
    def test_all_skipped_fails(self):
        self.report('Mage.Tests', PASS.replace('skipped="0"','skipped="1"').replace('<testcase name="proof"/>','<testcase name="proof"><skipped/></testcase>'))
        self.assertEqual(self.result('Mage.Tests'), 'FAIL')
    def test_source_and_run_mismatch(self):
        self.report('Mage.Tests', PASS)
        doc=signals.collect(self.root,self.identity)
        self.assertEqual(signals.consume(doc,'Mage.Tests','other','run',self.root),'UNKNOWN')
        self.assertEqual(signals.consume(doc,'Mage.Tests','source','other',self.root),'UNKNOWN')
    def test_forged_pass_rejected(self):
        self.report('Mage.Tests', FAIL)
        doc=signals.collect(self.root,self.identity)
        doc['modules']['Mage.Tests']['native_outcome']='PASS'
        self.assertEqual(signals.consume(doc,'Mage.Tests','source','run',self.root),'UNKNOWN')
    def test_interrupted_partial_run_is_unknown(self):
        self.report('Mage.Tests', PASS)
        self.log.write_text('[INFO] compiling...')
        self.assertEqual(self.result('Mage.Tests'), 'UNKNOWN')
    def test_skipped_reactor_module_is_not_run(self):
        self.report('Mage.Tests', PASS)
        self.log.write_text('[INFO] Mage Tests .......... SKIPPED\n')
        self.assertEqual(self.result('Mage.Tests'), 'NOT_RUN')
    def test_reactor_failure_cannot_be_hidden_by_xml(self):
        self.report('Mage.Tests', PASS)
        self.log.write_text('[INFO] Mage Tests .......... FAILURE\n')
        self.assertEqual(self.result('Mage.Tests'), 'FAIL')
    def test_duplicate_completion_is_unknown(self):
        self.report('Mage.Tests', PASS)
        self.log.write_text('[INFO] Mage Tests .......... SUCCESS\n'*2)
        self.assertEqual(self.result('Mage.Tests'), 'UNKNOWN')
    def test_xml_hashes_and_nonqualification(self):
        p=self.report('Mage.Tests',PASS)
        doc=signals.collect(self.root,self.identity)
        self.assertEqual(doc['modules']['Mage.Tests']['reports'][0]['sha256'], signals.digest(p))
        self.assertFalse(doc['trusted_qualification'])
        self.assertFalse(doc['modules']['Mage.Tests']['qualification_credit'])
    def test_logged_pipeline_preserves_build_failure(self):
        workflow=(Path(__file__).resolve().parents[1]/'workflows/maven.yml').read_text()
        block=workflow.split('    - name: Build and test\n',1)[1].split('    - name:',1)[0]
        self.assertIn('shell: bash',block)
        script=block.split('      run: |\n',1)[1]
        lines=[]
        for line in script.splitlines():
            command=line.strip()
            lines.append('false | tee evidence/reactor.log' if command.startswith('mvn test ') else command)
        result=subprocess.run(['bash','-e','-c','\n'.join(lines)],cwd=self.root,capture_output=True)
        self.assertNotEqual(result.returncode,0)
    def test_entity_refused(self):
        self.report('Mage.Tests', '<!DOCTYPE x [<!ENTITY y "z">]>'+PASS)
        self.assertEqual(self.result('Mage.Tests'),'UNKNOWN')

    def test_real_versioned_reactor_summary(self):
        self.report('Mage.Tests', PASS)
        self.report('Mage.Verify', FAIL)
        self.log.write_text('[INFO] Mage Tests 1.4.61 .................................. SUCCESS [02:47 min]\n[INFO] Mage Verify 1.4.61 ................................. FAILURE [01:45 min]\n')
        self.assertEqual(self.result('Mage.Tests'), 'PASS')
        self.assertEqual(self.result('Mage.Verify'), 'FAIL')
    def test_artifact_record_tampering_is_unknown(self):
        self.report('Mage.Tests', PASS)
        doc=signals.collect(self.root,self.identity)
        for change in ('impossible-skips', 'empty-record', 'counts', 'path', 'hash', 'duplicate', 'credit'):
            with self.subTest(change=change):
                altered=copy.deepcopy(doc); record=altered['modules']['Mage.Tests']
                if change=='impossible-skips': record['counts']['skipped']=2
                elif change=='empty-record': record['reports']=[{}]
                elif change=='counts': record['counts']['tests']=10
                elif change=='path': record['reports'][0]['path']='../../elsewhere.xml'
                elif change=='hash': record['reports'][0]['sha256']='0'*64
                elif change=='duplicate': record['reports']*=2
                else: record['qualification_credit']=True
                self.assertEqual(signals.consume(altered,'Mage.Tests','source','run',self.root),'UNKNOWN')
    def test_changed_or_missing_xml_is_unknown(self):
        path=self.report('Mage.Tests', PASS); doc=signals.collect(self.root,self.identity)
        path.write_text(FAIL)
        self.assertEqual(signals.consume(doc,'Mage.Tests','source','run',self.root),'UNKNOWN')
        path.unlink()
        self.assertEqual(signals.consume(doc,'Mage.Tests','source','run',self.root),'UNKNOWN')
    def test_changed_reactor_log_is_unknown(self):
        self.report('Mage.Tests', PASS); doc=signals.collect(self.root,self.identity)
        self.log.write_text('[INFO] Mage Tests 1.4.61 .... FAILURE\n')
        self.assertEqual(signals.consume(doc,'Mage.Tests','source','run',self.root),'UNKNOWN')
    def test_producer_mismatch_is_unknown(self):
        self.report('Mage.Tests', PASS); doc=signals.collect(self.root,self.identity)
        doc['identity']['producer_sha256']='other'
        self.assertEqual(signals.consume(doc,'Mage.Tests','source','run',self.root),'UNKNOWN')

if __name__=='__main__':
    unittest.main()
