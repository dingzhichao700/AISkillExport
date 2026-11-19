"""Synthetic, offline behavior checks; never uses a game project or produces art."""
import copy, importlib.util, json, struct, tempfile, unittest, zlib
from pathlib import Path

spec=importlib.util.spec_from_file_location('audit_contract',Path(__file__).resolve().parents[1]/'scripts/audit_contract.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class ContractAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
        width,height=19,43
        data=b''.join(b'\x00'+bytes([180,120,70,255])*width for _ in range(height))
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b'')
        (self.root/'source.png').write_bytes(png);(self.root/'approval.txt').write_text('synthetic approved fixture, not a human acceptance')
        (self.root/'existing.prefab').write_text('%YAML 1.1\n')
        self.contract={'schemaVersion':1,'character':'fixture','source':{'path':'source.png','appearanceConfirmed':True,'approvalEvidence':'approval.txt','canvasPx':[width,height]},'anchor':{'confirmed':True,'approvalEvidence':'approval.txt','coordinateSpace':'continuous-bottom-left','pixels':[7,11],'normalized':[7/width,11/height]},'changeScope':'new-character','motionRequirements':['micro-motion'],'actions':[{'id':'arbitrary-action','durationMs':731,'loop':False}]}
    def run_case(self,c):
        path=self.root/'contract.json';path.write_text(json.dumps(c));before=(self.root/'source.png').read_bytes();result=m.audit(path)
        self.assertEqual(before,(self.root/'source.png').read_bytes());return result
    def test_non_sample_canvas_duration_and_route(self):
        result=self.run_case(self.contract);self.assertEqual(result['status'],'passed');self.assertEqual(result['observed']['sourceCanvasPx'],[19,43]);self.assertEqual(result['observed']['route'],'single-image')
    def test_articulation_selects_layered(self):
        c=copy.deepcopy(self.contract);c['motionRequirements']=['independent-part-motion'];self.assertEqual(self.run_case(c)['observed']['route'],'layered')
    def test_fx_only_preserves_body_even_with_layered_motion(self):
        c=copy.deepcopy(self.contract);c.update(changeScope='fx-only',existingRig='existing.prefab',motionRequirements=['occlusion-change']);r=self.run_case(c);self.assertEqual(r['status'],'passed');self.assertEqual(r['observed']['route'],'existing-rig');self.assertTrue(r['observed']['preserveBodyMotion'])
    def test_missing_appearance_blocks(self):
        c=copy.deepcopy(self.contract);c['source']['appearanceConfirmed']=False;self.assertEqual(self.run_case(c)['status'],'blocked')
    def test_wrong_anchor_blocks(self):
        c=copy.deepcopy(self.contract);c['anchor']['normalized']=[.5,.5];self.assertEqual(self.run_case(c)['status'],'blocked')
    def test_top_left_conversion(self):
        c=copy.deepcopy(self.contract);c['anchor'].update(coordinateSpace='continuous-top-left',pixels=[7,32]);self.assertEqual(self.run_case(c)['status'],'passed')
    def test_incremental_without_existing_rig_blocks(self):
        c=copy.deepcopy(self.contract);c['changeScope']='timing-only';self.assertEqual(self.run_case(c)['status'],'blocked')
    def test_hash_change_blocks(self):
        c=copy.deepcopy(self.contract);c['source']['sha256']='incorrect';self.assertEqual(self.run_case(c)['status'],'blocked')
    def test_failed_historical_runtime_blocks(self):
        c=copy.deepcopy(self.contract);(self.root/'result.json').write_text('{"status":"failed","error":"fixture error"}');c['evidence']=[{'path':'result.json','expectedStatus':'passed','requireEmptyError':True}];self.assertEqual(self.run_case(c)['status'],'blocked')
    def test_arbitrary_bone_count_weights_and_cycle(self):
        c=copy.deepcopy(self.contract);c['rigSnapshot']='rig.json'
        rig={'bones':[{'parent':-1},{'parent':0},{'parent':1}],'vertices':[{'position':[1,2,0],'weights':[{'bone':0,'weight':.2},{'bone':2,'weight':.8}]}]}
        (self.root/'rig.json').write_text(json.dumps(rig));self.assertEqual(self.run_case(c)['status'],'passed')
        rig['vertices'][0]['weights'][1]['weight']=.7;(self.root/'rig.json').write_text(json.dumps(rig));self.assertEqual(self.run_case(c)['status'],'blocked')
        rig['vertices'][0]['weights'][1]['weight']=.8;rig['bones'][0]['parent']=2;(self.root/'rig.json').write_text(json.dumps(rig));self.assertEqual(self.run_case(c)['status'],'blocked')
    def test_serialized_parameter_mismatch_blocks(self):
        c=copy.deepcopy(self.contract);(self.root/'existing.prefab').write_text('%YAML 1.1\n--- !u!114 &1\nMonoBehaviour:\n  durationSeconds: 0.731\n')
        c['prefabChecks']=[{'path':'existing.prefab','fields':{'durationSeconds':.731}}];self.assertEqual(self.run_case(c)['status'],'passed')
        c['prefabChecks'][0]['fields']['durationSeconds']=1.2;self.assertEqual(self.run_case(c)['status'],'blocked')

if __name__=='__main__':unittest.main()
