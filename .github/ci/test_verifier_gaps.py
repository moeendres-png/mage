import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import verifier_gaps as gaps

class GapInventory(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        self.p=self.root/'Mage.Verify/src/test/java/ProbeTest.java';self.p.parent.mkdir(parents=True)
        self.p.write_text('class ProbeTest { @Test @Ignore public void disabledCheck() {} @Test public void active() {} }')
        self.commit()
        self.baseline=gaps.inventory(self.root,'HEAD')
        p=self.root/gaps.BASELINE;p.parent.mkdir(parents=True);p.write_text(json.dumps(self.baseline));self.commit()
    def commit(self):
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Control','-c','user.email=control@example.invalid','commit','-qm','control'],check=True)
    def observe(self):
        return gaps.observe(self.root,'HEAD',self.root)
    def test_disabled_remains_explicit_and_not_pass(self):
        doc=self.observe();self.assertEqual(doc['status'],'SOURCE_INVENTORY_MATCH')
        self.assertEqual(doc['disabled_tests'][0]['status'],'NOT_RUN');self.assertFalse(doc['qualification_credit'])
    def test_source_removed_and_new_suppression_require_review(self):
        for source in ('class ProbeTest {}','class ProbeTest { @Test @Ignore public void another() {} }'):
            self.p.write_text(source);self.commit();self.assertEqual(self.observe()['status'],'REVIEW_REQUIRED')
    def test_gap_list_cannot_silently_shrink(self):
        p=self.root/gaps.BASELINE;doc=json.loads(p.read_text());doc['records']=[];p.write_text(json.dumps(doc));self.commit()
        self.assertEqual(self.observe()['status'],'REVIEW_REQUIRED')
    def test_unknown_spelling_source_drift_requires_review(self):
        self.p.write_text(self.p.read_text()+' // \\u0040Ignore suppression spelling');self.commit()
        self.assertEqual(self.observe()['status'],'REVIEW_REQUIRED')
    def test_missing_and_symlinked_source_are_unknown(self):
        p=self.root/gaps.BASELINE;p.unlink();self.commit();self.assertEqual(self.observe()['status'],'UNKNOWN')
        self.p.unlink();self.p.symlink_to('/etc/passwd');self.commit();self.assertEqual(self.observe()['status'],'UNKNOWN')
    def test_green_xml_does_not_remove_disabled_gaps(self):
        p=self.root/'Mage.Verify/target/surefire-reports/TEST-Probe.xml';p.parent.mkdir(parents=True)
        p.write_text('<testsuite><testcase classname="ProbeTest" name="active"/><testcase classname="ProbeTest" name="disabledCheck"><skipped/></testcase></testsuite>')
        doc=self.observe();self.assertEqual(doc['runtime_executed_count'],1);self.assertEqual(len(doc['runtime_skipped']),1)
        self.assertEqual(len(doc['disabled_tests']),1);self.assertIn('NOT_RUN',gaps.render(doc));self.assertFalse(doc['qualification_credit'])
    def test_unrecognized_new_file_requires_review(self):
        p=self.p.with_name('NewVerifier.java');p.write_text('class NewVerifier {}');self.commit()
        self.assertEqual(self.observe()['status'],'REVIEW_REQUIRED')
    def test_candidate_worktree_cannot_change_git_source_inventory(self):
        before=self.observe();self.p.write_text('class Empty {}')
        self.assertEqual(self.observe(),before)

if __name__=='__main__':unittest.main()
