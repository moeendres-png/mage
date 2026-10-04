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
        self.anchor=self.rev()
    def commit(self):
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Control','-c','user.email=control@example.invalid','commit','-qm','control'],check=True)
    def rev(self):
        return subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
    def observe(self, rev='HEAD', baseline_rev=None):
        return gaps.observe(self.root,rev,self.root,baseline_rev or self.anchor)
    def test_disabled_remains_explicit_and_not_pass(self):
        doc=self.observe();self.assertEqual(doc['status'],'SOURCE_INVENTORY_MATCH')
        self.assertEqual(doc['baseline_anchor_sha'],self.anchor)
        self.assertTrue(doc['anchor_baseline_matches_source'])
        self.assertTrue(doc['candidate_baseline_matches_source'])
        self.assertFalse(doc['source_changed_from_anchor'])
        self.assertEqual(doc['disabled_tests'][0]['status'],'NOT_RUN');self.assertFalse(doc['qualification_credit'])
    def test_source_removed_and_new_suppression_require_review(self):
        for source in ('class ProbeTest {}','class ProbeTest { @Test @Ignore public void another() {} }'):
            self.p.write_text(source);self.commit();self.assertEqual(self.observe()['status'],'REVIEW_REQUIRED')
    def test_gap_list_cannot_silently_shrink(self):
        p=self.root/gaps.BASELINE;doc=json.loads(p.read_text());doc['records']=[];p.write_text(json.dumps(doc));self.commit()
        observed=self.observe()
        self.assertEqual(observed['status'],'REVIEW_REQUIRED')
        self.assertFalse(observed['candidate_baseline_matches_source'])
    def test_unknown_spelling_source_drift_requires_review(self):
        self.p.write_text(self.p.read_text()+' // \\u0040Ignore suppression spelling');self.commit()
        self.assertEqual(self.observe()['status'],'REVIEW_REQUIRED')
    def test_coordinated_candidate_source_and_baseline_drift_requires_review(self):
        self.p.write_text('class ProbeTest { @Test public void active() {} @Test @Ignore public void replacementDisabled() {} }')
        self.commit()
        p=self.root/gaps.BASELINE
        p.write_text(json.dumps(gaps.inventory(self.root,'HEAD')))
        self.commit()
        doc=self.observe()
        self.assertEqual(doc['status'],'REVIEW_REQUIRED')
        self.assertTrue(doc['candidate_baseline_matches_source'])
        self.assertTrue(doc['anchor_baseline_matches_source'])
        self.assertTrue(doc['source_changed_from_anchor'])
        self.assertTrue(doc['baseline_changed_from_anchor'])
    def test_missing_or_invalid_anchor_is_unknown(self):
        self.assertEqual(gaps.observe(self.root,'HEAD',self.root,None)['status'],'UNKNOWN')
        self.assertEqual(gaps.observe(self.root,'HEAD',self.root,'deadbeef')['status'],'UNKNOWN')

    def test_class_level_and_qualified_disables_are_explicit_not_run(self):
        self.p.write_text(
            '@org.junit.Ignore class ProbeTest { '
            '@org.junit.Test public void inheritedDisabled() {} '
            '@org.junit.Test @org.junit.jupiter.api.Disabled public void methodDisabled() {} '
            '}'
        )
        self.commit()
        doc=gaps.inventory(self.root,'HEAD')
        disabled={r['method']:r for r in doc['records'] if r['kind']=='DISABLED_TEST'}
        self.assertEqual(set(disabled),{'inheritedDisabled','methodDisabled'})
        self.assertTrue(all(r['status']=='NOT_RUN' for r in disabled.values()))
        self.assertTrue(all(r['evidence_class']=='CODE_DERIVED' for r in disabled.values()))
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

    def test_workflow_uses_pr_base_anchor_and_regenerates_after_maven(self):
        workflow=(Path(__file__).resolve().parents[1]/'workflows/maven.yml').read_text()
        checkout=workflow.index('    - uses: actions/checkout@')
        setup=workflow.index('    - name: Setup JDK 17')
        self.assertIn('fetch-depth: 2',workflow[checkout:setup])
        build=workflow.index('    - name: Build and test')
        regenerate=workflow.index('    - name: Regenerate verifier omission evidence after Maven')
        collect=workflow.index('    - name: Record distinct native module signals')
        upload=workflow.index('    - name: Upload native source-bound module evidence')
        self.assertLess(build,regenerate)
        self.assertLess(regenerate,collect)
        self.assertLess(regenerate,upload)
        self.assertEqual(workflow.count('BASELINE_REV: ${{ github.event.pull_request.base.sha || github.sha }}'),2)
        self.assertEqual(workflow.count('--baseline-rev "$BASELINE_REV"'),2)
        block=workflow[regenerate:collect]
        self.assertIn('if: ${{ !cancelled() }}',block)
        self.assertIn('python3 .github/ci/verifier_gaps.py check',block)
        self.assertIn('--out evidence/VERIFIER_GAPS.json',block)
        self.assertIn('--markdown evidence/VERIFIER_GAPS.md',block)

if __name__=='__main__':unittest.main()
