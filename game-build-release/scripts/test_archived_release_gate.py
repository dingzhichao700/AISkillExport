import json, tempfile, unittest, zipfile, sys
from pathlib import Path
from unittest.mock import patch
import release_resource_gate as g
from archived_release_gate import check_archived


class Archived(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.p=self.root/'project';self.p.mkdir()
  self.state=self.root/'state';self.state.mkdir();self.moves=self.root/'moves';self.moves.mkdir()
  self.identity={'projectId':'fixture','environment':'test','bootstrapUrl':'https://example.invalid/bootstrap.json'}
  self.bound={**self.identity,'sourceProject':str(self.root/'unrelated'),'journalRoot':str(self.moves),'evidenceRoot':str(self.root/'checks'),'python':sys.executable}
  self.write(self.p/'ProjectSettings/FrameworkPlatform.json',{'bootstrapUrl':self.identity['bootstrapUrl'],'buildRelease':{'releaseTransaction':{'stateRoot':str(self.state),'projectId':'fixture','environment':'test'}}})
  self.write(self.p/'Library/AIUI/hotupdate-build-state.json',{'baseVersion':'b','release':'c'})
  for n in g.MANDATORY+('Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs','Assets/Editor/ResourceGovernance/ResourceMoveTransaction.cs.meta','Packages/manifest.json'):
   f=self.p/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('fixture')
  self.zip=self.root/'source.zip'
  with zipfile.ZipFile(self.zip,'w') as z:
   for f in self.p.rglob('*'):
    if f.is_file():z.write(f,f.relative_to(self.p).as_posix())
  self.proof=self.root/'proof.json';self.write(self.proof,{'transactionId':'original','files':[{'path':str(self.zip),'sha256':g.digest(self.zip)}]})
  self.ledger={'identity':self.identity,'transactions':[{'id':'original','state':'delivered-pending-acceptance','steps':{'archive':{'evidence':str(self.proof),'sha256':g.digest(self.proof)}}},{'id':'publish','state':'registered','intent':'publish','buildKind':'none'}]};self.save_ledger()
  self.inv=self.root/'inventory.json';self.write(self.inv,{'project':str(self.p),'scopes':['Assets','Packages','ProjectSettings','Tools','Library/AIUI'],'excludes':[],'files':[{'path':f.relative_to(self.p).as_posix(),'sha256':g.digest(f)} for f in self.p.rglob('*') if f.is_file()]})
  self.permit={'schemaVersion':1,'approval':'fixture explicit approval','transactionId':'publish','project':str(self.p),'originTransaction':'original','archiveProofSha256':g.digest(self.proof),'archives':[{'path':str(self.zip),'sha256':g.digest(self.zip)}],'inventory':str(self.inv),'inventorySha256':g.digest(self.inv),'base':'b','release':'c','supplements':{}}
  self.permit_path=self.root/'permit.json';self.pin()
  self.mock=patch.object(g,'audit',side_effect=self.audit);self.calls=self.mock.start()
 def tearDown(self):self.mock.stop();self.tmp.cleanup()
 def write(self,p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d),encoding='utf-8')
 def save_ledger(self):self.write(self.state/'transactions.json',self.ledger)
 def pin(self):self.write(self.permit_path,self.permit);self.bound['archivedPublish']={'publish':{'path':str(self.permit_path),'sha256':g.digest(self.permit_path)}}
 def audit(self,p,b,out):
  r={'errors':[],'legacy':[],'warnings':[]};self.write(out,r);return r
 def run_gate(self,previous=None):return check_archived(g,self.p,self.bound,'publish',None,previous)
 def test_development_changes_do_not_change_candidate(self):
  self.write(Path(self.bound['sourceProject'])/'Assets/new-resource.json',{'new':True});self.run_gate();self.assertEqual(self.calls.call_count,1)
 def test_reuses_valid_report(self):
  f=self.run_gate();self.run_gate({'path':f,'sha256':g.digest(f)});self.assertEqual(self.calls.call_count,1)
 def test_changed_candidate_rejected(self):
  (self.p/g.MANDATORY[0]).write_text('tamper')
  with self.assertRaises(g.GateError):self.run_gate()
 def test_added_candidate_rejected(self):
  (self.p/'Assets/new.txt').write_text('new')
  with self.assertRaises(g.GateError):self.run_gate()
 def test_missing_dependency_rejected(self):
  (self.p/g.MANDATORY[1]).unlink()
  with self.assertRaises(g.GateError):self.run_gate()
 def test_archive_tamper_rejected(self):
  self.zip.write_bytes(b'tamper')
  with self.assertRaises(g.GateError):self.run_gate()
 def test_proof_tamper_rejected(self):
  self.proof.write_text('{}')
  with self.assertRaises(g.GateError):self.run_gate()
 def test_wrong_identity_rejected(self):
  self.bound['environment']='other'
  with self.assertRaises(g.GateError):self.run_gate()
 def test_build_intent_rejected(self):
  self.ledger['transactions'][1]['intent']='build-publish';self.save_ledger()
  with self.assertRaises(g.GateError):self.run_gate()
 def test_terminal_transaction_rejected(self):
  self.ledger['transactions'][1]['state']='delivered-pending-acceptance';self.save_ledger()
  with self.assertRaises(g.GateError):self.run_gate()
 def test_unfinished_candidate_move_rejected(self):
  self.write(self.moves/'pending/journal.json',{'project':str(self.p),'state':'moving'})
  with self.assertRaises(g.GateError):self.run_gate()
 def test_incorrect_release_rejected(self):
  self.permit['release']='other';self.pin()
  with self.assertRaises(g.GateError):self.run_gate()
 def test_inventory_tamper_rejected(self):
  self.inv.write_text('{}')
  with self.assertRaises(g.GateError):self.run_gate()
 def test_unproven_artifact_rejected(self):
  f=self.root/'wrong.bundle';f.write_text('unknown');self.permit['artifacts']=[{'path':str(f),'sha256':g.digest(f)}];self.pin()
  with self.assertRaises(g.GateError):self.run_gate()
 def test_binding_tamper_rejected(self):
  self.permit_path.write_text('{}')
  with self.assertRaises(g.GateError):self.run_gate()
 def test_unapproved_runtime_supplement_rejected(self):
  f=self.p/'Assets/new.txt';f.write_text('new');i=g.load(self.inv);i['files'].append({'path':'Assets/new.txt','sha256':g.digest(f)});self.write(self.inv,i);self.permit['inventorySha256']=g.digest(self.inv);self.permit['supplements']={'Assets/new.txt':g.digest(f)};self.pin()
  with self.assertRaises(g.GateError):self.run_gate()
 def test_errors_not_waived(self):
  self.calls.side_effect=g.GateError('strict error',2)
  with self.assertRaises(g.GateError):self.run_gate()
 def test_corrupt_report_rechecks(self):
  f=self.run_gate();e={'path':f,'sha256':g.digest(f)};r=g.load(f);Path(r['candidateReport']).write_text('{}');self.run_gate(e);self.assertEqual(self.calls.call_count,2)

if __name__=='__main__':unittest.main()
