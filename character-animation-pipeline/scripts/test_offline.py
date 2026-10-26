"""No network or paid generations. Run directly with the skill's Python dependencies."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
import animation
import video_api


class WorkflowTests(unittest.TestCase):
    def test_sampling_and_boundaries(self):
        self.assertEqual(animation.sample_indices(28,46,8),[27,33,39,44,50,56,61,67])
        self.assertEqual(animation.sample_indices(1,90,8,False)[-1],89)
        with self.assertRaises(ValueError):animation.sample_indices(1,3,8)
        with self.assertRaises(ValueError):animation.validate_range(0,10,90)

    def test_chroma_preserves_enclosed_matching_costume(self):
        im=Image.new('RGB',(96,128),'#ff00ff');d=ImageDraw.Draw(im)
        d.rectangle((22,20,74,100),fill='#504020');d.rectangle((40,40,50,50),fill='#ff00ff')
        rgba=animation.matte(np.array(im)[:,:,::-1].copy(),'chroma')
        a=np.array(rgba)
        self.assertEqual(a[0,0,3],0);self.assertEqual(a[45,45,3],255)
        profile={'target_body_height':100,'canvas':[80,116],'pivot':[40,108],
                 'directions':{'down-right':{'body_height_fraction':81/128,'ground_anchor':[.5,101/128]}}}
        out,_=animation.place(rgba,profile,'down-right')
        self.assertEqual(out.size,(80,116))
        profile['canvas']=[20,30];profile['pivot']=[10,28]
        with self.assertRaises(ValueError):animation.place(rgba,profile,'down-right')

    def test_unknown_submission_blocks_repurchase_and_no_secret_saved(self):
        with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'TEST_VIDEO_KEY':'offline-secret-never-log'}):
            root=Path(td);Image.new('RGB',(240,240),'gray').save(root/'ref.png')
            cfg={'provider':'bailian','region':'beijing','key_env':'TEST_VIDEO_KEY','model':'wan2.6-i2v-flash',
                 'reference':'ref.png','prompt':'Idle','parameters':{'duration':3,'resolution':'720P'}}
            animation.write(root/'request.json',cfg)
            with patch.object(video_api,'request_json',side_effect=RuntimeError('simulated timeout')) as req:
                with self.assertRaises(RuntimeError):video_api.submit(root/'request.json',root/'run')
                with self.assertRaises(FileExistsError):video_api.submit(root/'request.json',root/'run')
                self.assertEqual(req.call_count,1)
            state=(root/'run/state.json').read_text()
            self.assertNotIn('offline-secret-never-log',state);self.assertNotIn('base64',state)

    def test_poll_resume_uses_same_task(self):
        with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'TEST_VIDEO_KEY':'offline-secret'}):
            root=Path(td);video_api.save(root/'state.json',{'status':'submitted','task_id':'task-one',
                'config':{'region':'beijing','key_env':'TEST_VIDEO_KEY'}})
            with patch.object(video_api,'request_json',side_effect=[RuntimeError('network'),{'output':{'task_status':'RUNNING'}}]) as req:
                with self.assertRaises(RuntimeError):video_api.poll(root)
                result=video_api.poll(root)
                self.assertEqual(result['task_id'],'task-one')
                self.assertTrue(all(call.args[0].endswith('/tasks/task-one') for call in req.call_args_list))
                self.assertTrue(all(len(call.args)==2 for call in req.call_args_list))

    def test_video_to_eight_transparent_frames(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);im=Image.new('RGB',(96,128),'#ff00ff')
            ImageDraw.Draw(im).rectangle((22,20,74,100),fill='#504020');im.save(root/'ref.png')
            subprocess.run(['ffmpeg','-v','error','-loop','1','-i',str(root/'ref.png'),'-t','1','-r','30',
                '-c:v','libx264','-pix_fmt','yuv420p',str(root/'source.mp4')],check=True)
            profile={'character':'offline','version':1,'target_body_height':100,'canvas':[80,116],'pivot':[40,108],
                'directions':{'down-right':{'body_height_fraction':81/128,'ground_anchor':[.5,101/128]}}}
            animation.write(root/'geometry.json',profile)
            a=argparse.Namespace(video=str(root/'source.mp4'),start=1,length=30,count=8,one_shot=False,
                direction='down-right',profile=str(root/'geometry.json'),out=str(root/'out'),matte='chroma',
                masks_dir=None,key='FF00FF',tolerance=65,action='idle',evidence_out=str(root/'evidence'),pack_scale=50)
            animation.export(a)
            self.assertEqual(sorted(p.name for p in (root/'out').iterdir()),
                [f'{i:03d}.png' for i in range(1,9)]+['animation.json'])
            config=animation.read(root/'out/animation.json')
            self.assertEqual(set(config),{'duration','scale','pivot'})
            self.assertEqual(config['duration'],1000)
            self.assertEqual(config['scale'],50)
            self.assertAlmostEqual(config['pivot']['x'],.5)
            self.assertAlmostEqual(config['pivot']['y'],1-108/116)
            report=animation.read(root/'evidence/provenance.json')
            self.assertTrue((root/'evidence/overview.png').is_file())
            self.assertAlmostEqual(sum(f['duration_ms'] for f in report['frames']),1000)
            self.assertEqual(report['geometry'],profile)
            for path in (root/'out').glob('*.png'):
                image=Image.open(path);alpha=np.array(image)[:,:,3]
                self.assertEqual(image.size,(80,116))  # pack_scale is metadata, not applied twice.
                self.assertEqual(image.mode,'RGBA');self.assertFalse(alpha[0].any())
            with self.assertRaises(ValueError):animation.export(a)
            animation.cut(root/'source.mp4',1,20,root/'cycle.mp4',root/'preview.mp4',3)
            self.assertEqual(animation.probe(root/'preview.mp4')['count'],60)


if __name__=='__main__':unittest.main()
