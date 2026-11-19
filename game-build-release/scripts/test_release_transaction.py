import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
from release_transaction import Journal, read, sha, binding
import publish_cos as cos

class Transactions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='release-r2-')
        self.root = Path(self.tmp.name)
        self.j = Journal(self.root / 'state', {'projectId': 'fixture', 'environment': 'test'})
        self.evidence = self.root / 'evidence.json'
        self.evidence.write_text('{}')
        self.source = self.root/'source'; self.source.mkdir(); (self.source/'input.txt').write_text('fixed')
        self.manifest=self.root/'input-manifest.json'; self.manifest.write_text(json.dumps({'project':str(self.source),'scopes':['.'],'files':[{'path':'input.txt','sha256':sha(b'fixed')}]}))
        self.candidate=sha(self.manifest.read_bytes())
        self.baseline = {'bootstrap': None, 'currents': {'base/current.json': None}}
    def tearDown(self):
        self.tmp.cleanup()
    def request(self, n='one', **kw):
        return dict(requestId=n, messageId='human-'+n, source='thread-A', text='explicit build', target='same-content', intent='build-publish', buildKind='content', changes=[n], **kw)
    def freeze(self, request=None):
        tx = self.j.register(request or self.request())['transactionId']
        self.j.freeze(tx, 'owner', self.candidate, self.baseline, self.manifest)
        return tx
    def test_two_sources_one_origin_one_transaction(self):
        a = self.j.register(self.request())
        b = self.j.register({**self.request(), 'source': 'thread-B'})
        self.assertEqual(a['transactionId'], b['transactionId'])
        self.assertTrue(b['duplicate'])
        self.assertEqual(len(read(self.root/'state/transactions.json')['transactions'][0]['requests']), 2)
    def test_distinct_changes_merge_before_freeze(self):
        a = self.j.register(self.request())
        b = self.j.register(self.request('two'))
        self.assertEqual(a['transactionId'], b['transactionId'])
        self.assertEqual(len(read(self.root/'state/transactions.json')['transactions'][0]['requests']), 2)
    def test_changes_queue_after_freeze_and_other_base_cannot_start(self):
        a = self.freeze()
        b = self.j.register({**self.request('two'), 'target': 'another-base'})['transactionId']
        self.assertNotEqual(a,b)
        with self.assertRaisesRegex(ValueError,'active/unresolved'):
            self.j.freeze(b,'other',self.candidate,self.baseline,self.manifest)
    def test_build_only_no_publish_and_content_no_base(self):
        tx=self.freeze({**self.request(), 'intent':'content'})
        for step in ('stage','activate','publish-local','generate','export'):
            with self.assertRaises(ValueError): self.j.begin(tx,'owner',step,'op',self.source)
        self.j.begin(tx,'owner','content','op',self.source)
    def test_unknown_step_blocks_even_same_owner(self):
        tx=self.freeze()
        self.j.begin(tx,'owner','content','op',self.source)
        with self.assertRaisesRegex(ValueError,'active or unknown'): self.j.begin(tx,'owner','export','op2',self.source)
        self.j.fail(tx,'owner','op')
        with self.assertRaisesRegex(ValueError,'resolve failure'): self.j.begin(tx,'owner','content','op2',self.source)
    def test_no_expired_lock_stealing(self):
        self.j.root.mkdir()
        lock=self.j.root/'.journal.lock'; lock.write_text('{"pid":9999999,"time":"1900"}')
        with self.assertRaisesRegex(ValueError,'never auto-steal'): self.j.register(self.request())
        self.assertTrue(lock.exists())
    def test_successful_step_never_repeated_after_failure_recovery(self):
        tx=self.freeze()
        self.j.begin(tx,'owner','content','done',self.source); self.j.finish(tx,'owner','done',self.evidence)
        self.j.begin(tx,'owner','stage','unknown',self.source); self.j.fail(tx,'owner','unknown')
        self.evidence.write_text(json.dumps(dict(transactionId=tx,owner='owner',operationId='unknown',processesStopped=True,pointersReviewed=True)))
        self.j.resolve(tx,'owner',self.evidence,completed=True)
        for step in ('content','stage'):
            with self.assertRaisesRegex(ValueError,'already complete'): self.j.begin(tx,'owner',step,'new',self.source)
    def test_delivery_unlocks_but_duplicate_stays_terminal(self):
        tx=self.freeze()
        for step in ('content','stage','activate','archive'):
            self.j.begin(tx,'owner',step,step,self.source); self.j.finish(tx,'owner',step,self.evidence)
        self.j.deliver(tx,'owner',self.evidence)
        self.assertEqual(self.j.register(self.request())['state'],'delivered-pending-acceptance')
        next_tx=self.j.register(self.request('two'))['transactionId']; self.j.freeze(next_tx,'owner',self.candidate,self.baseline,self.manifest)
    def test_conflicting_duplicate_rejected(self):
        self.j.register(self.request())
        with self.assertRaisesRegex(ValueError,'conflicting'): self.j.register({**self.request(),'changes':['new']})
    def test_stale_baseline_rejected(self):
        with self.assertRaisesRegex(ValueError,'baseline changed'): cos.require_baseline(self.baseline,dict(bootstrap='new',currents=self.baseline['currents']))
    def test_bootstrap_other_bases_preserved(self):
        remote={'bases':[{'baseVersion':'old','manifestUrl':'old/current.json'},{'baseVersion':'base','manifestUrl':'base/current.json'}],'extra':'preserved'}
        local={'bases':[{'baseVersion':'base','manifestUrl':'base/current.json','extra':'new'}]}
        result=cos.merge_bootstrap(remote,local,'base')
        self.assertEqual(result['bases'][0],remote['bases'][0]); self.assertEqual(result['extra'],'preserved')
    def test_all_base_pointer_snapshot(self):
        remote={'bootstrap.json':json.dumps({'bases':[{'baseVersion':'old','manifestUrl':'old/current.json'}]}).encode(),'old/current.json':b'old'}
        with patch.object(cos,'fetch',side_effect=lambda url:remote.get(url.removeprefix('https://fixture/'))):
            result=cos.pointer_snapshot('https://fixture/','base')
        self.assertEqual(result['currents'],{'base/current.json':None,'old/current.json':sha(b'old')})
    def test_config_identity_and_cross_checkout_shared_root(self):
        for name in ('A','B'):
            project=self.root/name; (project/'ProjectSettings').mkdir(parents=True)
            (project/'ProjectSettings/FrameworkPlatform.json').write_text(json.dumps({'bootstrapUrl':'https://fixture/bootstrap.json','buildRelease':{'releaseTransaction':{'stateRoot':str(self.j.root),'projectId':'fixture','environment':'test'}}}))
        self.assertEqual(binding(self.root/'A'),binding(self.root/'B'))
    def test_publish_and_rollback_cannot_rebuild(self):
        for intent in ('publish','rollback'):
            separate=Journal(self.root/intent, {'projectId':intent,'environment':'test'})
            tx=separate.register({**self.request(), 'intent':intent, 'buildKind':'none'})['transactionId']
            separate.freeze(tx,'owner',self.candidate,self.baseline,self.manifest)
            for step in ('prepare','generate','export','content'):
                with self.assertRaises(ValueError): separate.begin(tx,'owner',step,'op',self.source)
    def test_wrong_execution_project_rejected(self):
        tx=self.freeze()
        other=self.root/'other'; other.mkdir()
        with self.assertRaisesRegex(ValueError,'another execution project'):
            self.j.begin(tx,'owner','content','op',other)
    def test_input_changes_and_additions_rejected(self):
        tx=self.freeze()
        (self.source/'input.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError,'input changed'): self.j.begin(tx,'owner','content','op',self.source)
        (self.source/'input.txt').write_text('fixed'); (self.source/'extra').write_text('new')
        with self.assertRaisesRegex(ValueError,'additions/deletions'): self.j.begin(tx,'owner','content','op',self.source)
    def test_stale_baseline_supersede_requires_review_new_freeze(self):
        tx=self.freeze(); self.j.begin(tx,'owner','activate','unknown',self.source); self.j.fail(tx,'owner','unknown')
        self.evidence.write_text(json.dumps(dict(transactionId=tx,owner='owner',operationId='unknown',processesStopped=True,pointersReviewed=True,reason='baseline changed; candidate re-review required')))
        successor=self.j.supersede(tx,'owner',self.evidence)['transactionId']
        self.assertNotEqual(tx,successor)
        self.assertEqual(self.j.register(self.request())['transactionId'],successor)
        with self.assertRaises(ValueError): self.j.begin(successor,'owner','activate','new',self.source)
        self.j.freeze(successor,'owner',self.candidate,self.baseline,self.manifest)
    def test_cancel_queued_transaction(self):
        first=self.j.register(self.request())['transactionId']
        second=self.j.register({**self.request('two'),'target':'other'})['transactionId']
        self.j.cancel(first,self.evidence)
        self.j.freeze(second,'owner',self.candidate,self.baseline,self.manifest)
    def test_full_mock_cos_stage_activate_and_other_mapping(self):
        project=self.root/'Project'; (project/'ProjectSettings').mkdir(parents=True); (self.root/'build').mkdir()
        cdn=self.root/'cdn'; folder=cdn/'base/releases/release'; folder.mkdir(parents=True)
        manifest={'version':'release'}
        for name,value in [('manifest.json',manifest),('settings.json',{}),('catalog.json',{'m_InternalIds':[]})]: (folder/name).write_text(json.dumps(value))
        (cdn/'base/current.json').write_text(json.dumps(manifest,indent=4))
        (cdn/'bootstrap.json').write_text(json.dumps({'bases':[{'baseVersion':'base','manifestUrl':'base/current.json'}]}))
        public='https://fixture.cos.region.myqcloud.com/fixture/'
        config={'bootstrapUrl':public+'bootstrap.json','cdnRoot':str(cdn),'buildRelease':{'deployment':{'kind':'cos','bucket':'fixture','region':'region','projectSubdirectory':'fixture','publicRoot':public},'releaseTransaction':{'stateRoot':str(self.root/'cos-state'),'projectId':'fixture','environment':'test'}}}
        (project/'ProjectSettings/FrameworkPlatform.json').write_text(json.dumps(config))
        (project/'Inputs').mkdir(); (project/'Inputs/input.txt').write_text('fixed')
        self.manifest.write_text(json.dumps({'project':str(project),'scopes':['Inputs'],'files':[{'path':'Inputs/input.txt','sha256':sha(b'fixed')}]})); self.candidate=sha(self.manifest.read_bytes())
        remote={'bootstrap.json':json.dumps({'bases':[{'baseVersion':'old','manifestUrl':'old/current.json'}]}).encode(),'old/current.json':b'old'}
        uploads=[]
        def fake_upload(args,deployment,key,path,immutable):
            uploads.append((key,immutable)); remote[key]=Path(path).read_bytes()
        with patch.object(cos,'validate',return_value={'baseVersion':'base','release':'release'}),patch.object(cos,'fetch',side_effect=lambda url:remote.get(url.removeprefix(public))),patch.object(cos,'upload',side_effect=fake_upload),patch('remote_verify.get_object',side_effect=lambda url,etag=None:(200,remote[url.removeprefix(public)],None) if url.removeprefix(public) in remote else (404,b'',None)):
            journal=Journal(*binding(project)); tx=journal.register(self.request())['transactionId']
            journal.freeze(tx,'owner',self.candidate,cos.pointer_snapshot(public,'base'),self.manifest)
            for action in ('stage','activate'):
                journal.begin(tx,'owner',action,action,project)
                args=SimpleNamespace(project=str(project),action=action,transaction=tx,owner='owner',operation=action)
                receipt=cos.execute(args); self.assertEqual(receipt.parent, self.root/'build/archives/base/content/release/receipts'); self.assertEqual(list((self.root/'build').glob('*.json')), []); journal.finish(tx,'owner',action,receipt)
            self.assertEqual(remote['base/current.json'],(folder/'manifest.json').read_bytes())
            self.assertEqual(remote['old/current.json'],b'old')
            self.assertEqual(json.loads(remote['bootstrap.json'])['bases'][0]['baseVersion'],'old')
            self.assertEqual(uploads[-2:],[('base/current.json',False),('bootstrap.json',False)])
            with self.assertRaisesRegex(ValueError,'already complete'): journal.begin(tx,'owner','activate','again',project)
    def test_parallel_freeze_has_one_environment_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        a=self.j.register(self.request())['transactionId']
        b=self.j.register({**self.request('two'),'target':'other-base'})['transactionId']
        barrier=Barrier(2)
        def attempt(tx):
            barrier.wait()
            try:
                self.j.freeze(tx,'owner',self.candidate,self.baseline,self.manifest)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(attempt,[a,b]))
        self.assertLessEqual(sum(result),1)
        # A later queued contender can win the edit lock and be refused FIFO, while
        # the earlier contender conservatively gets lock-busy. No pipeline started.
        if not any(result):
            self.j.freeze(a,'owner',self.candidate,self.baseline,self.manifest)
        state=read(self.j.root/'transactions.json')
        self.assertEqual(sum(t['state']=='frozen' for t in state['transactions']),1)
    def test_cos_binding_compatibility_and_fail_closed(self):
        project=self.root/'Project'; (project/'ProjectSettings').mkdir(parents=True); (self.root/'build').mkdir()
        config=project/'ProjectSettings/FrameworkPlatform.json'
        args=['publish_cos.py','--project',str(project),'--action','stage','--coscli','fixture','--cos-config','fixture']
        config.write_text(json.dumps({'buildRelease':{}}))
        with patch.object(sys,'argv',args),patch.object(cos,'execute',return_value=self.evidence) as execute,patch.object(cos,'print_receipt'):
            cos.main(); execute.assert_called_once()
        with patch.object(sys,'argv',args+['--transaction','explicit','--owner','owner']),patch.object(cos,'execute') as execute:
            with self.assertRaisesRegex(ValueError,'requires project binding'): cos.main()
            execute.assert_not_called()
        config.write_text(json.dumps({'buildRelease':{'releaseTransaction':{}}}))
        with patch.object(sys,'argv',args),patch.object(cos,'execute') as execute:
            with self.assertRaisesRegex(ValueError,'require transaction/owner'): cos.main()
            execute.assert_not_called()
        with patch.object(sys,'argv',args+['--transaction','explicit','--owner','owner']),patch.object(cos,'execute') as execute:
            with self.assertRaisesRegex(ValueError,'Configure releaseTransaction'): cos.main()
            execute.assert_not_called()
    def test_receipts_are_versioned_and_cannot_escape(self):
        project=self.root/'Project'
        path=cos.receipt_path(project,'stage','base','release')
        self.assertEqual(path,self.root/'build/archives/base/content/release/receipts/cos-stage-base-release.json')
        for base,release in [('../outside','release'),('base','../outside'),('C:/absolute','release')]:
            with self.assertRaisesRegex(ValueError,'Unsafe receipt version'):
                cos.receipt_path(project,'stage',base,release)
    def test_activate_rejects_stale_before_any_upload(self):
        project=self.root/'Project'; (project/'ProjectSettings').mkdir(parents=True)
        cdn=self.root/'cdn'; folder=cdn/'base/releases/release'; folder.mkdir(parents=True)
        for name,value in [('manifest.json',{}),('settings.json',{}),('catalog.json',{'m_InternalIds':[]})]: (folder/name).write_text(json.dumps(value))
        config={'bootstrapUrl':'https://fixture.cos.region.myqcloud.com/fixture/bootstrap.json','cdnRoot':str(cdn),'buildRelease':{'deployment':{'kind':'cos','bucket':'fixture','region':'region','projectSubdirectory':'fixture','publicRoot':'https://fixture.cos.region.myqcloud.com/fixture/'},'releaseTransaction':{'stateRoot':str(self.j.root),'projectId':'fixture','environment':'test'}}}
        (project/'ProjectSettings/FrameworkPlatform.json').write_text(json.dumps(config))
        (project/'Inputs').mkdir(); (project/'Inputs/input.txt').write_text('fixed')
        self.manifest.write_text(json.dumps({'project':str(project),'scopes':['Inputs'],'files':[{'path':'Inputs/input.txt','sha256':sha(b'fixed')}]})); self.candidate=sha(self.manifest.read_bytes())
        root,identity=binding(project); journal=Journal(root,identity)
        tx=journal.register(self.request())['transactionId']; journal.freeze(tx,'owner',self.candidate,self.baseline,self.manifest)
        journal.begin(tx,'owner','stage','s',project); journal.finish(tx,'owner','s',self.evidence)
        with journal.edit() as state: journal.tx(state,tx)['selection']={'baseVersion':'base','release':'release','resourcesSha256':sha(json.dumps({('base/releases/release/'+p.name):sha(p.read_bytes()) for p in folder.iterdir()},sort_keys=True).encode())}
        journal.begin(tx,'owner','activate','a',project)
        args=SimpleNamespace(project=str(project),action='activate',transaction=tx,owner='owner',operation='a')
        with patch.object(cos,'validate',return_value={'baseVersion':'base','release':'release'}), patch.object(cos,'pointer_snapshot',return_value={'bootstrap':'changed','currents':{}}),patch.object(cos,'upload') as upload:
            with self.assertRaisesRegex(ValueError,'baseline changed'): cos.execute(args)
            upload.assert_not_called()

if __name__=='__main__':
    unittest.main(verbosity=2)
