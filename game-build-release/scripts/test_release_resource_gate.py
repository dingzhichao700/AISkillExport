import hashlib, json, os, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import release_resource_gate as gate
from release_transaction import Journal, sha, scoped_files

class ResourceEntry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installed=Path(os.environ['B0_TEST_REFERENCE'])
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='b0-release-');self.root=Path(self.tmp.name)
        self.source=self.root/'source';self.candidate=self.root/'candidate';self.journals=self.root/'journals';self.journals.mkdir()
        for rel in gate.MANDATORY+('Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs','Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs.meta'):
            target=self.source/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(self.installed/rel,target)
        shutil.copytree(self.installed/'Tools/ResourceGovernance',self.source/'Tools/ResourceGovernance',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
        # Keep the fixture aligned with the installed CLI's locked dependency set.
        locked=json.loads((self.installed/'Tools/ResourceGovernance/ResourceGovernance.lock.json').read_text(encoding='utf-8-sig'))['files']
        for rel in locked:
            for name in (rel,rel+'.meta'):
                f=self.installed/name
                if f.is_file():
                    target=self.source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
        # This tests the release adapter, not a particular game's card/atlas inventory.
        # Use a self-contained fixture policy with the real, unmodified CLI and lock.
        policy_path=self.source/'ProjectSettings/ResourceGovernance.json'
        installed_policy=json.loads(policy_path.read_text(encoding='utf-8-sig'))
        policy={'schemaVersion':1,'toolVersion':'1.0.0','groups':installed_policy['groups'],
                'protectedVendorRoots':[],'globalResourceRoots':[],'modules':['fixture'],
                'bootstrapResources':[],'artTypes':['unpack'],'skeletalExtensions':[],
                'audioExtensions':[],'builtInVirtualGuids':[]}
        policy_path.write_text(json.dumps(policy),encoding='utf-8')
        lock_path=self.source/'Tools/ResourceGovernance/ResourceGovernance.lock.json'
        fixture_lock=json.loads(lock_path.read_text(encoding='utf-8-sig'))
        fixture_lock['files']['ProjectSettings/ResourceGovernance.json']=gate.digest(policy_path)
        lock_path.write_text(json.dumps(fixture_lock),encoding='utf-8')
        (self.source/'ProjectSettings/FrameworkPlatform.json').write_text(json.dumps({'bootstrapUrl':'https://fixture/bootstrap.json','buildRelease':{'releaseTransaction':{'projectId':'fixture','environment':'test'}}}))
        shutil.copytree(self.source,self.candidate)
        config=self.root/'machine.json';config.write_text(json.dumps({'schemaVersion':1,'resourceGovernance':[{'projectId':'fixture','environment':'test','bootstrapUrl':'https://fixture/bootstrap.json','sourceProject':str(self.source),'journalRoot':str(self.journals),'evidenceRoot':str(self.root/'evidence'),'python':sys.executable}]}))
        self.env=patch.dict(os.environ,{'GAME_BUILD_RELEASE_MACHINE_CONFIG':str(config)});self.env.start()
        self.j=Journal(self.root/'release-state',{'projectId':'fixture','environment':'test'})
        req=dict(requestId='one',messageId='human-one',source='fixture',text='build',target='fixture',intent='build-publish',buildKind='base',changes=['fixture'])
        self.tx=self.j.register(req)['transactionId']
        self.manifest=self.root/'input.json';self.snapshot()
        self.baseline={'bootstrap':None,'currents':{}}
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def snapshot(self):
        files=scoped_files(self.candidate,['Assets','Tools','ProjectSettings'],[])
        self.manifest.write_text(json.dumps({'project':str(self.candidate),'scopes':['Assets','Tools','ProjectSettings'],'files':[{'path':r,'sha256':gate.digest(self.candidate/r)} for r in sorted(files)]}))
    def freeze(self):self.j.freeze(self.tx,'owner',sha(self.manifest.read_bytes()),self.baseline,self.manifest)
    def state(self):return json.loads((self.j.root/'transactions.json').read_text())['transactions'][0]
    def blocked_freeze(self,code):
        self.snapshot()
        before=(self.j.root/'transactions.json').read_bytes()
        with self.assertRaises(gate.GateError) as caught:self.freeze()
        self.assertEqual(caught.exception.code,code)
        self.assertEqual(before,(self.j.root/'transactions.json').read_bytes())
        self.assertEqual(self.state()['state'],'registered')
        self.assertFalse((self.candidate/'Library/AIUI/pending-wechat-build.json').exists())
        self.assertFalse((self.root/'bootstrap.json').exists())
    def test_full_real_cli_source_and_candidate(self):
        self.freeze();s=self.state();self.assertEqual(s['state'],'frozen')
        report=json.loads(Path(s['resourceGovernanceFreeze']).read_text())
        self.assertEqual(json.loads(Path(report['sourceReport']).read_text())['scope'],['Assets'])
        self.assertEqual(json.loads(Path(report['candidateReport']).read_text())['scope'],['Assets'])
        self.j.begin(self.tx,'owner','generate','fixture-operation',self.candidate)
        self.assertTrue(self.state()['resourceGovernanceLatest'])
    def test_real_cli_same_project_reused_until_generated_output_changes(self):
        self.candidate=self.source;self.snapshot()
        m=json.loads(self.manifest.read_text());m['excludes']=['Assets/Generated'];self.manifest.write_text(json.dumps(m))
        with patch.object(gate,'audit',wraps=gate.audit) as calls:
            self.freeze();self.j.begin(self.tx,'owner','generate','first',self.source)
            self.assertEqual(calls.call_count,1)
            self.j.finish(self.tx,'owner','first',self.manifest)
            generated=self.source/'Assets/Generated';generated.mkdir();(generated/'code.bytes').write_bytes(b'new')
            self.j.begin(self.tx,'owner','export','second',self.source)
            self.assertEqual(calls.call_count,2)
    def test_missing_candidate_cli(self):
        (self.candidate/'Tools/ResourceGovernance/resource_governance.py').unlink();self.blocked_freeze(3)
    def test_broken_rules(self):
        for p in (self.source,self.candidate):(p/'ProjectSettings/ResourceGovernance.json').write_text('{')
        self.blocked_freeze(3)
    def test_source_unfinished_journal(self):
        p=self.journals/'move';p.mkdir();(p/'journal.json').write_text(json.dumps({'project':str(self.source),'state':'moving'}));self.blocked_freeze(2)
    def test_new_violation_outside_editor_scopes(self):
        p=self.candidate/'Assets/Art/unpack/invalid.png';p.parent.mkdir(parents=True);p.write_bytes(b'invalid')
        self.blocked_freeze(2)
    def test_gate_metadata_missing(self):
        (self.candidate/'Assets/Editor/ResourceGovernance/ResourceGovernanceGate.cs.meta').unlink();self.blocked_freeze(3)
    def test_lock_tampering_even_matching_source_candidate(self):
        for p in (self.source,self.candidate):
            f=p/'Tools/ResourceGovernance/resource_governance.py';f.write_bytes(f.read_bytes()+b'\n# changed\n')
        self.blocked_freeze(3)
    def test_manifest_cannot_omit_tools(self):
        m=json.loads(self.manifest.read_text());m['files']=[r for r in m['files'] if not r['path'].startswith('Tools/')];m['scopes']=['Assets','ProjectSettings'];self.manifest.write_text(json.dumps(m))
        with self.assertRaisesRegex(gate.GateError,'omits or excludes'):self.freeze()
        self.assertEqual(self.state()['state'],'registered')
    def test_begin_rechecks_source_journal_before_inflight(self):
        self.freeze();before=(self.j.root/'transactions.json').read_bytes()
        p=self.journals/'move';p.mkdir();(p/'journal.json').write_text(json.dumps({'project':str(self.source),'state':'verifying'}))
        with self.assertRaises(gate.GateError):self.j.begin(self.tx,'owner','activate','fixture',self.candidate)
        self.assertEqual(before,(self.j.root/'transactions.json').read_bytes())
    def test_absent_machine_binding_fails_closed(self):
        with patch.dict(os.environ,{'GAME_BUILD_RELEASE_MACHINE_CONFIG':str(self.root/'missing.json')}):self.blocked_freeze(3)
    def test_closed_journal_allowed(self):
        p=self.journals/'move';p.mkdir();(p/'journal.json').write_text(json.dumps({'project':str(self.source),'state':'committed'}));self.freeze()
    def test_unbound_cos_cannot_bypass_resource_gate(self):
        import publish_cos
        p=self.candidate/'ProjectSettings/FrameworkPlatform.json';data=json.loads(p.read_text());data['buildRelease'].pop('releaseTransaction');p.write_text(json.dumps(data))
        argv=['publish_cos.py','--project',str(self.candidate),'--action','stage','--coscli','not-executed','--cos-config','not-opened']
        with patch.object(sys,'argv',argv),patch.object(publish_cos,'execute') as execute:
            with self.assertRaises(gate.GateError):publish_cos.main()
            execute.assert_not_called()
        self.assertFalse((self.root/'build/.cos-publish.lock').exists())
    def test_no_reduced_scope_cli(self):
        import subprocess
        r=subprocess.run([sys.executable,str(Path(gate.__file__)),'--project',str(self.candidate),'--scope','Assets/Editor'],capture_output=True)
        self.assertNotEqual(r.returncode,0);self.assertFalse((self.root/'evidence').exists())

if __name__=='__main__':unittest.main()
