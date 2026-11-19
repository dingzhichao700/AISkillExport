import unittest,tempfile,json,hashlib,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import release_resource_gate as gate

class TemporaryApproval(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'Project';self.p.mkdir();self.state=Path(self.tmp.name)/'state';self.state.mkdir()
        self.target=self.p/'Assets/Art/old.png';self.target.parent.mkdir(parents=True);self.target.write_bytes(b'exact historical bytes')
        self.archive=Path(self.tmp.name)/'old.zip'
        with zipfile.ZipFile(self.archive,'w') as z:z.write(self.target,'Assets/Art/old.png')
        self.item={'code':'OLD','path':'Assets/Art/old.png','guid':'abc','message':'exact violation','relatedPaths':[],'sha256':gate.digest(self.target)}
        self.permit={'status':'active','transactionId':'T','candidateProject':str(self.p),'requestMessageId':'human-request','approvalMessageId':'human-approval','archivePath':str(self.archive),'archiveSha256':gate.digest(self.archive),'runtimePatches':{},'items':[self.item]}
        self.proof=Path(self.tmp.name)/'approval.json';self.proof.write_text(json.dumps(self.permit));self.binding={'transactionExceptions':{'T':{'path':str(self.proof),'sha256':gate.digest(self.proof)}}}
        (self.p/'ProjectSettings').mkdir();(self.p/'ProjectSettings/FrameworkPlatform.json').write_text(json.dumps({'bootstrapUrl':'https://example/bootstrap.json','buildRelease':{'releaseTransaction':{'stateRoot':str(self.state),'projectId':'P','environment':'test'}}}))
        self.ledger={'identity':{'projectId':'P','environment':'test','bootstrapUrl':'https://example/bootstrap.json'},'transactions':[{'id':'T','state':'registered','buildKind':'content','intent':'build-publish','requests':[{'messageId':'human-request'}]}]};self.save_state()
    def tearDown(self):self.tmp.cleanup()
    def save_state(self):(self.state/'transactions.json').write_text(json.dumps(self.ledger))
    def test_exact_allowed_and_source_report_preserved(self):
        p=gate.transaction_exception(self.p,self.binding,'T');raw={'errors':[dict(self.item)],'legacy':[],'warnings':[]};r=gate.approve_historical(self.p,raw,p)
        self.assertEqual(len(r['approvedHistoricalErrors']),1);self.assertEqual(len(raw['errors']),1)
    def test_wrong_transaction_has_no_exception(self):self.assertIsNone(gate.transaction_exception(self.p,self.binding,'another'))
    def test_terminal_transaction_expires(self):
        for state in ('delivered-pending-acceptance','failed','cancelled','superseded'):
            self.ledger['transactions'][0]['state']=state;self.save_state()
            with self.assertRaises(gate.GateError):gate.transaction_exception(self.p,self.binding,'T')
    def test_changed_approval_rejected(self):
        self.proof.write_text('{}')
        with self.assertRaises(gate.GateError):gate.transaction_exception(self.p,self.binding,'T')
    def test_changed_historical_file_rejected(self):
        self.target.write_bytes(b'changed')
        with self.assertRaises(gate.GateError):gate.transaction_exception(self.p,self.binding,'T')
    def test_added_runtime_file_rejected(self):
        (self.target.parent/'new.png').write_bytes(b'new')
        with self.assertRaises(gate.GateError):gate.transaction_exception(self.p,self.binding,'T')
    def test_added_error_rejected(self):
        with self.assertRaises(gate.GateError):gate.approve_historical(self.p,{'errors':[self.item,{**self.item,'code':'NEW'}]},self.permit)
    def test_changed_guid_message_and_related_paths_rejected(self):
        for change in ({'guid':'other'},{'message':'new problem'},{'relatedPaths':['Assets/Art/new.png']}):
            with self.assertRaises(gate.GateError):gate.approve_historical(self.p,{'errors':[{**self.item,**change}]},self.permit)
    def test_missing_approved_error_rejected(self):
        with self.assertRaises(gate.GateError):gate.approve_historical(self.p,{'errors':[]},self.permit)
    def test_wrong_candidate_rejected(self):
        with self.assertRaises(gate.GateError):gate.transaction_exception(self.p.parent,self.binding,'T')

if __name__=='__main__':unittest.main()
