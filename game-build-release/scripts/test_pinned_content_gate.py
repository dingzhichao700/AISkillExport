import unittest,json
from pathlib import Path
from test_archived_release_gate import Archived
from pinned_content_gate import bind_content
import release_resource_gate as g
from release_transaction import scoped_files

class Content(unittest.TestCase):
 write=Archived.write
 def setUp(self):
  self.fixture=Archived();self.fixture.setUp();self.__dict__.update({k:v for k,v in self.fixture.__dict__.items() if k not in ('_testMethodName','_testMethodDoc','_outcome')})
  f=self.p/'Assets/Scripts/Window.cs';f.parent.mkdir();f.write_text('opening=1.2')
  self.scope=['Assets','Tools','Packages','ProjectSettings'];files=[{'path':n,'sha256':g.digest(self.p/n)} for n in sorted(scoped_files(self.p,self.scope,[]))]
  self.original=self.root/'original.json';self.write(self.original,{'project':'original','scopes':self.scope,'excludes':[],'files':files})
  before=g.digest(f);f.write_text('opening=3');after=g.digest(f)
  self.manifest=self.root/'content.json';self.write(self.manifest,{'project':str(self.p),'scopes':self.scope,'excludes':[],'files':[{'path':r['path'],'sha256':after if r['path']=='Assets/Scripts/Window.cs' else r['sha256']} for r in files]})
  proof=g.load(self.proof);proof['files'].append({'path':str(self.original),'sha256':g.digest(self.original)});self.write(self.proof,proof)
  self.ledger['transactions'][0]['steps']['archive']['sha256']=g.digest(self.proof);self.ledger['transactions'][1].update(intent='build-publish',buildKind='content');self.write(self.state/'transactions.json',self.ledger)
  self.pin={'approval':'explicit fixture approval','transactionId':'publish','project':str(self.p),'originTransaction':'original','archiveProofSha256':g.digest(self.proof),'originalInput':str(self.original),'inputManifest':str(self.manifest),'inputSha256':g.digest(self.manifest),'patches':{'Assets/Scripts/Window.cs':{'before':before,'after':after}},'protected':{},'base':'b'}
  self.pinpath=self.root/'content-pin.json';self.save_pin()
 def save_pin(self):self.write(self.pinpath,self.pin);self.bound['pinnedContent']={'publish':{'path':str(self.pinpath),'sha256':g.digest(self.pinpath)}}
 def tearDown(self):self.fixture.tearDown()
 def check(self):return bind_content(g,self.p,self.bound,'publish',self.manifest)
 def test_exact_patch_passes(self):self.assertEqual(self.check()['sourceProject'],str(self.p))
 def test_development_change_does_not_mix(self):self.write(Path(self.bound['sourceProject'])/'Assets/new.json',{});self.check()
 def test_patch_changed_rejected(self):
  (self.p/'Assets/Scripts/Window.cs').write_text('opening=4')
  with self.assertRaises(ValueError):self.check()
 def test_new_resource_rejected(self):
  (self.p/'Assets/new.txt').write_text('new')
  with self.assertRaises(ValueError):self.check()
 def test_scope_expansion_rejected(self):
  m=g.load(self.manifest);m['scopes'].append('Other');self.write(self.manifest,m);self.pin['inputSha256']=g.digest(self.manifest);self.save_pin()
  with self.assertRaises(ValueError):self.check()
 def test_wrong_project_rejected(self):
  self.pin['project']=str(self.root);self.save_pin()
  with self.assertRaises(ValueError):self.check()
 def test_base_changed_rejected(self):
  self.write(self.p/'Library/AIUI/hotupdate-build-state.json',{'baseVersion':'other'})
  with self.assertRaises(ValueError):self.check()
 def test_protected_changed_rejected(self):
  self.pin['protected']={'Packages/manifest.json':'0'*64};self.save_pin()
  with self.assertRaises(ValueError):self.check()
 def test_publish_only_rejected(self):
  self.ledger['transactions'][1].update(intent='publish',buildKind='none');self.write(self.state/'transactions.json',self.ledger)
  with self.assertRaises(ValueError):self.check()
 def test_archive_proof_changed_rejected(self):
  self.proof.write_text('{}')
  with self.assertRaises(ValueError):self.check()
 def test_unfinished_candidate_rejected(self):
  self.write(self.moves/'task/journal.json',{'project':str(self.p),'state':'moving'})
  with self.assertRaises(ValueError):self.check()
 def test_unfinished_source_rejected(self):
  self.write(self.moves/'task/journal.json',{'project':self.bound['sourceProject'],'state':'moving'})
  with self.assertRaises(ValueError):self.check()

if __name__=='__main__':unittest.main()
