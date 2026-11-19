import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import release_resource_gate as gate
from release_transaction import Journal,sha,scoped_files,read

class Reuse(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.p=self.root/'project';self.p.mkdir();self.journal=self.root/'moves';self.journal.mkdir()
  for rel in gate.MANDATORY+('Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs','Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs.meta'):
   f=self.p/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('fixture')
  (self.p/'ProjectSettings/ResourceGovernance.json').write_text(json.dumps({'schemaVersion':1,'toolVersion':'1.0.0'}))
  (self.p/'Assets/Editor/ResourceGovernance/ResourceGovernanceGate.cs').write_text('const string ApiVersion = "1.0";')
  self.cfg=self.root/'machine.json';self.cfg.write_text(json.dumps({'schemaVersion':1,'resourceGovernance':[{'sourceProject':str(self.p),'journalRoot':str(self.journal),'evidenceRoot':str(self.root/'evidence'),'python':sys.executable}]}))
  self.env=patch.dict(os.environ,{'GAME_BUILD_RELEASE_MACHINE_CONFIG':str(self.cfg)});self.env.start()
  self.audit=patch.object(gate,'audit',side_effect=self.fake_audit);self.calls=self.audit.start()
  self.m=self.root/'input.json';self.excludes=['Assets/generated'];self.snapshot()
  self.j=Journal(self.root/'state',{'projectId':'fixture','environment':'test'});self.base={'bootstrap':None,'currents':{}}
  self.tx=self.j.register(dict(requestId='r',messageId='human',source='chat',text='publish',target='fixture',intent='build-publish',buildKind='content',changes=['fix']))['transactionId']
 def tearDown(self):self.audit.stop();self.env.stop();self.temp.cleanup()
 def fake_audit(self,project,binding,output,permit=None):
  report={'toolVersion':'1.0.0','project':str(project),'scope':['Assets'],'errors':[],'legacy':[],'warnings':[]};Path(output).write_text(json.dumps(report));return report
 def snapshot(self):
  scopes=['Assets','Tools','ProjectSettings'];files=scoped_files(self.p,scopes,self.excludes);self.m.write_text(json.dumps({'project':str(self.p),'scopes':scopes,'excludes':self.excludes,'files':[{'path':r,'sha256':gate.digest(self.p/r)} for r in sorted(files)]}))
 def freeze(self):self.j.freeze(self.tx,'owner',sha(self.m.read_bytes()),self.base,self.m)
 def txdata(self):return next(t for t in read(self.j.root/'transactions.json')['transactions'] if t['id']==self.tx)
 def begin(self,step='content'):self.j.begin(self.tx,'owner',step,step,self.p)
 def test_same_source_candidate_and_unchanged_steps_run_one_audit(self):
  self.freeze();self.begin();self.assertEqual(self.calls.call_count,1)
  old=self.txdata()['resourceGovernanceFreeze'];self.assertEqual(self.txdata()['resourceGovernanceLatest'],old)
  with patch.object(gate,'dependencies',side_effect=AssertionError('extra dependency scan')):
   self.j.finish(self.tx,'owner','content',self.m);self.begin('stage')
  self.assertEqual(self.calls.call_count,1)
 def test_source_edit_blocked_before_reuse(self):
  self.freeze();(self.p/'Assets/Editor/TexturePackerTool.cs').write_text('changed')
  with self.assertRaisesRegex(ValueError,'Frozen input changed'):self.begin()
  self.assertNotIn('inFlight',self.txdata())
 def test_new_file_blocked_before_reuse(self):
  self.freeze();(self.p/'Assets/new.txt').write_text('new')
  with self.assertRaisesRegex(ValueError,'additions/deletions'):self.begin()
 def test_deleted_file_blocked_before_reuse(self):
  self.freeze();(self.p/'Assets/Editor/TexturePackerTool.cs').unlink()
  with self.assertRaisesRegex(ValueError,'Frozen input changed'):self.begin()
 def test_unfinished_move_blocks_cached_success(self):
  self.freeze();d=self.journal/'move';d.mkdir();(d/'journal.json').write_text(json.dumps({'project':str(self.p),'state':'moving'}))
  with self.assertRaises(gate.GateError):self.begin()
  self.assertEqual(self.calls.call_count,1);self.assertNotIn('inFlight',self.txdata())
 def test_excluded_generated_change_requires_fresh_audit(self):
  self.freeze();d=self.p/'Assets/generated';d.mkdir();(d/'new.bytes').write_bytes(b'changed');self.begin();self.assertEqual(self.calls.call_count,2)
 def test_corrupt_report_requires_fresh_audit(self):
  self.freeze();r=read(self.txdata()['resourceGovernanceFreeze']);Path(r['sourceReport']).write_text('{}');self.begin();self.assertEqual(self.calls.call_count,2)
 def test_binding_change_requires_fresh_audit(self):
  self.freeze();c=read(self.cfg);c['resourceGovernance'][0]['evidenceRoot']=str(self.root/'new-evidence');self.cfg.write_text(json.dumps(c));self.begin();self.assertEqual(self.calls.call_count,2)
 def test_rule_change_after_refreeze_rejects_old_evidence(self):
  self.freeze();e=self.txdata()['resourceGovernanceEvidence'];(self.p/'ProjectSettings/ResourceGovernance.json').write_text(json.dumps({'schemaVersion':1,'toolVersion':'1.0.0','newRule':True}));self.snapshot()
  from release_transaction import verify_input
  v=verify_input(self.m,sha(self.m.read_bytes()));gate.check(self.p,self.m,verified_input=v,previous=e);self.assertEqual(self.calls.call_count,2)
 def test_tool_change_invalidates_key(self):
  self.freeze();real=gate.digest
  with patch.object(gate,'digest',side_effect=lambda f:'0'*64 if Path(f)==Path(gate.__file__) else real(f)):self.begin()
  self.assertEqual(self.calls.call_count,2)
 def test_supersede_same_input_reuses_without_fake_build(self):
  self.freeze();proof=self.root/'proof.json';proof.write_text(json.dumps({'transactionId':self.tx,'owner':'owner','processesStopped':True,'pointersReviewed':True,'reason':'reuse candidate'}));self.tx=self.j.supersede(self.tx,'owner',proof)['transactionId'];self.freeze();self.begin('stage')
  self.assertEqual(self.calls.call_count,1);self.assertNotIn('content',self.txdata()['steps'])
 def test_isolated_source_and_exception_disable_reuse(self):
  self.freeze();v=read(self.m);b=gate.settings(self.p)
  self.assertIsNone(gate.reuse_key(self.p,self.root/'another-source',b,v,None));self.assertIsNone(gate.reuse_key(self.p,self.p,b,v,{'temporary':'permit'}))

if __name__=='__main__':unittest.main()
